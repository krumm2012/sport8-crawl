#!/usr/bin/env python3
"""
Sport8 integration sync tool.

Reads local CSV exports (orders/bookings) and mirrors them into the Sport8 API
by creating bookings and optional payment records. Designed to run once or as a
loop between 07:00-23:00 every 15 minutes.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


BASE_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = BASE_DIR / "data" / "exports"
STATE_DIR = BASE_DIR / "data" / "state"
STATE_FILE = STATE_DIR / "sport8_synced.json"
CONFIG_PATH = BASE_DIR / "config" / "sport8_sync.json"

DEFAULT_BASE_URL = "https://51alljoin.cn:8000/api/v1"
DEFAULT_USERNAME = "superadmin"
DEFAULT_PASSWORD = "admin123"
DEFAULT_VENUE_ID = 12

COURT_ID_MAP = {
    "[学练馆][01]": 24,
    "[学练馆][02]": 25,
    "[学练馆小][03]": 26,
    "学练馆-01": 24,
    "学练馆-02": 25,
    "学练馆小-03": 26,
}

LOCKED_STATUSES = {"locked", "order", "online_reserved"}
PAID_STATUSES = {"已支付", "paid", "success"}

DEFAULT_LOOP_INTERVAL = 15 * 60  # 15 minutes
WINDOW_START = 7  # 07:00
WINDOW_END = 23  # 23:00 (exclusive)


def setup_logger(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class Sport8Error(RuntimeError):
    """Raised when the Sport8 API returns an error response."""


class Sport8Client:
    def __init__(self, base_url: str, username: str, password: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
        self._token: Optional[str] = None

    def login(self) -> None:
        logging.info("Logging in as %s", self.username)
        resp = self.session.post(
            f"{self.base_url}/auth/login",
            data={"username": self.username, "password": self.password},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        try:
            payload = resp.json()
        except ValueError as exc:
            logging.error("Login response not JSON: %s", resp.text[:500])
            raise Sport8Error(f"Login response parse error: {exc}") from exc
        if payload.get("code") != 0:
            raise Sport8Error(f"Login failed: {payload}")
        data_section = payload.get("data") or {}
        if isinstance(data_section, str):
            access_token = data_section
        else:
            access_token = (
                data_section.get("access_token")
                or data_section.get("token")
                or data_section.get("accessToken")
            )
            if isinstance(access_token, dict):
                access_token = access_token.get("token") or access_token.get("access_token")
        if not access_token:
            logging.error("Login response missing access_token field: %s", payload)
            raise Sport8Error("Login response missing access_token")
        self._token = access_token
        logging.info("Login successful, token acquired.")

    def _authorized_headers(self) -> Dict[str, str]:
        if not self._token:
            self.login()
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self._authorized_headers())
        resp = self.session.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        resp.raise_for_status()
        try:
            payload = resp.json()
        except ValueError as exc:
            logging.error("%s %s response not JSON: %s", method, path, resp.text[:500])
            raise Sport8Error(f"{method} {path} parse error: {exc}") from exc
        code = payload.get("code")
        if code is None:
            return payload.get("data") or payload
        if code != 0:
            raise Sport8Error(f"{method} {path} failed: {payload}")
        return payload.get("data") or payload

    def create_booking(self, payload: Dict) -> Dict:
        logging.debug("Creating booking: %s", payload)
        return self._request("POST", "/bookings/with-datetime", json=payload)

    def create_payment(self, payload: Dict) -> Dict:
        logging.debug("Creating payment: %s", payload)
        return self._request("POST", "/payments", json=payload)


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> Dict:
    ensure_state_dir()
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logging.warning("State file corrupted, starting fresh: %s", STATE_FILE)
    return {"orders": {}, "bookings": {}, "last_run": None}


def save_state(state: Dict) -> None:
    ensure_state_dir()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[sport8_sync] Failed to read config {path}: {exc}", file=sys.stderr)
        return {}


def parse_orders_files(files: List[Path]) -> Iterable[Dict]:
    for file_path in files:
        with file_path.open("r", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row["_source_file"] = str(file_path)
                yield row


def parse_bookings_files(files: List[Path]) -> Iterable[Dict]:
    for file_path in files:
        with file_path.open("r", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row["_source_file"] = str(file_path)
                yield row


def parse_order_date(value: str) -> date:
    value = value.strip()
    fmt = "%Y%m%d" if value.isdigit() else "%Y-%m-%d"
    return datetime.strptime(value, fmt).date()


def parse_booking_date(value: str) -> date:
    value = value.strip()
    fmt = "%Y-%m-%d" if "-" in value else "%Y%m%d"
    return datetime.strptime(value, fmt).date()


def parse_time_range(value: str) -> Tuple[str, str]:
    if "-" in value:
        start, end = value.split("-", 1)
        return start.strip(), end.strip()
    hour = int(value)
    start_hour = hour
    end_hour = hour + 1
    return f"{start_hour:02d}:00", f"{end_hour:02d}:00"


def resolve_court_id(text: str) -> Optional[int]:
    text = text.strip()
    for key, cid in COURT_ID_MAP.items():
        if key in text:
            return cid
    normalized = text.replace(" ", "")
    return COURT_ID_MAP.get(normalized)


def collect_files(pattern: str) -> List[Path]:
    return sorted(EXPORT_DIR.glob(pattern))


def date_in_window(target: date, since: Optional[date], until: Optional[date]) -> bool:
    if since and target < since:
        return False
    if until and target > until:
        return False
    return True


def build_note(prefix: str, **kwargs) -> str:
    parts = [f"{prefix}"]
    for key, value in kwargs.items():
        if value:
            parts.append(f"{key}={value}")
    return ";".join(parts)


def is_conflict_error(error: Exception) -> bool:
    text = str(error)
    return "3001" in text or "已被预约" in text or "time slot" in text.lower()


@dataclass
class SyncStats:
    created_orders: int = 0
    created_payments: int = 0
    created_bookings: int = 0
    skipped: int = 0


def sync_orders(args, client: Sport8Client, state: Dict) -> SyncStats:
    stats = SyncStats()
    files = collect_files(args.orders_glob)
    if not files:
        logging.info("No order CSV files found with pattern %s", args.orders_glob)
        return stats
    for row in parse_orders_files(files):
        order_no = (row.get("order_no") or "").strip()
        if not order_no:
            continue
        if order_no in state["orders"]:
            stats.skipped += 1
            continue
        status = (row.get("status") or "").strip()
        if status and status not in PAID_STATUSES:
            continue
        order_date = parse_order_date(row.get("date", ""))
        if not date_in_window(order_date, args.since_date, args.until_date):
            continue
        court_text = row.get("field_timebucket") or row.get("field_name") or ""
        court_id = resolve_court_id(court_text)
        if not court_id:
            logging.warning("Unable to map court_id for order %s (%s)", order_no, court_text)
            continue
        start_time, end_time = parse_time_range(row.get("time", ""))
        booking_payload = {
            "venue_id": args.venue_id,
            "court_id": court_id,
            "booking_date": order_date.isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "user_name": (row.get("customer_name") or row.get("customer_nickname") or "Sport8 User"),
            "phone": row.get("customer_phone") or "00000000000",
            "note": build_note(
                "sport8:orders",
                order_no=order_no,
                phone=row.get("customer_phone"),
                nickname=row.get("customer_nickname"),
                amount=row.get("price"),
                time=row.get("time"),
            ),
        }
        price = float(row.get("price") or 0)
        payment_payload = {
            "booking_id": None,  # placeholder, updated after booking creation
            "amount": price,
            "payment_method": args.payment_method,
            "description": build_note(
                "sport8:payment",
                order_no=order_no,
                phone=row.get("customer_phone"),
                nickname=row.get("customer_nickname"),
            ),
        }
        if args.dry_run:
            logging.info("[DRY-RUN] Would create order booking: %s", booking_payload)
            logging.info("[DRY-RUN] Would create payment: %s", payment_payload)
            state["orders"][order_no] = {"booking_id": "dry-run", "payment_id": "dry-run"}
            stats.created_orders += 1
            stats.created_payments += 1
            continue
        try:
            booking_resp = client.create_booking(booking_payload)
        except Sport8Error as exc:
            if is_conflict_error(exc):
                logging.warning("Order %s skipped: slot already booked (%s)", order_no, exc)
                state["orders"][order_no] = {
                    "booking_id": None,
                    "payment_id": None,
                    "synced_at": datetime.utcnow().isoformat(),
                    "source_file": row.get("_source_file"),
                    "reason": "conflict",
                }
                stats.skipped += 1
                continue
            raise
        booking_id = booking_resp.get("id") or booking_resp.get("data", {}).get("id")
        if not booking_id:
            raise Sport8Error(f"Booking response missing id: {booking_resp}")
        stats.created_orders += 1

        payment_payload["booking_id"] = booking_id
        payment_resp = client.create_payment(payment_payload)
        payment_id = payment_resp.get("payment_id") or payment_resp.get("id") or payment_resp.get("data", {}).get("payment_id")
        stats.created_payments += 1

        state["orders"][order_no] = {
            "booking_id": booking_id,
            "payment_id": payment_id,
            "synced_at": datetime.utcnow().isoformat(),
            "source_file": row.get("_source_file"),
        }
    return stats


def make_booking_key(row: Dict, court_id: int) -> str:
    return f"{row.get('date')}::{court_id}::{row.get('hour')}"


def sync_locked_bookings(args, client: Sport8Client, state: Dict) -> SyncStats:
    stats = SyncStats()
    files = collect_files(args.bookings_glob)
    if not files:
        logging.info("No bookings CSV files found with pattern %s", args.bookings_glob)
        return stats
    for row in parse_bookings_files(files):
        status = (row.get("status") or "").strip().lower()
        if status not in LOCKED_STATUSES:
            continue
        target_date = parse_booking_date(row.get("date", ""))
        if not date_in_window(target_date, args.since_date, args.until_date):
            continue
        court_text = row.get("field_timebucket") or row.get("court_name") or ""
        court_id = resolve_court_id(court_text)
        if not court_id:
            # Try combining venue + court columns
            combined = f"{row.get('venue_name','')}-{row.get('court_name','')}"
            court_id = resolve_court_id(combined)
        if not court_id:
            logging.warning("Unable to map court_id for locked booking %s", row)
            continue
        booking_key = make_booking_key(row, court_id)
        if booking_key in state["bookings"]:
            stats.skipped += 1
            continue
        start_time, end_time = parse_time_range(row.get("hour", "0"))
        booking_payload = {
            "venue_id": args.venue_id,
            "court_id": court_id,
            "booking_date": target_date.isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "user_name": row.get("user_name") or f"Locked-{court_id}",
            "phone": row.get("phone") or args.default_phone,
            "price": float(row.get("price") or 0),
            "note": build_note(
                "sport8:locked",
                venue=row.get("venue_name"),
                court=row.get("court_name"),
                status=row.get("status"),
                source=row.get("_source_file"),
            ),
        }
        if args.dry_run:
            logging.info("[DRY-RUN] Would create locked booking: %s", booking_payload)
            state["bookings"][booking_key] = {
                "booking_id": "dry-run",
                "synced_at": datetime.utcnow().isoformat(),
            }
            stats.created_bookings += 1
            continue
        try:
            booking_resp = client.create_booking(booking_payload)
        except Sport8Error as exc:
            if is_conflict_error(exc):
                logging.warning("Locked slot %s skipped: already booked (%s)", booking_key, exc)
                state["bookings"][booking_key] = {
                    "booking_id": None,
                    "synced_at": datetime.utcnow().isoformat(),
                    "source_file": row.get("_source_file"),
                    "reason": "conflict",
                }
                stats.skipped += 1
                continue
            raise
        booking_id = booking_resp.get("id") or booking_resp.get("data", {}).get("id")
        if not booking_id:
            raise Sport8Error(f"Locked booking response missing id: {booking_resp}")
        state["bookings"][booking_key] = {
            "booking_id": booking_id,
            "synced_at": datetime.utcnow().isoformat(),
            "source_file": row.get("_source_file"),
        }
        stats.created_bookings += 1
    return stats


def within_active_window(now: datetime) -> bool:
    return WINDOW_START <= now.hour < WINDOW_END


def parse_cli_args():
    parser = argparse.ArgumentParser(description="Sync Sport8 bookings/payments from local CSV exports.")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Path to JSON config file")
    parser.add_argument("--base-url", default=None, help="Sport8 API base URL")
    parser.add_argument("--username", default=None, help="Sport8 username")
    parser.add_argument("--password", default=None, help="Sport8 password")
    parser.add_argument("--venue-id", type=int, default=None, help="Default venue_id for new bookings")
    parser.add_argument("--orders-glob", default=None, help="Glob pattern for orders CSV files")
    parser.add_argument("--bookings-glob", default=None, help="Glob pattern for bookings CSV files")
    parser.add_argument("--since", dest="since", help="Earliest booking date (YYYY-MM-DD)")
    parser.add_argument("--until", dest="until", help="Latest booking date (YYYY-MM-DD)")
    parser.add_argument("--loop", action="store_true", help="Enable continuous sync loop (overrides config)")
    parser.add_argument("--no-loop", action="store_true", help="Force disable loop even if config enables it")
    parser.add_argument("--interval", type=int, default=None, help="Loop interval seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without calling the API")
    parser.add_argument("--orders-only", action="store_true", help="Process only orders CSV")
    parser.add_argument("--bookings-only", action="store_true", help="Process only bookings CSV")
    parser.add_argument("--default-phone", default=None, help="Fallback phone number for locked bookings")
    parser.add_argument("--payment-method", default=None, help="Payment method for created payments")
    parser.add_argument("--log-level", default=None, help="Logging level (INFO/DEBUG/WARN)")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    config_data = load_config_file(config_path)

    def resolve(key: str, current, fallback):
        if current not in (None, ""):
            return current
        if key in config_data:
            return config_data[key]
        return fallback

    args.base_url = resolve("base_url", args.base_url, DEFAULT_BASE_URL)
    args.username = resolve("username", args.username, DEFAULT_USERNAME)
    args.password = resolve("password", args.password, DEFAULT_PASSWORD)
    args.venue_id = int(resolve("venue_id", args.venue_id, DEFAULT_VENUE_ID))
    args.orders_glob = resolve("orders_glob", args.orders_glob, "orders-*.csv")
    args.bookings_glob = resolve("bookings_glob", args.bookings_glob, "bookings-*.csv")
    args.default_phone = resolve("default_phone", args.default_phone, "00000000000")
    args.payment_method = resolve("payment_method", args.payment_method, "offline")
    args.log_level = resolve("log_level", args.log_level, "INFO")
    args.interval = int(resolve("loop_interval", args.interval, DEFAULT_LOOP_INTERVAL))

    global WINDOW_START, WINDOW_END
    if "window_start" in config_data:
        WINDOW_START = int(config_data["window_start"])
    if "window_end" in config_data:
        WINDOW_END = int(config_data["window_end"])

    court_map = config_data.get("court_id_map")
    if isinstance(court_map, dict):
        COURT_ID_MAP.update({str(k): int(v) for k, v in court_map.items()})

    if args.no_loop:
        args.loop = False
    elif args.loop:
        args.loop = True
    else:
        args.loop = bool(config_data.get("loop_enabled", False))

    args.since_date = datetime.strptime(args.since, "%Y-%m-%d").date() if args.since else None
    args.until_date = datetime.strptime(args.until, "%Y-%m-%d").date() if args.until else None
    return args


def run_once(args, client: Sport8Client) -> None:
    state = load_state()
    if not args.bookings_only:
        order_stats = sync_orders(args, client, state)
        logging.info(
            "Orders sync complete. created=%s payments=%s skipped=%s",
            order_stats.created_orders,
            order_stats.created_payments,
            order_stats.skipped,
        )
    if not args.orders_only:
        locked_stats = sync_locked_bookings(args, client, state)
        logging.info(
            "Locked bookings sync complete. created=%s skipped=%s",
            locked_stats.created_bookings,
            locked_stats.skipped,
        )
    state["last_run"] = datetime.utcnow().isoformat()
    save_state(state)


def main():
    args = parse_cli_args()
    setup_logger(args.log_level)
    client = Sport8Client(args.base_url, args.username, args.password)

    if not args.loop:
        run_once(args, client)
        return

    logging.info("Starting looped sync every %s seconds", args.interval)
    while True:
        now = datetime.now()
        if within_active_window(now):
            logging.info("Within active window (%02d:00-%02d:00). Running sync...", WINDOW_START, WINDOW_END)
            try:
                run_once(args, client)
            except Exception as exc:
                logging.exception("Sync iteration failed: %s", exc)
        else:
            logging.info(
                "Current time %s outside window %02d:00-%02d:00. Sleeping until window opens.",
                now.strftime("%H:%M"),
                WINDOW_START,
                WINDOW_END,
            )
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except Sport8Error as err:
        logging.error("Sport8 API error: %s", err)
        sys.exit(2)
    except requests.RequestException as err:
        logging.error("Network error: %s", err)
        sys.exit(3)

