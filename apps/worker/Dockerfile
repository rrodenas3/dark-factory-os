FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY apps /app/apps
COPY packages/py /app/packages/py
COPY infra/migrations /app/infra/migrations

RUN pip install --no-cache-dir uv \
    && uv sync --package dark-factory-worker --no-dev --no-install-project --frozen

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/apps/worker/src
ENV DFOS_MIGRATIONS_DIR=/app/infra/migrations

CMD ["python", "-m", "dark_factory_worker.main"]
