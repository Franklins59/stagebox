# Stagebox Personal

**Smart Home Provisioning System for Shelly IoT Devices**

Stagebox is a Raspberry Pi-based system for provisioning and managing Shelly smart home devices. It provides a web interface for device discovery, configuration, and deployment across buildings.

## Features

- **Stage 1:** Discover Shelly devices in AP mode via WiFi scanning
- **Stage 2:** Adopt devices to your network
- **Stage 3:** Configure device profiles and settings
- **Stage 4:** Deploy scripts and finalize configuration
- **Device Management:** Monitor, configure, and update devices
- **Script Pool:** Deploy custom scripts to devices
- **Multi-language:** EN, DE, FR, IT, NL

## Requirements

- Raspberry Pi 4 or 5
- Raspberry Pi OS (Bookworm, 64-bit)
- Python 3.11+
- Network connection (Ethernet recommended)

## Installation

### Option 1: SD Card Image (Recommended)

Download the pre-configured SD card image from [Releases](https://github.com/franklins59/stagebox/releases).

### Option 2: Manual Installation

```bash
# Clone repository
git clone https://github.com/franklins59/stagebox.git
cd stagebox

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Copy example configs
cp data/config.yaml.example data/config.yaml
cp data/secrets.yaml.example data/secrets.yaml

# Run
python3 -m web
```

Access the web interface at `http://<raspberry-pi-ip>:5000`

## Configuration

Edit `data/config.yaml` for network settings:

```yaml
network:
  wifi_ssid: "YourNetwork"
  wifi_password: "YourPassword"
  ip_range_start: "192.168.1.100"
  ip_range_end: "192.168.1.200"
```

## Documentation

See [docs/manual/](docs/manual/) for detailed user guides in multiple languages.

## Editions

| Feature | Personal | Pro |
|---------|----------|-----|
| Device Provisioning | ✅ | ✅ |
| Single Building | ✅ | ✅ |
| Multi Building | ❌ | ✅ |
| USB Backup | ❌ | ✅ |
| Snapshots | ❌ | ✅ |
| Admin Features | Limited | Full |
| Price | Free | CHF 480 |

**Stagebox Pro** is available as a pre-configured hardware product at [franklins.forstec.ch](https://franklins.forstec.ch).

## Updates

Stagebox Personal receives updates directly from GitHub. Check for updates in the web interface under System → Updates.

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

- ✅ Free to use, modify, and distribute
- ✅ Access to source code guaranteed
- ⚠️ Derivative works must also be GPL-3.0
- ⚠️ Changes must be documented

See [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html) for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/franklins59/stagebox/issues)
- **Pro Support:** [franklins.forstec.ch](https://franklins.forstec.ch)

---

Made with ❤️ by [forstec](https://franklins.forstec.ch)