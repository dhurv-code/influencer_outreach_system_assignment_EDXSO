
import json
import random
import re
from pathlib import Path
from urllib.parse import urlencode
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
NICHER_LIST = ["Fashion & Beauty", "Fitness", "Tech", "Gaming", "Lifestyle"]
PLATFORMS = ["Instagram", "YouTube", "TikTok"]
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
EMAIL_RE = re.compile(r"(?i)[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+")


def generate_mock_influencers(count=50) -> list[dict]:
    """Create synthetic records for local testing only; never represent as real."""
    records = []
    for i in range(count):
        niche = random.choice(NICHER_LIST)
        handle = f"demo_creator_{i+1:03d}"
        records.append({
            "influencer_id": f"DEMO_{i+1:03d}",
            "name": f"Demo Creator {i+1}",
            "platform": random.choice(PLATFORMS),
            "profile_url": "",
            "follower_count": random.randint(3000, 120000),
            "engagement_rate": round(random.uniform(0.8, 6.5), 2),
            "category_niche": niche,
            "contact_email": None,
            "recent_post_caption": f"Synthetic test caption about {niche.lower()} content.",
            "data_source": "SYNTHETIC DEMO DATA - NOT A REAL PROFILE",
        })
    return records


def _youtube_get(resource: str, params: dict, api_key: str) -> dict:
    response = requests.get(
        f"{YOUTUBE_API_BASE}/{resource}",
        params={**params, "key": api_key}, timeout=25,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", "YouTube API error"))
    return data


def discover_youtube_influencers(api_key: str, query: str, count: int = 50, niche: str = "Fashion & Beauty") -> list[dict]:
    """Discover public YouTube channels and calculate a transparent video engagement proxy.

    Engagement proxy = (likes + comments) / views * 100 for videos returned by
    the search. It is not the creator's private audience analytics. Email is only
    extracted if explicitly present in the public channel description.
    """
    if not api_key or not api_key.strip():
        raise ValueError("Add a YouTube Data API key to discover real public channels.")
    if not query.strip():
        raise ValueError("Enter a niche/search query, for example: Indian skincare routine.")

    found_videos = []
    page_token = None
    seen_video_ids = set()
    # YouTube search.list costs quota; stop once enough unique channels have been found.
    for _ in range(5):
        params = {"part": "snippet", "q": query, "type": "video", "maxResults": 50, "order": "relevance"}
        if page_token:
            params["pageToken"] = page_token
        page = _youtube_get("search", params, api_key)
        for item in page.get("items", []):
            vid = item.get("id", {}).get("videoId")
            sn = item.get("snippet", {})
            if vid and vid not in seen_video_ids:
                seen_video_ids.add(vid)
                found_videos.append({"video_id": vid, "channel_id": sn.get("channelId", ""), "channel_title": sn.get("channelTitle", ""), "title": sn.get("title", "")})
        unique_channels = {v["channel_id"] for v in found_videos if v["channel_id"]}
        page_token = page.get("nextPageToken")
        if len(unique_channels) >= count or not page_token:
            break

    if not found_videos:
        return []

    video_ids = [v["video_id"] for v in found_videos]
    video_stats = {}
    for start in range(0, len(video_ids), 50):
        stats = _youtube_get("videos", {"part": "statistics,snippet", "id": ",".join(video_ids[start:start+50])}, api_key)
        for item in stats.get("items", []):
            video_stats[item["id"]] = item

    channel_ids = list(dict.fromkeys(v["channel_id"] for v in found_videos if v["channel_id"]))[:count]
    channels = {}
    for start in range(0, len(channel_ids), 50):
        result = _youtube_get("channels", {"part": "snippet,statistics" , "id": ",".join(channel_ids[start:start+50])}, api_key)
        for item in result.get("items", []):
            channels[item["id"]] = item

    videos_by_channel = {}
    for v in found_videos:
        stat = video_stats.get(v["video_id"], {})
        st = stat.get("statistics", {})
        views = int(st.get("viewCount", 0) or 0)
        likes = int(st.get("likeCount", 0) or 0)
        comments = int(st.get("commentCount", 0) or 0)
        v["engagement_proxy"] = ((likes + comments) / views * 100) if views else 0.0
        v["views"] = views
        videos_by_channel.setdefault(v["channel_id"], []).append(v)

    records = []
    for channel_id in channel_ids:
        channel = channels.get(channel_id)
        if not channel:
            continue
        sn = channel.get("snippet", {})
        stats = channel.get("statistics", {})
        subscribers = int(stats.get("subscriberCount", 0) or 0)
        # Channels that hide subscriber counts cannot be checked against follower criteria.
        if stats.get("hiddenSubscriberCount") or not subscribers:
            followers = 0
        else:
            followers = subscribers
        vids = videos_by_channel.get(channel_id, [])
        recent = max(vids, key=lambda x: x.get("views", 0), default={})
        description = sn.get("description", "")
        emails = EMAIL_RE.findall(description)
        records.append({
            "influencer_id": f"YT_{channel_id}",
            "name": sn.get("title", "Unknown channel"),
            "platform": "YouTube",
            "profile_url": f"https://www.youtube.com/channel/{channel_id}",
            "follower_count": followers,
            "engagement_rate": round(sum(v.get("engagement_proxy", 0) for v in vids) / max(len(vids), 1), 2),
            "category_niche": niche,
            "contact_email": emails[0] if emails else None,
            "recent_post_caption": recent.get("title", "No video title available from search results"),
            "data_source": "YouTube Data API; engagement is a public-video proxy",
        })
        if len(records) >= count:
            break
    return records


def save_discovery_records(records: list[dict], output_path=None):
    path = Path(output_path) if output_path else DATA_DIR / "raw_influencers.json"
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    print("Use the Streamlit app to discover public YouTube channels with your own API key.")
    print("Synthetic records are for testing only; they are not real influencer data.")
