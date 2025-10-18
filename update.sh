#!/bin/bash
# Update and restart the haunted house system

set -e

echo "=== Haunted House Update Script ==="
echo ""

# Save current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Pull latest changes
echo "Pulling latest changes from git..."
git pull origin main

echo ""
echo "Restarting service..."
sudo systemctl restart haunted-house

echo ""
echo "Waiting for service to start..."
sleep 3

echo ""
echo "Service status:"
sudo systemctl status haunted-house --no-pager | head -15

echo ""
echo "=== Update Complete ==="
echo ""
echo "Check logs with: sudo journalctl -u haunted-house -f"
echo "Web interface: http://$(hostname -I | awk '{print $1}'):8080"
