FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# 1) Bring in Ubuntu’s archive signing keys
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ubuntu-keyring \
      ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 2) Now ports.ubuntu.com will be trusted
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      curl \
      python3 python3-pip python3-venv \
      default-jdk build-essential nodejs npm \
 && rm -rf /var/lib/apt/lists/*

# … copy code, install pytest …

WORKDIR /app
COPY sandbox.py .
COPY test_sandbox.py .

RUN python3 -m venv venv \
 && . venv/bin/activate \
 && pip install --no-cache-dir pytest pytest-asyncio psutil

ENV PATH="/app/venv/bin:$PATH"
CMD ["pytest", "-q", "test_sandbox.py"]
