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

THM_BINARY_SENSORS: tuple[HbxBinarySensorDescription, ...] = (
    HbxBinarySensorDescription(
        key="heating_active",
        name="Heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda d: (d.get("demand1") or 0) > 0,
    ),
    HbxBinarySensorDescription(
        key="cooling_active",
        name="Cooling",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=lambda d: (d.get("demand2") or 0) > 0,
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

# ── ECO boiler controller binary sensors ─────────────────────────────────────

def _relay(key: str) -> Callable[[dict], bool | None]:
    return lambda d: d.get("relays", {}).get(key)


def _demand(name: str) -> Callable[[dict], bool | None]:
    def _fn(d: dict) -> bool | None:
        for demand in d.get("demands", []):
            if demand.get("name") == name:
                return demand.get("activated", False)
        return None
    return _fn


ECO_BINARY_SENSORS: tuple[HbxBinarySensorDescription, ...] = (
    # Relays
    HbxBinarySensorDescription(
        key="relay_stage1",
        name="Stage 1",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("stage1"),
    ),
    HbxBinarySensorDescription(
        key="relay_stage2",
        name="Stage 2",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("stage2"),
    ),
    HbxBinarySensorDescription(
        key="relay_stage3",
        name="Stage 3",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("stage3"),
    ),
    HbxBinarySensorDescription(
        key="relay_stage4",
        name="Stage 4",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("stage4"),
    ),
    HbxBinarySensorDescription(
        key="relay_pump1",
        name="Pump 1",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("pump1"),
    ),
    HbxBinarySensorDescription(
        key="relay_pump2",
        name="Pump 2",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("pump2"),
    ),
    HbxBinarySensorDescription(
        key="relay_pump3",
        name="Pump 3",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("pump3"),
    ),
    HbxBinarySensorDescription(
        key="relay_backup",
        name="Backup",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("backup"),
    ),
    HbxBinarySensorDescription(
        key="relay_reversing_valve",
        name="Reversing Valve",
        device_class=BinarySensorDeviceClass.OPENING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_relay("reversingValve"),
    ),
    # Demands
    HbxBinarySensorDescription(
        key="demand_heat",
        name="Heat Demand",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=_demand("hd"),
    ),
    HbxBinarySensorDescription(
        key="demand_cool",
        name="Cool Demand",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=_demand("cd"),
    ),
    HbxBinarySensorDescription(
        key="demand_dhw",
        name="Domestic Hot Water Demand",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=_demand("dhw"),
    ),
    # Connectivity
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
