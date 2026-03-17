"""Constants for HBX HVAC integration."""

DOMAIN = "hbx_hvac"

CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

API_BASE = "https://connect.sensorlinx.co/v1"

DEFAULT_SCAN_INTERVAL = 30  # seconds


def device_display_name(sync_code: str) -> str:
    """Return display name from syncCode, stripping the leading 'A' prefix.

    e.g. 'ATHM-6062' -> 'THM-6062', 'AECO-2078' -> 'ECO-2078'
    """
    return sync_code[1:] if sync_code.startswith("A") else sync_code
