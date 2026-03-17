"""DataUpdateCoordinator for HBX HVAC."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HbxApiError, HbxHvacApi
from .const import CONF_API_KEY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class HbxHvacCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Polls all SensorLinx devices and distributes data to entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.api = HbxHvacApi(
            api_key=entry.data[CONF_API_KEY],
            session=async_get_clientsession(hass),
        )
        interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            return await self.api.get_all_devices()
        except HbxApiError as err:
            raise UpdateFailed(str(err)) from err

    def device_data(self, sync_code: str) -> dict[str, Any]:
        """Return the latest data dict for a specific syncCode."""
        for device in (self.data or []):
            if device.get("syncCode") == sync_code:
                return device
        return {}
