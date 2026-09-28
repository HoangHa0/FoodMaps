"""Fail unless the Alembic history has exactly ONE head (run in CI and by `make check`).

Two heads mean two branches added migrations in parallel. Fix it with:
    cd backend && uv run alembic merge heads -m "merge"
and commit the generated merge migration.
"""

import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

backend_dir = Path(__file__).resolve().parents[1]
cfg = Config(str(backend_dir / "alembic.ini"))
cfg.set_main_option("script_location", str(backend_dir / "migrations"))
heads = ScriptDirectory.from_config(cfg).get_heads()

if len(heads) != 1:
    print(f"[ERROR] {len(heads)} alembic heads: {heads}")
    print('        Run: cd backend && uv run alembic merge heads -m "merge"')
    sys.exit(1)
print(f"[OK] single alembic head ({heads[0]})")
