"""Constants for Powerline Network integration (HomePlug AV / MEDIAXTREAM)."""

from typing import Any

DOMAIN = "tplink_powerline"
MANUFACTURER = "Powerline"

# Polling interval (seconds)
DEFAULT_SCAN_INTERVAL = 60
CONF_SCAN_INTERVAL = "scan_interval"
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 600

# Platforms
PLATFORMS = ["sensor", "switch", "button"]

# Network-wide device identifier
NETWORK_DEVICE_ID = "powerline_network"
NETWORK_DEVICE_NAME = "Powerline Network"


def get_mac(dev: dict[str, Any]) -> str:
    """Extract and normalize MAC address from a device dict."""
    return (dev.get("mac") or dev.get("plcmac") or "").upper()
