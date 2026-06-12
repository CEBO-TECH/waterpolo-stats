FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY src/ src/
COPY alembic/ alembic/
COPY scripts/ scripts/
COPY alembic.ini .

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["sh", "-c", "python scripts/ensure_db.py && alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
