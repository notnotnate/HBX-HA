"""Sensor entities for HBX HVAC (SensorLinx)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, device_display_name
from .coordinator import HbxHvacCoordinator

FLOOR_SENSOR_FAULT = -36.9


@dataclass(frozen=True, kw_only=True)
class HbxSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    available_fn: Callable[[dict[str, Any]], bool] = lambda d: True


# ── THM thermostat sensors ────────────────────────────────────────────────────

THM_SENSORS: tuple[HbxSensorDescription, ...] = (
    HbxSensorDescription(
        key="room",
        name="Room Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("room"),
    ),
    HbxSensorDescription(
        key="floor",
        name="Floor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: (
            None if d.get("floor") == FLOOR_SENSOR_FAULT else d.get("floor")
        ),
    ),
    HbxSensorDescription(
        key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("humidity"),
    ),
    HbxSensorDescription(
        key="heatTarget",
        name="Heat Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("heatTarget"),
    ),
    HbxSensorDescription(
        key="coolTarget",
        name="Cool Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("coolTarget"),
    ),
    HbxSensorDescription(
        key="zone",
        name="Zone",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("zone"),
    ),
    HbxSensorDescription(
        key="priority",
        name="Priority",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("priority"),
    ),
    HbxSensorDescription(
        key="demand1",
        name="Heating Demand",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        value_fn=lambda d: d.get("demand1"),
    ),
    HbxSensorDescription(
        key="demand2",
        name="Cooling Demand",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        value_fn=lambda d: d.get("demand2"),
    ),
)

# ── ECO boiler controller sensors ────────────────────────────────────────────

def _eco_temp(index: int, field: str) -> Callable[[dict], Any]:
    def _fn(d: dict) -> Any:
        temps = d.get("temperatures", [])
        if index < len(temps) and temps[index].get("enabled"):
            return temps[index].get(field)
        return None
    return _fn


ECO_SENSORS: tuple[HbxSensorDescription, ...] = (
    HbxSensorDescription(
        key="tank_temp",
        name="Tank Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_eco_temp(0, "current"),
    ),
    HbxSensorDescription(
        key="tank_target",
        name="Tank Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.CONFIG,
        value_fn=_eco_temp(0, "target"),
    ),
    HbxSensorDescription(
        key="outdoor_temp",
        name="Outdoor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_eco_temp(2, "current"),
    ),
)


# ── Platform setup ────────────────────────────────────────────────────────────

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HbxHvacCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[HbxSensor] = []

    for device in coordinator.data or []:
        sync_code = device["syncCode"]
        dtype = device.get("deviceType")

        if dtype == "THM":
            entities += [
                HbxSensor(coordinator, sync_code, desc) for desc in THM_SENSORS
            ]
        elif dtype == "ECO":
            entities += [
                HbxSensor(coordinator, sync_code, desc) for desc in ECO_SENSORS
            ]

    async_add_entities(entities)


class HbxSensor(CoordinatorEntity[HbxHvacCoordinator], SensorEntity):
    entity_description: HbxSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HbxHvacCoordinator,
        sync_code: str,
        description: HbxSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._sync_code = sync_code
        self._attr_unique_id = f"{DOMAIN}_{sync_code}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sync_code)},
            "name": device_display_name(sync_code),
        }

    @property
    def _device(self) -> dict[str, Any]:
        return self.coordinator.device_data(self._sync_code)

    @property
    def available(self) -> bool:
        return self._device.get("connected", False)

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._device)
