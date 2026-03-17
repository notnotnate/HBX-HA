"""Climate entities for HBX HVAC (SensorLinx THM thermostats).

The SensorLinx Connect API is read-only for THM devices — all fields are
marked readOnly in the OpenAPI schema. Control is done at the physical device.

THM field reference (all °F, all readOnly):
  room        current room temperature
  floor       current floor temperature (-36.9 = sensor fault/unplugged)
  heatTarget  heating setpoint (32–150 °F)
  coolTarget  cooling setpoint (32–150 °F)
  humidity    relative humidity %
  demand1     heating demand byte  (0 = idle, >0 = active)
  demand2     cooling demand byte  (0 = idle, >0 = active)
  zone        zone number
  humidityOn  1 = humidity control enabled
"""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HbxHvacCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HbxHvacCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create one climate entity per connected THM device
    entities = [
        HbxThermostat(coordinator, device["syncCode"])
        for device in (coordinator.data or [])
        if device.get("deviceType") == "THM" and device.get("connected")
    ]
    async_add_entities(entities)


class HbxThermostat(CoordinatorEntity[HbxHvacCoordinator], ClimateEntity):
    """Read-only climate entity representing a SensorLinx THM thermostat.

    Supported HVAC modes: heat, cool, off (derived from demand bytes).
    No write support — the API is read-only for THM devices.
    """

    _attr_has_entity_name = True
    _attr_name = None  # uses device name
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL]
    _attr_supported_features = 0  # read-only: no HA-initiated setpoint changes

    def __init__(self, coordinator: HbxHvacCoordinator, sync_code: str) -> None:
        super().__init__(coordinator)
        self._sync_code = sync_code
        self._attr_unique_id = f"{DOMAIN}_{sync_code}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sync_code)},
            "name": self._device.get("name", sync_code),
            "manufacturer": "HBX Control Systems",
            "model": "THM Thermostat",
            "sw_version": str(self._device.get("firmVer", "")),
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
        """Return the active setpoint based on current mode."""
        mode = self.hvac_mode
        if mode == HVACMode.COOL:
            return self._device.get("coolTarget")
        return self._device.get("heatTarget")

    @property
    def target_temperature_high(self) -> float | None:
        return self._device.get("coolTarget")

    @property
    def target_temperature_low(self) -> float | None:
        return self._device.get("heatTarget")

    @property
    def hvac_mode(self) -> HVACMode:
        demand1 = self._device.get("demand1", 0)
        demand2 = self._device.get("demand2", 0)
        if demand1 > 0 and demand2 > 0:
            return HVACMode.HEAT_COOL
        if demand1 > 0:
            return HVACMode.HEAT
        if demand2 > 0:
            return HVACMode.COOL
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        demand1 = self._device.get("demand1", 0)
        demand2 = self._device.get("demand2", 0)
        if demand1 > 0:
            return HVACAction.HEATING
        if demand2 > 0:
            return HVACAction.COOLING
        return HVACAction.IDLE

