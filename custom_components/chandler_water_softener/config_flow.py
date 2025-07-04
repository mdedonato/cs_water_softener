"""Config flow for Chandler Water Softener integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client

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
        self.user_input: dict[str, Any] = {}

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

        # Store user input and start scanning for devices
        self.user_input = user_input
        return await self.async_step_scan()

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the scanning step."""
        if user_input is None:
            # Start scanning
            try:
                scan_timeout = self.user_input.get(CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT)
                devices = await self.api.softener.scan_for_devices(timeout=scan_timeout)
                
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

                # Add manual entry option
                self.discovered_devices = {
                    f"{device['name'] or 'Unknown'} ({device['address']})": device['address']
                    for device in devices
                }
                self.discovered_devices["Manual Entry"] = "MANUAL_ENTRY"

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
        if self.discovered_devices[selected_device] == "MANUAL_ENTRY":
            return await self.async_step_manual_entry()
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
                title=self.user_input.get(CONF_NAME, device_name),
                data={
                    CONF_DEVICE_ADDRESS: device_address,
                    CONF_DEVICE_NAME: device_name,
                    CONF_SCAN_TIMEOUT: self.user_input.get(CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT),
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

    async def async_step_manual_entry(self, user_input=None):
        if user_input is not None:
            device_address = user_input["manual_address"]
            device_name = device_address
            # Try to connect to verify the device
            try:
                connected = await self.api.softener.connect(device_address)
                if not connected:
                    return self.async_show_form(
                        step_id="manual_entry",
                        data_schema=vol.Schema(
                            {
                                vol.Required("manual_address"): str,
                            }
                        ),
                        errors={"base": "connection_failed"},
                    )
                await self.api.softener.disconnect()
                return self.async_create_entry(
                    title=self.user_input.get(CONF_NAME, device_name),
                    data={
                        CONF_DEVICE_ADDRESS: device_address,
                        CONF_DEVICE_NAME: device_name,
                        CONF_SCAN_TIMEOUT: self.user_input.get(CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT),
                    },
                )
            except Exception as err:
                _LOGGER.error("Error connecting to device: %s", err)
                return self.async_show_form(
                    step_id="manual_entry",
                    data_schema=vol.Schema(
                        {
                            vol.Required("manual_address"): str,
                        }
                    ),
                    errors={"base": "connection_failed"},
                )
        return self.async_show_form(
            step_id="manual_entry",
            data_schema=vol.Schema(
                {
                    vol.Required("manual_address"): str,
                }
            ),
        )

    async def async_step_import(self, import_info: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)


class ChandlerWaterSoftenerOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.api = ChandlerWaterSoftenerAPI()
        self.discovered_devices = {}
        self.user_input = {}

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # User selected a device and/or scan timeout, update the config entry
            selected_device = user_input["device"]
            scan_timeout = user_input.get("scan_timeout", DEFAULT_SCAN_TIMEOUT)
            device_address = self.discovered_devices[selected_device]
            device_name = selected_device.split(" (")[0]
            return self.async_create_entry(
                title="",
                data={
                    **self.config_entry.options,
                    CONF_DEVICE_ADDRESS: device_address,
                    CONF_DEVICE_NAME: device_name,
                    CONF_SCAN_TIMEOUT: scan_timeout,
                },
            )

        # Show scan timeout field and scan for all BLE devices
        scan_timeout = self.config_entry.options.get(CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT)
        devices = await self.api.softener.scan_for_devices(timeout=scan_timeout)
        if not devices:
            return self.async_abort(reason="no_devices_found")
        self.discovered_devices = {
            f"{device['name'] or 'Unknown'} ({device['address']})": device['address']
            for device in devices
        }
        self.discovered_devices["Manual Entry"] = "MANUAL_ENTRY"
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("scan_timeout", default=scan_timeout): int,
                    vol.Required("device"): vol.In(list(self.discovered_devices.keys())),
                }
            ),
        )


# Register the options flow
async def async_get_options_flow(config_entry):
    return ChandlerWaterSoftenerOptionsFlowHandler(config_entry) 