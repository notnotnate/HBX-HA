"""Climate entities for HBX HVAC (SensorLinx THM thermostats)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, device_display_name
from .coordinator import HbxHvacCoordinator

# cngOvr field: 0=auto, 1=heat, 2=cool, 3=off
_CNGVR_TO_MODE: dict[int, HVACMode] = {
    0: HVACMode.HEAT_COOL,
    1: HVACMode.HEAT,
    2: HVACMode.COOL,
    3: HVACMode.OFF,
}
_MODE_TO_CNGVR: dict[HVACMode, int] = {v: k for k, v in _CNGVR_TO_MODE.items()}

# fanMode field: 0=off, 1=on, 2=intermittent
_FAN_INT_TO_STR: dict[int, str] = {0: "off", 1: "on", 2: "auto"}
_FAN_STR_TO_INT: dict[str, int] = {v: k for k, v in _FAN_INT_TO_STR.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HbxHvacCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        HbxThermostat(
            coordinator,
            device["syncCode"],
            device.get("name") or device_display_name(device["syncCode"]),
        )
        for device in (coordinator.data or [])
        if device.get("deviceType") == "THM"
    ]
    async_add_entities(entities)


class HbxThermostat(CoordinatorEntity[HbxHvacCoordinator], ClimateEntity):
    """Climate entity representing a SensorLinx THM thermostat."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL]
    _attr_fan_modes = ["off", "on", "auto"]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.FAN_MODE
    )

    def __init__(self, coordinator: HbxHvacCoordinator, sync_code: str, device_name: str) -> None:
        super().__init__(coordinator)
        self._sync_code = sync_code
        self._attr_unique_id = f"{DOMAIN}_{sync_code}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sync_code)},
            "name": device_name,
            "manufacturer": "HBX Control Systems",
            "model": "THM Thermostat",
            "sw_version": str(coordinator.device_data(sync_code).get("firmVer", "")),
        }

    @property
    def _device(self) -> dict:
        return self.coordinator.device_data(self._sync_code)

    @property
    def available(self) -> bool:
        return self._device.get("connected", False)

    @property
    def current_temperature(self) -> float | None:
        return self._device.get("room")

    @property
    def target_temperature(self) -> float | None:
        mode = self.hvac_mode
        if mode == HVACMode.HEAT:
            return self._device.get("heatTarget")
        if mode == HVACMode.COOL:
            return self._device.get("coolTarget")
        return None

    @property
    def target_temperature_high(self) -> float | None:
        return self._device.get("coolTarget")

    @property
    def target_temperature_low(self) -> float | None:
        return self._device.get("heatTarget")

    @property
    def hvac_mode(self) -> HVACMode:
        return _CNGVR_TO_MODE.get(self._device.get("cngOvr", 3), HVACMode.OFF)

    @property
    def hvac_action(self) -> HVACAction:
        for demand in self._device.get("demands", []):
            if demand.get("key") == "heating" and demand.get("activated"):
                return HVACAction.HEATING
            if demand.get("key") == "cooling" and demand.get("activated"):
                return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def fan_mode(self) -> str:
        return _FAN_INT_TO_STR.get(self._device.get("fanMode", 0), "off")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        patch: dict[str, Any] = {}
        if (high := kwargs.get("target_temp_high")) is not None:
            patch["coolTarget"] = high
        if (low := kwargs.get("target_temp_low")) is not None:
            patch["heatTarget"] = low
        if (temp := kwargs.get("temperature")) is not None:
            if self.hvac_mode == HVACMode.COOL:
                patch["coolTarget"] = temp
            else:
                patch["heatTarget"] = temp
        if patch:
            await self.coordinator.api.patch_device(self._sync_code, patch)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.coordinator.api.patch_device(
            self._sync_code, {"cngOvr": _MODE_TO_CNGVR[hvac_mode]}
        )
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self.coordinator.api.patch_device(
            self._sync_code, {"fanMode": _FAN_STR_TO_INT[fan_mode]}
        )
        await self.coordinator.async_request_refresh()
