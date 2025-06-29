# Chandler Water Softener Home Assistant Integration

A Home Assistant integration for Chandler Systems CS_Meter_Soft water softener devices that communicate via Bluetooth Low Energy (BLE).

## Features

- **Automatic Device Discovery**: Scans for Chandler CS_Meter_Soft devices on your network
- **Real-time Monitoring**: Tracks water softener status and metrics
- **Multiple Sensors**: 
  - Salt level (percentage)
  - Water usage (gallons)
  - Flow rate (gallons per minute)
  - Hardness setting (grains per gallon)
  - Battery level (percentage)
- **Status Indicators**:
  - Regeneration status (on/off)
  - System status (operational/error)

## Installation

### Method 1: Manual Installation (Recommended)

1. **Download the Integration**:
   - Clone or download this repository
   - Copy the `custom_components/chandler_water_softener` folder to your Home Assistant `config/custom_components/` directory

2. **Install Dependencies**:
   ```bash
   # If using Home Assistant OS or Supervised
   # The integration will automatically install bleak via requirements.txt
   
   # If using Home Assistant Core, install manually:
   pip install bleak>=0.20.0
   ```

3. **Restart Home Assistant**:
   - Go to Settings → System → Restart
   - Or restart your Home Assistant instance

4. **Add the Integration**:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Chandler Water Softener"
   - Follow the setup wizard

### Method 2: HACS Installation (Future)

This integration may be available through HACS in the future.

## Configuration

### Setup Wizard

1. **Initial Setup**:
   - Enter a name for your integration (optional)
   - Set scan timeout (default: 10 seconds)

2. **Device Discovery**:
   - The integration will scan for Chandler CS_Meter_Soft devices
   - Select your device from the list
   - The integration will test the connection

3. **Configuration Complete**:
   - Your water softener will appear as a device in Home Assistant
   - All sensors will be automatically created

### Manual Configuration (Optional)

You can also configure the integration manually in your `configuration.yaml`:

```yaml
chandler_water_softener:
  device_address: "XX:XX:XX:XX:XX:XX"  # Your device's MAC address
  device_name: "My Water Softener"     # Optional custom name
  scan_timeout: 10                     # Optional scan timeout
```

## Sensors

The integration creates the following sensors:

### Numeric Sensors

| Sensor | Unit | Description |
|--------|------|-------------|
| `sensor.salt_level` | % | Current salt level in the brine tank |
| `sensor.water_usage` | gal | Total water usage (cumulative) |
| `sensor.flow_rate` | gal/min | Current water flow rate |
| `sensor.hardness_setting` | grains/gal | Water hardness setting |
| `sensor.battery_level` | % | Device battery level |

### Binary Sensors

| Sensor | Description |
|--------|-------------|
| `binary_sensor.regeneration_status` | Whether regeneration is currently running |
| `binary_sensor.system_status` | Overall system operational status |

## Usage Examples

### Automations

**Low Salt Alert**:
```yaml
automation:
  - alias: "Low Salt Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.salt_level
      below: 20
    action:
      - service: notify.mobile_app
        data:
          message: "Water softener salt level is low ({{ states('sensor.salt_level') }}%)"
```

**High Water Usage Alert**:
```yaml
automation:
  - alias: "High Water Usage Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.flow_rate
      above: 10
    action:
      - service: notify.mobile_app
        data:
          message: "High water flow detected: {{ states('sensor.flow_rate') }} gal/min"
```

### Dashboards

Create a custom dashboard to monitor your water softener:

```yaml
# Example dashboard configuration
views:
  - title: "Water Softener"
    path: water-softener
    cards:
      - type: vertical-stack
        cards:
          - type: gauge
            entity: sensor.salt_level
            name: "Salt Level"
            min: 0
            max: 100
            severity:
              green: 0
              yellow: 20
              red: 10
          
          - type: gauge
            entity: sensor.battery_level
            name: "Battery"
            min: 0
            max: 100
            
          - type: entities
            entities:
              - entity: sensor.water_usage
              - entity: sensor.flow_rate
              - entity: binary_sensor.regeneration_status
              - entity: binary_sensor.system_status
```

## Troubleshooting

### Common Issues

1. **No Devices Found**:
   - Ensure your Chandler CS_Meter_Soft device is powered on and in range
   - Check that Bluetooth is enabled on your Home Assistant system
   - Try increasing the scan timeout

2. **Connection Failed**:
   - Verify the device address is correct
   - Ensure the device is not connected to another application
   - Check Bluetooth permissions

3. **Sensors Show "Unavailable"**:
   - The device may be out of range or powered off
   - Check the integration logs for connection errors
   - Restart the integration

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: info
  logs:
    custom_components.chandler_water_softener: debug
    bleak: debug
```

### Logs

Check the Home Assistant logs for detailed error information:
- Go to Settings → System → Logs
- Look for entries from `custom_components.chandler_water_softener`

## Technical Details

### Device Communication

The integration uses the `bleak` library to communicate with Chandler CS_Meter_Soft devices via Bluetooth Low Energy. It:

1. Discovers available BLE devices
2. Filters for Chandler CS_Meter_Soft devices
3. Connects to the selected device
4. Reads characteristic values
5. Parses the data into meaningful metrics

### Data Parsing

The integration attempts to parse various data formats:
- Percentage values (salt level, battery)
- Flow rates (float values)
- Usage counters (32-bit integers)
- Status flags (binary values)

### Update Frequency

- Default update interval: 30 seconds
- Configurable via the coordinator
- Real-time notifications supported (if device supports them)

## Development

### Local Development

1. Clone this repository
2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Run tests:
   ```bash
   pytest
   ```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the Home Assistant community forums

## Changelog

### Version 1.0.0
- Initial release
- Basic sensor support
- Device discovery and configuration
- Bluetooth LE communication 