import asyncio
import shutil
import sys
import pytest

from sandbox import run_in_sandbox

# Helpers for tool availability and platform checks
has_gpp    = shutil.which("g++")    is not None
has_javac  = shutil.which("javac")  is not None
has_java   = shutil.which("java")   is not None
has_node   = shutil.which("node")   is not None
has_python = shutil.which("python3") is not None
is_linux   = sys.platform.startswith("linux")

# Skip tests that rely on resource limits when not on Linux
skip_non_linux = pytest.mark.skipif(
    not is_linux,
    reason="Resource limits only enforced on Linux"
)

@pytest.mark.asyncio
async def test_unsupported_language():
    res = await run_in_sandbox(
        "ruby", "puts 'hello'", "",
        timeout_sec=1, memory_bytes=16 * 1024 * 1024
    )
    assert res["verdict"] == "UnsupportedLanguage"


# ─── Python Tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_python, reason="python3 not on PATH")
async def test_python_success_and_input():
    code = "s = input()\nprint(s[::-1])"
    res = await run_in_sandbox(
        "python", code, "stressed",
        timeout_sec=1, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "OK"
    assert res["stdout"] == "desserts"
    # must report timing and peak memory
    assert "runtime_ms" in res and isinstance(res["runtime_ms"], float)
    assert "memory_bytes" in res and isinstance(res["memory_bytes"], int)

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_python, reason="python3 not on PATH")
async def test_python_timeout():
    code = "while True: pass"
    res = await run_in_sandbox(
        "python", code, "",
        timeout_sec=0.5, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "TimeLimitExceeded"
    # on timeout we zero out memory_bytes
    assert isinstance(res["runtime_ms"], float)
    assert res["memory_bytes"] == 0

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_python, reason="python3 not on PATH")
async def test_python_runtime_error():
    code = "print(1/0)"
    res = await run_in_sandbox(
        "python", code, "",
        timeout_sec=1, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "RuntimeError"
    # stderr should show the Python exception
    assert "ZeroDivisionError" in res.get("stderr", "")
    assert isinstance(res["runtime_ms"], float)
    assert isinstance(res["memory_bytes"], int)

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_python, reason="python3 not on PATH")
async def test_python_memory_limit():
    code = "a = ' ' * (1024 * 1024 * 200)"  # 200 MB
    res = await run_in_sandbox(
        "python", code, "",
        timeout_sec=2, memory_bytes=2 * 1024 * 1024  # 2 MB
    )
    assert res["verdict"] == "MemoryLimitExceeded"
    # peak memory should be reported
    assert isinstance(res["runtime_ms"], float)
    assert isinstance(res["memory_bytes"], int)


# ─── C++ Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_gpp, reason="g++ not on PATH")
async def test_cpp_success():
    code = r'''
    #include <iostream>
    int main() {
        std::cout << "42";
        return 0;
    }
    '''
    res = await run_in_sandbox(
        "cpp", code, "",
        timeout_sec=2, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "OK"
    assert res["stdout"] == "42"
    assert isinstance(res["runtime_ms"], float)
    assert isinstance(res["memory_bytes"], int)

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_gpp, reason="g++ not on PATH")
async def test_cpp_compile_error():
    code = "int main() { undeclared_var = 1; }"
    res = await run_in_sandbox(
        "cpp", code, "",
        timeout_sec=2, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "CompilationError"
    # compile errors report compiler_msg and zeroed stats
    assert "compiler_msg" in res
    assert res["runtime_ms"] == 0
    assert res["memory_bytes"] == 0

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_gpp, reason="g++ not on PATH")
async def test_cpp_runtime_error():
    code = r'''
    #include <iostream>
    int main() {
        int *p = nullptr;
        *p = 1;
        return 0;
    }
    '''
    res = await run_in_sandbox(
        "cpp", code, "",
        timeout_sec=2, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "RuntimeError"
    assert isinstance(res["stderr"], str)
    assert isinstance(res["runtime_ms"], float)
    assert isinstance(res["memory_bytes"], int)

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_gpp, reason="g++ not on PATH")
async def test_cpp_memory_limit():
    code = r'''
    #include <vector>
    int main() {
        std::vector<int> v(100000000);
        return 0;
    }
    '''
    res = await run_in_sandbox(
        "cpp", code, "",
        timeout_sec=2, memory_bytes=2 * 1024 * 1024  # 2 MB
    )
    assert res["verdict"] == "MemoryLimitExceeded"
    assert isinstance(res["runtime_ms"], float)
    assert isinstance(res["memory_bytes"], int)


# ─── Java Tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not (has_javac and has_java), reason="javac/java not on PATH")
async def test_java_success():
    code = """
    public class Main {
      public static void main(String[] args) {
        System.out.print("hello");
      }
    }
    """
    res = await run_in_sandbox(
        "java", code, "",
        timeout_sec=2, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "OK"
    assert res["stdout"] == "hello"
    assert isinstance(res["runtime_ms"], float)
    assert isinstance(res["memory_bytes"], int)

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not (has_javac and has_java), reason="javac/java not on PATH")
async def test_java_compile_error():
    code = """
    public class Main {
      public static void main(String[] args) {
        System.out.print("oops")
      }
    }
    """
    res = await run_in_sandbox(
        "java", code, "",
        timeout_sec=2, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "CompilationError"
    assert "compiler_msg" in res
    assert res["runtime_ms"] == 0
    assert res["memory_bytes"] == 0


# ─── JavaScript Tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_node, reason="node not on PATH")
async def test_js_success():
    code = "let input='X'; console.log(input);"
    res = await run_in_sandbox(
        "javascript", code, "",
        timeout_sec=2, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "OK"
    assert res["stdout"].strip() == "X"
    assert isinstance(res["runtime_ms"], float)
    assert isinstance(res["memory_bytes"], int)

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_node, reason="node not on PATH")
async def test_js_syntax_error():
    code = "console.log('missing quote);"
    res = await run_in_sandbox(
        "javascript", code, "",
        timeout_sec=2, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "RuntimeError"
    assert isinstance(res.get("stderr", ""), str)

@pytest.mark.asyncio
@skip_non_linux
@pytest.mark.skipif(not has_node, reason="node not on PATH")
async def test_js_runtime_exception():
    code = "throw new Error('fail');"
    res = await run_in_sandbox(
        "javascript", code, "",
        timeout_sec=2, memory_bytes=1 * 1024 * 1024 * 1024
    )
    assert res["verdict"] == "RuntimeError"
    assert "error: fail" in res.get("stderr", "").lower()
