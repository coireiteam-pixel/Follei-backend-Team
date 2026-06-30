import os
import sys
from pathlib import Path


TEST_DB_PATH = Path(__file__).resolve().parent / "test_follei.db"
APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.as_posix()}")

from app.database.init_db import init_db  # noqa: E402


init_db()
