# syntax=docker/dockerfile:1

# The official postgis/postgis image is published for linux/amd64 only.
# Build under emulation on ARM hosts such as Apple Silicon.
FROM --platform=linux/amd64 postgis/postgis:16-3.5

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
