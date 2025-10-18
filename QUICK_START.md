# Quick Start Guide

## Installation (5 minutes)

1. Copy this folder to your Raspberry Pi
2. Run the install script:
   ```bash
   cd haunted-house
   ./install.sh
   ```
3. Choose "y" when asked to install as a service

## Setup Your Videos (2 minutes)

1. Copy your main story video:
   ```bash
   cp /path/to/your/scary-video.mp4 videos/story/main.mp4
   ```

2. Copy your ambient loop videos:
   ```bash
   cp /path/to/ambient/*.mp4 videos/ambient/
   ```

## Test It (1 minute)

Run manually to test:
```bash
./run.py
```

- Wave in front of the camera - story video should play
- After it finishes, ambient videos should loop
- Press Ctrl+C to stop

## Start the Service

```bash
sudo systemctl start haunted-house
```

It will now run automatically on boot!

## Access Web Control

From any device on the same network:
```
http://<your-pi-ip>:8080
```

Don't know your Pi's IP? Run:
```bash
hostname -I
```

## Common Adjustments

### Motion too sensitive?
Edit `config.json`:
```json
{
  "motion_threshold": 50,      // Increase this (was 25)
  "motion_min_area": 10000     // Increase this (was 5000)
}
```

### Cooldown between triggers?
```json
{
  "story_cooldown_seconds": 60  // Wait 60 seconds between triggers
}
```

### Different camera?
```json
{
  "camera_index": 1  // Try 1, 2, etc.
}
```

## Troubleshooting

**Camera not working?**
```bash
v4l2-ctl --list-devices
```

**Check logs:**
```bash
sudo journalctl -u haunted-house -f
```

**Stop the service:**
```bash
sudo systemctl stop haunted-house
```

That's it! For more details, see README.md
