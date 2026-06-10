FROM python:3.11-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./

RUN uv pip install --system -r pyproject.toml 2>/dev/null || true

ENV PYTHONPATH="/app/src"

EXPOSE 8000
