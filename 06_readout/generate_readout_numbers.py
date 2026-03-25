"""
Generates real numbers from the scorecard/analytics CSVs
to paste into the executive readout.
"""
import pandas as pd, glob

df  = pd.read_csv("data/clean/glowmetric_analytics_table.csv")
sc  = pd.read_csv("data/clean/creator_scorecard.csv")
fmt = pd.read_csv("data/powerbi/vw_format_performance.csv")
tier= pd.read_csv("data/powerbi/vw_tier_analysis.csv")
fun = pd.read_csv("data/powerbi/vw_funnel_stage.csv")

yt = df[df.platform=="YouTube"]
tt = df[df.platform=="TikTok"]

print("="*60)
print(" REAL NUMBERS FOR EXECUTIVE READOUT")
print("="*60)

print("\n── SLIDE 1: PROGRAM NUMBERS ─────────────────────────────")
for plat, sub in [("YouTube", yt), ("TikTok", tt)]:
    print(f"\n  {plat}:")
    print(f"    Creators:         {sub.creator_handle.nunique()}")
    print(f"    Videos:           {sub.video_id.nunique()}")
    print(f"    Total views:      {sub.view_count.sum():,.0f}  ({sub.view_count.sum()/1e6:.1f}M)")
    print(f"    Total engagements:{sub.total_engagements.sum():,.0f}")
    print(f"    Avg ER:           {sub.engagement_rate.mean()*100:.2f}%")
    print(f"    Modeled spend:    ${sub.modeled_spend_usd.sum():,.0f}")
    print(f"    Avg CPE:          ${sub.cost_per_engagement.mean():.4f}")

total_views = df.view_count.sum()
total_eng   = df.total_engagements.sum()
total_spend = df.modeled_spend_usd.sum()
print(f"\n  COMBINED:")
print(f"    Total views:      {total_views:,.0f}  ({total_views/1e6:.1f}M)")
print(f"    Total engagements:{total_eng:,.0f}")
print(f"    Total spend:      ${total_spend:,.0f}")
print(f"    Blended CPE:      ${total_eng and total_spend/total_eng:.4f}")

print("\n── SLIDE 2: TOP PERFORMERS ──────────────────────────────")
top3 = sc[sc.recommendation=="Scale"].head(3)
print(top3[["creator_handle","platform","tier","avg_er","avg_reach_ratio","avg_cpe","performance_score"]].to_string(index=False))

print("\n── SLIDE 2: NANO vs MEGA comparison ─────────────────────")
tt_tier = tier[tier.platform=="TikTok"][["tier","avg_er","avg_reach_ratio","avg_cpe","views_per_dollar"]]
print(tt_tier.to_string(index=False))

print("\n── SLIDE 2: FORMAT PERFORMANCE (top 5 by ER) ────────────")
print(fmt.sort_values("avg_er",ascending=False).head(5)[
    ["platform","content_format","funnel_stage","avg_er","avg_cpe","pct_strong_er"]].to_string(index=False))

print("\n── SLIDE 2: FUNNEL DISTRIBUTION ─────────────────────────")
print(fun[["funnel_stage","platform","video_count","total_views","avg_er"]].to_string(index=False))

print("\n── SLIDE 3: BUDGET REALLOCATION SIGNAL ──────────────────")
cut = sc[sc.recommendation=="Cut"]
scale = sc[sc.recommendation=="Scale"]
print(f"  Scale candidates:  {len(scale)} creators")
print(f"  Cut candidates:    {len(cut)} creators")
cut_spend = sc[sc.recommendation=="Cut"]["total_spend"].sum()
print(f"  Spend on 'Cut' creators: ${cut_spend:,.0f} → reallocate to TikTok Nano/Micro")

yt_sc = sc[sc.platform=="YouTube"]
tt_sc = sc[sc.platform=="TikTok"]
print(f"\n  YouTube avg CPE:  ${yt_sc.avg_cpe.mean():.4f}")
print(f"  TikTok avg CPE:   ${tt_sc.avg_cpe.mean():.4f}")
print(f"  CPE efficiency gap: {yt_sc.avg_cpe.mean()/tt_sc.avg_cpe.mean():.1f}x")
