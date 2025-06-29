#!/usr/bin/env python3
"""
Simple Bluetooth LE scanner to test device discovery for Chandler Water Softener.
"""

import asyncio
from bleak import BleakScanner

CHANDLER_KEYWORDS = ['CS_Meter_Soft', 'CS_Meter', 'chandler', 'Chandler']

async def scan_devices(timeout=15):
    print(f"Scanning for Bluetooth LE devices for {timeout} seconds...\n")
    devices = await BleakScanner.discover(timeout=timeout)
    if not devices:
        print("No BLE devices found.")
        return

    found_chandler = False
    for i, device in enumerate(devices, 1):
        name = device.name or "Unknown"
        address = device.address
        rssi = getattr(device, 'rssi', 'N/A')
        print(f"{i:2d}. {name} ({address}) RSSI: {rssi}", end="")
        if any(keyword in name for keyword in CHANDLER_KEYWORDS):
            print("   <-- Chandler candidate!")
            found_chandler = True
        else:
            print()
    if not found_chandler:
        print("\nNo Chandler water softener devices found.")
        print("Tips:")
        print(" - Make sure your device is powered on and in range.")
        print(" - Ensure it is not connected to another app.")
        print(" - Try increasing the scan timeout.")

if __name__ == "__main__":
    import sys
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    asyncio.run(scan_devices(timeout)) 