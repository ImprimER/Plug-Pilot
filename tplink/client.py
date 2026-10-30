from __future__ import annotations

import asyncio
import socket
from typing import Any

from kasa import Credentials, Device, Discover, Module

from models.plug import PlugView


class TpLinkClient:
    @staticmethod
    def local_ipv4() -> str | None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except Exception:
            return None
        finally:
            sock.close()

    @staticmethod
    def guessed_broadcast(ip: str | None) -> str | None:
        if not ip:
            return None
        parts = ip.split(".")
        return ".".join(parts[:3] + ["255"]) if len(parts) == 4 else None

    async def connect_from_cache(
        self,
        host: str,
        credentials: Credentials,
        metadata: dict[str, Any],
    ) -> PlugView:
        device = None
        cached_config = metadata.get("connection_config")

        if isinstance(cached_config, dict):
            try:
                config_data = dict(cached_config)
                config_data["host"] = host
                config_data["credentials"] = {
                    "username": credentials.username,
                    "password": credentials.password,
                }
                device_config = Device.Config.from_dict(config_data)
                device = await asyncio.wait_for(
                    Device.connect(config=device_config),
                    timeout=4.0,
                )
            except Exception:
                device = None

        if device is None:
            try:
                device = await Discover.discover_single(
                    host,
                    credentials=credentials,
                    discovery_timeout=4,
                    timeout=6,
                )
            except Exception:
                device = None

        if device is None:
            try:
                device = await Discover.try_connect_all(
                    host,
                    credentials=credentials,
                    timeout=9,
                )
            except Exception:
                device = None

        if device is not None:
            plug = await self.read_device(host, device, update=False)
            if plug is not None:
                return plug

        return PlugView(
            host=host,
            alias=str(metadata.get("alias") or host),
            model=str(metadata.get("model") or "Prise TP-Link"),
            is_on=False,
            power_w=None,
            energy_today_kwh=None,
            online=False,
            device=None,
            connecting=False,
        )

    async def discover(
        self,
        credentials: Credentials,
        manual_ips: list[str],
    ) -> list[PlugView]:
        devices: dict[str, Any] = {}
        target = self.guessed_broadcast(self.local_ipv4())
        targets = ["255.255.255.255"]
        if target and target not in targets:
            targets.append(target)

        for discovery_target in targets:
            try:
                devices.update(
                    await Discover.discover(
                        target=discovery_target,
                        credentials=credentials,
                        discovery_timeout=5,
                        timeout=6,
                    )
                )
            except Exception:
                pass

        for host in manual_ips:
            if host in devices:
                continue
            try:
                device = await Discover.try_connect_all(
                    host,
                    credentials=credentials,
                    timeout=9,
                )
                if device:
                    devices[host] = device
            except Exception:
                pass

        results = await asyncio.gather(
            *(
                self.read_device(str(host), device, update=True)
                for host, device in devices.items()
            )
        )
        return sorted(
            [plug for plug in results if plug is not None],
            key=lambda plug: plug.alias.lower(),
        )

    async def refresh_device(
        self,
        host: str,
        device: Any,
        previous: PlugView,
    ) -> PlugView:
        plug = await self.read_device(host, device, update=True)
        if plug is not None:
            return plug

        return PlugView(
            host=host,
            alias=previous.alias,
            model=previous.model,
            is_on=False,
            power_w=None,
            energy_today_kwh=None,
            online=False,
            device=device,
            connecting=False,
        )

    async def read_device(
        self,
        host: str,
        device: Any,
        *,
        update: bool,
    ) -> PlugView | None:
        try:
            if update:
                await asyncio.wait_for(device.update(), timeout=4.0)

            if not hasattr(device, "turn_on"):
                return None

            power_w = None
            energy_today = None
            try:
                energy = device.modules.get(Module.Energy)
                if energy is not None:
                    current = energy.current_consumption
                    today = energy.consumption_today
                    power_w = float(current) if current is not None else None
                    energy_today = float(today) if today is not None else None
            except Exception:
                pass

            return PlugView(
                host=host,
                alias=str(device.alias or host),
                model=str(device.model or "Modèle inconnu"),
                is_on=bool(device.is_on),
                power_w=power_w,
                energy_today_kwh=energy_today,
                online=True,
                device=device,
                connecting=False,
            )
        except Exception:
            return None

    @staticmethod
    async def set_state(device: Any, target_on: bool) -> None:
        if target_on:
            await asyncio.wait_for(device.turn_on(), timeout=5.0)
        else:
            await asyncio.wait_for(device.turn_off(), timeout=5.0)
        await asyncio.wait_for(device.update(), timeout=4.0)
