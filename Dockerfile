# OpenMetaphysics API image (Python 3.11; sxtwl cp311 manylinux wheel available).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY knowledge ./knowledge
COPY reference ./reference

RUN pip install --no-cache-dir ".[persist,rag]"

# Runtime data lives outside the installed package. Point the resolver at the
# copied trees instead of relying on a repository layout that doesn't exist in
# the image (the old code used Path.parents[3] and silently found nothing).
ENV OM_KNOWLEDGE_DIR=/app/knowledge \
    OM_REFERENCE_DIR=/app/reference

EXPOSE 8000

# /health + /knowledge/corpora + Explain (offline deterministic fallback) smoke.
# A broken knowledge path turns the container unhealthy instead of silently
# serving Explain responses without citations.
HEALTHCHECK --interval=30s --timeout=20s --start-period=20s --retries=3 \
    CMD ["python", "-m", "openmetaphysics.healthcheck"]

CMD ["uvicorn", "openmetaphysics.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
