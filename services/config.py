from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


APP_DIR = Path.home() / ".tapo_pc_control"
CONFIG_FILE = APP_DIR / "config.json"
LEGACY_CONFIG_FILE = Path.home() / ".tapo_pc_control.json"
LOG_FILE = APP_DIR / "plugpilot.log"


@dataclass
class AppConfig:
    manual_ips: list[str] = field(default_factory=list)
    close_action: str = "tray"
    tray_notification: str = "once"
    start_minimized: bool = False
    dark_mode: bool = True
    kwh_price: float = 0.2516
    refresh_interval_seconds: int = 8
    known_devices: list[dict[str, str]] = field(default_factory=list)
    custom_aliases: dict[str, str] = field(default_factory=dict)
    window_width: int = 1080
    window_height: int = 720

    @classmethod
    def default(cls) -> "AppConfig":
        return cls()


class ConfigService:
    def __init__(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        data = asdict(AppConfig.default())

        try:
            current = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(current, dict):
                data.update(current)
        except Exception:
            pass

        # Migration des anciennes versions.
        try:
            legacy = json.loads(LEGACY_CONFIG_FILE.read_text(encoding="utf-8"))
            old_ips = legacy.get("manual_ips", [])
            data["manual_ips"] = list(
                dict.fromkeys(list(data.get("manual_ips", [])) + list(old_ips))
            )
        except Exception:
            pass

        known_devices: list[dict[str, str]] = []
        seen_hosts: set[str] = set()

        for item in data.get("known_devices", []):
            if not isinstance(item, dict):
                continue

            host = str(item.get("host", "")).strip()
            if not host or host in seen_hosts:
                continue

            seen_hosts.add(host)
            normalized: dict[str, Any] = {
                "host": host,
                "alias": str(item.get("alias") or host).strip(),
                "model": str(item.get("model") or "Prise TP-Link").strip(),
            }
            connection_config = item.get("connection_config")
            if isinstance(connection_config, dict):
                normalized["connection_config"] = connection_config
            known_devices.append(normalized)

        custom_aliases = {
            str(host).strip(): str(alias).strip()
            for host, alias in data.get("custom_aliases", {}).items()
            if str(host).strip() and str(alias).strip()
        }

        manual_ips = list(
            dict.fromkeys(
                str(ip).strip()
                for ip in data.get("manual_ips", [])
                if str(ip).strip()
            )
        )

        interval = max(
            5,
            min(int(data.get("refresh_interval_seconds", 8)), 60),
        )

        config = AppConfig(
            manual_ips=manual_ips,
            close_action=(
                str(data.get("close_action", "")).strip()
                if str(data.get("close_action", "")).strip()
                in {"tray", "quit", "ask"}
                else (
                    "tray"
                    if bool(data.get("close_to_tray", True))
                    else "quit"
                )
            ),
            tray_notification=(
                str(data.get("tray_notification", "once")).strip()
                if str(data.get("tray_notification", "once")).strip()
                in {"always", "once", "never"}
                else "once"
            ),
            start_minimized=bool(data.get("start_minimized", False)),
            dark_mode=bool(data.get("dark_mode", True)),
            kwh_price=max(0.0, float(data.get("kwh_price", 0.2516))),
            refresh_interval_seconds=interval,
            known_devices=known_devices,
            custom_aliases=custom_aliases,
            window_width=max(820, int(data.get("window_width", 1080))),
            window_height=max(560, int(data.get("window_height", 720))),
        )
        self.save(config)
        return config

    def save(self, config: AppConfig) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        temporary = CONFIG_FILE.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(asdict(config), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(CONFIG_FILE)

    def remember_devices(self, config: AppConfig, plugs: Iterable) -> None:
        remembered = {
            item["host"]: dict(item)
            for item in config.known_devices
            if item.get("host")
        }

        for plug in plugs:
            alias = config.custom_aliases.get(plug.host, plug.alias)
            item: dict[str, Any] = {
                "host": plug.host,
                "alias": alias,
                "model": plug.model,
            }

            cached = remembered.get(plug.host, {}).get("connection_config")
            if isinstance(cached, dict):
                item["connection_config"] = cached
            try:
                if plug.device is not None:
                    connection_config = plug.device.config.to_dict()
                    connection_config.pop("credentials", None)
                    item["connection_config"] = connection_config
            except Exception:
                previous = remembered.get(plug.host, {})
                cached = previous.get("connection_config")
                if isinstance(cached, dict):
                    item["connection_config"] = cached

            remembered[plug.host] = item

        config.known_devices = sorted(
            remembered.values(),
            key=lambda item: item["alias"].lower(),
        )
        self.save(config)

    def apply_custom_aliases(self, config: AppConfig, plugs: Iterable) -> None:
        for plug in plugs:
            alias = config.custom_aliases.get(plug.host)
            if alias:
                plug.alias = alias

    def rename_device(
        self,
        config: AppConfig,
        host: str,
        alias: str,
    ) -> None:
        alias = alias.strip()
        if not host or not alias:
            return

        config.custom_aliases[host] = alias
        for item in config.known_devices:
            if item.get("host") == host:
                item["alias"] = alias
                break

        self.save(config)

    def forget_device(self, config: AppConfig, host: str) -> None:
        config.known_devices = [
            item
            for item in config.known_devices
            if item.get("host") != host
        ]
        config.manual_ips = [
            ip for ip in config.manual_ips if ip != host
        ]
        config.custom_aliases.pop(host, None)
        self.save(config)

    def add_manual_ip(self, config: AppConfig, host: str) -> None:
        host = host.strip()
        if host and host not in config.manual_ips:
            config.manual_ips.append(host)
        self.save(config)
