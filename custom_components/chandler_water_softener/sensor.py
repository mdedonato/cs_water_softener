"""Sensor platform for Chandler Water Softener."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    VOLUME_GALLONS,
    VOLUME_LITERS,
    UnitOfVolume,
    UnitOfFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    SENSOR_BATTERY_LEVEL,
    SENSOR_FLOW_RATE,
    SENSOR_HARDNESS_SETTING,
    SENSOR_SALT_LEVEL,
    SENSOR_WATER_USAGE,
)
from .coordinator import ChandlerWaterSoftenerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Chandler Water Softener sensor based on a config entry."""
    coordinator: ChandlerWaterSoftenerCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        ChandlerSaltLevelSensor(coordinator, entry),
        ChandlerWaterUsageSensor(coordinator, entry),
        ChandlerFlowRateSensor(coordinator, entry),
        ChandlerHardnessSettingSensor(coordinator, entry),
        ChandlerBatteryLevelSensor(coordinator, entry),
    ]

    async_add_entities(sensors)


class ChandlerWaterSoftenerSensor(SensorEntity):
    """Base class for Chandler Water Softener sensors."""

    def __init__(
        self,
        coordinator: ChandlerWaterSoftenerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.entry = entry
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.entry.data.get("device_name", "Chandler Water Softener"),
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success


class ChandlerSaltLevelSensor(ChandlerWaterSoftenerSensor):
    """Representation of a Chandler Water Softener salt level sensor."""

    _attr_name = "Salt Level"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None
        
        data = self.coordinator.data.get("data", {})
        parsed_data = data.get("parsed_data", {})
        return parsed_data.get("salt_level")

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:water-percent"


class ChandlerWaterUsageSensor(ChandlerWaterSoftenerSensor):
    """Representation of a Chandler Water Softener water usage sensor."""

    _attr_name = "Water Usage"
    _attr_native_unit_of_measurement = VOLUME_GALLONS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None
        
        data = self.coordinator.data.get("data", {})
        parsed_data = data.get("parsed_data", {})
        return parsed_data.get("water_usage")

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:water"


class ChandlerFlowRateSensor(ChandlerWaterSoftenerSensor):
    """Representation of a Chandler Water Softener flow rate sensor."""

    _attr_name = "Flow Rate"
    _attr_native_unit_of_measurement = "gal/min"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None
        
        data = self.coordinator.data.get("data", {})
        parsed_data = data.get("parsed_data", {})
        return parsed_data.get("flow_rate")

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:water-pump"


class ChandlerHardnessSettingSensor(ChandlerWaterSoftenerSensor):
    """Representation of a Chandler Water Softener hardness setting sensor."""

    _attr_name = "Hardness Setting"
    _attr_native_unit_of_measurement = "grains/gal"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None
        
        data = self.coordinator.data.get("data", {})
        parsed_data = data.get("parsed_data", {})
        return parsed_data.get("hardness_setting")

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:tune"


class ChandlerBatteryLevelSensor(ChandlerWaterSoftenerSensor):
    """Representation of a Chandler Water Softener battery level sensor."""

    _attr_name = "Battery Level"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None
        
        data = self.coordinator.data.get("data", {})
        parsed_data = data.get("parsed_data", {})
        return parsed_data.get("battery_level")

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:battery" 