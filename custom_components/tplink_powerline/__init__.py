"""TP-Link Powerline integration for Home Assistant.

Communicates with Powerline adapters via HomePlug AV Management Messages
(raw Ethernet, Ethertype 0x88E1). No IP address needed — works with
pure PLC adapters that are invisible to the router.

Requires: CAP_NET_RAW capability or running HA as root.

Reverse-engineered from the tpPLC Android app + HomePlug AV specification.
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import TpLinkPowerlineCoordinator
from .homeplug import is_available

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TP-Link Powerline from a config entry."""
    interface = entry.data.get("interface")
    initial_devices = entry.data.get("devices", [])

    if not is_available():
        _LOGGER.error(
            "HomePlug AV raw sockets not available. "
            "Home Assistant needs CAP_NET_RAW capability. "
            "For HAOS: install as add-on with host network. "
            "For Docker: use --cap-add=NET_RAW --network=host. "
            "For venv: sudo setcap cap_net_raw+ep $(readlink -f $(which python3))"
        )
        return False

    coordinator = TpLinkPowerlineCoordinator(hass, interface, initial_devices)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
