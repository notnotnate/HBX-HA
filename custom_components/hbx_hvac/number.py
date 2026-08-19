"""Number entities for HBX HVAC — writable setpoints for ZON and ECO devices."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, device_display_name
from .coordinator import HbxHvacCoordinator


@dataclass(frozen=True, kw_only=True)
class HbxNumberDescription(NumberEntityDescription):
    value_fn: Callable[[dict[str, Any]], float | None]
    patch_key: str


# ── ZON zone controller numbers ───────────────────────────────────────────────

ZON_NUMBERS: tuple[HbxNumberDescription, ...] = (
    HbxNumberDescription(
        key="wwsd",
        name="WWSD Setpoint",
        patch_key="wwsd",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        native_min_value=32,
        native_max_value=150,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("wwsd"),
    ),
    HbxNumberDescription(
        key="dhwTarget",
        name="DHW Target",
        patch_key="dhwTarget",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        native_min_value=32,
        native_max_value=200,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("dhwTarget"),
    ),
)

# ── ECO boiler controller numbers ─────────────────────────────────────────────

ECO_NUMBERS: tuple[HbxNumberDescription, ...] = (
    HbxNumberDescription(
        key="wwsd",
        name="WWSD Setpoint",
        patch_key="wwsd",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        native_min_value=32,
        native_max_value=150,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("wwsd"),
    ),
    HbxNumberDescription(
        key="cwsd",
        name="CWSD Setpoint",
        patch_key="cwsd",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        native_min_value=32,
        native_max_value=150,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("cwsd"),
    ),
    HbxNumberDescription(
        key="dhwTarget",
        name="DHW Target",
        patch_key="dhwTarget",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        native_min_value=32,
        native_max_value=200,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("dhwTarget"),
    ),
    HbxNumberDescription(
        key="hotTankSetpointMax",
        name="Hot Tank Max",
        patch_key="hotTankSetpointMax",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        native_min_value=32,
        native_max_value=200,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("hotTankSetpointMax"),
    ),
    HbxNumberDescription(
        key="coldTankSetpointMax",
        name="Cold Tank Max",
        patch_key="coldTankSetpointMax",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        native_min_value=32,
        native_max_value=150,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.get("coldTankSetpointMax"),
    ),
)


# ── Platform setup ────────────────────────────────────────────────────────────

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HbxHvacCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[HbxNumber] = []

    for device in coordinator.data or []:
        sync_code = device["syncCode"]
        dtype = device.get("deviceType")
        device_name = device.get("name") or device_display_name(sync_code)

        if dtype == "ZON":
            entities += [
                HbxNumber(coordinator, sync_code, desc, device_name)
                for desc in ZON_NUMBERS
            ]
        elif dtype == "ECO":
            entities += [
                HbxNumber(coordinator, sync_code, desc, device_name)
                for desc in ECO_NUMBERS
            ]

    async_add_entities(entities)


class HbxNumber(CoordinatorEntity[HbxHvacCoordinator], NumberEntity):
    entity_description: HbxNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HbxHvacCoordinator,
        sync_code: str,
        description: HbxNumberDescription,
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
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self._device)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api.patch_device(
            self._sync_code, {self.entity_description.patch_key: value}
        )
        await self.coordinator.async_request_refresh()
