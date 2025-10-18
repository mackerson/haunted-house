#!/usr/bin/env python3
"""
Web interface for remote control of the Haunted House system
"""

from flask import Flask, render_template, jsonify, request
import threading
import json
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
haunted_house = None


@app.route('/')
def index():
    """Serve the control interface"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current system status"""
    if haunted_house:
        return jsonify(haunted_house.get_status())
    return jsonify({'error': 'System not initialized'}), 500


@app.route('/api/trigger', methods=['POST'])
def trigger_story():
    """Manually trigger story mode"""
    if haunted_house:
        haunted_house.trigger_story_mode()
        return jsonify({'success': True, 'message': 'Story mode triggered'})
    return jsonify({'error': 'System not initialized'}), 500


@app.route('/api/stop', methods=['POST'])
def stop_story():
    """Stop story mode and return to ambient"""
    if haunted_house:
        haunted_house.stop_story_mode()
        return jsonify({'success': True, 'message': 'Story mode stopped'})
    return jsonify({'error': 'System not initialized'}), 500


@app.route('/api/motion/enable', methods=['POST'])
def enable_motion():
    """Enable motion detection"""
    if haunted_house:
        haunted_house.enable_motion_detection()
        return jsonify({'success': True, 'message': 'Motion detection enabled'})
    return jsonify({'error': 'System not initialized'}), 500


@app.route('/api/motion/disable', methods=['POST'])
def disable_motion():
    """Disable motion detection"""
    if haunted_house:
        haunted_house.disable_motion_detection()
        return jsonify({'success': True, 'message': 'Motion detection disabled'})
    return jsonify({'error': 'System not initialized'}), 500


@app.route('/api/ambient/reload', methods=['POST'])
def reload_ambient():
    """Reload ambient video playlist"""
    if haunted_house and haunted_house.mode.value == 'ambient':
        haunted_house.enter_ambient_mode()
        return jsonify({'success': True, 'message': 'Ambient playlist reloaded'})
    return jsonify({'error': 'Not in ambient mode'}), 400


def run_web_server(haunted_house_instance, host='0.0.0.0', port=8080):
    """Run the Flask web server"""
    global haunted_house
    haunted_house = haunted_house_instance

    logger.info(f"Starting web server on {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    # For testing the web interface standalone
    from haunted_house import HauntedHouse
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"

    with open(config_path, 'r') as f:
        config = json.load(f)

    haunted_house_instance = HauntedHouse(config_path)

    # Start haunted house in separate thread
    haunted_thread = threading.Thread(target=haunted_house_instance.start, daemon=True)
    haunted_thread.start()

    # Run web server
    run_web_server(
        haunted_house_instance,
        host=config.get('web_host', '0.0.0.0'),
        port=config.get('web_port', 8080)
    )
