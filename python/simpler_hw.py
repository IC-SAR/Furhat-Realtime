from furhat_realtime_api import FurhatClient
from dotenv import load_dotenv
import logging
import random
import time
import colorsys
import os

#pip install python-dotenv

# Load environment variables
load_dotenv()

# Configuration from .env
FURHAT_HOST = os.getenv("FURHAT_HOST", "172.27.8.18")
FURHAT_AUTH_KEY = os.getenv("FURHAT_AUTH_KEY")
VOICE_NAME = os.getenv("FURHAT_VOICE_NAME", "william")
VOICE_GENDER = os.getenv("FURHAT_VOICE_GENDER", "MALE")
VOICE_LANGUAGE = os.getenv("FURHAT_VOICE_LANGUAGE", "en-GB")

if __name__ == "__main__":
    # Connect to Furhat
    furhat = FurhatClient(FURHAT_HOST, auth_key=FURHAT_AUTH_KEY)
    furhat.set_logging_level(logging.INFO)

    try:
        furhat.connect()
    except Exception as e:
        print(f"Failed to connect to Furhat on {FURHAT_HOST}.")
        exit(0)

    # Configure voice
    furhat.request_voice_config(name=VOICE_NAME, gender=VOICE_GENDER, language=VOICE_LANGUAGE)

    # Get available voices and faces
    voice_status = furhat.request_voice_status()
    face_status = furhat.request_face_status()
    
    # Greet and show capabilities
    furhat.request_speak_text(
        f"Hello, I am Furhat. I have {len(voice_status['voice_list'])} voices "
        f"and {len(face_status['face_list'])} faces available."
    )

    # Count users
    user_data = furhat.request_users_once()
    furhat.request_speak_text(f"I can currently see {len(user_data['users'])} users.")

    # LED light show
    furhat.request_speak_text("Let me show off my LED lights.")
    for _ in range(10):
        hue = random.random()
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        furhat.request_led_set(color=color)
        time.sleep(0.5)

    furhat.request_led_set(color="#000000")
    furhat.request_speak_text("That's it for now.")

    print("Done")
    furhat.disconnect()