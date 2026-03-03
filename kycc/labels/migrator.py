import sqlite3
from pathlib import Path

MIGRATIONS = [
    # version 1 — initial schema
    """
    CREATE TABLE IF NOT EXISTS labels (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        wallet_id   TEXT    NOT NULL DEFAULT 'default',
        ref_type    TEXT    NOT NULL CHECK(ref_type IN ('tx','utxo','addr','xpub')),
        ref         TEXT    NOT NULL,
        label       TEXT    NOT NULL,
        origin      TEXT    NOT NULL DEFAULT 'user',
        spendable   INTEGER,
        created_at  INTEGER NOT NULL,
        updated_at  INTEGER NOT NULL,
        UNIQUE(wallet_id, ref_type, ref)
    );

    CREATE TABLE IF NOT EXISTS heuristic_cache (
        txid        TEXT PRIMARY KEY,
        result_json TEXT NOT NULL,
        cached_at   INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions (
        session_id  TEXT PRIMARY KEY,
        wallet_ids  TEXT NOT NULL,
        root_txid   TEXT NOT NULL,
        created_at  INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS schema_meta (
        version     INTEGER PRIMARY KEY
    );
    """
]


def migrate(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(MIGRATIONS[0])
        current = (
            conn.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] or 0
        )

        for i, sql in enumerate(MIGRATIONS[current:], start=current + 1):
            conn.executescript(sql)
            conn.execute("INSERT OR REPLACE INTO schema_meta(version) VALUES(?)", (i,))
        conn.commit()
    finally:
        conn.close()
