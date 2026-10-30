from __future__ import annotations

import asyncio
from typing import Any

from kasa import Credentials

from models.plug import PlugView
from services.config import AppConfig, ConfigService
from tplink.client import TpLinkClient


class PlugManager:
    """Couche réseau unique entre l'interface et python-kasa."""

    def __init__(
        self,
        config_service: ConfigService,
        config: AppConfig,
    ) -> None:
        self.config_service = config_service
        self.config = config
        self.client = TpLinkClient()
        self.devices: dict[str, Any] = {}
        self.plugs: dict[str, PlugView] = {}
        self._refresh_cursor = 0

    def cached_views(self) -> list[PlugView]:
        metadata = {
            item["host"]: item
            for item in self.config.known_devices
            if item.get("host")
        }
        for host in self.config.manual_ips:
            metadata.setdefault(
                host,
                {
                    "host": host,
                    "alias": host,
                    "model": "Prise TP-Link",
                },
            )

        views = [
            PlugView(
                host=host,
                alias=str(item.get("alias") or host),
                model=str(item.get("model") or "Prise TP-Link"),
                is_on=False,
                power_w=None,
                energy_today_kwh=None,
                online=False,
                device=None,
                connecting=True,
            )
            for host, item in metadata.items()
        ]
        self.config_service.apply_custom_aliases(self.config, views)
        self.plugs = {plug.host: plug for plug in views}
        return views

    async def connect_known(
        self,
        credentials: Credentials,
    ) -> list[PlugView]:
        metadata = {
            item["host"]: item
            for item in self.config.known_devices
            if item.get("host")
        }
        for host in self.config.manual_ips:
            metadata.setdefault(
                host,
                {
                    "host": host,
                    "alias": host,
                    "model": "Prise TP-Link",
                },
            )

        if not metadata:
            return []

        results = await asyncio.gather(
            *(
                self.client.connect_from_cache(
                    host,
                    credentials,
                    item,
                )
                for host, item in metadata.items()
            )
        )

        self.config_service.apply_custom_aliases(self.config, results)
        self._accept(results)
        self.config_service.remember_devices(self.config, results)
        return sorted(results, key=lambda plug: plug.alias.lower())

    async def discover(
        self,
        credentials: Credentials,
    ) -> list[PlugView]:
        discovered = await self.client.discover(
            credentials,
            self.config.manual_ips,
        )
        self.config_service.apply_custom_aliases(
            self.config,
            discovered,
        )

        merged = dict(self.plugs)
        for plug in discovered:
            merged[plug.host] = plug

        # Une recherche complète terminée résout les états "Connexion…".
        for plug in merged.values():
            plug.connecting = False

        results = sorted(
            merged.values(),
            key=lambda plug: plug.alias.lower(),
        )
        self._accept(results)
        self.config_service.remember_devices(
            self.config,
            discovered,
        )
        return results

    async def refresh_next(self) -> PlugView | None:
        online_hosts = [
            host
            for host, device in self.devices.items()
            if device is not None and host in self.plugs
        ]
        if not online_hosts:
            return None

        self._refresh_cursor %= len(online_hosts)
        host = online_hosts[self._refresh_cursor]
        self._refresh_cursor += 1

        previous = self.plugs[host]
        plug = await self.client.refresh_device(
            host,
            self.devices[host],
            previous,
        )
        self.config_service.apply_custom_aliases(
            self.config,
            [plug],
        )
        self.plugs[host] = plug
        if plug.device is not None:
            self.devices[host] = plug.device
        return plug

    async def set_state(
        self,
        host: str,
        target_on: bool,
    ) -> PlugView:
        plug = self.plugs[host]
        device = self.devices.get(host) or plug.device
        if device is None:
            raise RuntimeError("La prise n'est pas connectée.")

        await self.client.set_state(device, target_on)
        refreshed = await self.client.refresh_device(
            host,
            device,
            plug,
        )
        self.config_service.apply_custom_aliases(
            self.config,
            [refreshed],
        )
        self.plugs[host] = refreshed
        self.devices[host] = device
        return refreshed

    def forget(self, host: str) -> None:
        self.plugs.pop(host, None)
        self.devices.pop(host, None)
        self.config_service.forget_device(
            self.config,
            host,
        )

    def rename(self, host: str, alias: str) -> None:
        self.config_service.rename_device(
            self.config,
            host,
            alias,
        )
        if host in self.plugs:
            self.plugs[host].alias = alias

    def _accept(self, plugs: list[PlugView]) -> None:
        self.plugs = {plug.host: plug for plug in plugs}
        self.devices = {
            plug.host: plug.device
            for plug in plugs
            if plug.online and plug.device is not None
        }
