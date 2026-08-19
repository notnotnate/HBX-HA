"""Switch entities for HBX HVAC (SensorLinx)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, device_display_name
from .coordinator import HbxHvacCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HbxHvacCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        HbxAwaySwitch(
            coordinator,
            device["syncCode"],
            device.get("name") or device_display_name(device["syncCode"]),
        )
        for device in (coordinator.data or [])
        if device.get("deviceType") == "THM"
    ]
    async_add_entities(entities)


class HbxAwaySwitch(CoordinatorEntity[HbxHvacCoordinator], SwitchEntity):
    """Switch to toggle away mode on a THM thermostat."""

    _attr_has_entity_name = True
    _attr_name = "Away"
    _attr_icon = "mdi:home-export-outline"

    def __init__(self, coordinator: HbxHvacCoordinator, sync_code: str, device_name: str) -> None:
        super().__init__(coordinator)
        self._sync_code = sync_code
        self._attr_unique_id = f"{DOMAIN}_{sync_code}_away"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sync_code)},
            "name": device_name,
        }

    @property
    def _device(self) -> dict[str, Any]:
        return self.coordinator.device_data(self._sync_code)

    @property
    def available(self) -> bool:
        return self._device.get("connected", False)

    @property
    def is_on(self) -> bool:
        return self._device.get("away", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.patch_device(self._sync_code, {"away": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.patch_device(self._sync_code, {"away": False})
        await self.coordinator.async_request_refresh()
