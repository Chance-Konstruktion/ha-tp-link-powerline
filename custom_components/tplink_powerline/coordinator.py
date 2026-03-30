"""DataUpdateCoordinator for Powerline Network.

Uses HomePlug AV raw Ethernet (Layer 2) -- no IP needed.
Discovers new devices every poll cycle (default 120s).
"""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, get_mac

_LOGGER = logging.getLogger(__name__)

LED_SET_TIMEOUT = 10.0


class TpLinkPowerlineCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls Powerline adapters via HomePlug AV Layer 2."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        interface: str | None,
        initial_devices: list[dict[str, Any]],
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        from .homeplug import HomeplugAV

        self.hp = HomeplugAV(interface)
        self.interface = interface or self.hp.interface
        self.devices: dict[str, dict[str, Any]] = {}
        self._known_macs: set[str] = set()
        self._new_device_callbacks: list[Callable[[list[dict[str, Any]]], None]] = []
        self.led_states: dict[str, bool] = {}

        # Index initial devices by MAC
        for dev in initial_devices:
            mac = get_mac(dev)
            if mac:
                self.devices[mac] = dev
                self._known_macs.add(mac)
                self.led_states[mac] = True  # assume on

        super().__init__(
            hass, _LOGGER,
            name=f"{DOMAIN}_homeplug",
            update_interval=timedelta(seconds=scan_interval),
        )

    def register_new_device_callback(self, cb: Callable[[list[dict[str, Any]]], None]) -> None:
        """Register callback for when new devices are discovered."""
        self._new_device_callbacks.append(cb)

    async def _async_update_data(self) -> dict[str, Any]:
        """Full discovery + stats every poll cycle."""
        try:
            discovered = await self.hass.async_add_executor_job(
                self.hp.discover, 5.0
            )

            new_devices: list[dict[str, Any]] = []

            for dev in discovered:
                mac = get_mac(dev)
                if not mac:
                    continue

                if mac in self.devices:
                    self.devices[mac].update(dev)
                else:
                    self.devices[mac] = dev
                    self.led_states.setdefault(mac, True)
                    _LOGGER.info("New Powerline adapter discovered: %s (FW: %s)",
                                 mac, dev.get("firmware_ver", "?"))

                if mac not in self._known_macs:
                    self._known_macs.add(mac)
                    new_devices.append(dev)

            # Mark devices not seen in this scan
            seen_macs = {get_mac(d) for d in discovered}
            for mac in self.devices:
                self.devices[mac]["_online"] = mac in seen_macs

            # Notify platforms about new devices so they create entities
            if new_devices:
                _LOGGER.info("Notifying platforms about %d new device(s)", len(new_devices))
                for cb in self._new_device_callbacks:
                    try:
                        cb(new_devices)
                    except Exception:
                        _LOGGER.exception("Error in new device callback")

            # Build output data
            online_devices = {m: d for m, d in self.devices.items() if d.get("_online", True)}
            total_tx = sum(d.get("tx_rate", 0) for d in online_devices.values())
            total_rx = sum(d.get("rx_rate", 0) for d in online_devices.values())

            plc_rates: dict[str, dict[str, int]] = {}
            for mac, dev in self.devices.items():
                plc_rates[mac] = {
                    "tx": dev.get("tx_rate", 0),
                    "rx": dev.get("rx_rate", 0),
                }

            return {
                "online": len(online_devices) > 0,
                "plc_devices": self.devices,
                "plc_device_count": len(online_devices),
                "plc_device_count_total": len(self.devices),
                "plc_rates": plc_rates,
                "total_tx_rate": total_tx,
                "total_rx_rate": total_rx,
            }

        except Exception as err:
            _LOGGER.debug("Error polling Powerline adapters: %s", err)
            raise UpdateFailed(f"HomePlug AV error: {err}") from err

    async def async_set_led(self, mac: str, on: bool) -> bool:
        """Set LED on a specific adapter (by MAC)."""
        try:
            result = await asyncio.wait_for(
                self.hass.async_add_executor_job(self.hp.set_led, mac, on),
                timeout=LED_SET_TIMEOUT,
            )
            if result:
                self.led_states[mac] = on
            return result
        except asyncio.TimeoutError:
            _LOGGER.warning("LED control timed out for %s", mac)
            return False
        except Exception:
            _LOGGER.exception("LED control crashed for %s (on=%s)", mac, on)
            return False
