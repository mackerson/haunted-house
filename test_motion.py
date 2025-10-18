#!/usr/bin/env python3
"""
Minimal motion detection tester
Shows live camera feed with motion detection overlay
Press 'q' to quit
"""

import cv2
import time

# Configuration
CAMERA_INDEX = 0
MOTION_THRESHOLD = 30  # Background subtractor sensitivity
MIN_AREA = 2000        # Minimum motion area to detect
FRAMES_REQUIRED = 2    # Consecutive frames needed

def main():
    print("Starting motion detection test...")
    print(f"Settings: threshold={MOTION_THRESHOLD}, min_area={MIN_AREA}, frames={FRAMES_REQUIRED}")
    print("Press 'q' to quit")

    # Open camera
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    if not camera.isOpened():
        print("ERROR: Could not open camera")
        return

    # Warmup
    print("Camera warming up...")
    time.sleep(2)

    # Create background subtractor
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=MOTION_THRESHOLD,
        detectShadows=False
    )

    motion_count = 0

    while True:
        ret, frame = camera.read()
        if not ret:
            print("Failed to read frame")
            break

        # Apply background subtraction
        fg_mask = bg_subtractor.apply(frame)

        # Threshold and find contours
        _, thresh = cv2.threshold(fg_mask, 244, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find largest contour
        max_area = 0
        max_contour = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                max_contour = contour

        # Check if motion detected
        motion_detected = max_area > MIN_AREA

        # Update motion counter
        if motion_detected:
            motion_count += 1
            if motion_count >= FRAMES_REQUIRED:
                print(f"!!! MOTION CONFIRMED !!! max_area={max_area:.0f}")
                motion_count = 0  # Reset
        else:
            if motion_count > 0:
                print(f"Motion lost (count was {motion_count})")
            motion_count = 0

        # Draw on frame
        if max_contour is not None and max_area > 100:  # Show all significant contours
            cv2.drawContours(frame, [max_contour], -1, (0, 255, 0), 2)

        # Add text overlay
        color = (0, 255, 0) if motion_detected else (255, 255, 255)
        cv2.putText(frame, f"max_area: {max_area:.0f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(frame, f"threshold: {MIN_AREA}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"count: {motion_count}/{FRAMES_REQUIRED}", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # Show frames
        cv2.imshow('Motion Detection Test', frame)
        cv2.imshow('Threshold', thresh)

        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()
    print("Test complete")

if __name__ == "__main__":
    main()
