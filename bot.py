import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = "UC4ZScRxLikYf82B5CZ_ZZJQ"
UPLOADS_PLAYLIST_ID = YOUTUBE_CHANNEL_ID.replace("UC", "UU", 1)

def check_youtube():
    if os.path.exists("last_video.txt"):
        with open("last_video.txt", "r") as f:
            saved_state = f.read().strip()
    else:
        saved_state = ""

    try:
        playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={UPLOADS_PLAYLIST_ID}&maxResults=1&key={YOUTUBE_API_KEY}"
        playlist_resp = requests.get(playlist_url).json()

        if "items" not in playlist_resp or not playlist_resp["items"]:
            return
            
        snippet = playlist_resp["items"][0]["snippet"]
        latest_video_id = snippet["resourceId"]["videoId"]
        title = snippet["title"]
        author = snippet["channelTitle"]
        link = f"https://www.youtube.com/watch?v={latest_video_id}"

        api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={latest_video_id}&key={YOUTUBE_API_KEY}"
        api_resp = requests.get(api_url).json()

        if "items" not in api_resp or not api_resp["items"]:
            return 

        video_snippet = api_resp["items"][0]["snippet"]
        live_status = video_snippet.get("liveBroadcastContent", "none") 
        thumbnail_url = f"https://img.youtube.com/vi/{latest_video_id}/maxresdefault.jpg"

        current_state = f"{latest_video_id},{live_status}"

        if current_state != saved_state:
            if saved_state == "":
                print(f"Tracking initialized on '{title}'. No ping sent.")
                with open("last_video.txt", "w") as f:
                    f.write(current_state)
            else:
                print(f"Status change detected: {title} is now {live_status}")
                
                if live_status == "upcoming":
                    status_text = f"📅 {author} scheduled a new stream!"
                    embed_color = 16753920
                elif live_status == "live":
                    status_text = f"🔴 {author} just went LIVE!"
                    embed_color = 16711680
                else:
                    status_text = f"🔵 {author} uploaded a new video!"
                    embed_color = 3447003

                message = {
                    "content": f"@everyone {status_text}",
                    "embeds": [
                        {
                            "title": title,
                            "url": link,
                            "description": f"[Click here to watch]({link})",
                            "color": embed_color,
                            "author": {
                                "name": status_text
                            },
                            "thumbnail": {
                                "url": thumbnail_url
                            }
                        }
                    ]
                }
                
                if DISCORD_WEBHOOK_URL:
                    requests.post(DISCORD_WEBHOOK_URL, json=message)
                    print(f"Sent {live_status} embed to Discord.")
                else:
                    print("ERROR: Webhook is missing from .env.")

                with open("last_video.txt", "w") as f:
                    f.write(current_state)
        else:
            print("Checked: No status changes.")
                
    except Exception as e:
        print(f"Error checking YouTube: {e}")

if __name__ == "__main__":
    print(f"Webhook loaded: {bool(DISCORD_WEBHOOK_URL)}")
    print(f"YouTube API Key loaded: {bool(YOUTUBE_API_KEY)}")
    print("Bot is tracking channel status...")
    while True:
        check_youtube()
        time.sleep(300)