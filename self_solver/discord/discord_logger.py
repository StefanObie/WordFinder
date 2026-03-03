import os
import requests
from enum import Enum
from dotenv import load_dotenv

class MessageType(Enum):
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

# Discord embed colors (decimal RGB)
EMBED_COLORS = {
    MessageType.WARNING: 0xFFA500,  # Orange
    MessageType.ERROR: 0xFF0000,    # Red
    MessageType.SUCCESS: 0x00FF00,  # Green (not used for embed, but can be added)
}

# Optionally, you can add color codes or Discord embeds for richer formatting

def send_discord_message(message: str, msg_type: MessageType = MessageType.SUCCESS, exception: Exception = None):
    """Send a formatted message to Discord webhook according to message type, with embed color for warning/error."""
    load_dotenv()
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    username = os.getenv("DISCORD_USERNAME")

    if not webhook_url:
        print("Discord webhook URL missing (DISCORD_WEBHOOK_URL)")
        return

    content = f"{message}"
    if exception is not None:
        content += f"\n{str(exception)}"

    # Use embed for warning and error
    if msg_type in (MessageType.WARNING, MessageType.ERROR):
        color = EMBED_COLORS.get(msg_type, 0x000000)
        embed = {
            "description": content,
            "color": color
        }
        payload = {
            "embeds": [embed]
        }
    else:
        payload = {
            "content": content
        }

    if username:
        payload["username"] = username

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code not in (200, 204):
            print(f"Discord webhook failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Discord webhook error: {e}")
