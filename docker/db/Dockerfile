# syntax=docker/dockerfile:1

# The official postgis/postgis image is published for linux/amd64 only.
# Build under emulation on ARM hosts such as Apple Silicon.
FROM --platform=linux/amd64 postgis/postgis:16-3.5

# Bullseye PGDG packages moved to the PostgreSQL archive.
RUN find /etc/apt -type f \( -name '*.list' -o -name '*.sources' \) -exec sed -i \
      -e 's#apt.postgresql.org/pub/repos/apt#apt-archive.postgresql.org/pub/repos/apt#g' \
      -e 's#bullseye-pgdg#bullseye-pgdg-archive#g' {} + \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
