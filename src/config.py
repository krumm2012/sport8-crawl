from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    username: str
    password: str
    base_url: str = "https://stadium.sports8.com.cn"
    db_path: Path = Path("data") / "sport8.db"
    csv_dir: Path = Path("data") / "exports"


def load_settings(
    username: Optional[str] = None,
    password: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Settings:
    """Load configuration from environment variables or provided overrides."""
    load_dotenv()

    resolved_username = username or os.getenv("SPORT8_USERNAME")
    resolved_password = password or os.getenv("SPORT8_PASSWORD")
    default_base = "https://stadium.sports8.com.cn"
    resolved_base_url = base_url or os.getenv("SPORT8_BASE_URL", default_base)

    if not resolved_username or not resolved_password:
        raise ValueError(
            "Missing credentials. Provide SPORT8_USERNAME and SPORT8_PASSWORD "
            "environment variables or pass them explicitly."
        )

    return Settings(
        username=resolved_username,
        password=resolved_password,
        base_url=resolved_base_url.rstrip("/"),
    )

