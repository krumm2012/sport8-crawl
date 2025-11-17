from __future__ import annotations

import re
from typing import Dict
from urllib.parse import urljoin


LOCAL_STORAGE_PATTERN = re.compile(
    r'window\.localStorage\.setItem\("(?P<key>[^"]+)",\s*"(?P<value>[^"]*)"\)',
    re.IGNORECASE,
)


def parse_local_storage(html: str) -> Dict[str, str]:
    """Extract key/value pairs stored via window.localStorage.setItem."""
    matches = LOCAL_STORAGE_PATTERN.findall(html)
    return {key: value for key, value in matches}


def with_base(base_url: str, path: str) -> str:
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))


