from __future__ import annotations
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


class Cache:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.conn = sqlite3.connect(db_path)
            self._create_tables()
        except sqlite3.DatabaseError:
            print(f"Warning: cache DB corrupt at {db_path}, rebuilding.", file=sys.stderr)
            db_path.unlink(missing_ok=True)
            self.conn = sqlite3.connect(db_path)
            self._create_tables()

    def _create_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS project_list_cache (
                category     TEXT NOT NULL,
                fetched_at   TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS project_detail_cache (
                project_id   INTEGER PRIMARY KEY,
                fetched_at   TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS llm_classification_cache (
                input_hash    TEXT PRIMARY KEY,
                classified_at TEXT NOT NULL,
                output_json   TEXT NOT NULL
            );
        """)
        self.conn.commit()

    # --- project list ---

    def get_project_list(self, category: str, ttl_hours: int) -> list | None:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=ttl_hours)).isoformat()
        row = self.conn.execute(
            "SELECT payload_json FROM project_list_cache "
            "WHERE category=? AND fetched_at>? ORDER BY fetched_at DESC LIMIT 1",
            (category, cutoff),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def set_project_list(self, category: str, projects: list) -> None:
        self.conn.execute("DELETE FROM project_list_cache WHERE category=?", (category,))
        self.conn.execute(
            "INSERT INTO project_list_cache VALUES (?,?,?)",
            (category, datetime.now(timezone.utc).isoformat(), json.dumps(projects)),
        )
        self.conn.commit()

    # --- project detail ---

    def get_project_detail(self, project_id: int, ttl_days: int) -> dict | None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=ttl_days)).isoformat()
        row = self.conn.execute(
            "SELECT payload_json FROM project_detail_cache "
            "WHERE project_id=? AND fetched_at>?",
            (project_id, cutoff),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def set_project_detail(self, project_id: int, detail: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO project_detail_cache VALUES (?,?,?)",
            (project_id, datetime.now(timezone.utc).isoformat(), json.dumps(detail)),
        )
        self.conn.commit()

    # --- LLM classification ---

    def get_classification(self, input_hash: str) -> dict | None:
        row = self.conn.execute(
            "SELECT output_json FROM llm_classification_cache WHERE input_hash=?",
            (input_hash,),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def set_classification(self, input_hash: str, result: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO llm_classification_cache VALUES (?,?,?)",
            (input_hash, datetime.now(timezone.utc).isoformat(), json.dumps(result)),
        )
        self.conn.commit()
