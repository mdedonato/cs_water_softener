"""Data coordinator for Chandler Water Softener."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL
from .chandler_api import ChandlerWaterSoftenerAPI

_LOGGER = logging.getLogger(__name__)


class ChandlerWaterSoftenerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Chandler Water Softener data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.api = ChandlerWaterSoftenerAPI()
        self.device_address = entry.data.get("device_address")
        self.device_name = entry.data.get("device_name", "Chandler Water Softener")

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Ensure we're connected
            if not self.api.connected:
                await self.api.initialize(self.device_address)
                if not self.api.connected:
                    raise UpdateFailed("Failed to connect to water softener")

            # Get current status
            status = await self.api.get_status()
            
            if "error" in status:
                raise UpdateFailed(f"Failed to get status: {status['error']}")

            # Add timestamp
            status["last_update"] = datetime.now().isoformat()
            
            return status

        except Exception as err:
            _LOGGER.error("Error updating Chandler Water Softener data: %s", err)
            raise UpdateFailed(f"Error updating data: {err}") from err

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.api.connected:
            await self.api.softener.disconnect()
        await super().async_shutdown() 