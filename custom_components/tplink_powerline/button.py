"""Button platform for Powerline Network diagnostics.

Press to run a full diagnostic scan and dump raw HomePlug AV
frame data to the Home Assistant logs for troubleshooting.
"""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .homeplug import async_diagnose
from .sensor import _network_device_info

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
        self._attr_device_info = _network_device_info()

    async def async_press(self) -> None:
        """Run diagnostics and log results."""
        _LOGGER.info("=== Powerline Network Diagnostic Scan START ===")
        report = await async_diagnose(self._interface, timeout=8.0)
        for line in report.split("\n"):
            _LOGGER.info("DIAG: %s", line)
        _LOGGER.info("=== Powerline Network Diagnostic Scan END ===")
