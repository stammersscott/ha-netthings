# NetThings Energy Manager Integration for Home Assistant

[![GitHub Release](https://shields.io)](https://github.com)
[![License: GPL v3](https://shields.io)](https://github.com)
[![hacs_badge](https://shields.io)](https://github.com)

A custom integration for **Home Assistant** to monitor real-time electricity and utility consumption data from a local **NetThings Energy Manager**.

This component listens to your local hardware's internal Websocket to record sensor metrics without relying on deprecated cloud endpoints or firewalled servers.

## Features

- **Real-Time Electricity Monitoring:** Tracks instant active power consumption via connected CT clamps.
- **Pulse Meter Support:** Accesses accumulated pulse measurements for configured water, gas, or heat meters.
- **Native Energy Dashboard Integration:** Provides continuous `energy` and `power` device classes configured with appropriate state classes (`total_increasing` and `measurement`), allowing you to hook data straight into the native Home Assistant Energy dashboard.
- **Local Control:** Functions completely over the local network via HTTP API pooling.

---

## Installation

### Method 1: Via HACS (Recommended)

1. Open **Home Assistant** and navigate to the **HACS** (Home Assistant Community Store) panel.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste the URL of this repository: `https://github.com/stammersscott/ha-netthings`
4. Choose **Integration** as the category, then click **Add**.
5. Find **NetThings Energy Manager** in the HACS interface and click **Download**.
6. **Restart Home Assistant** to initialize the component.

### Method 2: Manual Installation

1. Download the latest release source code `.zip` archive.
2. Extract the contents and copy the `netthings` folder located inside `custom_components/`.
3. Paste the `netthings` directory into your Home Assistant configuration directory under `custom_components/` (so your tree structure looks like `/config/custom_components/netthings/`).
4. **Restart Home Assistant**.

---

## Configuration

Once installed and restarted, configure the integration directly through the Home Assistant user interface:

1. In Home Assistant, go to **Settings** ➔ **Devices & Services**.
2. Click **+ Add Integration** in the bottom-right corner.
3. Search for **NetThings Energy Manager** and select it.
4. Provide the configuration details requested by the setup wizard:
   - **Host / IP Address:** The local network IP address of your NetThings unit (This should be reserved by your DHCP server so it doesnt change IP).
5. Click **Submit**.

---

## Sensors Exposed

Depending on your physical hardware configuration (up to 3x CT clamps and 3x pulse inputs), this integration dynamically exposes the following entities:

| Sensor Entity | Device Class | State Class | Unit | Description |
|---|---|---|---|---|
| `sensor.netthings_power_channel_1` | `power` | `measurement` | `W` | Live active power consumption |
| `sensor.netthings_energy_channel_1` | `energy` | `total_increasing` | `kWh` | Daily or total accumulated energy usage |
| `sensor.netthings_pulse_input_1` | `water` / `gas` | `total_increasing` | `m³` / `L` | Volumetric tracker for pulse meters |

---

## Troubleshooting & Local Pairing

- **Static IP Assignment:** Ensure you bind your NetThings controller to a static IP address or a static DHCP reservation in your home router settings so the integration doesn't lose connection when the device reboots.
- **Time Sync Issues:** Legacy NetThings hardware has known hardcoded NTP server limitations. Ensure your local gateway handles NTP requests correctly if your unit is displaying inaccurate local history timestamps.

## License

This project is open-source software licensed under the **GNU GPL v3 License**. See the `LICENSE` file for more details.
