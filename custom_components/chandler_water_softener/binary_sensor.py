"""Binary sensor platform for Chandler Water Softener."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    BINARY_SENSOR_REGENERATION_STATUS,
    BINARY_SENSOR_SYSTEM_STATUS,
)
from .coordinator import ChandlerWaterSoftenerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Chandler Water Softener binary sensor based on a config entry."""
    coordinator: ChandlerWaterSoftenerCoordinator = hass.data[DOMAIN][entry.entry_id]

    binary_sensors = [
        ChandlerRegenerationStatusBinarySensor(coordinator, entry),
        ChandlerSystemStatusBinarySensor(coordinator, entry),
    ]

    async_add_entities(binary_sensors)


class ChandlerWaterSoftenerBinarySensor(BinarySensorEntity):
    """Base class for Chandler Water Softener binary sensors."""

    def __init__(
        self,
        coordinator: ChandlerWaterSoftenerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
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


class ChandlerRegenerationStatusBinarySensor(ChandlerWaterSoftenerBinarySensor):
    """Representation of a Chandler Water Softener regeneration status binary sensor."""

    _attr_name = "Regeneration Status"
    _attr_device_class = "running"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None
        
        data = self.coordinator.data.get("data", {})
        parsed_data = data.get("parsed_data", {})
        regeneration_status = parsed_data.get("regeneration_status")
        
        # For now, we'll assume any non-None value means regeneration is active
        # This will need to be refined based on actual device behavior
        return regeneration_status is not None and regeneration_status != 0

    @property
    def icon(self) -> str:
        """Return the icon of the binary sensor."""
        return "mdi:refresh"


class ChandlerSystemStatusBinarySensor(ChandlerWaterSoftenerBinarySensor):
    """Representation of a Chandler Water Softener system status binary sensor."""

    _attr_name = "System Status"
    _attr_device_class = "connectivity"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None
        
        data = self.coordinator.data.get("data", {})
        parsed_data = data.get("parsed_data", {})
        system_status = parsed_data.get("system_status")
        
        # For now, we'll assume any non-None value means system is operational
        # This will need to be refined based on actual device behavior
        return system_status is not None and system_status != 0

    @property
    def icon(self) -> str:
        """Return the icon of the binary sensor."""
        return "mdi:check-circle" 