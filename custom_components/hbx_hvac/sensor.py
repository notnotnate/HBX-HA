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
        value_fn=lambda d: d.get("heatTarget"),
    ),
    HbxSensorDescription(
        key="coolTarget",
        name="Cool Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
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
        key="humidityTarget",
        name="Humidity Target",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("humidityTarget"),
    ),
    HbxSensorDescription(
        key="floorMin",
        name="Floor Min",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("floorMin"),
    ),
    HbxSensorDescription(
        key="floorMax",
        name="Floor Max",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("floorMax"),
    ),
    HbxSensorDescription(
        key="program",
        name="Program",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("program"),
    ),
)

# ── ZON zone controller sensors ───────────────────────────────────────────────

ZON_SENSORS: tuple[HbxSensorDescription, ...] = (
    HbxSensorDescription(
        key="wwsd",
        name="WWSD Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("wwsd"),
    ),
    HbxSensorDescription(
        key="dhwTarget",
        name="DHW Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("dhwTarget"),
    ),
    HbxSensorDescription(
        key="zonePriority",
        name="Priority",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("zonePriority"),
    ),
)

# ── ECO boiler controller sensors ────────────────────────────────────────────

def _eco_temp_by_type(type_val: str, field: str) -> Callable[[dict], Any]:
    def _fn(d: dict) -> Any:
        for t in d.get("temperatures", []):
            if t.get("enabled") and t.get("type") == type_val:
                return t.get(field)
        return None
    return _fn

def _eco_tank_current(d: dict) -> Any:
    """Return current temp for the main tank (type single or hot)."""
    for t in d.get("temperatures", []):
        if t.get("enabled") and t.get("type") in ("single", "hot"):
            return t.get("current")
    return None

def _eco_tank_target(d: dict) -> Any:
    """Return target temp for the main tank (type single or hot)."""
    for t in d.get("temperatures", []):
        if t.get("enabled") and t.get("type") in ("single", "hot"):
            return t.get("target")
    return None


ECO_SENSORS: tuple[HbxSensorDescription, ...] = (
    HbxSensorDescription(
        key="tank_temp",
        name="Tank Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_eco_tank_current,
    ),
    HbxSensorDescription(
        key="tank_target",
        name="Tank Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_eco_tank_target,
    ),
    HbxSensorDescription(
        key="cold_tank_temp",
        name="Cold Tank Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_eco_temp_by_type("cold", "current"),
    ),
    HbxSensorDescription(
        key="outdoor_temp",
        name="Outdoor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_eco_temp_by_type("outdoor", "current"),
    ),
    HbxSensorDescription(
        key="dhwTarget",
        name="DHW Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("dhwTarget"),
    ),
    HbxSensorDescription(
        key="wwsd",
        name="WWSD Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("wwsd"),
    ),
    HbxSensorDescription(
        key="cwsd",
        name="CWSD Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("cwsd"),
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
        device_name = device.get("name") or device_display_name(sync_code)

        if dtype == "THM":
            entities += [
                HbxSensor(coordinator, sync_code, desc, device_name) for desc in THM_SENSORS
            ]
        elif dtype == "ZON":
            entities += [
                HbxSensor(coordinator, sync_code, desc, device_name) for desc in ZON_SENSORS
            ]
        elif dtype == "ECO":
            entities += [
                HbxSensor(coordinator, sync_code, desc, device_name) for desc in ECO_SENSORS
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
        device_name: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._sync_code = sync_code
        self._attr_unique_id = f"{DOMAIN}_{sync_code}_{description.key}"
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
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._device)
