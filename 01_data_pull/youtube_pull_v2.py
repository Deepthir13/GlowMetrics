"""
HardScope Challenge — M1: YouTube Data Pull (v2)
Looks up channel IDs dynamically via forHandle search — no hardcoded IDs.
"""

import os, time, re
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime

API_KEY = "Add your own Google -> Yotube data v3 API Key"

# Verified handles — will resolve IDs dynamically
CREATORS = [
    {"handle": "NikkieTutorials",   "search": "NikkieTutorials",    "tier": "Mega"},
    {"handle": "WayneGoss",         "search": "Wayne Goss",         "tier": "Macro"},
    {"handle": "Hyram",             "search": "Hyram skincare",     "tier": "Macro"},
    {"handle": "DrDrayzday",        "search": "Dr Dray skincare",   "tier": "Macro"},
    {"handle": "JamieGenevieve",    "search": "Jamie Genevieve",    "tier": "Mid"},
    {"handle": "ShaaanXO",          "search": "Shaaan XO makeup",   "tier": "Micro"},
    {"handle": "GlitterAndLazers",  "search": "Glitter And Lazers", "tier": "Mid"},
    {"handle": "AlexandrasGirly",   "search": "Alexandra Anele beauty", "tier": "Mid"},
    {"handle": "CassieTrayna",      "search": "Cassie Trayna skincare", "tier": "Nano"},
    {"handle": "KathleenLights",    "search": "KathleenLights makeup",  "tier": "Macro"},
]

MAX_VIDEOS = 15

def build_service():
    return build("youtube", "v3", developerKey=API_KEY)

def resolve_channel_id(service, search_query: str) -> tuple[str, str]:
    """Search for a channel by name, return (channel_id, channel_name)."""
    resp = service.search().list(
        part="snippet", q=search_query, type="channel", maxResults=1
    ).execute()
    items = resp.get("items", [])
    if not items:
        return None, None
    item = items[0]
    return item["snippet"]["channelId"], item["snippet"]["title"]

def get_channel_stats(service, channel_id: str) -> dict:
    resp = service.channels().list(
        part="snippet,statistics", id=channel_id
    ).execute()
    if not resp.get("items"):
        return {}
    item = resp["items"][0]
    stats = item.get("statistics", {})
    snippet = item.get("snippet", {})
    return {
        "channel_name":      snippet.get("title", ""),
        "subscriber_count":  int(stats.get("subscriberCount", 0)),
        "total_view_count":  int(stats.get("viewCount", 0)),
        "video_count":       int(stats.get("videoCount", 0)),
    }

def get_recent_videos(service, channel_id: str, max_results: int) -> list:
    resp = service.search().list(
        part="id,snippet", channelId=channel_id,
        order="date", type="video", maxResults=max_results
    ).execute()
    videos = []
    for item in resp.get("items", []):
        vid_id = item["id"].get("videoId")
        if vid_id:
            videos.append({
                "video_id":     vid_id,
                "published_at": item["snippet"]["publishedAt"],
                "title":        item["snippet"]["title"],
            })
    return videos

def get_video_stats(service, video_ids: list) -> dict:
    resp = service.videos().list(
        part="statistics,contentDetails,snippet",
        id=",".join(video_ids)
    ).execute()
    out = {}
    for item in resp.get("items", []):
        vid_id = item["id"]
        stats  = item.get("statistics", {})
        dur    = parse_duration(item.get("contentDetails", {}).get("duration", "PT0S"))
        out[vid_id] = {
            "view_count":    int(stats.get("viewCount", 0)),
            "like_count":    int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "duration_sec":  dur,
            "tags":          "|".join(item.get("snippet", {}).get("tags", [])[:10]),
        }
    return out

def parse_duration(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m: return 0
    return int(m.group(1) or 0)*3600 + int(m.group(2) or 0)*60 + int(m.group(3) or 0)

def infer_format(title: str, duration_sec: int) -> str:
    t = title.lower()
    if duration_sec < 60: return "Short"
    if any(k in t for k in ["routine","grwm","get ready","morning","night"]): return "Routine"
    if any(k in t for k in ["review","honest","worth it","first impression"]): return "Review"
    if any(k in t for k in ["tutorial","how to","technique"]): return "Tutorial"
    if any(k in t for k in ["haul","unboxing","pr "]): return "Haul"
    if any(k in t for k in ["rank","tier","testing","tried"]): return "Test/Rank"
    return "Vlog/Other"

def pull_all() -> pd.DataFrame:
    service = build_service()
    records = []

    for creator in CREATORS:
        handle = creator["handle"]
        tier   = creator["tier"]
        print(f"  Resolving: {handle}...")

        channel_id, channel_name = resolve_channel_id(service, creator["search"])
        if not channel_id:
            print(f"    ⚠ Channel not found for {handle}, skipping.")
            continue

        ch_stats = get_channel_stats(service, channel_id)
        if not ch_stats:
            print(f"    ⚠ No stats for {handle}, skipping.")
            continue

        subs = ch_stats["subscriber_count"]
        print(f"    ✓ {channel_name} — {subs:,} subscribers")

        videos = get_recent_videos(service, channel_id, MAX_VIDEOS)
        if not videos:
            print(f"    ⚠ No videos found, skipping.")
            continue

        video_ids = [v["video_id"] for v in videos]
        stats_map = get_video_stats(service, video_ids)

        for v in videos:
            vid_id  = v["video_id"]
            vs      = stats_map.get(vid_id, {})
            views   = vs.get("view_count", 0)
            likes   = vs.get("like_count", 0)
            comments= vs.get("comment_count", 0)
            dur     = vs.get("duration_sec", 0)
            er      = round((likes + comments) / subs, 5) if subs > 0 else 0
            vsr     = round(views / subs, 4) if subs > 0 else 0
            wti     = round((dur / 600) * er * 100, 4)

            records.append({
                "platform":            "YouTube",
                "creator_handle":      handle,
                "channel_name":        channel_name,
                "channel_id":          channel_id,
                "tier":                tier,
                "video_id":            vid_id,
                "title":               v["title"],
                "published_at":        v["published_at"],
                "published_date":      v["published_at"][:10],
                "content_format":      infer_format(v["title"], dur),
                "subscriber_count":    subs,
                "view_count":          views,
                "like_count":          likes,
                "comment_count":       comments,
                "share_count":         None,
                "duration_sec":        dur,
                "engagement_rate":     er,
                "view_reach_ratio":    vsr,
                "watch_through_rate":  None,
                "watch_time_index":    wti,
                "modeled_spend_usd":   None,
                "cost_per_engagement": None,
                "tags":                vs.get("tags", ""),
                "campaign":            "GlowMetric_Q1_2025",
                "brand":               "GlowMetric",
            })

        time.sleep(0.4)

    return pd.DataFrame(records)

if __name__ == "__main__":
    print("=" * 55)
    print(" HardScope — GlowMetric Campaign: YouTube Pull v2")
    print("=" * 55)
    print(f"\nResolving + pulling {len(CREATORS)} creators...\n")

    df = pull_all()

    if df.empty:
        print("\n❌ No data pulled. Check API key or quota.")
    else:
        print(f"\n📊 Quick summary:")
        print(df.groupby("creator_handle")[["view_count","engagement_rate"]].mean().round(4))

        os.makedirs("data/raw", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"data/raw/youtube_raw_{ts}.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n✅ Saved {len(df)} records → {csv_path}")
