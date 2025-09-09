FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first for better layer caching
COPY Platform/requirements-dev.txt /app/Platform/requirements-dev.txt
RUN pip install -r /app/Platform/requirements-dev.txt

# Copy project
COPY . /app

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "Platform.src.main:app", "--host", "0.0.0.0", "--port", "8000"]

