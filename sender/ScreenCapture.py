import mss
import mss.tools
from datetime import datetime
import os
from playsound3 import playsound


def take_screenshot(save_path=None, sound_path=None):

    # Use mss to capture screenshot
    with mss.mss() as sct:
        # Capture entire screen
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)

        # Determine save path
        if save_path is None:
            save_path = "files/screenshot"

        # Ensure the directory exists
        os.makedirs(save_path, exist_ok=True)

        # Generate a unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot.png"
        full_path = os.path.join(save_path, filename)

        # Save screenshot
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=full_path)
        print(f"Screenshot saved to: {full_path}")

        # Play sound if a sound path is provided
        if sound_path:
            playsound(sound_path)
        else:
            # Play system default sound if no sound path is given
            playsound('files/screenshot_sound.mp3')

