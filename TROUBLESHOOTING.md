# Troubleshooting Guide

## Video plays audio but no picture

**Symptoms:** You can hear the video but see no video output.

**Cause:** Missing H.264 video codec support in VLC.

**Solution:**

On Arch Linux:
```bash
sudo pacman -S ffmpeg vlc
```

On Raspberry Pi OS / Debian:
```bash
sudo apt install libavcodec-extra vlc
```

On Ubuntu:
```bash
sudo apt install ubuntu-restricted-extras vlc
```

Then test again:
```bash
source venv/bin/activate
./test_vlc.py videos/story/main.mp4
```

## Video codec debugging

Check what codecs VLC has available:
```bash
vlc --list | grep -i h264
```

Test video playback with VLC directly:
```bash
vlc videos/story/main.mp4
```

## Camera not detected

List available cameras:
```bash
v4l2-ctl --list-devices
```

Test camera:
```bash
ffplay /dev/video0
```

If camera is on different index, update `config.json`:
```json
{
  "camera_index": 1
}
```

## Motion detection too sensitive

Edit `config.json`:
```json
{
  "motion_threshold": 50,
  "motion_min_area": 10000
}
```

Higher values = less sensitive

## Web interface not accessible

Check the service is running:
```bash
sudo systemctl status haunted-house
```

Check what's listening on port 8080:
```bash
sudo netstat -tlnp | grep 8080
```

Try accessing locally first:
```bash
curl http://localhost:8080/api/status
```

## Video format issues

Convert video to compatible format using ffmpeg:
```bash
ffmpeg -i input.mp4 -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k output.mp4
```

## Display issues on Pi

Set HDMI output in `/boot/config.txt`:
```
hdmi_drive=2
hdmi_force_hotplug=1
```

Force audio to HDMI:
```bash
sudo raspi-config
# System Options -> Audio -> HDMI
```

## Service won't start on boot

Check service logs:
```bash
sudo journalctl -u haunted-house -n 100
```

Check service file permissions:
```bash
sudo systemctl daemon-reload
sudo systemctl enable haunted-house
```

## Python dependency issues

Rebuild virtual environment:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
