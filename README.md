# Haunted House Motion-Activated Video System

A Raspberry Pi-based system that detects motion via webcam and plays a "story" video, then loops ambient videos when idle. Perfect for haunted houses, escape rooms, or interactive installations.

## Features

- Motion detection via webcam using OpenCV
- Automatic story video playback when motion detected
- Ambient video looping when idle
- Remote control via web interface
- Configurable cooldown period between story triggers
- Manual trigger/stop controls
- Enable/disable motion detection remotely
- Systemd service for auto-start on boot

## Hardware Requirements

- Raspberry Pi 5 (or Pi 4)
- USB Webcam
- Projector (HDMI)
- Speakers (HDMI audio or 3.5mm jack)
- Power supply
- Optional: WiFi dongle for hotspot mode

## Quick Start

### 1. Installation

```bash
# Clone or copy this directory to your Pi
cd /home/pi
git clone <your-repo> haunted-house
cd haunted-house

# Run the installation script
./install.sh
```

The install script will:
- Install system dependencies (Python, VLC, OpenCV)
- Create a Python virtual environment
- Install Python packages
- Optionally set up systemd service

### 2. Add Your Videos

```bash
# Place your main story video
cp /path/to/your/story.mp4 videos/story/main.mp4

# Add ambient/loop videos
cp /path/to/ambient/*.mp4 videos/ambient/
```

### 3. Configure Settings

Edit `config.json` to adjust settings:

```json
{
  "story_video": "videos/story/main.mp4",
  "ambient_videos_dir": "videos/ambient",
  "motion_threshold": 25,
  "motion_min_area": 5000,
  "camera_index": 0,
  "camera_warmup_time": 2.0,
  "story_cooldown_seconds": 30,
  "web_port": 8080,
  "web_host": "0.0.0.0"
}
```

**Configuration Options:**
- `story_video`: Path to the main video that plays on motion detection
- `ambient_videos_dir`: Directory containing videos to loop when idle
- `motion_threshold`: Sensitivity for motion detection (lower = more sensitive)
- `motion_min_area`: Minimum pixel area to count as motion
- `camera_index`: Camera device index (usually 0)
- `camera_warmup_time`: Seconds to wait for camera initialization
- `story_cooldown_seconds`: Minimum seconds between story triggers
- `web_port`: Port for web interface
- `web_host`: Host for web server (0.0.0.0 = all interfaces)

### 4. Run the System

**Manual run:**
```bash
./run.py
```

**As a systemd service:**
```bash
sudo systemctl start haunted-house
sudo systemctl status haunted-house
```

**View logs:**
```bash
sudo journalctl -u haunted-house -f
```

## Web Interface

Access the control panel at: `http://<pi-ip-address>:8080`

The web interface allows you to:
- View current system status
- Manually trigger story mode
- Stop story mode and return to ambient
- Enable/disable motion detection
- Reload ambient video playlist

## Network Setup

### Option 1: Connect to Existing WiFi

```bash
sudo raspi-config
# System Options -> Wireless LAN -> Enter SSID and password
```

Find your Pi's IP address:
```bash
hostname -I
```

### Option 2: Create WiFi Hotspot

If there's no existing network, you can turn your Pi into a WiFi hotspot:

```bash
# Install required packages
sudo apt install hostapd dnsmasq

# Stop services
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# Configure static IP for wlan0
sudo nano /etc/dhcpcd.conf
```

Add to the end of `/etc/dhcpcd.conf`:
```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

Configure DHCP server (`/etc/dnsmasq.conf`):
```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
```

Configure access point (`/etc/hostapd/hostapd.conf`):
```
interface=wlan0
driver=nl80211
ssid=HauntedHouse
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=spooky123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

Enable and start services:
```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

Connect to WiFi network "HauntedHouse" with password "spooky123", then access:
`http://192.168.4.1:8080`

## Troubleshooting

### Camera Not Detected

```bash
# List video devices
v4l2-ctl --list-devices

# Test camera
ffplay /dev/video0
```

If camera is on a different index, update `camera_index` in config.json.

### Motion Detection Too Sensitive/Not Sensitive

Adjust these values in `config.json`:
- Increase `motion_threshold` to reduce sensitivity
- Increase `motion_min_area` to ignore small movements
- Decrease values for more sensitivity

### Video Won't Play

Check VLC is installed:
```bash
vlc --version
```

Test video playback:
```bash
cvlc --no-xlib /path/to/video.mp4
```

### Web Interface Not Accessible

Check the service is running:
```bash
sudo systemctl status haunted-house
```

Check firewall (if enabled):
```bash
sudo ufw allow 8080
```

### No Audio

Check HDMI audio is selected:
```bash
# Force HDMI audio
sudo raspi-config
# System Options -> Audio -> HDMI
```

Or edit `/boot/config.txt`:
```
hdmi_drive=2
```

### Service Won't Start on Boot

Check service status:
```bash
sudo systemctl status haunted-house
```

View detailed logs:
```bash
sudo journalctl -u haunted-house -n 50
```

## File Structure

```
haunted-house/
├── haunted_house.py      # Main application logic
├── web_server.py          # Flask web interface
├── run.py                 # Launcher script
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── install.sh             # Installation script
├── haunted-house.service  # Systemd service file
├── templates/
│   └── index.html         # Web interface template
└── videos/
    ├── story/
    │   └── main.mp4       # Your story video
    └── ambient/
        ├── ambient1.mp4   # Ambient loop videos
        └── ambient2.mp4
```

## API Endpoints

The web server exposes these REST API endpoints:

- `GET /api/status` - Get current system status
- `POST /api/trigger` - Manually trigger story mode
- `POST /api/stop` - Stop story mode
- `POST /api/motion/enable` - Enable motion detection
- `POST /api/motion/disable` - Disable motion detection
- `POST /api/ambient/reload` - Reload ambient playlist

## Tips

1. **Testing Motion Detection**: Start with lower thresholds and adjust based on your environment
2. **Video Formats**: Use H.264 encoded MP4 files for best compatibility
3. **Performance**: If playback is choppy, reduce video resolution or bitrate
4. **Lighting**: Motion detection works best with consistent lighting
5. **Cooldown Period**: Set `story_cooldown_seconds` to prevent rapid re-triggers

## License

MIT License - Feel free to use and modify for your projects!
