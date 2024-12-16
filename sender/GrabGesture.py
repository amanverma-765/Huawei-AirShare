import os
import threading

import cv2
import mediapipe as mp
import time

from sender.FileSender import NetworkFileSender
from sender.ScreenCapture import take_screenshot

class GrabDetector:
    def __init__(self, detection_delay=0.5):
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mpDraw = mp.solutions.drawing_utils

        self.detection_delay = detection_delay
        self.last_gesture_time = 0
        self.was_open = False

    def is_hand_closed(self, hand_landmarks):
        finger_tips = [8, 12, 16, 20]
        finger_bases = [6, 10, 14, 18]
        return all(
            hand_landmarks.landmark[tip].y > hand_landmarks.landmark[base].y
            for tip, base in zip(finger_tips, finger_bases)
        )

    def can_trigger_gesture(self):
        current_time = time.time()
        return current_time - self.last_gesture_time >= self.detection_delay

    def grabbed(self):
        print("Object Grabbed!")
        os.makedirs('files/screenshot', exist_ok=True)

        take_screenshot()
        print("[*] Captured Screenshot")

        file_path = 'files/screenshot/screenshot.png'
        sender = NetworkFileSender(file_path)
        send_thread = threading.Thread(target=sender.start_sending, daemon=True)
        send_thread.start()

        self.last_gesture_time = time.time()

    def process_frame(self, frame):
        frame = cv2.flip(frame, 1)
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(imgRGB)

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                self.mpDraw.draw_landmarks(frame, handLms, self.mpHands.HAND_CONNECTIONS)

                if self.is_hand_closed(handLms):
                    if self.was_open and self.can_trigger_gesture():
                        self.grabbed()

                    self.was_open = False
                else:
                    self.was_open = True

        return frame


def main():
    cap = cv2.VideoCapture(0)
    detector = GrabDetector(detection_delay=2.0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        processed_frame = detector.process_frame(frame)
        cv2.imshow('Grab Gesture Detection', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()