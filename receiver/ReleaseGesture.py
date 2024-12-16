import cv2
import mediapipe as mp
import time

class ReleaseDetector:
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
        self.was_closed = False

    def is_hand_open(self, hand_landmarks):
        finger_tips = [8, 12, 16, 20]
        finger_bases = [6, 10, 14, 18]
        return all(
            hand_landmarks.landmark[tip].y < hand_landmarks.landmark[base].y
            for tip, base in zip(finger_tips, finger_bases)
        )

    def can_trigger_gesture(self):
        current_time = time.time()
        return current_time - self.last_gesture_time >= self.detection_delay

    def released(self):
        print("Object Released!")
        self.last_gesture_time = time.time()

    def process_frame(self, frame):
        frame = cv2.flip(frame, 1)
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(imgRGB)

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                self.mpDraw.draw_landmarks(frame, handLms, self.mpHands.HAND_CONNECTIONS)

                if self.is_hand_open(handLms):
                    if self.was_closed and self.can_trigger_gesture():
                        self.released()

                    self.was_closed = False
                else:
                    self.was_closed = True

        return frame


def main():
    cap = cv2.VideoCapture(0)
    detector = ReleaseDetector(detection_delay=2.0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        processed_frame = detector.process_frame(frame)
        cv2.imshow('Release Gesture Detection', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
