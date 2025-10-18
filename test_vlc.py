#!/usr/bin/env python3
"""
Simple VLC test to diagnose video output issues
"""

import vlc
import time
import sys
import os

def test_vlc_playback(video_path):
    """Test VLC video playback"""
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        return False

    print(f"Testing VLC playback with: {video_path}")
    print(f"VLC version: {vlc.libvlc_get_version().decode('utf-8')}")

    # Try different VLC configurations
    configs = [
        {
            "name": "Auto video output",
            "args": ['--vout=auto', '--verbose=2']
        },
        {
            "name": "X11 video output",
            "args": ['--vout=xcb_x11', '--verbose=2']
        },
        {
            "name": "OpenGL video output",
            "args": ['--vout=gl', '--verbose=2']
        }
    ]

    for config in configs:
        print(f"\n{'='*60}")
        print(f"Testing: {config['name']}")
        print(f"Args: {config['args']}")
        print('='*60)

        try:
            instance = vlc.Instance(config['args'])
            player = instance.media_player_new()
            media = instance.media_new(video_path)

            player.set_media(media)
            player.play()

            # Wait for playback to start
            time.sleep(2)

            state = player.get_state()
            has_vout = player.has_vout()

            print(f"Player state: {state}")
            print(f"Has video output: {has_vout}")

            if has_vout:
                print("✓ SUCCESS - Video output is working!")
                print("Playing for 5 seconds...")
                time.sleep(5)
                player.stop()
                return True
            else:
                print("✗ FAILED - No video output window")

            player.stop()

        except Exception as e:
            print(f"✗ ERROR: {e}")

        time.sleep(1)

    print("\n" + "="*60)
    print("All tests completed - none succeeded")
    print("\nPossible issues:")
    print("1. X11/Wayland display not available (check $DISPLAY)")
    print("2. VLC video output modules not installed")
    print("3. Video file is corrupted or unsupported format")
    print(f"\nCurrent DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Try to find a video in the project
        test_paths = [
            "videos/story/main.mp4",
            "videos/ambient/*.mp4"
        ]
        video_path = None
        for path in test_paths:
            if os.path.exists(path):
                video_path = path
                break

        if not video_path:
            print("Usage: python test_vlc.py <path-to-video.mp4>")
            print("\nOr place a video at: videos/story/main.mp4")
            sys.exit(1)

    test_vlc_playback(video_path)
