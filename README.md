# HBX HVAC — SensorLinx Connect Integration

A Home Assistant custom integration for monitoring HBX HVAC systems via the [SensorLinx Connect API](https://docs.connect.sensorlinx.co/reference).

## Features

- Polls all connected THM thermostats from your SensorLinx account
- Exposes each thermostat as a `climate` entity with:
  - Current room temperature (°F)
  - Heat and cool setpoints
  - HVAC action (heating / cooling / idle) derived from demand signals
  - Floor temperature and humidity as extra attributes
- Cloud polling via the SensorLinx Connect API

> **Note:** The SensorLinx Connect API is read-only for thermostat devices. Setpoints and modes can only be changed at the physical device.

## Installation via HACS

1. In HACS, go to **Integrations → ⋮ → Custom repositories**
2. Add this repository URL and select category **Integration**
3. Install **HBX HVAC (SensorLinx)** and restart Home Assistant

## Manual Installation

Copy `custom_components/hbx_hvac/` into your HA config `custom_components/` directory and restart.

## Configuration

1. Settings → Integrations → Add Integration → **HBX HVAC**
2. Enter your SensorLinx Connect API key (create one at [app.sensorlinx.co](https://app.sensorlinx.co))
3. Optionally adjust the polling interval (default: 30 seconds)

## Devices

| Device Type | Description |
|-------------|-------------|
| THM | Thermostat — room/floor temp, heat/cool targets, humidity |
| ECO | Boiler controller — read via coordinator, no entity yet |
| ZON | Zone controller — internal only |
