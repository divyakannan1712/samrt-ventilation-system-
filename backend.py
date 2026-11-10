from datetime import datetime, timezone
import json
import os
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = os.getenv("DB_PATH", "telemetry.db")
app = FastAPI(title="Smart Ventilation Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Telemetry(BaseModel):
    mq135: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pir_motion: Optional[bool] = None
    mode: Optional[str] = None
    fan_on: Optional[bool] = None
    relay_on: Optional[bool] = None
    red_led: Optional[bool] = None
    green_led: Optional[bool] = None
    buzzer_on: Optional[bool] = None
    air_status: Optional[str] = None
    temperature_status: Optional[str] = None
    alert_message: Optional[str] = None

def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
def startup():
    with connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        conn.commit()

@app.get("/")
def root():
    return {"message": "Smart Ventilation Backend is running"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/telemetry")
def receive_telemetry(item: Telemetry):
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = item.model_dump()
    payload["timestamp"] = timestamp
    try:
        with connection() as conn:
            conn.execute(
                "INSERT INTO telemetry (timestamp, payload) VALUES (?, ?)",
                (timestamp, json.dumps(payload)),
            )
            conn.commit()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Could not save telemetry") from exc
    return {"success": True, "timestamp": timestamp}

@app.get("/api/latest")
def latest():
    with connection() as conn:
        row = conn.execute(
            "SELECT payload FROM telemetry ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if row is None:
        return {"available": False, "data": None}
    return {"available": True, "data": json.loads(row["payload"])}

@app.get("/api/history")
def history(limit: int = 100):
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit must be 1 to 5000")
    with connection() as conn:
        rows = conn.execute(
            "SELECT payload FROM telemetry ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"data": [json.loads(row["payload"]) for row in reversed(rows)]}
