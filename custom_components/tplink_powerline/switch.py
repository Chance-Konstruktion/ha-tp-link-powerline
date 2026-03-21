"""Switch platform for TP-Link Powerline — LED control per adapter.

LED control via HomePlug AV vendor-specific MME.
Note: This is experimental — not all adapters may support
LED control over Layer 2. If it doesn't work, a Wireshark
capture of the Windows TP-Link Utility toggling LEDs would
help identify the correct MME format.
"""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import TpLinkPowerlineCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LED switches."""
    coordinator: TpLinkPowerlineCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_macs: set[str] = set()

    def _create_switches(devices: list[dict[str, Any]]) -> None:
        new_switches: list[SwitchEntity] = []
        for dev in devices:
            mac = (dev.get("mac") or dev.get("plcmac") or "").upper()
            if not mac or mac in tracked_macs:
                continue
            tracked_macs.add(mac)
            fw = dev.get("firmware_ver", "")
            new_switches.append(LedSwitch(coordinator, mac, fw))
            _LOGGER.info("Creating LED switch for adapter %s", mac)
        if new_switches:
            async_add_entities(new_switches)

    # Register for dynamic device discovery
    coordinator.register_new_device_callback(_create_switches)

    # Create switches for already-known devices
    if coordinator.data:
        _create_switches(coordinator.data.get("plc_devices", []))


class LedSwitch(CoordinatorEntity[TpLinkPowerlineCoordinator], SwitchEntity):
    """LED on/off switch for a single Powerline adapter."""

    _attr_has_entity_name = True
    _attr_name = "LED"
    _attr_icon = "mdi:led-on"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: TpLinkPowerlineCoordinator,
                 mac: str, firmware: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._is_on = True  # Assume on by default
        self._attr_unique_id = f"plc_{mac}_led"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            name=f"Powerline {mac[-8:]}",
            manufacturer=MANUFACTURER, model="Powerline Adapter",
            sw_version=firmware or None,
            via_device=(DOMAIN, "tplink_powerline_network"))

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        ok = await self.coordinator.async_set_led(self._mac, True)
        if ok:
            self._is_on = True
            self.async_write_ha_state()
        else:
            _LOGGER.warning("LED on failed for %s — may not support Layer 2 LED control", self._mac)

    async def async_turn_off(self, **kwargs: Any) -> None:
        ok = await self.coordinator.async_set_led(self._mac, False)
        if ok:
            self._is_on = False
            self.async_write_ha_state()
        else:
            _LOGGER.warning("LED off failed for %s — may not support Layer 2 LED control", self._mac)
