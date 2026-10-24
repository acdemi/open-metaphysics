# OpenMetaphysics API image (Python 3.11; sxtwl cp311 manylinux wheel available).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY knowledge ./knowledge

RUN pip install --no-cache-dir ".[persist,rag]"

EXPOSE 8000

CMD ["uvicorn", "openmetaphysics.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
