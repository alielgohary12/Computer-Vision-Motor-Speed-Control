import cv2
import mediapipe as mp
import numpy as np
import serial
import time
import math
import os

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ==========================================
# Arduino Serial
# ==========================================

arduino = serial.Serial("COM6", 9600)
time.sleep(2)


# ==========================================
# MediaPipe Hand Landmarker
# ==========================================

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "hand_landmarker.task"
)

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

detector = vision.HandLandmarker.create_from_options(options)


# ==========================================
# Camera
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera Error")
    arduino.close()
    detector.close()
    exit()


# ==========================================
# Main Loop
# ==========================================

while True:

    ret, frame = cap.read()

    if not ret:
        print("Camera Error")
        break

    # Mirror image
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    # ======================================
    # Convert BGR -> RGB
    # ======================================

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # ======================================
    # Create MediaPipe Image
    # ======================================

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # ======================================
    # Detect Hand
    # ======================================

    result = detector.detect(mp_image)

    pwm = 0

    # ======================================
    # Hand Detected
    # ======================================

    if result.hand_landmarks:

        hand_landmarks = result.hand_landmarks[0]

        # ==================================
        # Thumb Tip = 4
        # Index Finger Tip = 8
        # ==================================

        thumb = hand_landmarks[4]
        index = hand_landmarks[8]

        # Convert normalized coordinates
        # to pixels

        x1 = int(thumb.x * w)
        y1 = int(thumb.y * h)

        x2 = int(index.x * w)
        y2 = int(index.y * h)

        # ==================================
        # Calculate Distance
        # ==================================

        distance = math.sqrt(
            (x2 - x1) ** 2 +
            (y2 - y1) ** 2
        )

        # ==================================
        # Distance -> PWM
        # ==================================

        pwm = np.interp(
            distance,
            [20, 200],
            [0, 255]
        )

        pwm = int(pwm)

        # ==================================
        # Draw Line
        # ==================================

        cv2.line(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )

        # ==================================
        # Draw Thumb
        # ==================================

        cv2.circle(
            frame,
            (x1, y1),
            10,
            (255, 0, 0),
            -1
        )

        # ==================================
        # Draw Index Finger
        # ==================================

        cv2.circle(
            frame,
            (x2, y2),
            10,
            (255, 0, 0),
            -1
        )

        # ==================================
        # Display Distance
        # ==================================

        cv2.putText(
            frame,
            f"Distance: {int(distance)} px",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # ==================================
        # Display PWM
        # ==================================

        cv2.putText(
            frame,
            f"PWM: {pwm}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # ==================================
        # Motor Speed %
        # ==================================

        speed_percent = int(
            (pwm / 255) * 100
        )

        cv2.putText(
            frame,
            f"Motor: {speed_percent}%",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # ==================================
        # Draw Hand Landmarks
        # ==================================

        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (17, 18), (18, 19), (19, 20),
            (0, 17)
        ]

        for start, end in connections:

            x_start = int(
                hand_landmarks[start].x * w
            )

            y_start = int(
                hand_landmarks[start].y * h
            )

            x_end = int(
                hand_landmarks[end].x * w
            )

            y_end = int(
                hand_landmarks[end].y * h
            )

            cv2.line(
                frame,
                (x_start, y_start),
                (x_end, y_end),
                (255, 255, 255),
                2
            )

    else:

        # ==================================
        # No Hand -> Stop Motor
        # ==================================

        pwm = 0

        cv2.putText(
            frame,
            "NO HAND DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    # ======================================
    # Send PWM to Arduino
    # ======================================

    arduino.write(
        f"{pwm}\n".encode()
    )

    # ======================================
    # Show Camera
    # ======================================

    cv2.imshow(
        "Thumb + Index Motor Control",
        frame
    )

    # ======================================
    # Press Q to Exit
    # ======================================

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ==========================================
# Stop Motor
# ==========================================

arduino.write(b"0\n")

time.sleep(0.2)


# ==========================================
# Cleanup
# ==========================================

cap.release()
arduino.close()
detector.close()
cv2.destroyAllWindows()