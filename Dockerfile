FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app


FROM base AS builder

RUN python -m venv /opt/venv

COPY pyproject.toml .
COPY app ./app

RUN pip install --no-cache-dir .


FROM base AS runtime

COPY --from=builder /opt/venv /opt/venv

RUN useradd --create-home --uid 10001 appuser

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
    
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
