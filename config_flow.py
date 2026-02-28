"""Adds config flow for 17track.net."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaOptionsFlowHandler,
)

from .api import SeventeenTrackApiClient, SeventeenTrackError
from .const import (
    CONF_SHOW_ARCHIVED,
    CONF_SHOW_DELIVERED,
    DEFAULT_SHOW_ARCHIVED,
    DEFAULT_SHOW_DELIVERED,
    DOMAIN,
)

CONF_SHOW = {
    vol.Optional(CONF_SHOW_ARCHIVED, default=DEFAULT_SHOW_ARCHIVED): bool,
    vol.Optional(CONF_SHOW_DELIVERED, default=DEFAULT_SHOW_DELIVERED): bool,
}

_LOGGER = logging.getLogger(__name__)

OPTIONS_SCHEMA = vol.Schema(CONF_SHOW)
OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA),
}

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class SeventeenTrackConfigFlow(ConfigFlow, domain=DOMAIN):
    """17track config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> SchemaOptionsFlowHandler:
        """Get options flow for this handler."""
        return SchemaOptionsFlowHandler(config_entry, OPTIONS_FLOW)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""

        errors = {}
        if user_input:
            client = self._get_client(user_input[CONF_API_KEY])

            try:
                if not await client.async_validate_token():
                    errors["base"] = "invalid_auth"
            except SeventeenTrackError as err:
                _LOGGER.error("There was an error while validating token: %s", err)
                errors["base"] = "cannot_connect"

            if not errors:
                account_id = user_input[CONF_API_KEY][-8:]
                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"17TRACK {account_id}",
                    data=user_input,
                    options={
                        CONF_SHOW_ARCHIVED: DEFAULT_SHOW_ARCHIVED,
                        CONF_SHOW_DELIVERED: DEFAULT_SHOW_DELIVERED,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    @callback
    def _get_client(self, api_key: str) -> SeventeenTrackApiClient:
        session = aiohttp_client.async_get_clientsession(self.hass)
        return SeventeenTrackApiClient(session=session, api_key=api_key)
