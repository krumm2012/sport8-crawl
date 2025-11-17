from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any, Dict, Optional


@dataclass
class BookingSlot:
    """Represents a single court slot for a specific hour."""

    venue_name: str
    court_name: str
    day: date
    hour: int
    status: str
    price: float
    flag: str
    show_flag: str
    raw: Dict[str, Any] = field(default_factory=dict)
    order_uid: Optional[str] = None
    order_user: Optional[str] = None
    order_mobile: Optional[str] = None
    time_detail: Optional[str] = None

    @property
    def start_time(self) -> time:
        return time(hour=self.hour)

    @property
    def end_time(self) -> time:
        end_hour = min(self.hour + 1, 23)
        return time(hour=end_hour)

