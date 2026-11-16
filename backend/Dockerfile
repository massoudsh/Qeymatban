# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    QEYMATBAN_MODEL_PATH=/app/models/current.joblib \
    DATABASE_URL=sqlite:////app/data/qeymatban.db

# libgomp1 is required by the XGBoost and LightGBM wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl gosu \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin qeymatban

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=qeymatban:qeymatban app ./app
COPY --chown=qeymatban:qeymatban migrations ./migrations
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY docker/wait_for_db.py /usr/local/bin/wait_for_db.py

RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /app/models /app/data /app/benchmarks \
    && chown qeymatban:qeymatban /app/models /app/data /app/benchmarks

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM runtime AS dev

COPY --chown=qeymatban:qeymatban tests ./tests
# requirements-dev.txt includes `-r requirements.txt`, resolved relative to /tmp.
COPY requirements.txt requirements-dev.txt /tmp/
RUN pip install -r /tmp/requirements-dev.txt

CMD ["pytest", "-q", "-p", "no:cacheprovider", "tests"]
