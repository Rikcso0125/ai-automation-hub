# -*- coding: utf-8 -*-
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import os
import shutil

if os.environ.get("VERCEL"):
    DB_PATH = Path("/tmp") / "hub_data.db"
    orig_db = Path(__file__).resolve().parent.parent / "data" / "hub_data.db"
    if orig_db.exists() and not DB_PATH.exists():
        try:
            shutil.copy2(orig_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hub_data.db"

def init_db():
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    input_payload TEXT,
                    output_payload TEXT,
                    error_message TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS module_configs (
                    module_id TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"Warning: could not init_db: {e}")

init_db()

def log_execution(module_id: str, status: str, duration_ms: int,
                  input_payload: Any, output_payload: Any, error_message: Optional[str] = None) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO execution_logs 
            (timestamp, module_id, status, duration_ms, input_payload, output_payload, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            now,
            module_id,
            status,
            duration_ms,
            json.dumps(input_payload, ensure_ascii=False) if input_payload else None,
            json.dumps(output_payload, ensure_ascii=False) if output_payload else None,
            error_message
        ))
        conn.commit()
        return cursor.lastrowid

def get_recent_logs(limit: int = 50, module_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if module_id:
            cursor.execute("""
                SELECT * FROM execution_logs 
                WHERE module_id = ? 
                ORDER BY id DESC LIMIT ?
            """, (module_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM execution_logs 
                ORDER BY id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        logs = []
        for r in rows:
            logs.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "module_id": r["module_id"],
                "status": r["status"],
                "duration_ms": r["duration_ms"],
                "input_payload": json.loads(r["input_payload"]) if r["input_payload"] else {},
                "output_payload": json.loads(r["output_payload"]) if r["output_payload"] else {},
                "error_message": r["error_message"]
            })
        return logs

def save_module_config(module_id: str, config: Dict[str, Any], is_active: bool = True):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO module_configs (module_id, config_json, is_active, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(module_id) DO UPDATE SET
                config_json = excluded.config_json,
                is_active = excluded.is_active,
                updated_at = excluded.updated_at
        """, (module_id, json.dumps(config, ensure_ascii=False), 1 if is_active else 0, now))
        conn.commit()

def get_module_config(module_id: str) -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT config_json, is_active FROM module_configs WHERE module_id = ?", (module_id,))
        row = cursor.fetchone()
        if row:
            cfg = json.loads(row["config_json"])
            cfg["_is_active"] = bool(row["is_active"])
            return cfg
        return {"_is_active": True}

def get_stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM execution_logs")
        total_runs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM execution_logs WHERE status = 'success'")
        successful_runs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM execution_logs WHERE status = 'error'")
        failed_runs = cursor.fetchone()[0]

        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM execution_logs WHERE timestamp LIKE ?", (f"{today}%",))
        runs_today = cursor.fetchone()[0]

        success_rate = round((successful_runs / total_runs * 100), 1) if total_runs > 0 else 100.0

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "runs_today": runs_today,
            "success_rate": success_rate
        }
