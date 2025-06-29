"""API wrapper for Chandler Water Softener."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import struct

try:
    from bleak import BleakScanner, BleakClient
    from bleak.backends.characteristic import BleakGATTCharacteristic
except ImportError:
    logging.error("Please install bleak: pip install bleak")
    raise

_LOGGER = logging.getLogger(__name__)


class ChandlerWaterSoftener:
    """Main class for communicating with Chandler water softener"""

    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None
        self.device_name: Optional[str] = None
        self.characteristics: Dict[str, str] = {}
        self.data_cache: Dict[str, Any] = {}

    async def scan_for_devices(self, timeout: int = 10) -> List[Dict[str, str]]:
        """Scan for Bluetooth LE devices, filtering for Chandler CS_Meter_Soft devices"""
        _LOGGER.info(f"[SCAN] Scanning for Chandler CS_Meter_Soft devices for {timeout} seconds...")

        devices = await BleakScanner.discover(timeout=timeout)
        _LOGGER.debug(f"[SCAN] Found {len(devices)} BLE devices.")
        chandler_devices = []

        for device in devices:
            _LOGGER.debug(f"[SCAN] Device found: {device.name} ({device.address})")
            # Look specifically for CS_Meter_Soft or similar Chandler devices
            if device.name and any(keyword in device.name for keyword in
                                   ['CS_Meter_Soft', 'CS_Meter', 'chandler', 'Chandler']):
                # Handle RSSI safely - it might not be available in all bleak versions
                rssi = getattr(device, 'rssi', None)
                chandler_devices.append({
                    'name': device.name,
                    'address': device.address,
                    'rssi': rssi
                })
                rssi_str = f" RSSI: {rssi}" if rssi is not None else ""
                _LOGGER.info(f"[SCAN] Found Chandler device: {device.name} ({device.address}){rssi_str}")

        if not chandler_devices:
            _LOGGER.warning("[SCAN] No CS_Meter_Soft devices found. Here are all discovered devices:")
            for device in devices:
                if device.name:
                    _LOGGER.info(f"[SCAN]   {device.name} ({device.address})")

        return chandler_devices

    async def connect(self, device_address: str) -> bool:
        """Connect to the water softener device"""
        try:
            _LOGGER.info(f"[CONNECT] Connecting to device: {device_address}")
            self.client = BleakClient(device_address)
            await self.client.connect()

            if self.client.is_connected:
                self.device_address = device_address
                _LOGGER.info("[CONNECT] Successfully connected!")
                await self._discover_services()
                return True
            else:
                _LOGGER.error("[CONNECT] Failed to connect")
                return False

        except Exception as e:
            _LOGGER.error(f"[CONNECT] Connection error: {str(e)}")
            return False

    async def _discover_services(self):
        """Discover available services and characteristics"""
        if not self.client:
            _LOGGER.warning("[DISCOVER] No client to discover services on.")
            return

        _LOGGER.info("[DISCOVER] Discovering services and characteristics...")
        services = self.client.services

        for service in services:
            _LOGGER.info(f"[DISCOVER] Service: {service.uuid}")
            for char in service.characteristics:
                _LOGGER.info(f"[DISCOVER]   Characteristic: {char.uuid} - Properties: {char.properties}")

                # Store characteristics that might be useful
                if "read" in char.properties:
                    self.characteristics[f"read_{len(self.characteristics)}"] = char.uuid
                if "write" in char.properties:
                    self.characteristics[f"write_{len(self.characteristics)}"] = char.uuid
                if "notify" in char.properties:
                    self.characteristics[f"notify_{len(self.characteristics)}"] = char.uuid

    async def read_device_info(self) -> Dict[str, Any]:
        """Read basic device information"""
        if not self.client or not self.client.is_connected:
            _LOGGER.error("[READ] Not connected to device")
            return {}

        device_info = {
            'timestamp': datetime.now().isoformat(),
            'device_address': self.device_address,
            'connection_status': 'connected'
        }

        # Try to read from various standard characteristics
        standard_chars = {
            'device_name': "00002a00-0000-1000-8000-00805f9b34fb",
            'manufacturer': "00002a29-0000-1000-8000-00805f9b34fb",
            'model_number': "00002a24-0000-1000-8000-00805f9b34fb",
            'serial_number': "00002a25-0000-1000-8000-00805f9b34fb",
            'firmware_revision': "00002a26-0000-1000-8000-00805f9b34fb",
            'battery_level': "00002a19-0000-1000-8000-00805f9b34fb"
        }

        for info_type, char_uuid in standard_chars.items():
            try:
                data = await self.client.read_gatt_char(char_uuid)
                if data:
                    # Try to decode as string first, then as raw bytes
                    try:
                        device_info[info_type] = data.decode('utf-8').strip()
                        _LOGGER.info(f"[READ] {info_type}: {device_info[info_type]}")
                    except:
                        if info_type == 'battery_level' and len(data) >= 1:
                            device_info[info_type] = data[0]  # Battery level is usually a single byte
                        else:
                            device_info[info_type] = data.hex()
                        _LOGGER.info(f"[READ] {info_type}: {device_info[info_type]} (raw)")
            except Exception as e:
                _LOGGER.debug(f"[READ] Could not read {info_type}: {str(e)}")

        return device_info

    async def read_water_softener_data(self) -> Dict[str, Any]:
        """Read CS_Meter_Soft specific data"""
        if not self.client or not self.client.is_connected:
            _LOGGER.error("[READ] Not connected to device")
            return {}

        softener_data = {
            'timestamp': datetime.now().isoformat(),
            'device_type': 'CS_Meter_Soft',
            'raw_readings': {},
            'parsed_data': {}
        }

        # Try to read from all discovered readable characteristics
        for char_name, char_uuid in self.characteristics.items():
            if 'read' in char_name or 'notify' in char_name:
                try:
                    data = await self.client.read_gatt_char(char_uuid)
                    if data:
                        # Store raw data
                        char_info = {
                            'hex': data.hex(),
                            'bytes': list(data),
                            'length': len(data),
                            'timestamp': datetime.now().isoformat()
                        }
                        _LOGGER.info(f"[READ] Char {char_uuid}: {data.hex()}")

                        # Try to interpret the data for CS_Meter_Soft
                        char_info.update(self._parse_cs_meter_data(data, char_uuid))

                        softener_data['raw_readings'][char_uuid] = char_info

                except Exception as e:
                    _LOGGER.debug(f"[READ] Could not read characteristic {char_uuid}: {str(e)}")

        # Extract common water softener metrics if identifiable
        softener_data['parsed_data'] = self._extract_softener_metrics(softener_data['raw_readings'])
        _LOGGER.info(f"[PARSE] Extracted metrics: {softener_data['parsed_data']}")

        return softener_data

    def _parse_cs_meter_data(self, data: bytes, char_uuid: str) -> Dict[str, Any]:
        """Parse CS_Meter_Soft specific data formats"""
        parsed = {}

        try:
            # Common data interpretations for water softeners
            if len(data) >= 4:
                # Try as 32-bit float (common for sensor readings)
                try:
                    float_val = struct.unpack('<f', data[:4])[0]
                    if -1000 < float_val < 10000:  # Reasonable range check
                        parsed['as_float'] = round(float_val, 2)
                        _LOGGER.debug(f"[PARSE] {char_uuid} as_float: {parsed['as_float']}")
                except:
                    pass

                # Try as 32-bit integer (for counts, settings)
                try:
                    int_val = struct.unpack('<I', data[:4])[0]
                    if int_val < 1000000:  # Reasonable range
                        parsed['as_uint32'] = int_val
                        _LOGGER.debug(f"[PARSE] {char_uuid} as_uint32: {parsed['as_uint32']}")
                except:
                    pass

            if len(data) >= 2:
                # Try as 16-bit integer (common for smaller values)
                try:
                    int16_val = struct.unpack('<H', data[:2])[0]
                    parsed['as_uint16'] = int16_val
                    _LOGGER.debug(f"[PARSE] {char_uuid} as_uint16: {parsed['as_uint16']}")
                except:
                    pass

            if len(data) >= 1:
                # Single byte values (percentages, flags, etc.)
                parsed['as_uint8'] = data[0]
                if data[0] <= 100:
                    parsed['as_percentage'] = data[0]
                    _LOGGER.debug(f"[PARSE] {char_uuid} as_percentage: {parsed['as_percentage']}")

            # Try as ASCII string
            try:
                str_val = data.decode('ascii').strip()
                if str_val.isprintable() and len(str_val) > 0:
                    parsed['as_string'] = str_val
                    _LOGGER.debug(f"[PARSE] {char_uuid} as_string: {parsed['as_string']}")
            except:
                pass

            # Look for common patterns in CS_Meter_Soft data
            if len(data) == 8:
                # Could be timestamp or dual 32-bit values
                try:
                    val1, val2 = struct.unpack('<II', data)
                    parsed['as_dual_uint32'] = [val1, val2]
                    _LOGGER.debug(f"[PARSE] {char_uuid} as_dual_uint32: {parsed['as_dual_uint32']}")
                except:
                    pass

            # Check for specific CS_Meter patterns based on characteristic UUID
            if char_uuid.endswith('2a19'):  # Battery service
                if len(data) == 1:
                    parsed['battery_percentage'] = data[0]
                    _LOGGER.debug(f"[PARSE] {char_uuid} battery_percentage: {parsed['battery_percentage']}")

        except Exception as e:
            _LOGGER.debug(f"[PARSE] Error parsing data for {char_uuid}: {str(e)}")

        return parsed

    def _extract_softener_metrics(self, raw_readings: Dict) -> Dict[str, Any]:
        """Extract meaningful water softener metrics from raw data"""
        metrics = {
            'salt_level': None,
            'water_usage': None,
            'regeneration_status': None,
            'system_status': None,
            'last_regeneration': None,
            'hardness_setting': None,
            'flow_rate': None,
            'battery_level': None
        }

        # This will need to be customized based on actual data patterns
        # For now, look for likely candidates based on data ranges and types

        for char_uuid, char_data in raw_readings.items():
            # Look for percentage values (likely salt level)
            if 'as_percentage' in char_data and char_data['as_percentage'] <= 100:
                if metrics['salt_level'] is None:
                    metrics['salt_level'] = char_data['as_percentage']
                if metrics['battery_level'] is None:
                    metrics['battery_level'] = char_data['as_percentage']

            # Look for reasonable flow rates (GPM)
            if 'as_float' in char_data:
                float_val = char_data['as_float']
                if 0 < float_val < 50:  # Reasonable flow rate range
                    if metrics['flow_rate'] is None:
                        metrics['flow_rate'] = float_val

            # Look for usage counters
            if 'as_uint32' in char_data:
                uint_val = char_data['as_uint32']
                if uint_val > 100:  # Likely a cumulative counter
                    if metrics['water_usage'] is None:
                        metrics['water_usage'] = uint_val

        _LOGGER.debug(f"[PARSE] Final extracted metrics: {metrics}")
        return metrics

    async def disconnect(self):
        """Disconnect from the device"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            _LOGGER.info("[DISCONNECT] Disconnected from device")


class ChandlerWaterSoftenerAPI:
    """REST-like API wrapper for the water softener"""

    def __init__(self):
        self.softener = ChandlerWaterSoftener()
        self.connected = False

    async def initialize(self, device_address: Optional[str] = None) -> Dict[str, Any]:
        """Initialize connection to CS_Meter_Soft water softener"""
        _LOGGER.info(f"[API] Initializing connection to CS_Meter_Soft (address={device_address})")
        if not device_address:
            # Scan for CS_Meter_Soft devices
            devices = await self.softener.scan_for_devices()
            if not devices:
                _LOGGER.warning("[API] No CS_Meter_Soft devices found during initialization.")
                return {'error': 'No CS_Meter_Soft devices found', 'devices': []}

            # Auto-connect to first CS_Meter_Soft device found
            device_address = devices[0]['address']
            _LOGGER.info(f"[API] Auto-connecting to CS_Meter_Soft: {devices[0]['name']} ({device_address})")

        self.connected = await self.softener.connect(device_address)

        if self.connected:
            device_info = await self.softener.read_device_info()
            _LOGGER.info(f"[API] Connected. Device info: {device_info}")
            return {'status': 'connected', 'device_info': device_info, 'device_type': 'CS_Meter_Soft'}
        else:
            _LOGGER.error(f"[API] Failed to connect to CS_Meter_Soft at {device_address}")
            return {'error': 'Failed to connect to CS_Meter_Soft', 'device_address': device_address}

    async def get_status(self) -> Dict[str, Any]:
        """Get current water softener status and readings"""
        if not self.connected:
            _LOGGER.error("[API] Not connected to device when calling get_status.")
            return {'error': 'Not connected to device'}

        try:
            data = await self.softener.read_water_softener_data()
            _LOGGER.info(f"[API] get_status data: {data}")
            return {'status': 'success', 'data': data}
        except Exception as e:
            _LOGGER.error(f"[API] Failed to read data: {str(e)}")
            return {'error': f'Failed to read data: {str(e)}'} 