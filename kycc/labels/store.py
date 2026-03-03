import sqlite3
import time
from dataclasses import dataclass
from typing import Literal, Optional

from kycc.labels.migrator import migrate

RefType = Literal["tx", "utxo", "addr", "xpub"]


@dataclass
class Label:
    wallet_id: str
    ref_type: RefType
    ref: str
    label: str
    origin: str = "user"
    spendable: Optional[bool] = None
    created_at: int = 0
    updated_at: int = 0


class LabelStore:
    def __init__(self, db_path: str):
        migrate(db_path)
        self._path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def upsert(self, label: Label) -> None:
        now = int(time.time())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO labels
                    (wallet_id, ref_type, ref, label, origin, spendable,
                     created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(wallet_id, ref_type, ref) DO UPDATE SET
                    label      = excluded.label,
                    origin     = excluded.origin,
                    spendable  = excluded.spendable,
                    updated_at = excluded.updated_at
            """,
                (
                    label.wallet_id,
                    label.ref_type,
                    label.ref,
                    label.label,
                    label.origin,
                    int(label.spendable) if label.spendable is not None else None,
                    now,
                    now,
                ),
            )

    def get(
        self, ref_type: RefType, ref: str, wallet_id: str = "default"
    ) -> Optional[Label]:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM labels
                WHERE wallet_id=? AND ref_type=? AND ref=?
            """,
                (wallet_id, ref_type, ref),
            ).fetchone()
        return _row_to_label(row) if row else None

    def delete(self, ref_type: RefType, ref: str, wallet_id: str = "default") -> None:
        with self._conn() as conn:
            conn.execute(
                """
                DELETE FROM labels
                WHERE wallet_id=? AND ref_type=? AND ref=?
            """,
                (wallet_id, ref_type, ref),
            )

    def list(
        self, wallet_id: str = "default", ref_type: Optional[RefType] = None
    ) -> list[Label]:
        with self._conn() as conn:
            if ref_type:
                rows = conn.execute(
                    """
                    SELECT * FROM labels
                    WHERE wallet_id=? AND ref_type=?
                    ORDER BY updated_at DESC
                """,
                    (wallet_id, ref_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM labels WHERE wallet_id=?
                    ORDER BY updated_at DESC
                """,
                    (wallet_id,),
                ).fetchall()
        return [_row_to_label(r) for r in rows]

    def hydrate_tx(self, txid: str, wallet_id: str = "default") -> Optional[str]:
        """Return label text for a txid, or None."""
        result = self.get("tx", txid, wallet_id)
        return result.label if result else None

    def hydrate_utxo(
        self, txid: str, vout: int, wallet_id: str = "default"
    ) -> Optional[str]:
        result = self.get("utxo", f"{txid}:{vout}", wallet_id)
        return result.label if result else None


def _row_to_label(row: sqlite3.Row) -> Label:
    spendable = row["spendable"]
    return Label(
        wallet_id=row["wallet_id"],
        ref_type=row["ref_type"],
        ref=row["ref"],
        label=row["label"],
        origin=row["origin"],
        spendable=bool(spendable) if spendable is not None else None,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
