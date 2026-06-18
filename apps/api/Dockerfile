FROM python:3.12-slim

WORKDIR /app

COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml
COPY apps/api/src /app/apps/api/src

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic

ENV PYTHONPATH=/app/apps/api/src

CMD ["uvicorn", "dark_factory_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
