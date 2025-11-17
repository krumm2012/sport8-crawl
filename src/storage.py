from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

from .models import BookingSlot

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS bookings (
    venue_name TEXT NOT NULL,
    court_name TEXT NOT NULL,
    day TEXT NOT NULL,
    hour INTEGER NOT NULL,
    status TEXT NOT NULL,
    price REAL NOT NULL,
    flag TEXT,
    show_flag TEXT,
    order_uid TEXT,
    order_user TEXT,
    order_mobile TEXT,
    time_detail TEXT,
    raw JSON,
    PRIMARY KEY (venue_name, court_name, day, hour)
)
"""

INSERT_SQL = """
INSERT OR REPLACE INTO bookings (
    venue_name, court_name, day, hour, status, price,
    flag, show_flag, order_uid, order_user, order_mobile,
    time_detail, raw
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class SQLiteStorage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, slots: Sequence[BookingSlot]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(CREATE_TABLE_SQL)
            rows = [
                (
                    slot.venue_name,
                    slot.court_name,
                    slot.day.isoformat(),
                    slot.hour,
                    slot.status,
                    slot.price,
                    slot.flag,
                    slot.show_flag,
                    slot.order_uid,
                    slot.order_user,
                    slot.order_mobile,
                    slot.time_detail,
                    json.dumps(slot.raw, ensure_ascii=False),
                )
                for slot in slots
            ]
            conn.executemany(INSERT_SQL, rows)
            conn.commit()


def export_csv(slots: Iterable[BookingSlot], output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / filename
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(
            [
                "venue_name",
                "court_name",
                "date",
                "hour",
                "status",
                "price",
                "flag",
                "show_flag",
                "order_uid",
                "order_user",
                "order_mobile",
                "time_detail",
            ]
        )
        for slot in slots:
            writer.writerow(
                [
                    slot.venue_name,
                    slot.court_name,
                    slot.day.isoformat(),
                    slot.hour,
                    slot.status,
                    slot.price,
                    slot.flag,
                    slot.show_flag,
                    slot.order_uid or "",
                    slot.order_user or "",
                    slot.order_mobile or "",
                    slot.time_detail or "",
                ]
            )
    return csv_path


