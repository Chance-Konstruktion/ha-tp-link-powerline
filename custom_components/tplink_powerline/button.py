"""Button platform for TP-Link Powerline diagnostics.

Press to run a full diagnostic scan and dump raw HomePlug AV
frame data to the Home Assistant logs for troubleshooting.
"""

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .homeplug import async_diagnose

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up diagnostic button."""
    interface = entry.data.get("interface")
    async_add_entities([DiagnosticButton(interface)])


class DiagnosticButton(ButtonEntity):
    """Button that runs full HomePlug AV diagnostics and logs raw frames."""

    _attr_has_entity_name = True
    _attr_name = "Diagnose"
    _attr_icon = "mdi:stethoscope"

    def __init__(self, interface: str | None) -> None:
        self._interface = interface
        self._attr_unique_id = "tplink_plc_diagnose"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "tplink_powerline_network")},
            name="TP-Link Powerline Netzwerk",
            manufacturer=MANUFACTURER, model="Powerline Network")

    async def async_press(self) -> None:
        """Run diagnostics and log results."""
        _LOGGER.info("=== TP-Link Powerline Diagnostic Scan START ===")
        report = await async_diagnose(self._interface, timeout=8.0)
        for line in report.split("\n"):
            _LOGGER.info("DIAG: %s", line)
        _LOGGER.info("=== TP-Link Powerline Diagnostic Scan END ===")
