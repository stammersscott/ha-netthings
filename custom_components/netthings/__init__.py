"""NetThings integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import socketio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_HOST, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


@dataclass
class NetThingsData:
    """Runtime data for a NetThings config entry."""

    host: str
    sio: socketio.Client
    data: list[dict[str, Any]] | None = None
    process_data: Any = None
    process_connection: Any = None
    available: bool = False


type NetThingsConfigEntry = ConfigEntry[NetThingsData]


async def async_setup(
    hass: HomeAssistant,
    config: dict[str, Any],
) -> bool:
    """Set up the NetThings integration."""

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NetThingsConfigEntry,
) -> bool:
    """Set up NetThings from a config entry."""

    host = entry.data[CONF_HOST]

    sio = socketio.Client(
        reconnection=True,
        reconnection_attempts=0,
        reconnection_delay=5,
        reconnection_delay_max=60,
        randomization_factor=0.25,
        request_timeout=10,
    )

    runtime_data = NetThingsData(
        host=host,
        sio=sio,
    )

    entry.runtime_data = runtime_data

    @sio.event
    def connect() -> None:
        """Handle a successful connection."""

        _LOGGER.info(
            "Connected to NetThings at %s with SID %s",
            host,
            sio.sid,
        )

        runtime_data.available = True

        hass.add_job(
            _async_connection_changed,
            True,
        )

    @sio.event
    def disconnect() -> None:
        """Handle a disconnection."""

        _LOGGER.warning(
            "Disconnected from NetThings at %s. "
            "Automatic reconnection will be attempted.",
            host,
        )

        runtime_data.available = False

        hass.add_job(
            _async_connection_changed,
            False,
        )

    @sio.event
    def connect_error(data: Any) -> None:
        """Handle a connection error."""

        _LOGGER.warning(
            "NetThings connection error for %s: %s",
            host,
            data,
        )

    @sio.on("refresh:instantaneous")
    def refresh(data: list[dict[str, Any]]) -> None:
        """Handle instantaneous data from NetThings."""

        hass.add_job(
            _async_process_data,
            data,
        )

    async def _async_process_data(
        data: list[dict[str, Any]],
    ) -> None:
        """Process data received from NetThings."""

        runtime_data.data = data
        runtime_data.available = True

        if runtime_data.process_data is not None:
            await runtime_data.process_data(data)

    async def _async_connection_changed(
        available: bool,
    ) -> None:
        """Notify sensors of a connection state change."""

        runtime_data.available = available

        if runtime_data.process_connection is not None:
            await runtime_data.process_connection(available)

    try:
        await hass.async_add_executor_job(
            lambda: sio.connect(
                f"http://{host}",
            )
        )

    except Exception as err:
        _LOGGER.error(
            "Unable to connect to NetThings at %s: %s",
            host,
            err,
        )

        if sio.connected:
            await hass.async_add_executor_job(
                sio.disconnect,
            )

        raise ConfigEntryNotReady from err

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: NetThingsConfigEntry,
) -> bool:
    """Unload a NetThings config entry."""

    sio = entry.runtime_data.sio

    if sio.connected:
        await hass.async_add_executor_job(
            sio.disconnect,
        )

    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )