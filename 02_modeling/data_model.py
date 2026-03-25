"""
HardScope Challenge — M2: Data Modeling Pipeline
Brand: GlowMetric Q1 2025

Inputs:  data/raw/youtube_raw_*.csv   (from youtube_pull_v2.py)
         data/raw/tiktok_synthetic_*.csv

Outputs: data/clean/glowmetric_analytics_table.csv
         data/clean/creator_scorecard.csv
         data/clean/platform_summary.csv
"""

import glob, os
import pandas as pd
import numpy as np
from datetime import datetime

# ── Benchmarks (CreatorIQ 2024, Social Insider Q4 2024) ───────
BENCHMARKS = {
    "YouTube": {"good_er": 0.030, "avg_er": 0.010, "good_vsr": 0.15, "avg_vsr": 0.05},
    "TikTok":  {"good_er": 0.060, "avg_er": 0.040, "good_vfr": 0.50, "avg_vfr": 0.30},
}

# YouTube beauty rate cards (Influencer Marketing Hub 2024)
RATE_PER_1K_VIEWS = {"Mega": 18.0, "Macro": 14.0, "Mid": 10.0, "Micro": 7.0, "Nano": 4.0}

FUNNEL_MAP = {
    "Tutorial": "Consideration", "Routine": "Awareness",  "Short": "Awareness",
    "Review":   "Consideration", "Haul":    "Engagement",  "Vlog/Other": "Awareness",
    "Test/Rank":"Consideration", "GRWM":    "Awareness",
    "Skincare Routine": "Awareness", "Product Review": "Consideration",
    "Duet/Stitch": "Engagement", "Trending Sound": "Engagement",
}

def load_latest(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching: {pattern}")
    print(f"  ✓ Loading: {files[-1]}")
    return pd.read_csv(files[-1])

def normalize_youtube(df):
    df = df.copy()
    # v2 uses subscriber_count (not audience_size) — remap
    df["audience_size"]     = df["subscriber_count"]
    df["view_reach_ratio"]  = df.get("view_reach_ratio",
                                pd.Series(df["view_count"] / df["subscriber_count"].replace(0,1)))
    df["total_engagements"] = df["like_count"] + df["comment_count"]

    # Modeled spend
    df["modeled_spend_usd"] = df.apply(
        lambda r: round((r["view_count"] / 1000) * RATE_PER_1K_VIEWS.get(r["tier"], 10), 2), axis=1
    )
    df["cost_per_engagement"] = df.apply(
        lambda r: round(r["modeled_spend_usd"] / r["total_engagements"], 4)
                  if r["total_engagements"] > 0 else 0, axis=1
    )

    # Funnel + flags
    df["funnel_stage"] = df["content_format"].map(FUNNEL_MAP).fillna("Awareness")
    bench = BENCHMARKS["YouTube"]
    df["er_flag"]    = df["engagement_rate"].apply(
        lambda x: "Strong" if x >= bench["good_er"] else ("Average" if x >= bench["avg_er"] else "Weak"))
    df["reach_flag"] = df["view_reach_ratio"].apply(
        lambda x: "Strong" if x >= bench["good_vsr"] else ("Average" if x >= bench["avg_vsr"] else "Weak"))

    df["published_date"] = pd.to_datetime(df["published_date"])
    df["period_month"]   = df["published_date"].dt.to_period("M").astype(str)

    return _select_cols(df, "YouTube")

def normalize_tiktok(df):
    df = df.copy()
    df["audience_size"]     = df["follower_count"]
    df["view_reach_ratio"]  = df["view_follower_ratio"]
    df["watch_time_index"]  = round((df["duration_sec"] / 600) * df["engagement_rate"] * 100, 4)
    df["title"]             = df["content_format"] + " · " + df["tiktok_handle"]
    df["funnel_stage"]      = df["content_format"].map(FUNNEL_MAP).fillna("Engagement")

    bench = BENCHMARKS["TikTok"]
    df["er_flag"]    = df["engagement_rate"].apply(
        lambda x: "Strong" if x >= bench["good_er"] else ("Average" if x >= bench["avg_er"] else "Weak"))
    df["reach_flag"] = df["view_reach_ratio"].apply(
        lambda x: "Strong" if x >= bench["good_vfr"] else ("Average" if x >= bench["avg_vfr"] else "Weak"))

    df["published_date"] = pd.to_datetime(df["published_date"])
    df["period_month"]   = df["published_date"].dt.to_period("M").astype(str)

    return _select_cols(df, "TikTok")

def _select_cols(df, platform):
    df["platform"] = platform
    cols = [
        "platform","campaign","brand","creator_handle","tier","video_id","title",
        "published_date","period_month","content_format","funnel_stage",
        "audience_size","view_count","like_count","comment_count","share_count",
        "duration_sec","total_engagements","engagement_rate","view_reach_ratio",
        "watch_through_rate","watch_time_index","modeled_spend_usd","cost_per_engagement",
        "er_flag","reach_flag",
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    return df[cols]

def build_creator_scorecard(df):
    grp = df.groupby(["creator_handle","platform","tier","campaign"])
    sc = grp.agg(
        audience_size        =("audience_size","first"),
        total_videos         =("video_id","count"),
        total_views          =("view_count","sum"),
        total_engagements    =("total_engagements","sum"),
        avg_er               =("engagement_rate","mean"),
        avg_reach_ratio      =("view_reach_ratio","mean"),
        total_spend          =("modeled_spend_usd","sum"),
        avg_cpe              =("cost_per_engagement","mean"),
        avg_wti              =("watch_time_index","mean"),
        pct_strong_er        =("er_flag", lambda x: round(100*(x=="Strong").sum()/len(x),1)),
    ).reset_index().round(5)

    def score(r):
        b = BENCHMARKS.get(r["platform"], BENCHMARKS["YouTube"])
        er_n  = min(r["avg_er"]           / b.get("good_er",  0.03), 1.5)
        re_n  = min(r["avg_reach_ratio"]  / b.get("good_vsr", 0.15), 1.5)
        wt_n  = min(r["avg_wti"]          / 5.0,  1.5)
        cpe_s = 1 / (1 + r["avg_cpe"]) if r["avg_cpe"] > 0 else 0.5
        return round((er_n*.40 + re_n*.30 + wt_n*.20 + cpe_s*.10)*100, 1)

    sc["performance_score"] = sc.apply(score, axis=1)
    sc["recommendation"]    = sc["performance_score"].apply(
        lambda s: "Scale" if s>=70 else ("Optimize" if s>=45 else "Cut"))

    return sc.sort_values("performance_score", ascending=False)

def build_platform_summary(df):
    return df.groupby(["platform","period_month"]).agg(
        total_views       =("view_count","sum"),
        total_engagements =("total_engagements","sum"),
        avg_er            =("engagement_rate","mean"),
        total_spend       =("modeled_spend_usd","sum"),
        video_count       =("video_id","count"),
        creator_count     =("creator_handle","nunique"),
    ).reset_index().round(4)

def run():
    print("="*55)
    print(" HardScope — M2: Data Modeling Pipeline")
    print("="*55)
    os.makedirs("data/clean", exist_ok=True)

    print("\n[1/4] Loading raw data...")
    yt_raw = load_latest("data/raw/youtube_raw_*.csv")
    tt_raw = load_latest("data/raw/tiktok_synthetic_*.csv")

    print("\n[2/4] Normalizing + joining...")
    yt = normalize_youtube(yt_raw)
    tt = normalize_tiktok(tt_raw)
    df = pd.concat([yt, tt], ignore_index=True)
    print(f"  ✓ Combined: {len(df)} rows ({len(yt)} YT + {len(tt)} TT)")

    print("\n[3/4] Building scorecard + platform summary...")
    scorecard = build_creator_scorecard(df)
    platform_summary = build_platform_summary(df)

    print("\n[4/4] Saving outputs...")
    df.to_csv("data/clean/glowmetric_analytics_table.csv", index=False)
    scorecard.to_csv("data/clean/creator_scorecard.csv", index=False)
    platform_summary.to_csv("data/clean/platform_summary.csv", index=False)

    print(f"\n✅ Analytics table:   {len(df)} rows × {len(df.columns)} cols")
    print(f"✅ Creator scorecard: {len(scorecard)} rows")
    print(f"✅ Platform summary:  {len(platform_summary)} rows")

    print("\n🏆 Creator Scorecard (ranked by performance score):")
    print(scorecard[["creator_handle","platform","tier","avg_er",
                      "avg_reach_ratio","avg_cpe","performance_score","recommendation"]]
          .to_string(index=False))

    return df, scorecard, platform_summary

if __name__ == "__main__":
    run()
