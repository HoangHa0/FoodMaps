"""Export the OpenAPI schema to a file (no running server or database needed).

    cd backend
    uv run python scripts/export_openapi.py ../frontend/openapi.json

The frontend generates its TypeScript types from this file, so a backend schema change
surfaces as a frontend type error at build time. Usually run via `make api-types`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402

out = Path(sys.argv[1] if len(sys.argv) > 1 else "openapi.json")
# Force UTF-8 + LF: Windows defaults (cp1252/CRLF) would corrupt non-ASCII text and make the
# file differ between machines.
out.write_text(
    json.dumps(create_app().openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
    newline="\n",
)
print(f"[OK] wrote {out}")
