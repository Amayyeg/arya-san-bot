import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = "UC4ZScRxLikYf82B5CZ_ZZJQ"

def get_uploads_playlist_id():
    try:
        channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={YOUTUBE_CHANNEL_ID}&key={YOUTUBE_API_KEY}"
        resp = requests.get(channel_url).json()
        if "items" in resp and resp["items"]:
            return resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except Exception as e:
        print(f"Error fetching channel playlist: {e}")
    return YOUTUBE_CHANNEL_ID.replace("UC", "UU", 1)

def check_youtube():
    if os.path.exists("last_video.txt"):
        with open("last_video.txt", "r") as f:
            saved_state = f.read().strip()
    else:
        saved_state = ""

    try:
        uploads_playlist_id = get_uploads_playlist_id()
        playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=3&key={YOUTUBE_API_KEY}"
        playlist_resp = requests.get(playlist_url).json()

        if "items" not in playlist_resp or not playlist_resp["items"]:
            print(f"Debug: Playlist {uploads_playlist_id} returned no items.")
            return
            
        for item in playlist_resp["items"]:
            snippet = item["snippet"]
            latest_video_id = snippet["resourceId"]["videoId"]
            title = snippet["title"]
            author = snippet["channelTitle"]
            link = f"https://www.youtube.com/watch?v={latest_video_id}"

            api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={latest_video_id}&key={YOUTUBE_API_KEY}"
            api_resp = requests.get(api_url).json()

            if "items" not in api_resp or not api_resp["items"]:
                continue 

            video_data = api_resp["items"][0]
            video_snippet = video_data["snippet"]
            live_status = video_snippet.get("liveBroadcastContent", "none") 
            thumbnail_url = f"https://img.youtube.com/vi/{latest_video_id}/maxresdefault.jpg"

            current_state = f"{latest_video_id},{live_status}"

            if current_state != saved_state:
                if saved_state == "":
                    print(f"Tracking initialized on '{title}'. Saving state without ping.")
                    with open("last_video.txt", "w") as f:
                        f.write(current_state)
                    return
                
                saved_id = saved_state.split(",")[0] if "," in saved_state else ""
                saved_status = saved_state.split(",")[1] if "," in saved_state else ""
                
                if latest_video_id == saved_id and live_status == "none" and saved_status in ["live", "upcoming"]:
                    print(f"Stream '{title}' ended. Updating state silently.")
                    with open("last_video.txt", "w") as f:
                        f.write(current_state)
                    break

                print(f"New content detected for '{title}'! Sending to Discord...")
                
                if live_status == "upcoming":
                    status_text = f"📅 {author} scheduled a new stream/premiere!"
                    embed_color = 16753920
                elif live_status == "live":
                    status_text = f"🔴 {author} just went LIVE!"
                    embed_color = 16711680
                else:
                    if "#shorts" in title.lower() or "#short" in title.lower():
                        status_text = f"📱 {author} uploaded a new YouTube Short!"
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
                    response = requests.post(DISCORD_WEBHOOK_URL, json=message)
                    print(f"Discord Response Status: {response.status_code}")
                else:
                    print("ERROR: Webhook URL is missing.")
                
                with open("last_video.txt", "w") as f:
                    f.write(current_state)
                break 
            else:
                current_time = time.strftime("%I:%M:%S %p")
                print(f"[{current_time}] Checked '{title}' - No update found. No notification sent.")
                break
                
    except Exception as e:
        print(f"Error checking YouTube: {e}")

if __name__ == "__main__":
    print(f"Webhook loaded: {bool(DISCORD_WEBHOOK_URL)}")
    print(f"YouTube API Key loaded: {bool(YOUTUBE_API_KEY)}")
    print("Bot is tracking channel status (Stream-Fix Mode)...")
    while True:
        check_youtube()
        time.sleep(60)