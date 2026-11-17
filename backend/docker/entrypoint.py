"""Prepare the container, wait for PostgreSQL, drop privileges, then exec.

The image starts as root only long enough to fix ownership of the mounted
volumes (they can be root-owned if an earlier build created them) and then
switches to the unprivileged application user, which is the uid the process
keeps for its whole life.

Dropping privileges here instead of using gosu/su-exec keeps the image free of
extra apt packages: every apt package is another archive the build can fail to
download.
"""

from __future__ import annotations

import os
import sys

APP_UID = 10001
APP_GID = 10001
WRITABLE_DIRS = ("/app/models", "/app/data", "/app/benchmarks")


def _chown_tree(path: str) -> None:
    """Best-effort recursive chown; a read-only mount is not a fatal error."""
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        return
    for root, directories, files in os.walk(path):
        for name in (root, *(os.path.join(root, item) for item in directories + files)):
            try:
                os.chown(name, APP_UID, APP_GID, follow_symlinks=False)
            except OSError:
                pass


def _wait_for_database() -> int:
    if os.environ.get("QEYMATBAN_WAIT_FOR_DB", "1") != "1":
        return 0
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import wait_for_db

    return wait_for_db.main()


def main() -> int:
    if os.geteuid() == 0:
        for directory in WRITABLE_DIRS:
            _chown_tree(directory)

    status = _wait_for_database()
    if status != 0:
        return status

    if os.geteuid() == 0:
        os.setgroups([])
        os.setgid(APP_GID)
        os.setuid(APP_UID)
        os.environ["HOME"] = "/home/qeymatban"

    command = sys.argv[1:]
    if not command:
        print("entrypoint: no command given", file=sys.stderr)
        return 2
    os.execvp(command[0], command)
    return 1  # unreachable


if __name__ == "__main__":
    raise SystemExit(main())
