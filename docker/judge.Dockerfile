FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install toolchains to support multiple languages (optional but useful)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      default-jdk \
      nodejs npm \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Reuse platform requirements (judge imports Platform modules)
COPY Platform/requirements-dev.txt /app/Platform/requirements-dev.txt
RUN pip install -r /app/Platform/requirements-dev.txt

# Copy project
COPY . /app

ENV PYTHONPATH=/app

CMD ["python", "judge_service/main.py"]

