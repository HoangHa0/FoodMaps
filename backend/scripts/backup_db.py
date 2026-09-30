"""Back up a database with pg_dump running inside Docker (no local PostgreSQL install needed).

    make backup url="postgresql://user:pass@host:5433/postgres"

- Use a plain postgresql:// URL (the +asyncpg suffix is stripped automatically).
- Dumps go to backend/backups/ (git-ignored).
- Restore:
    docker run --rm -v "$PWD/backend/backups:/backups" postgres:17 \
        pg_restore --clean --no-owner -d "<url>" /backups/<file>.dump
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# pg_dump must be the same or a newer major version than the server; 17 can dump 15 and 16.
PG_IMAGE = "postgres:17"

if len(sys.argv) != 2 or not sys.argv[1].startswith("postgres"):
    print(__doc__)
    sys.exit(1)

url = sys.argv[1].replace("postgresql+asyncpg://", "postgresql://")
# Inside the container "localhost" is the container itself; point at the host machine instead.
url = url.replace("@localhost:", "@host.docker.internal:").replace("@127.0.0.1:", "@host.docker.internal:")

backups = Path(__file__).resolve().parents[1] / "backups"
backups.mkdir(exist_ok=True)
name = f"foodmaps_{datetime.now():%Y%m%d_%H%M}.dump"

cmd = [
    "docker", "run", "--rm",
    "--add-host=host.docker.internal:host-gateway",  # needed on Linux; harmless elsewhere
    "-v", f"{backups}:/backups",
    PG_IMAGE,
    "pg_dump", "--format=custom", "--no-owner", f"--dbname={url}", f"--file=/backups/{name}",
]  # fmt: skip
result = subprocess.run(cmd)
if result.returncode != 0:
    sys.exit(result.returncode)
print(f"[OK] backup written to {backups / name}")
