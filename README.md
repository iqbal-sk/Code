<div align="center">

# Code Platform — FastAPI + Judge (CSES-powered)

Practice algorithms with a smooth submit-and-run flow for the excellent CSES problem set — with your own backend, live status updates, and a sandboxed judge.

</div>

## Why This Exists

- CSES has a fantastic set of problems, but no built-in “code here and run” experience.
- I wanted the smoothest practice loop: browse problems, code in my editor, click submit, watch live verdicts, and inspect results — all locally hosted.
- This repo is the backend + judge that powers that experience. The frontend lives separately:
  - Frontend repo: https://github.com/iqbal-sk/Code-Frontrend

## What It Offers

- FastAPI backend with clean REST APIs and JWT auth (login/register/me).
- Problem library sourced from CSES (title, description, constraints, images, sample tests).
- Hidden/public test cases imported via a scraper (requires your CSES PHPSESSID).
- Submissions in multiple languages (Python, C++, Java, JavaScript) with resource limits.
- Asynchronous judge worker, sandboxed execution, and SSE live status updates.
- MongoDB persistence and Redis queue/pubsub.
- Single-command Docker Compose to run everything reproducibly.

## High-Level Architecture

- `Platform` (FastAPI):
  - Endpoints under `/api/v1/...` for users, problems, test-cases, submissions.
  - Streams submission updates via Server-Sent Events: `/api/v1/submissions/{id}/events`.
  - Uses MongoDB for storage, Redis for queueing and pubsub.
- `judge_service` (Worker):
  - Listens to Redis queue, executes code in a sandbox, updates Mongo, and publishes status.
- `scraper` (One-shot job):
  - Pulls problems from CSES and downloads testcases; stores large inputs/outputs as local files.
  - Requires your CSES `PHPSESSID` cookie.

## Tech Stack

- FastAPI, Uvicorn, Pydantic (v2), ODMantic (Mongo), Motor, Redis (asyncio), SSE
- Python sandbox for running code; installs `g++`, `default-jdk`, `node` in the judge container
- Docker Compose for orchestration

## Quick Start (Docker Compose)

Prerequisites: Docker and Docker Compose.

1) Clone and enter the repo

```bash
git clone https://github.com/iqbal-sk/CodeForge.git
cd CodeForge
```

2) Start core services (Mongo, Redis, API, Judge)

```bash
docker compose up -d --build mongo redis platform judge
```

3) Seed problems and testcases (scrape 5 problems)

You need your CSES PHPSESSID cookie value (sign in to https://cses.fi and copy `PHPSESSID`).

```bash
export CSES_SESSION_ID='paste_your_cookie_here'
docker compose run --rm scraper
```

4) Open the API

```text
http://localhost:8000
```

5) Run the frontend

Clone and run the UI from: https://github.com/iqbal-sk/Code-Frontrend

Configure its API base to `http://localhost:8000` and use the normal flow:
- Register: `POST /api/v1/users/register`
- Login: `POST /api/v1/users/login` → get JWT
- Browse Problems: `GET /api/v1/problems`
- Submit Code: `POST /api/v1/submission`
- Live Status: connect to `GET /api/v1/submissions/{id}/events` (SSE)

## Configuration Notes

- Container env is the source of truth when running with Docker Compose. The `.env` files in the repo are intended for local (non-container) runs and are overridden by Compose.
- By default, Mongo is exposed on host port `27017`. If you prefer `27018` on your host, change the mapping in `docker-compose.yml`:

```yaml
services:
  mongo:
    ports:
      - "27018:27017"  # host:container
```

- The scraper writes large test files into a shared volume mounted at `/data/testcases` in Platform, Judge, and Scraper. This ensures file paths saved in Mongo are valid in all containers.
- JWT secret defaults are for development only. The frontend must login against the currently running backend to get a valid token.

## API Overview (Selected)

- Auth
  - `POST /api/v1/users/register` — create account
  - `POST /api/v1/users/login` — returns `{ access_token, token_type }`
  - `GET /api/v1/users/me` — profile (requires `Authorization: Bearer <token>`)

- Problems & Test Cases
  - `GET /api/v1/problems` — list/browse
  - `GET /api/v1/problems/{problemId}` — details
  - `GET /api/v1/problems/{problemId}/test-cases` — full set (hidden included with `?includeHidden=true`)
  - `GET /api/v1/problems/{problemId}/test-cases/public` — only public

- Submissions
  - `POST /api/v1/submission` — enqueue a submission
  - `GET /api/v1/submissions/{submissionId}` — submission details
  - `GET /api/v1/submissions/{submissionId}/events` — live SSE updates (status/results)

## Development

- Prefer Docker Compose for consistency. It builds images that include all required toolchains for the judge.
- If you want to run without Docker, use the Python requirements in `Platform/requirements-dev.txt`, start Mongo and Redis locally, and run `uvicorn Platform.src.main:app`. The judge can be started with `PYTHONPATH=$(pwd) python judge_service/main.py`.

## Security & Operational Notes

- Scraper requires your personal CSES `PHPSESSID`. Treat it like a secret; do not commit it.
- Resource limits are strongest on Linux; on macOS some memory limits are relaxed.
- Only use the provided development JWT secret in local setups. Rotate/change for any shared or hosted environment.

## Roadmap Ideas

- Containerized “execution service” isolation profiles.
- More languages and tooling cache for faster builds.
- Enhanced problem browsing (search, tags, difficulty).
- Submission history insights and editor integrations.

## Acknowledgements

- CSES Problem Set — https://cses.fi
- FastAPI, Pydantic, Uvicorn, ODMantic, Redis

---

Frontend repo again for convenience: https://github.com/iqbal-sk/Code-Frontrend
