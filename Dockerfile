FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# --- dev stage (hot-reload, includes dev deps) ---
FROM base AS dev
COPY pyproject.toml .
COPY src/ src/
RUN pip install -e ".[dev]"
COPY alembic.ini .
CMD ["uvicorn", "changelens.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- builder stage ---
FROM base AS builder
COPY pyproject.toml .
COPY src/ src/
RUN pip install build && python -m build --wheel --outdir /dist

# --- runtime stage (production, non-root) ---
FROM base AS runtime
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder /dist/*.whl /tmp/
RUN pip install /tmp/*.whl && rm /tmp/*.whl
COPY --chown=app:app alembic.ini .
USER app
EXPOSE 8000
CMD ["uvicorn", "changelens.main:app", "--host", "0.0.0.0", "--port", "8000"]
