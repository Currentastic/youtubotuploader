# Main Python Script: youtube_uploader_bot.py

import os
import json
import time
import shutil
import random
import requests
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, concatenate_videoclips
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load config
with open("config.json") as f:
    config = json.load(f)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    flow = InstalledAppFlow.from_client_secrets_file(
        config["youtube_api_secret_file"], SCOPES)
    creds = flow.run_console()
    return build("youtube", "v3", credentials=creds)

def download_video_from_youtube(keyword):
    search_url = f"https://www.youtube.com/results?search_query={keyword}"
    # Placeholder: should use yt-dlp or similar to download video based on keyword
    # Simulate download
    print(f"[+] Downloading video for keyword: {keyword}")
    return "downloaded_video.mp4"

def download_video_from_reddit(subreddit):
    # Placeholder: logic to scrape Reddit and download a video
    print(f"[+] Downloading video from subreddit: {subreddit}")
    return "reddit_video.mp4"

def is_video_allowed(title):
    forbidden_keywords = config["forbidden_keywords"]
    return not any(word.lower() in title.lower() for word in forbidden_keywords)

def add_intro_to_video(video_path):
    intro_path = config["intro_video"]
    final_path = f"processed_{video_path}"
    clip_intro = VideoFileClip(intro_path)
    clip_main = VideoFileClip(video_path)
    final_clip = concatenate_videoclips([clip_intro, clip_main])
    final_clip.write_videofile(final_path, codec="libx264")
    return final_path

def generate_thumbnail(title):
    # Placeholder: generate branded thumbnail
    thumbnail_path = f"thumbnail_{int(time.time())}.jpg"
    with open(thumbnail_path, "wb") as f:
        f.write(requests.get(config["default_thumbnail"]).content)
    return thumbnail_path

def generate_summary(title):
    return f"Yeh episode hai: {title} - isme aapko maza aayega!"

def schedule_uploads(videos_by_category):
    now = datetime.now()
    for day in range(7):
        for category, videos in videos_by_category.items():
            to_upload = videos[day*2:day*2+2]
            for video in to_upload:
                upload_time = now + timedelta(days=day)
                upload_video(video, upload_time)

def upload_video(video_info, scheduled_time):
    youtube = authenticate_youtube()
    file_path = video_info["file_path"]
    title = video_info["title"]
    description = video_info["description"]
    thumbnail_path = video_info["thumbnail"]

    request_body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': config.get("tags", []),
            'categoryId': config.get("category_id", "22"),
        },
        'status': {
            'privacyStatus': 'public',
            'publishAt': scheduled_time.isoformat() + "Z",
        }
    }

    media = MediaFileUpload(file_path)
    video_response = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media
    ).execute()

    video_id = video_response['id']
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail_path)
    ).execute()

    print(f"[+] Uploaded: {title}")

# Sample driver code
def main():
    categories = config["categories"]
    videos_by_category = {cat: [] for cat in categories}

    for cat in categories:
        for keyword in categories[cat]:
            video_path = download_video_from_youtube(keyword)
            if not is_video_allowed(keyword):
                print(f"[-] Skipping video for keyword: {keyword}")
                continue

            processed_video = add_intro_to_video(video_path)
            thumbnail = generate_thumbnail(keyword)
            summary = generate_summary(keyword)

            videos_by_category[cat].append({
                "file_path": processed_video,
                "title": f"{keyword} Episode",
                "description": summary,
                "thumbnail": thumbnail
            })

    schedule_uploads(videos_by_category)

if __name__ == "__main__":
    main()
