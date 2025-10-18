#!/usr/bin/env python3
"""
Haunted House Motion-Activated Video System
Detects motion via webcam and plays story video, then loops ambient videos
"""

import cv2
import vlc
import time
import json
import threading
import os
import glob
from pathlib import Path
from enum import Enum
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlaybackMode(Enum):
    AMBIENT = "ambient"
    STORY = "story"
    IDLE = "idle"


class MotionDetector:
    """Detects motion using webcam and background subtraction"""

    def __init__(self, camera_index=0, threshold=25, min_area=5000, warmup_time=2.0, frames_required=3):
        self.camera_index = camera_index
        self.threshold = threshold
        self.min_area = min_area
        self.warmup_time = warmup_time
        self.frames_required = frames_required
        self.motion_frame_count = 0
        self.camera = None
        self.background_subtractor = None
        self.running = False
        self.last_frame = None
        self.frame_change_count = 0

        # For continuous frame reading
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None

    def _capture_frames_continuously(self):
        """Background thread to continuously read frames from camera"""
        logger.info("Frame capture thread started")
        while self.running:
            ret, frame = self.camera.read()
            if ret:
                with self.frame_lock:
                    self.current_frame = frame
            time.sleep(0.01)  # Small delay to prevent CPU spinning
        logger.info("Frame capture thread stopped")

    def start(self):
        """Initialize camera and background subtractor"""
        logger.info(f"Starting camera {self.camera_index}")
        # Use V4L2 backend explicitly
        self.camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)

        if not self.camera.isOpened():
            raise Exception(f"Could not open camera {self.camera_index}")

        self.running = True

        # Start background thread to continuously read frames
        self.capture_thread = threading.Thread(target=self._capture_frames_continuously, daemon=True)
        self.capture_thread.start()

        # Give camera time to warm up and start capturing
        logger.info(f"Camera warming up for {self.warmup_time}s")
        time.sleep(self.warmup_time)

        # Create background subtractor
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=self.threshold,
            detectShadows=False
        )

        logger.info("Motion detector started")

    def stop(self):
        """Release camera resources"""
        self.running = False
        if self.camera:
            self.camera.release()
        logger.info("Motion detector stopped")

    def detect_motion(self):
        """Check if motion is detected in current frame with debouncing"""
        if not self.running:
            return False

        # Get the latest frame from the background thread
        with self.frame_lock:
            frame = self.current_frame

        if frame is None:
            logger.warning("No frame available from camera")
            return False

        # Check if frame is actually changing (diagnostic)
        import numpy as np
        if self.last_frame is not None:
            frame_diff = np.sum(np.abs(frame.astype(float) - self.last_frame.astype(float)))
            if frame_diff > 1000:  # Arbitrary threshold for "frame changed"
                self.frame_change_count += 1
            if self.frame_change_count % 50 == 0:  # Log every 50 frames
                logger.info(f"Frame diagnostic: frame_diff={frame_diff:.0f}, frames_changed={self.frame_change_count}")
        self.last_frame = frame.copy()

        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)

        # Threshold and find contours
        _, thresh = cv2.threshold(fg_mask, 244, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Check if any contour is large enough
        motion_detected = False
        max_area = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
            if area > self.min_area:
                motion_detected = True
                break

        # Save debug frames when motion detected
        if motion_detected:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            debug_dir = "motion_debug"
            os.makedirs(debug_dir, exist_ok=True)

            # Save original frame
            cv2.imwrite(f"{debug_dir}/frame_{timestamp}.jpg", frame)
            # Save foreground mask
            cv2.imwrite(f"{debug_dir}/mask_{timestamp}.jpg", fg_mask)
            # Save thresholded contours
            cv2.imwrite(f"{debug_dir}/thresh_{timestamp}.jpg", thresh)
            logger.info(f"Saved debug frames to {debug_dir}/")

        # Always log motion detection for debugging (even when no motion)
        logger.info(f"Motion check: detected={motion_detected}, max_area={max_area:.0f}, frame_count={self.motion_frame_count}/{self.frames_required}, threshold={self.min_area}")

        # Debouncing logic - require consecutive frames
        if motion_detected:
            self.motion_frame_count += 1
            if self.motion_frame_count >= self.frames_required:
                logger.info(f"!!! MOTION CONFIRMED after {self.motion_frame_count} frames - TRIGGERING !!!")
                self.motion_frame_count = 0  # Reset counter
                return True
        else:
            if self.motion_frame_count > 0:
                logger.info(f"Motion lost - resetting counter from {self.motion_frame_count}")
            self.motion_frame_count = 0  # Reset if no motion

        return False


class VideoController:
    """Controls video playback using VLC"""

    def __init__(self, fullscreen=True, mute_ambient=False):
        # VLC options for video playback
        vlc_args = ['--no-video-title-show', '--vout=xcb_xv', '--video-on-top', '--no-osd', '--avcodec-hw=none']

        logger.info(f"Initializing VLC with args: {vlc_args}")
        logger.info(f"VideoController settings: fullscreen={fullscreen}, mute_ambient={mute_ambient}")
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        self.fullscreen = fullscreen
        self.mute_ambient = mute_ambient

        # Set fullscreen mode
        if self.fullscreen:
            self.player.set_fullscreen(True)

        self.current_playlist = []
        self.playlist_index = 0
        self.is_playing = False
        self.current_mode = None

    def play_video(self, video_path, loop=False, mode=None):
        """Play a single video"""
        if not os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return False

        logger.info(f"Playing video: {video_path} (loop={loop}, mode={mode}, mute_ambient={self.mute_ambient})")
        media = self.instance.media_new(video_path)

        if loop:
            media.add_option('input-repeat=-1')

        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self.current_mode = mode

        # Give it a moment to start
        time.sleep(0.5)

        # Mute ambient videos if configured - do this AFTER play starts
        if mode == 'ambient' and self.mute_ambient:
            logger.info(f"MUTING ambient audio (mute_ambient={self.mute_ambient})")
            self.player.audio_set_mute(True)
            # Double check it worked
            is_muted = self.player.audio_get_mute()
            logger.info(f"Audio mute status after setting: {is_muted}")
        else:
            logger.info(f"NOT muting - mode={mode}, mute_ambient={self.mute_ambient}")
            self.player.audio_set_mute(False)

        state = self.player.get_state()
        logger.info(f"VLC player state after play(): {state}")

        # Check if we have a video output window
        if not self.player.has_vout():
            logger.warning("VLC has no video output window!")

        return True

    def play_playlist(self, video_paths, mode=None):
        """Play videos in sequence, looping through the playlist"""
        if not video_paths:
            logger.warning("Empty playlist")
            return False

        self.current_playlist = video_paths
        self.playlist_index = 0
        self.current_mode = mode
        return self.play_video(self.current_playlist[self.playlist_index], mode=mode)

    def next_in_playlist(self):
        """Move to next video in playlist"""
        if not self.current_playlist:
            return False

        self.playlist_index = (self.playlist_index + 1) % len(self.current_playlist)
        return self.play_video(self.current_playlist[self.playlist_index], mode=self.current_mode)

    def stop(self):
        """Stop playback"""
        logger.info("Stopping video playback")
        self.player.stop()
        self.is_playing = False

    def is_video_playing(self):
        """Check if video is currently playing"""
        state = self.player.get_state()
        return state in [vlc.State.Playing, vlc.State.Opening, vlc.State.Buffering]

    def is_video_ended(self):
        """Check if current video has ended"""
        state = self.player.get_state()
        return state == vlc.State.Ended


class HauntedHouse:
    """Main controller for the haunted house experience"""

    def __init__(self, config_path="config.json"):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        logger.info(f"Loaded configuration: {json.dumps(self.config, indent=2)}")

        self.motion_detector = MotionDetector(
            camera_index=self.config.get('camera_index', 0),
            threshold=self.config.get('motion_threshold', 25),
            min_area=self.config.get('motion_min_area', 5000),
            warmup_time=self.config.get('camera_warmup_time', 2.0),
            frames_required=self.config.get('motion_frames_required', 3)
        )

        self.video_controller = VideoController(
            fullscreen=self.config.get('fullscreen', True),
            mute_ambient=self.config.get('mute_ambient', False)
        )

        self.mode = PlaybackMode.IDLE
        self.running = False
        self.last_story_time = 0
        self.story_cooldown = self.config.get('story_cooldown_seconds', 30)

        # State control
        self.manual_trigger = False
        self.manual_stop = False
        self.motion_detection_enabled = True

    def get_ambient_videos(self):
        """Get list of all ambient videos"""
        ambient_dir = self.config['ambient_videos_dir']
        pattern = os.path.join(ambient_dir, "*.mp4")
        videos = sorted(glob.glob(pattern))
        logger.info(f"Found {len(videos)} ambient videos")
        return videos

    def can_trigger_story(self):
        """Check if enough time has passed since last story"""
        if self.manual_stop:
            return False

        time_since_story = time.time() - self.last_story_time
        return time_since_story >= self.story_cooldown

    def trigger_story_mode(self):
        """Manually trigger story mode"""
        logger.info("Story mode manually triggered")
        self.manual_trigger = True
        self.manual_stop = False

    def stop_story_mode(self):
        """Stop story mode and return to ambient"""
        logger.info("Story mode manually stopped")
        self.manual_stop = True
        self.manual_trigger = False

    def enable_motion_detection(self):
        """Enable automatic motion detection"""
        logger.info("Motion detection enabled")
        self.motion_detection_enabled = True

    def disable_motion_detection(self):
        """Disable automatic motion detection"""
        logger.info("Motion detection disabled")
        self.motion_detection_enabled = False

    def start(self):
        """Start the haunted house system"""
        logger.info("Starting Haunted House system")
        self.running = True

        # Start motion detector
        self.motion_detector.start()

        # Start with ambient videos
        ambient_videos = self.get_ambient_videos()
        if ambient_videos:
            self.mode = PlaybackMode.AMBIENT
            self.video_controller.play_playlist(ambient_videos, mode='ambient')
        else:
            logger.warning("No ambient videos found")
            self.mode = PlaybackMode.IDLE

        # Main control loop
        self.run_loop()

    def run_loop(self):
        """Main control loop"""
        logger.info("Entering main control loop")

        while self.running:
            try:
                # Check for manual trigger
                if self.manual_trigger and self.mode != PlaybackMode.STORY:
                    logger.info("Manual trigger detected - switching to story mode")
                    self.enter_story_mode()
                    self.manual_trigger = False

                # Check for manual stop
                if self.manual_stop and self.mode == PlaybackMode.STORY:
                    logger.info("Manual stop detected - switching to ambient mode")
                    self.enter_ambient_mode()
                    self.manual_stop = False

                # Handle current mode
                if self.mode == PlaybackMode.AMBIENT:
                    self.handle_ambient_mode()
                elif self.mode == PlaybackMode.STORY:
                    self.handle_story_mode()

                time.sleep(0.1)  # Small delay to prevent CPU spinning

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(1)

        self.stop()

    def handle_ambient_mode(self):
        """Handle ambient mode logic"""
        # Check if video ended, move to next
        if self.video_controller.is_video_ended():
            self.video_controller.next_in_playlist()

        # Check for motion to trigger story
        can_trigger = self.can_trigger_story()
        logger.info(f"Ambient mode: motion_enabled={self.motion_detection_enabled}, can_trigger={can_trigger}")

        if self.motion_detection_enabled and can_trigger:
            if self.motion_detector.detect_motion():
                logger.info("Motion detected - triggering story mode")
                self.enter_story_mode()

    def handle_story_mode(self):
        """Handle story mode logic"""
        # Check if story video has ended
        if self.video_controller.is_video_ended():
            logger.info("Story video ended - returning to ambient mode")
            self.enter_ambient_mode()

    def enter_story_mode(self):
        """Switch to story mode"""
        logger.info("Entering STORY mode")
        self.mode = PlaybackMode.STORY
        self.last_story_time = time.time()

        story_video = self.config['story_video']
        if os.path.exists(story_video):
            self.video_controller.stop()
            self.video_controller.play_video(story_video, loop=False, mode='story')
        else:
            logger.error(f"Story video not found: {story_video}")
            self.enter_ambient_mode()

    def enter_ambient_mode(self):
        """Switch to ambient mode"""
        logger.info("Entering AMBIENT mode")
        self.mode = PlaybackMode.AMBIENT

        ambient_videos = self.get_ambient_videos()
        if ambient_videos:
            self.video_controller.stop()
            self.video_controller.play_playlist(ambient_videos, mode='ambient')
        else:
            logger.warning("No ambient videos found")
            self.mode = PlaybackMode.IDLE

    def stop(self):
        """Stop the system"""
        logger.info("Stopping Haunted House system")
        self.running = False
        self.motion_detector.stop()
        self.video_controller.stop()
        cv2.destroyAllWindows()

    def get_status(self):
        """Get current system status"""
        return {
            'mode': self.mode.value,
            'motion_detection_enabled': self.motion_detection_enabled,
            'is_playing': self.video_controller.is_playing,
            'time_since_last_story': time.time() - self.last_story_time,
            'can_trigger_story': self.can_trigger_story()
        }


if __name__ == "__main__":
    haunted_house = HauntedHouse()
    haunted_house.start()
