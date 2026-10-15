"""Verify fixed audit invariants with the shared PostgreSQL regression tests.

Run from backend with DATABASE_URL targeting a dedicated petapintar_audit_review_*
base database. Pytest creates and clears its separate <base>_test database;
existing evidence in the base database is preserved. LLM/Redis are mocked.
"""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy.engine import make_url


def main() -> int:
    audit_url = make_url(os.environ["DATABASE_URL"])
    if not (audit_url.database or "").startswith("petapintar_audit_review_"):
        raise SystemExit("Refusing writes: use a dedicated petapintar_audit_review_* database")
    return subprocess.call(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "pytest_asyncio.plugin",
            "tests/test_core_audit_fixes.py",
            "tests/test_level_lesson.py",
            "tests/test_progress.py",
            "tests/test_worker_generate.py",
            "-q",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env={
            **os.environ,
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
