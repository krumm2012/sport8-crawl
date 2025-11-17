from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from .models import BookingSlot

FLAG_TO_STATUS = {
    "0": "available",
    "1": "reserved_online",
    "2": "reserved_offline",
    "3": "long_term",
    "4": "locked",
    "5": "free",
}


def _parse_hour(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def parse_sales_detail(result_data: Dict[str, Any], target_date: date) -> List[BookingSlot]:
    slots: List[BookingSlot] = []
    status_list = result_data.get("statusList") or []

    for block in status_list:
        venue_name = block.get("name") or ""
        site_statuses = block.get("siteStatus") or []

        for item in site_statuses:
            flag = str(item.get("flag", ""))
            show_flag = str(item.get("showFlag", ""))
            status = FLAG_TO_STATUS.get(flag, "unknown")
            if show_flag != "0":
                status = f"hidden_{status}"

            bookinfo = item.get("bookinfo") or {}

            slot = BookingSlot(
                venue_name=venue_name or item.get("fieldName", ""),
                court_name=item.get("fieldName", venue_name),
                day=target_date,
                hour=_parse_hour(item.get("time")),
                status=status,
                price=float(item.get("relprice") or 0),
                flag=flag,
                show_flag=show_flag,
                raw=item,
                order_uid=bookinfo.get("orderUID"),
                order_user=bookinfo.get("userName"),
                order_mobile=bookinfo.get("mobile"),
                time_detail=bookinfo.get("timeDetail"),
            )
            slots.append(slot)

    return slots


