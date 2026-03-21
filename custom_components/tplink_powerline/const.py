"""Constants for TP-Link Powerline integration."""

DOMAIN = "tplink_powerline"
MANUFACTURER = "TP-Link"

# Polling interval (seconds)
DEFAULT_SCAN_INTERVAL = 60
CONF_SCAN_INTERVAL = "scan_interval"
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 600

# Platforms
PLATFORMS = ["sensor", "switch", "button"]
