#!/bin/sh
set -eu

# Named volumes are created as root; hand them to the runtime user before dropping privileges.
for directory in /app/models /app/data /app/benchmarks; do
    if [ -d "$directory" ]; then
        chown -R qeymatban:qeymatban "$directory" 2>/dev/null || true
    fi
done

# Wait for PostgreSQL when the app is configured to use it (compose already gates on a healthcheck).
if [ "${QEYMATBAN_WAIT_FOR_DB:-1}" = "1" ]; then
    python /usr/local/bin/wait_for_db.py
fi

exec gosu qeymatban "$@"
