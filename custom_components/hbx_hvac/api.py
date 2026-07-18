"""REST API client for the SensorLinx Connect API (HBX HVAC).

Authentication: X-Api-Key header, format "PREFIX:uuid"
Base URL: https://connect.sensorlinx.co/v1

All THM thermostat fields are readOnly per the OpenAPI schema.
This API is read-only — thermostat control is done at the physical device.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class HbxApiError(Exception):
    """Raised when the API returns an error or is unreachable."""


class HbxHvacApi:
    """Async wrapper around the SensorLinx Connect REST API."""

    def __init__(self, api_key: str, session: aiohttp.ClientSession) -> None:
        self._headers = {"X-Api-Key": api_key}
        self._session = session

    async def get_all_devices(self) -> list[dict[str, Any]]:
        """Return all devices from GET /devices."""
        data = await self._get("/devices")
        return data.get("items", [])

    async def patch_device(self, sync_code: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update device fields via PATCH /devices/{syncCode}."""
        url = API_BASE + f"/devices/{sync_code}"
        try:
            async with self._session.patch(
                url, headers=self._headers, json=data, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise HbxApiError(f"PATCH {url} failed: {err}") from err

    async def _get(self, path: str) -> dict[str, Any]:
        url = API_BASE + path
        try:
            async with self._session.get(
                url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise HbxApiError(f"GET {url} failed: {err}") from err
