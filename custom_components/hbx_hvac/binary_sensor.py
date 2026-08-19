"""Binary sensor entities for HBX HVAC (SensorLinx)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, device_display_name
from .coordinator import HbxHvacCoordinator


@dataclass(frozen=True, kw_only=True)
class HbxBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None]


# ── THM thermostat binary sensors ────────────────────────────────────────────

def _thm_demand(key: str) -> Callable[[dict[str, Any]], bool | None]:
    def _fn(d: dict[str, Any]) -> bool | None:
        for demand in d.get("demands", []):
            if demand.get("key") == key:
                return demand.get("activated", False)
        return None
    return _fn


THM_BINARY_SENSORS: tuple[HbxBinarySensorDescription, ...] = (
    HbxBinarySensorDescription(
        key="heating_active",
        name="Heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=_thm_demand("heating"),
    ),
    HbxBinarySensorDescription(
        key="cooling_active",
        name="Cooling",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=_thm_demand("cooling"),
    ),
    HbxBinarySensorDescription(
        key="fan_active",
        name="Fan",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=_thm_demand("fan"),
    ),
    HbxBinarySensorDescription(
        key="satisfied",
        name="Satisfied",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_thm_demand("satisfied"),
    ),
    HbxBinarySensorDescription(
        key="humidity_control",
        name="Humidity Control",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: bool(d.get("humidityOn")),
    ),
    HbxBinarySensorDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("connected", False),
    ),
    HbxBinarySensorDescription(
        key="floor_sensor_fault",
        name="Floor Sensor Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("floor") == -36.9,
    ),
)

# ── ZON zone controller binary sensors ───────────────────────────────────────

def _zon_demand(key: str) -> Callable[[dict[str, Any]], bool | None]:
    def _fn(d: dict[str, Any]) -> bool | None:
        for demand in d.get("demands", []):
            if demand.get("key") == key:
                return demand.get("activated", False)
        return None
    return _fn


def _zon_fancoil(key: str) -> Callable[[dict[str, Any]], bool | None]:
    def _fn(d: dict[str, Any]) -> bool | None:
        for fc in d.get("fancoil", []):
            if fc.get("key") == key:
                return fc.get("activated", False)
        return None
    return _fn


def _zon_pump(key: str) -> Callable[[dict[str, Any]], bool | None]:
    def _fn(d: dict[str, Any]) -> bool | None:
        for pump in d.get("pumps", []):
            if pump.get("key") == key:
                return pump.get("activated", False)
        return None
    return _fn


ZON_BINARY_SENSORS: tuple[HbxBinarySensorDescription, ...] = (
    HbxBinarySensorDescription(
        key="demand1",
        name="Demand 1",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=_zon_demand("demand1"),
    ),
    HbxBinarySensorDescription(
        key="demand2",
        name="Demand 2",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=_zon_demand("demand2"),
    ),
    HbxBinarySensorDescription(
        key="demand3",
        name="Demand 3",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=_zon_demand("demand3"),
    ),
    HbxBinarySensorDescription(
        key="fancoil_heating",
        name="Heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=_zon_fancoil("heating"),
    ),
    HbxBinarySensorDescription(
        key="fancoil_cooling",
        name="Cooling",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=_zon_fancoil("cooling"),
    ),
    HbxBinarySensorDescription(
        key="fancoil_fan",
        name="Fan",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=_zon_fancoil("fan"),
    ),
    HbxBinarySensorDescription(
        key="pump1",
        name="Pump 1",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_zon_pump("pump1"),
    ),
    HbxBinarySensorDescription(
        key="pump2",
        name="Pump 2",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_zon_pump("pump2"),
    ),
    HbxBinarySensorDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("connected", False),
    ),
)

# ── ECO boiler controller binary sensors ─────────────────────────────────────

def _eco_demand(name: str) -> Callable[[dict[str, Any]], bool | None]:
    def _fn(d: dict[str, Any]) -> bool | None:
        for demand in d.get("demands", []):
            if demand.get("name") == name:
                return demand.get("activated", False)
        return None
    return _fn


def _eco_pump(key: str) -> Callable[[dict[str, Any]], bool | None]:
    def _fn(d: dict[str, Any]) -> bool | None:
        for pump in d.get("pumps", []):
            if pump.get("key") == key:
                return pump.get("activated", False)
        return None
    return _fn


ECO_BINARY_SENSORS: tuple[HbxBinarySensorDescription, ...] = (
    HbxBinarySensorDescription(
        key="demand_heat",
        name="Heat Demand",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=_eco_demand("hd"),
    ),
    HbxBinarySensorDescription(
        key="demand_cool",
        name="Cool Demand",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=_eco_demand("cd"),
    ),
    HbxBinarySensorDescription(
        key="demand_dhw",
        name="Domestic Hot Water Demand",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=_eco_demand("dhw"),
    ),
    HbxBinarySensorDescription(
        key="stage1",
        name="Stage 1",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("stages", {}).get("stage1"),
    ),
    HbxBinarySensorDescription(
        key="stage2",
        name="Stage 2",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("stages", {}).get("stage2"),
    ),
    HbxBinarySensorDescription(
        key="stage3",
        name="Stage 3",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("stages", {}).get("stage3"),
    ),
    HbxBinarySensorDescription(
        key="stage4",
        name="Stage 4",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("stages", {}).get("stage4"),
    ),
    HbxBinarySensorDescription(
        key="backup",
        name="Backup",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("backup", {}).get("activated"),
    ),
    HbxBinarySensorDescription(
        key="reversing_valve",
        name="Reversing Valve",
        device_class=BinarySensorDeviceClass.OPENING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("reversingValve", {}).get("activated"),
    ),
    HbxBinarySensorDescription(
        key="pump1",
        name="Pump 1",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_eco_pump("pump1"),
    ),
    HbxBinarySensorDescription(
        key="pump2",
        name="Pump 2",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_eco_pump("pump2"),
    ),
    HbxBinarySensorDescription(
        key="wwsd",
        name="WWSD",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("wsd", {}).get("wwsd", {}).get("activated"),
    ),
    HbxBinarySensorDescription(
        key="cwsd",
        name="CWSD",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("wsd", {}).get("cwsd", {}).get("activated"),
    ),
    HbxBinarySensorDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("connected", False),
    ),
)


# ── Platform setup ────────────────────────────────────────────────────────────

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HbxHvacCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[HbxBinarySensor] = []

    for device in coordinator.data or []:
        sync_code = device["syncCode"]
        dtype = device.get("deviceType")
        device_name = device.get("name") or device_display_name(sync_code)

        if dtype == "THM":
            entities += [
                HbxBinarySensor(coordinator, sync_code, desc, device_name)
                for desc in THM_BINARY_SENSORS
            ]
        elif dtype == "ZON":
            entities += [
                HbxBinarySensor(coordinator, sync_code, desc, device_name)
                for desc in ZON_BINARY_SENSORS
            ]
        elif dtype == "ECO":
            entities += [
                HbxBinarySensor(coordinator, sync_code, desc, device_name)
                for desc in ECO_BINARY_SENSORS
            ]

    async_add_entities(entities)


class HbxBinarySensor(CoordinatorEntity[HbxHvacCoordinator], BinarySensorEntity):
    entity_description: HbxBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HbxHvacCoordinator,
        sync_code: str,
        description: HbxBinarySensorDescription,
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
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self._device)
