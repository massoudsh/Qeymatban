# syntax=docker/dockerfile:1

# Base image is a build arg so a registry mirror can be used without editing
# this file, e.g. when registry-1.docker.io is unreachable:
#   docker compose build --build-arg PYTHON_IMAGE=mirror.example/python:3.12-slim backend
ARG PYTHON_IMAGE=python:3.12-slim

FROM ${PYTHON_IMAGE} AS builder

# Override with a closer mirror if PyPI is slow or flaky from your network:
#   docker compose build --build-arg PIP_INDEX_URL=https://mirror.example/simple backend
ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10 \
    PIP_INDEX_URL=${PIP_INDEX_URL}

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt requirements-benchmark.txt /tmp/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt


# Full model-family set used by app/scripts/benchmark_models.py.
FROM builder AS benchmark-builder

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-benchmark.txt


FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    QEYMATBAN_MODEL_PATH=/app/models/current.joblib \
    DATABASE_URL=sqlite:////app/data/qeymatban.db

# No apt packages. The XGBoost wheel vendors the libgomp it needs
# (xgboost.libs/libgomp-*.so.1.0.0, resolved through $ORIGIN/../../xgboost.libs),
# so the runtime image is pure python:3.12-slim and needs no Debian archive at all.
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin qeymatban

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=qeymatban:qeymatban app ./app
COPY --chown=qeymatban:qeymatban migrations ./migrations
COPY docker/entrypoint.py docker/wait_for_db.py /usr/local/bin/

RUN mkdir -p /app/models /app/data /app/benchmarks \
    && chown -R qeymatban:qeymatban /app/models /app/data /app/benchmarks

# Starts as root only to fix volume ownership, then execs as qeymatban (uid 10001).
ENTRYPOINT ["python", "/usr/local/bin/entrypoint.py"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000

# Uses the interpreter already in the image; no curl dependency.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)" || exit 1


# Same image plus CatBoost/LightGBM for the model benchmark.
# Unlike the XGBoost wheel, the LightGBM wheel does NOT vendor libgomp
# (its lib_lightgbm.so has no RUNPATH), so this target needs the apt package.
# It is opt-in via the `tools` compose profile, so the slow apt layer never
# blocks a normal `docker compose up`.
FROM runtime AS benchmark

USER root

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -o Acquire::Retries=10 update \
    && apt-get -o Acquire::Retries=10 install -y --no-install-recommends libgomp1

COPY --from=benchmark-builder /opt/venv /opt/venv


FROM runtime AS dev

COPY --chown=qeymatban:qeymatban tests ./tests
# requirements-dev.txt includes `-r requirements.txt`, resolved relative to /tmp.
COPY requirements.txt requirements-dev.txt /tmp/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-dev.txt

# The entrypoint still drops to qeymatban before running the tests.
CMD ["pytest", "-q", "-p", "no:cacheprovider", "tests"]
