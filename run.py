#!/usr/bin/env python3
"""
Main launcher for Haunted House system with integrated web server
"""

import sys
import json
import threading
import logging
from haunted_house import HauntedHouse
from web_server import run_web_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"

    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Create haunted house instance
    haunted_house = HauntedHouse(config_path)

    # Start web server in separate thread
    web_thread = threading.Thread(
        target=run_web_server,
        args=(haunted_house, config.get('web_host', '0.0.0.0'), config.get('web_port', 8080)),
        daemon=True
    )
    web_thread.start()

    # Run haunted house main loop (blocks)
    haunted_house.start()


if __name__ == "__main__":
    main()
