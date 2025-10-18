#!/bin/bash
# Installation script for Haunted House system on Raspberry Pi

set -e

echo "=== Haunted House Installation ==="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv vlc libvlc-dev python3-opencv

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
chmod +x run.py
chmod +x haunted_house.py
chmod +x web_server.py

# Set up systemd service (optional)
read -p "Install as systemd service to run on boot? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Get current directory
    INSTALL_DIR=$(pwd)

    # Update service file with correct paths
    sed -i "s|/home/pi/haunted-house|$INSTALL_DIR|g" haunted-house.service
    sed -i "s|User=pi|User=$USER|g" haunted-house.service

    # Install service
    sudo cp haunted-house.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable haunted-house.service

    echo "Service installed. You can control it with:"
    echo "  sudo systemctl start haunted-house"
    echo "  sudo systemctl stop haunted-house"
    echo "  sudo systemctl status haunted-house"
    echo "  sudo journalctl -u haunted-house -f  (view logs)"
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Place your story video at: videos/story/main.mp4"
echo "2. Place ambient videos in: videos/ambient/"
echo "3. Edit config.json to adjust settings"
echo "4. Run with: ./run.py"
echo ""
echo "Web interface will be available at: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
