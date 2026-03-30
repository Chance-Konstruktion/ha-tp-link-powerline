"""Constants for Powerline Network integration (HomePlug AV / MEDIAXTREAM)."""

from functools import lru_cache
from typing import Any

DOMAIN = "tplink_powerline"
MANUFACTURER = "Powerline"

# Polling interval (seconds)
DEFAULT_SCAN_INTERVAL = 120
CONF_SCAN_INTERVAL = "scan_interval"
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 600

# Platforms
PLATFORMS = ["sensor", "binary_sensor", "switch", "button"]

# Network-wide device identifier
NETWORK_DEVICE_ID = "powerline_network"
NETWORK_DEVICE_NAME = "Powerline Network"


@lru_cache(maxsize=128)
def normalize_mac(mac: str) -> str:
    """Normalize MAC address to uppercase colon-separated format."""
    return mac.upper().strip()


def get_mac(dev: dict[str, Any]) -> str:
    """Extract and normalize MAC address from a device dict."""
    raw = dev.get("mac") or dev.get("plcmac") or ""
    return normalize_mac(raw) if raw else ""
