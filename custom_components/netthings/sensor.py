"""NetThings sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NetThingsConfigEntry
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NetThingsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NetThings sensors."""

    runtime_data = entry.runtime_data

    entities: dict[str, NetThingsSensor] = {}

    async def async_process_data(
        data: list[dict[str, Any]],
    ) -> None:
        """Process new NetThings data."""

        new_entities: list[NetThingsSensor] = []

        for channel in data:
            channel_id = str(channel["channelId"])

            sensors = (
                ("consumption", NetThingsConsumptionSensor),
                ("current_rate", NetThingsCurrentRateSensor),
                ("current_cost", NetThingsCurrentCostSensor),
                ("monthly_cost", NetThingsMonthlyCostSensor),
                ("estimated_co2", NetThingsCO2Sensor),
            )

            for sensor_type, sensor_class in sensors:
                unique_id = (
                    f"{entry.entry_id}_"
                    f"{channel_id}_"
                    f"{sensor_type}"
                )

                if unique_id in entities:
                    entities[unique_id].update_channel(channel)
                    continue

                entity = sensor_class(
                    entry,
                    channel,
                    sensor_type,
                )

                entities[unique_id] = entity
                new_entities.append(entity)

        if new_entities:
            async_add_entities(new_entities)

        for entity in entities.values():
            entity.async_write_ha_state()

    async def async_process_connection(
        available: bool,
    ) -> None:
        """Process a Socket.IO connection state change."""

        for entity in entities.values():
            entity.set_connection_state(available)
            entity.async_write_ha_state()

    runtime_data.process_data = async_process_data
    runtime_data.process_connection = async_process_connection

    if runtime_data.data is not None:
        await async_process_data(runtime_data.data)


class NetThingsSensor(SensorEntity):
    """Base class for a NetThings sensor."""

    _attr_should_poll = False

    def __init__(
        self,
        entry: NetThingsConfigEntry,
        channel: dict[str, Any],
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""

        self._entry = entry
        self._sensor_type = sensor_type
        self._channel = channel

        self._attr_unique_id = (
            f"{entry.entry_id}_"
            f"{channel['channelId']}_"
            f"{sensor_type}"
        )

        self._attr_has_entity_name = False

        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, entry.entry_id),
            },
            name="NetThings Energy Meter",
            manufacturer="NetThings",
        )

        self._attr_available = entry.runtime_data.available

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""

        return str(self._channel["channelId"])

    @property
    def channel_name(self) -> str:
        """Return the channel name."""

        return self._channel["channelName"]

    @property
    def channel_type(self) -> str:
        """Return the channel type."""

        return self._channel["channelType"]

    @callback
    def update_channel(
        self,
        channel: dict[str, Any],
    ) -> None:
        """Update the channel data."""

        self._channel = channel

    @callback
    def set_connection_state(
        self,
        available: bool,
    ) -> None:
        """Update connection availability."""

        self._attr_available = available


class NetThingsConsumptionSensor(NetThingsSensor):
    """NetThings consumption sensor."""

    def __init__(
        self,
        entry: NetThingsConfigEntry,
        channel: dict[str, Any],
        sensor_type: str,
    ) -> None:
        super().__init__(entry, channel, sensor_type)
        self._attr_name = channel["channelName"]

    @property
    def native_value(self) -> float | None:
        """Return the consumption value."""

        try:
            return float(self._channel["consumption"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the consumption unit."""

        return self._channel.get("consumptionUnit")

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return the sensor device class."""

        if self.channel_type == "water":
            return SensorDeviceClass.WATER

        return SensorDeviceClass.POWER

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class."""

        return SensorStateClass.MEASUREMENT


class NetThingsCurrentRateSensor(NetThingsSensor):
    """NetThings current rate sensor."""

    def __init__(
        self,
        entry: NetThingsConfigEntry,
        channel: dict[str, Any],
        sensor_type: str,
    ) -> None:
        super().__init__(entry, channel, sensor_type)
        self._attr_name = f"{channel['channelName']} Current Rate"

    @property
    def native_value(self) -> float | None:
        """Return the current rate."""

        try:
            return float(self._channel["unitCostInPence"]) / 100
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the currency."""

        return self._channel.get("currency")

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return the sensor device class."""

        return SensorDeviceClass.MONETARY

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class."""

        return SensorStateClass.MEASUREMENT

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""

        return {
            "Channel ID": self.channel_id,
            "Channel Type": self.channel_type,
            "Current Rate in Pence": (
                f"{self._channel.get('unitCostInPence')} p"
            ),
        }


class NetThingsCurrentCostSensor(NetThingsSensor):
    """NetThings current cost sensor."""

    def __init__(
        self,
        entry: NetThingsConfigEntry,
        channel: dict[str, Any],
        sensor_type: str,
    ) -> None:
        super().__init__(entry, channel, sensor_type)
        self._attr_name = f"{channel['channelName']} Current Cost"

    @property
    def native_value(self) -> float | None:
        """Return the current cost."""

        try:
            return float(self._channel["currentCost"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the cost unit."""

        currency = self._channel.get("currency")

        if currency is None:
            return None

        return f"{currency}/h"

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class."""

        return SensorStateClass.MEASUREMENT

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""

        return {
            "Channel ID": self.channel_id,
            "Channel Type": self.channel_type,
        }


class NetThingsMonthlyCostSensor(NetThingsSensor):
    """NetThings monthly accumulated cost sensor."""

    def __init__(
        self,
        entry: NetThingsConfigEntry,
        channel: dict[str, Any],
        sensor_type: str,
    ) -> None:
        super().__init__(entry, channel, sensor_type)
        self._attr_name = (
            f"{channel['channelName']} Monthly Accumulated Cost"
        )

    @property
    def native_value(self) -> float | None:
        """Return the monthly accumulated cost."""

        try:
            return float(self._channel["monthlyAccumulatedCost"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the currency."""

        return self._channel.get("currency")

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class."""

        return SensorStateClass.MEASUREMENT

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""

        return {
            "Channel ID": self.channel_id,
            "Channel Type": self.channel_type,
        }


class NetThingsCO2Sensor(NetThingsSensor):
    """NetThings estimated CO2 sensor."""

    def __init__(
        self,
        entry: NetThingsConfigEntry,
        channel: dict[str, Any],
        sensor_type: str,
    ) -> None:
        super().__init__(entry, channel, sensor_type)
        self._attr_name = (
            f"{channel['channelName']} Current Estimated CO2"
        )

    @property
    def native_value(self) -> float | None:
        """Return the estimated CO2 value."""

        try:
            return float(self._channel["CO2"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the CO2 unit."""

        return "Kg/h"

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class."""

        return SensorStateClass.MEASUREMENT

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""

        return {
            "Channel ID": self.channel_id,
            "Channel Type": self.channel_type,
        }