# AgentForge Production Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 使用国内镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 使用国内 pip 镜像源
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple --target=/build/deps -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim as production

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

COPY --from=builder /build/deps /usr/local/lib/python3.12/site-packages

COPY agentforge ./agentforge
COPY integrations ./integrations
COPY run.py .

RUN mkdir -p logs data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "integrations.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
