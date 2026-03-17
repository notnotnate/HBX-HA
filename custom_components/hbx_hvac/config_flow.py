"""Config flow for HBX HVAC (SensorLinx Connect)."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HbxApiError, HbxHvacApi
from .const import CONF_API_KEY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class HbxHvacConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HBX HVAC."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            api = HbxHvacApi(
                api_key=user_input[CONF_API_KEY],
                session=async_get_clientsession(self.hass),
            )
            try:
                devices = await api.get_all_devices()
            except HbxApiError:
                errors["base"] = "cannot_connect"
            else:
                # Use the account prefix (before ":") as the unique ID
                account_id = user_input[CONF_API_KEY].split(":")[0]
                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_configured()

                thm_count = sum(1 for d in devices if d.get("deviceType") == "THM")
                return self.async_create_entry(
                    title=f"SensorLinx ({thm_count} thermostat{'s' if thm_count != 1 else ''})",
                    data=user_input,
                )

        return self.async_show_form(step_id="user", data_schema=STEP_SCHEMA, errors=errors)
