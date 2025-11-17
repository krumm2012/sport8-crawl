from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table

from .config import load_settings
from .fetch import fetch_sales_detail
from .login import LoginError, Sport8Client
from .models import BookingSlot
from .parse import parse_sales_detail
from .storage import SQLiteStorage, export_csv


console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="抓取体育场馆的日程，并保存到 SQLite 或 CSV。"
    )
    parser.add_argument("--username", help="登录账号（可用环境变量 SPORT8_USERNAME）")
    parser.add_argument("--password", help="登录密码（可用环境变量 SPORT8_PASSWORD）")
    parser.add_argument("--base-url", help="自定义站点根地址")
    parser.add_argument(
        "--start-date",
        help="开始日期，格式 YYYY-MM-DD，默认今天",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="抓取的天数，默认 7 天",
    )
    parser.add_argument(
        "--output",
        choices=("sqlite", "csv", "both"),
        default="sqlite",
        help="输出类型，默认写入 SQLite",
    )
    parser.add_argument(
        "--db-path",
        help="SQLite 文件路径，默认 data/sport8.db",
    )
    parser.add_argument(
        "--csv-name",
        help="CSV 文件名称，默认 bookings-YYYYMMDD.csv",
    )
    return parser.parse_args()


def daterange(start: date, days: int) -> List[date]:
    return [start + timedelta(days=i) for i in range(days)]


def main() -> None:
    args = parse_args()
    try:
        settings = load_settings(args.username, args.password, args.base_url)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        return
    if args.db_path:
        settings.db_path = Path(args.db_path)
    start_day = date.fromisoformat(args.start_date) if args.start_date else date.today()

    client = Sport8Client(settings)
    try:
        client.interactive_login()
    except LoginError as exc:
        console.print(f"[red]登录失败：{exc}[/red]")
        return

    slots: List[BookingSlot] = []
    for current_day in daterange(start_day, args.days):
        console.print(f"[cyan]抓取 {current_day.isoformat()}[/cyan]")
        data = fetch_sales_detail(client, current_day)
        slots.extend(parse_sales_detail(data, current_day))

    slots.sort(key=lambda s: (s.day, s.court_name, s.hour))

    console.print(f"[green]共获取 {len(slots)} 条时段记录[/green]")

    if args.output in ("sqlite", "both"):
        sqlite_storage = SQLiteStorage(settings.db_path)
        sqlite_storage.save(slots)
        console.print(f"[green]已写入 SQLite：{settings.db_path}[/green]")

    if args.output in ("csv", "both"):
        csv_name = (
            args.csv_name
            if args.csv_name
            else f"bookings-{start_day.strftime('%Y%m%d')}.csv"
        )
        csv_path = export_csv(
            slots,
            settings.csv_dir,
            csv_name,
        )
        console.print(f"[green]已导出 CSV：{csv_path}[/green]")

    sample_table = Table(title="样例记录（前 10 条）", show_lines=True)
    sample_table.add_column("日期")
    sample_table.add_column("场馆")
    sample_table.add_column("场地")
    sample_table.add_column("时间段")
    sample_table.add_column("状态")
    sample_table.add_column("价格")

    for slot in slots[:10]:
        sample_table.add_row(
            slot.day.isoformat(),
            slot.venue_name,
            slot.court_name,
            f"{slot.hour:02d}:00-{slot.hour+1:02d}:00",
            slot.status,
            f"{slot.price:.2f}",
        )

    console.print(sample_table)


if __name__ == "__main__":
    main()

