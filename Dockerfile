FROM debian:bookworm-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=auto

FROM base AS backend

COPY backend/pyproject.toml backend/uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY backend/ .

COPY artifacts/flight_price_model.joblib /app/artifacts/flight_price_model.joblib

CMD ["uv", "run", "uvicorn", "main:app"]


FROM base AS frontend

COPY frontend/pyproject.toml frontend/uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY frontend/ .

CMD ["uv", "run", "streamlit", "run", "main.py"]