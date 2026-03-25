

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# BENCHMARK PARAMETERS (sourced from public reports)
# Beauty category TikTok benchmarks:
#   Median ER: 5.8% (beauty > avg platform ER of 4.1%)
#   Median views per video: varies heavily by follower tier
#   Watch-through rate (WTR): ~45% average for beauty tutorials

SEED = 42
np.random.seed(SEED)

# Same 10 creators, TikTok presence (approximate real follower counts)
CREATORS_TIKTOK = [
    {"handle": "HyramYT",         "tiktok_handle": "@hyram",           "followers": 6_800_000, "tier": "Macro"},
    {"handle": "DrDrayzday",      "tiktok_handle": "@drdrayzday",      "followers": 950_000,   "tier": "Macro"},
    {"handle": "NikkieTutorials", "tiktok_handle": "@nikkietutorials", "followers": 14_200_000,"tier": "Mega"},
    {"handle": "WayneGoss",       "tiktok_handle": "@waynegoss",       "followers": 2_100_000, "tier": "Macro"},
    {"handle": "JamieGenevieve",  "tiktok_handle": "@jamiegenevieve",  "followers": 680_000,   "tier": "Mid"},
    {"handle": "RachelHigginson", "tiktok_handle": "@rachelhigginson", "followers": 420_000,   "tier": "Mid"},
    {"handle": "GlitterandLazers","tiktok_handle": "@glitterandlazers","followers": 310_000,   "tier": "Mid"},
    {"handle": "HouseOfCB",       "tiktok_handle": "@houseofcb_beauty","followers": 48_000,    "tier": "Nano"},
    {"handle": "ShaaanXO",        "tiktok_handle": "@shaaanxo",        "followers": 890_000,   "tier": "Micro"},
    {"handle": "LisaHeldmann",    "tiktok_handle": "@lisaheldmann",    "followers": 62_000,     "tier": "Nano"},
]

FORMATS = ["GRWM", "Skincare Routine", "Product Review", "Duet/Stitch", "Tutorial", "Trending Sound", "Haul"]

# Format-level engagement multipliers (beauty category)
FORMAT_ER_MULT = {
    "GRWM":            1.05,
    "Skincare Routine":1.12,
    "Product Review":  0.95,
    "Duet/Stitch":     1.20,
    "Tutorial":        1.08,
    "Trending Sound":  1.30,
    "Haul":            0.90,
}

# Tier-level base ER (beauty TikTok benchmarks)
TIER_BASE_ER = {
    "Mega":   0.041,
    "Macro":  0.058,
    "Mid":    0.082,
    "Micro":  0.094,
    "Nano":   0.118,
}

# View-to-follower ratio by tier (TikTok algorithm boost for smaller accounts)
TIER_VFR = {
    "Mega":   0.22,
    "Macro":  0.35,
    "Mid":    0.55,
    "Micro":  0.72,
    "Nano":   0.90,
}

N_VIDEOS_PER_CREATOR = 15
CAMPAIGN_START = datetime(2025, 1, 1)
CAMPAIGN_END   = datetime(2025, 3, 31)


def generate_tiktok_data() -> pd.DataFrame:
    records = []
    date_range = (CAMPAIGN_END - CAMPAIGN_START).days

    for creator in CREATORS_TIKTOK:
        handle    = creator["handle"]
        tk_handle = creator["tiktok_handle"]
        followers = creator["followers"]
        tier      = creator["tier"]

        base_er  = TIER_BASE_ER[tier]
        base_vfr = TIER_VFR[tier]

        for i in range(N_VIDEOS_PER_CREATOR):
            fmt = np.random.choice(FORMATS, p=[0.20, 0.18, 0.15, 0.10, 0.15, 0.12, 0.10])
            er_mult = FORMAT_ER_MULT[fmt]

            # Views: follower × vfr ratio with noise
            views = int(followers * base_vfr * np.random.lognormal(0, 0.4))
            views = max(500, views)

            # Engagement rate with format multiplier + noise
            er = base_er * er_mult * np.random.lognormal(0, 0.25)
            er = round(min(er, 0.45), 5)  # cap at 45%

            likes    = int(followers * er * 0.85)
            comments = int(followers * er * 0.10)
            shares   = int(followers * er * 0.05)

            # Duration: TikTok beauty content 30s–180s
            duration_sec = int(np.random.choice(
                [15, 30, 45, 60, 90, 120, 180],
                p=[0.05, 0.15, 0.20, 0.25, 0.20, 0.10, 0.05]
            ))

            # Watch-through rate: shorter = higher
            base_wtr = 0.72 if duration_sec <= 30 else (0.55 if duration_sec <= 60 else 0.38)
            wtr = round(min(base_wtr * np.random.lognormal(0, 0.15), 0.99), 3)

            # Watch time proxy (seconds × views × WTR)
            watch_time_total = int(duration_sec * views * wtr)

            # Publish date
            pub_date = CAMPAIGN_START + timedelta(days=np.random.randint(0, date_range))

            # Modeled CPE (cost per engagement) — using $0.01–$0.04 per engagement typical for beauty
            base_cpe = {"Mega": 0.042, "Macro": 0.031, "Mid": 0.022, "Micro": 0.016, "Nano": 0.011}[tier]
            total_engagements = likes + comments + shares
            modeled_spend = round(total_engagements * base_cpe * np.random.lognormal(0, 0.15), 2)
            cpe = round(modeled_spend / total_engagements if total_engagements > 0 else 0, 4)

            # Sound type
            sound_type = "Trending" if fmt == "Trending Sound" else np.random.choice(
                ["Original", "Trending", "Licensed"], p=[0.45, 0.35, 0.20]
            )

            records.append({
                "platform":            "TikTok",
                "creator_handle":      handle,
                "tiktok_handle":       tk_handle,
                "tier":                tier,
                "video_id":            f"tt_{handle.lower()}_{i:03d}",
                "content_format":      fmt,
                "sound_type":          sound_type,
                "published_date":      pub_date.date(),

                # audience
                "follower_count":      followers,

                # performance
                "view_count":          views,
                "like_count":          likes,
                "comment_count":       comments,
                "share_count":         shares,
                "duration_sec":        duration_sec,
                "watch_through_rate":  wtr,
                "watch_time_total_sec":watch_time_total,

                # engineered features
                "engagement_rate":     er,
                "view_follower_ratio": round(views / followers, 4),
                "total_engagements":   total_engagements,
                "modeled_spend_usd":   modeled_spend,
                "cost_per_engagement": cpe,

                # campaign label
                "campaign":            "GlowMetric_Q1_2025",
                "brand":               "GlowMetric",
            })

    df = pd.DataFrame(records)
    return df


def save_outputs(df: pd.DataFrame, out_dir: str = "data/raw"):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = f"{out_dir}/tiktok_synthetic_{ts}.csv"
    df.to_csv(csv_path, index=False)

    print(f"\n✅ Generated {len(df)} TikTok records (synthetic, benchmark-grounded)")
    print(f"   CSV → {csv_path}")
    print(f"\n📊 Quick summary by tier:")
    print(df.groupby("tier")[["engagement_rate", "view_follower_ratio", "cost_per_engagement"]].mean().round(4))
    return csv_path


if __name__ == "__main__":
    print("=" * 55)
    print(" HardScope — GlowMetric: TikTok Synthetic Dataset")
    print("=" * 55)
    print("\nNote: Using benchmark-grounded synthetic data.")
    print("TikTok Research API requires formal approval (2–4 weeks).")
    print("Benchmarks sourced: Influencer Marketing Hub 2024, CreatorIQ Beauty Report.\n")

    df = generate_tiktok_data()
    save_outputs(df, out_dir="data/raw")
