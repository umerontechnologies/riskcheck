import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from .config import DATABASE_PATH


def _ensure_parent_dir(path: str) -> None:
    Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_parent_dir(DATABASE_PATH)
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # Submissions (generated risk reports)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,

            entity_type TEXT NOT NULL,
            entity_key TEXT NOT NULL,
            entity_value TEXT NOT NULL,

            intent TEXT,
            price_range TEXT,

            seller_phone TEXT,
            seller_email TEXT,
            seller_website TEXT,

            user_contact TEXT,

            risk_level TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            grade TEXT NOT NULL,
            rationale TEXT NOT NULL,

            signals_json TEXT NOT NULL,
            evidence_json TEXT,
            attachment_sha256s_json TEXT,
            linked_accounts_json TEXT,
            footprint_json TEXT
        )
        """
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_submissions_entity_key ON submissions(entity_key)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_submissions_entity_type ON submissions(entity_type)")

    # Community reports (user-submitted incidents)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS community_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,

            entity_type TEXT NOT NULL,
            entity_key TEXT NOT NULL,
            entity_value TEXT NOT NULL,

            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount INTEGER,
            evidence_url TEXT,
            reporter_contact TEXT,

            attachment_sha256s_json TEXT,
            linked_accounts_json TEXT,

            status TEXT NOT NULL
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_community_entity_key ON community_reports(entity_key)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_community_status ON community_reports(status)")

    # Uploaded media files
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS media (
            sha256 TEXT PRIMARY KEY,
            phash TEXT,
            filename TEXT NOT NULL,
            mime_type TEXT,
            size_bytes INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # Link media to entities (for reuse detection)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entity_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_key TEXT NOT NULL,
            media_sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_entity_media_key ON entity_media(entity_key)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_entity_media_sha ON entity_media(media_sha256)")

    # Google search cache (to avoid burning API quota)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS search_cache (
            query_hash TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


@contextmanager
def db_conn() -> Iterator[sqlite3.Connection]:
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def json_loads(s: Optional[str]) -> Any:
    if not s:
        return None
    return json.loads(s)
