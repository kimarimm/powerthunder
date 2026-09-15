# syntax=docker/dockerfile:1

## ---- Stage 1: build dependencies in an isolated venv ----
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

## ---- Stage 2: minimal runtime image ----
FROM python:3.12-slim AS runtime

# tini reaps zombie processes and forwards signals correctly as PID 1
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY --chown=app:app main.py ./
COPY --chown=app:app app ./app
COPY --chown=app:app static ./static

# /data is the only writable location at runtime (see docker-compose.yml:
# read_only root filesystem + a named volume mounted here). The app is
# pointed at it via the DATABASE_URL / STORAGE_ROOT env vars.
RUN mkdir -p /data/uploads && chown -R app:app /data

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/', timeout=3).status < 500 else 1)"

ENTRYPOINT ["tini", "--"]
# Runs uvicorn directly (not `python main.py`) so container startup never
# depends on the dev-oriented RELOAD setting in app/infrastructure/config.py.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
