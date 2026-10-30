from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PlugView:
    host: str
    alias: str
    model: str
    is_on: bool
    power_w: float | None
    energy_today_kwh: float | None
    online: bool
    device: Any
    connecting: bool = False
