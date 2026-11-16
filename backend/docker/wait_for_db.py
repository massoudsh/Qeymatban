"""Block container startup until the configured PostgreSQL instance accepts connections."""

import os
import sys
import time

from sqlalchemy import create_engine, text

URL = os.getenv("DATABASE_URL", "")
ATTEMPTS = int(os.getenv("QEYMATBAN_DB_WAIT_ATTEMPTS", "30"))
DELAY_SECONDS = float(os.getenv("QEYMATBAN_DB_WAIT_DELAY", "2"))


def main() -> int:
    if not URL.startswith(("postgresql", "postgres")):
        return 0

    engine = create_engine(URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return 0
        except Exception as error:  # noqa: BLE001 - startup probe reports any driver error
            print(f"[wait-for-db] attempt {attempt}/{ATTEMPTS} failed: {error}", flush=True)
            if attempt < ATTEMPTS:
                time.sleep(DELAY_SECONDS)
    print("[wait-for-db] PostgreSQL is not reachable; giving up", file=sys.stderr, flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
