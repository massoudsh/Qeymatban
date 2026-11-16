# syntax=docker/dockerfile:1

# PostGIS ships in the base image; pgvector comes from the PostgreSQL apt repository
# that the official image already configures.
FROM postgis/postgis:16-3.5

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
