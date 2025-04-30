import contextlib
import asyncio
import tempfile
import shutil
import os
import resource
import signal
import sys
import time
from typing import Dict, Any
import logging

# Exit/status conventions
EX_DATAERR = 65  # compilation error
TIMEOUT_EXIT = 124  # manual timeout exit code
OOM_SIGNAL = signal.SIGKILL  # memory kill

_SANDBOX_CFG = {
    "cpp": ("g++ Main.cpp -o Main".split(), ["./Main"]),
    "java": ("javac Main.java".split(), ["java", "-cp", ".", "Main"]),
    "python": (None, ["python3", "Main.py"]),
    "javascript": (None, ["node", "Main.js"]),
}

GRACE_MEMORY_BYTES = 15 * 1024 * 1024  # 15MB

logger = logging.getLogger(__name__)

async def run_in_sandbox(
    language: str,
    source_code: str,
    stdin: str = "",
    timeout_sec: float = 2,
    memory_bytes: int = 12 * 1024 * 1024
) -> Dict[str, Any]:
    response: Dict[str, Any] = {
        "verdict": None,
        "stdout": "",
        "stderr": "",
        "compiler_msg": "",
        "runtime_ms": 0.0,
        "memory_bytes": 0,
    }

    logger.info("Starting sandbox for language=%s, timeout=%.2fs, memory_limit=%d bytes", language, timeout_sec, memory_bytes)

    memory_bytes += GRACE_MEMORY_BYTES
    cfg = _SANDBOX_CFG.get(language.lower())
    if not cfg:
        logger.error("Unsupported language requested: %s", language)
        response["verdict"] = "UnsupportedLanguage"
        return response

    compile_cmd, default_run_cmd = cfg
    workdir = tempfile.mkdtemp(prefix="sandbox_")
    logger.debug("Created workspace directory: %s", workdir)

    try:
        # Write source file
        ext_map = {"cpp": ".cpp", "java": ".java", "python": ".py", "javascript": ".js"}
        ext = ext_map.get(language.lower(), "")
        src_path = os.path.join(workdir, f"Main{ext}")
        with open(src_path, "w") as src_file:
            src_file.write(source_code)
        logger.debug("Source code written to %s", src_path)

        # Compile if needed
        if compile_cmd:
            logger.info("Compiling with command: %s", " ".join(compile_cmd))
            proc = await asyncio.create_subprocess_exec(
                *compile_cmd,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            out, err = await proc.communicate()
            if proc.returncode != 0:
                compiler_msg = err.decode(errors="ignore")
                logger.error("Compilation failed (exit_code=%d): %s", proc.returncode, compiler_msg)
                response.update({
                    "verdict": "CompilationError",
                    "compiler_msg": compiler_msg,
                })
                return response
            logger.info("Compilation succeeded for %s", language)

        # Prepare run command and resource limits
        run_cmd = list(default_run_cmd)
        preexec_fn = None
        if language.lower() == "java":
            mem_mb = memory_bytes // (1024 * 1024)
            run_cmd = ["java", f"-Xmx{mem_mb}m", "-cp", ".", "Main"]
            logger.debug("Java memory limit set to %dm", mem_mb)
        else:
            if sys.platform.startswith("linux"):
                def _limit_as():
                    try:
                        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
                        logger.debug("Address space limit set to %d bytes", memory_bytes)
                    except Exception as e:
                        logger.warning("Failed to set AS limit: %s", e)
                preexec_fn = _limit_as
                logger.debug("AS limit enforcement enabled for Linux")
            else:
                logger.warning("Skipping AS limits on non-Linux platform: %s", sys.platform)

        # Monitor memory usage
        async def monitor_process(process, limit):
            try:
                import psutil
                peak = 0
                proc_ps = psutil.Process(process.pid)
                logger.debug("Started memory monitoring for PID %d", process.pid)
                while process.returncode is None:
                    usage = proc_ps.memory_info().rss
                    peak = max(peak, usage)
                    if usage > limit:
                        process.kill()
                        logger.warning("Memory limit exceeded: used=%d, limit=%d", usage, limit)
                        return True, peak
                    await asyncio.sleep(0.05)
                return False, peak
            except ImportError:
                logger.warning("psutil not available, memory monitoring disabled")
                return False, 0
            except Exception as e:
                logger.error("Error during memory monitoring: %s", e)
                return False, peak

        # Execute the program
        logger.info("Executing command: %s", " ".join(run_cmd))
        start = time.perf_counter()
        proc = await asyncio.create_subprocess_exec(
            *run_cmd,
            cwd=workdir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=preexec_fn
        )
        monitor_task = asyncio.create_task(monitor_process(proc, memory_bytes))

        try:
            out, err = await asyncio.wait_for(
                proc.communicate(stdin.encode()),
                timeout=timeout_sec
            )
            duration = (time.perf_counter() - start) * 1000
            mem_killed, peak_usage = await monitor_task

            if mem_killed:
                logger.error("Process killed due to memory limit")
                response.update({
                    "verdict": "MemoryLimitExceeded",
                    "stderr": err.decode(errors="ignore"),
                    "runtime_ms": duration,
                    "memory_bytes": peak_usage,
                })
                return response
        except asyncio.TimeoutError:
            monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await monitor_task
            proc.kill()
            duration = (time.perf_counter() - start) * 1000
            logger.error("Process exceeded time limit of %.2fs", timeout_sec)
            response.update({
                "verdict": "TimeLimitExceeded",
                "runtime_ms": duration,
                "memory_bytes": 0,
            })
            return response

        stderr_decoded = err.decode(errors="ignore")
        _, peak_usage = await monitor_task

        # Detect memory-related errors in stderr
        memory_patterns = [
            "MemoryError", "std::bad_alloc", "OutOfMemoryError",
            "out of memory", "malloc failed", "mmap failed"
        ]
        if any(pat in stderr_decoded for pat in memory_patterns):
            logger.error("Memory-related error detected in stderr: %s", stderr_decoded)
            response.update({
                "verdict": "MemoryLimitExceeded",
                "stderr": stderr_decoded,
                "runtime_ms": duration,
                "memory_bytes": peak_usage,
            })
            return response

        # Check exit code
        if proc.returncode != 0:
            logger.error("Runtime error (exit_code=%d): %s", proc.returncode, stderr_decoded)
            response.update({
                "verdict": "RuntimeError",
                "stderr": stderr_decoded,
                "runtime_ms": duration,
                "memory_bytes": peak_usage,
            })
            return response

        # Success
        stdout_decoded = out.decode(errors="ignore").strip()
        logger.info("Execution succeeded, output length=%d", len(stdout_decoded))
        response.update({
            "verdict": "OK",
            "stdout": stdout_decoded,
            "runtime_ms": duration,
            "memory_bytes": peak_usage,
        })
        return response

    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        logger.debug("Cleaned up workspace directory: %s", workdir)


if __name__ == "__main__":

    async def _demo():
        code_java = 'public class Main { public static void main(String[] args){ System.out.print("hello"); }}'
        res = await run_in_sandbox("java", code_java)
        print("Demo result:", res)
    asyncio.run(_demo())
