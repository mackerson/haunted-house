# Development Workflow

## Making Changes Locally and Deploying to Pi

### 1. Make changes locally (on your dev machine)

Edit any files:
- `haunted_house.py` - Main application logic
- `config.json` - Configuration settings
- `web_server.py` - Web interface
- etc.

### 2. Commit and push to GitHub

```bash
git add .
git commit -m "Your change description"
git push origin main
```

### 3. Update on the Pi

SSH into your Pi and run:
```bash
cd ~/haunted-house
./update.sh
```

That's it! The update script will:
- Pull latest changes from GitHub
- Restart the service
- Show you the status

## Quick Commands for Pi

**Update and restart:**
```bash
cd ~/haunted-house && ./update.sh
```

**View logs:**
```bash
sudo journalctl -u haunted-house -f
```

**Manual restart:**
```bash
sudo systemctl restart haunted-house
```

**Check status:**
```bash
sudo systemctl status haunted-house
```

**Edit config directly:**
```bash
cd ~/haunted-house
nano config.json
sudo systemctl restart haunted-house
```

## Configuration Settings

Edit `config.json` to adjust:

```json
{
  "motion_threshold": 30,          // Higher = less sensitive
  "motion_min_area": 5000,         // Larger = needs bigger movement
  "motion_frames_required": 2,     // Consecutive frames for trigger
  "story_cooldown_seconds": 120,   // Time between triggers
  "mute_ambient": true             // Mute ambient videos
}
```

## Testing Motion Sensitivity

1. SSH into Pi: `ssh michael@10.74.95.63`
2. Watch logs: `sudo journalctl -u haunted-house -f`
3. Wave in front of camera
4. Look for "Motion detected" messages
5. Adjust config if needed
6. Restart: `sudo systemctl restart haunted-house`

## Troubleshooting

**Service won't start:**
```bash
sudo journalctl -u haunted-house -n 50
```

**Video not playing:**
- Check VLC logs in journal
- Verify videos exist: `ls -la ~/haunted-house/videos/`

**Web interface not accessible:**
```bash
curl http://localhost:8080/api/status
```

**Reset to working state:**
```bash
cd ~/haunted-house
git reset --hard origin/main
./update.sh
```
