"""Switch platform for Powerline Network — LED control per adapter.

LED control via HomePlug AV vendor-specific MME.
Note: This is experimental — not all adapters may support
LED control over Layer 2.
"""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_mac
from .coordinator import TpLinkPowerlineCoordinator
from .sensor import _device_info

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
            mac = get_mac(dev)
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
        devs = coordinator.data.get("plc_devices", {})
        device_list = list(devs.values()) if isinstance(devs, dict) else devs
        _create_switches(device_list)


class LedSwitch(CoordinatorEntity[TpLinkPowerlineCoordinator], SwitchEntity):
    """LED on/off switch for a single Powerline adapter."""

    _attr_has_entity_name = True
    _attr_name = "LED"
    _attr_icon = "mdi:led-on"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: TpLinkPowerlineCoordinator,
                 mac: str, firmware: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._is_on = True  # Assume on by default
        self._attr_unique_id = f"plc_{mac}_led"
        self._attr_device_info = _device_info(mac, firmware)

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
