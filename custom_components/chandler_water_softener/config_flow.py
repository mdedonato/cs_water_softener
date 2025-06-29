"""Config flow for Chandler Water Softener integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    CONF_SCAN_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_SCAN_TIMEOUT,
    DOMAIN,
)
from .chandler_api import ChandlerWaterSoftenerAPI

_LOGGER = logging.getLogger(__name__)


class ChandlerWaterSoftenerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Chandler Water Softener."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api = ChandlerWaterSoftenerAPI()
        self.discovered_devices: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                        vol.Optional(CONF_SCAN_TIMEOUT, default=DEFAULT_SCAN_TIMEOUT): int,
                    }
                ),
            )

        # Start scanning for devices
        return await self.async_step_scan(user_input)

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the scanning step."""
        if user_input is None:
            # Start scanning
            try:
                devices = await self.api.softener.scan_for_devices(
                    timeout=user_input.get(CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT)
                )
                
                if not devices:
                    return self.async_show_form(
                        step_id="user",
                        data_schema=vol.Schema(
                            {
                                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                                vol.Optional(CONF_SCAN_TIMEOUT, default=DEFAULT_SCAN_TIMEOUT): int,
                            }
                        ),
                        errors={"base": "no_devices_found"},
                    )

                # Store discovered devices
                self.discovered_devices = {
                    f"{device['name']} ({device['address']})": device['address']
                    for device in devices
                }

                # Show device selection
                return self.async_show_form(
                    step_id="scan",
                    data_schema=vol.Schema(
                        {
                            vol.Required("device"): vol.In(list(self.discovered_devices.keys())),
                        }
                    ),
                )

            except Exception as err:
                _LOGGER.error("Error scanning for devices: %s", err)
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                            vol.Optional(CONF_SCAN_TIMEOUT, default=DEFAULT_SCAN_TIMEOUT): int,
                        }
                    ),
                    errors={"base": "scan_failed"},
                )

        # User selected a device
        selected_device = user_input["device"]
        device_address = self.discovered_devices[selected_device]
        device_name = selected_device.split(" (")[0]

        # Try to connect to verify the device
        try:
            connected = await self.api.softener.connect(device_address)
            if not connected:
                return self.async_show_form(
                    step_id="scan",
                    data_schema=vol.Schema(
                        {
                            vol.Required("device"): vol.In(list(self.discovered_devices.keys())),
                        }
                    ),
                    errors={"base": "connection_failed"},
                )

            # Disconnect after testing
            await self.api.softener.disconnect()

            # Create the config entry
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, device_name),
                data={
                    CONF_DEVICE_ADDRESS: device_address,
                    CONF_DEVICE_NAME: device_name,
                    CONF_SCAN_TIMEOUT: user_input.get(CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT),
                },
            )

        except Exception as err:
            _LOGGER.error("Error connecting to device: %s", err)
            return self.async_show_form(
                step_id="scan",
                data_schema=vol.Schema(
                    {
                        vol.Required("device"): vol.In(list(self.discovered_devices.keys())),
                    }
                ),
                errors={"base": "connection_failed"},
            )

    async def async_step_import(self, import_info: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info) 