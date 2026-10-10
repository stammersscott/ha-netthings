"""Config flow for NetThings."""

from __future__ import annotations

import logging

import socketio
import voluptuous as vol

from homeassistant import config_entries

from .const import CONF_HOST, DOMAIN

_LOGGER = logging.getLogger(__name__)


class NetThingsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a NetThings config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ):
        """Handle the initial configuration."""

        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()

            self._async_abort_entries_match(
                {CONF_HOST: host}
            )

            try:
                await self.hass.async_add_executor_job(
                    self._test_connection,
                    host,
                )

            except Exception:
                _LOGGER.exception(
                    "Unable to connect to NetThings device at %s",
                    host,
                )
                errors["base"] = "cannot_connect"

            else:
                return self.async_create_entry(
                    title=f"NetThings ({host})",
                    data={
                        CONF_HOST: host,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def _test_connection(host: str) -> None:
        """Test the connection to the NetThings device."""

        sio = socketio.Client(
            reconnection=False,
        )

        try:
            sio.connect(f"http://{host}")
        finally:
            if sio.connected:
                sio.disconnect()