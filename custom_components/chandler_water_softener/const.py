"""Constants for the Chandler Water Softener integration."""

DOMAIN = "chandler_water_softener"

# Configuration keys
CONF_DEVICE_ADDRESS = "device_address"
CONF_DEVICE_NAME = "device_name"
CONF_SCAN_TIMEOUT = "scan_timeout"

# Default values
DEFAULT_SCAN_TIMEOUT = 10
DEFAULT_NAME = "Chandler Water Softener"

# Update intervals
UPDATE_INTERVAL = 30  # seconds

# Sensor names
SENSOR_SALT_LEVEL = "salt_level"
SENSOR_WATER_USAGE = "water_usage"
SENSOR_FLOW_RATE = "flow_rate"
SENSOR_HARDNESS_SETTING = "hardness_setting"
SENSOR_BATTERY_LEVEL = "battery_level"

# Binary sensor names
BINARY_SENSOR_REGENERATION_STATUS = "regeneration_status"
BINARY_SENSOR_SYSTEM_STATUS = "system_status"

# Device info
MANUFACTURER = "Chandler Systems"
MODEL = "CS_Meter_Soft" 