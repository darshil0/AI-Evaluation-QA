# Multi-stage Dockerfile
ARG PYTHON_VERSION=3.14
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py README.md requirements.txt /app/
COPY evaluation /app/evaluation
COPY config /app/config
COPY scripts /app/scripts
COPY main.py /app/main.py
COPY __init__.py /app/__init__.py

RUN pip install --no-cache-dir wheel && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -e .

# Final stage
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

COPY --from=builder /app/wheels /app/wheels
COPY . .

# Install packages from wheels
RUN pip install --no-cache-dir /app/wheels/*.whl && \
    mkdir -p logs && \
    touch logs/evaluation.log

# Environment variables
ENV EVAL_LOG_FILE=logs/evaluation.log

ENTRYPOINT ["ai-eval"]
