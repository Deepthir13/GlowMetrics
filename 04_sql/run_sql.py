"""
HardScope Challenge — M4: SQL Feature Engineering via SQLite
Loads clean analytics table → runs 8 SQL views → exports Power BI CSVs

Usage (from hardscope/ folder):
    python3 04_sql/run_sql.py
"""

import sqlite3, os
import pandas as pd

ANALYTICS_CSV = "data/clean/glowmetric_analytics_table.csv"
DB_PATH       = "data/clean/glowmetric.db"
EXPORT_DIR    = "data/powerbi"

SQL = """
CREATE VIEW IF NOT EXISTS vw_creator_video_metrics AS
SELECT *,
  CASE WHEN view_count>0 AND modeled_spend_usd IS NOT NULL
       THEN ROUND(modeled_spend_usd/view_count,6) ELSE NULL END AS cost_per_view,
  CASE WHEN platform='TikTok' AND view_count>0
       THEN ROUND(CAST(share_count AS FLOAT)/view_count,5) ELSE NULL END AS share_rate,
  CASE WHEN duration_sec<60  THEN 'Short (<1 min)'
       WHEN duration_sec<180 THEN 'Medium (1-3 min)'
       WHEN duration_sec<600 THEN 'Long (3-10 min)'
       ELSE 'Deep (10+ min)' END AS duration_bucket,
  CASE WHEN er_flag='Strong' AND reach_flag='Strong' THEN 'Top Performer'
       WHEN er_flag='Strong' OR  reach_flag='Strong' THEN 'Strong'
       WHEN er_flag='Weak'   AND reach_flag='Weak'   THEN 'Underperformer'
       ELSE 'Average' END AS overall_performance
FROM analytics;

CREATE VIEW IF NOT EXISTS vw_creator_scorecard AS
SELECT
  creator_handle, platform, tier,
  MAX(audience_size)                                    AS audience_size,
  COUNT(DISTINCT video_id)                              AS video_count,
  SUM(view_count)                                       AS total_views,
  SUM(total_engagements)                                AS total_engagements,
  ROUND(AVG(engagement_rate),5)                         AS avg_er,
  ROUND(AVG(view_reach_ratio),4)                        AS avg_reach_ratio,
  ROUND(SUM(modeled_spend_usd),2)                       AS total_spend,
  ROUND(AVG(cost_per_engagement),4)                     AS avg_cpe,
  ROUND(AVG(watch_time_index),3)                        AS avg_wti,
  ROUND(100.0*SUM(CASE WHEN er_flag='Strong' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_strong_er,
  CASE WHEN AVG(cost_per_engagement)<=0.03 THEN 'Efficient'
       WHEN AVG(cost_per_engagement)<=0.05 THEN 'Average'
       ELSE 'Expensive' END                             AS cpe_efficiency,
  CASE
    WHEN AVG(engagement_rate)>=(CASE platform WHEN 'YouTube' THEN 0.030 ELSE 0.060 END)
     AND AVG(view_reach_ratio)>=(CASE platform WHEN 'YouTube' THEN 0.15  ELSE 0.50  END)
    THEN 'Scale'
    WHEN AVG(engagement_rate)>=(CASE platform WHEN 'YouTube' THEN 0.010 ELSE 0.040 END)
    THEN 'Optimize'
    ELSE 'Cut' END                                      AS recommendation
FROM analytics
GROUP BY creator_handle, platform, tier
ORDER BY avg_er DESC;

CREATE VIEW IF NOT EXISTS vw_funnel_stage AS
SELECT funnel_stage, platform,
  COUNT(DISTINCT video_id)          AS video_count,
  SUM(view_count)                   AS total_views,
  SUM(total_engagements)            AS total_engagements,
  ROUND(AVG(engagement_rate),5)     AS avg_er,
  ROUND(SUM(modeled_spend_usd),2)   AS total_spend,
  ROUND(AVG(cost_per_engagement),4) AS avg_cpe
FROM analytics
GROUP BY funnel_stage, platform
ORDER BY CASE funnel_stage WHEN 'Awareness' THEN 1 WHEN 'Engagement' THEN 2 ELSE 3 END, platform;

CREATE VIEW IF NOT EXISTS vw_platform_trend AS
SELECT platform, period_month,
  COUNT(DISTINCT creator_handle)    AS active_creators,
  COUNT(DISTINCT video_id)          AS video_count,
  SUM(view_count)                   AS total_views,
  SUM(total_engagements)            AS total_engagements,
  ROUND(AVG(engagement_rate),5)     AS avg_er,
  ROUND(SUM(modeled_spend_usd),2)   AS total_spend
FROM analytics
GROUP BY platform, period_month
ORDER BY platform, period_month;

CREATE VIEW IF NOT EXISTS vw_format_performance AS
SELECT platform, content_format, funnel_stage,
  COUNT(DISTINCT video_id)                                                       AS video_count,
  ROUND(AVG(engagement_rate),5)                                                  AS avg_er,
  ROUND(AVG(view_reach_ratio),4)                                                 AS avg_reach_ratio,
  ROUND(AVG(watch_time_index),3)                                                 AS avg_wti,
  ROUND(AVG(cost_per_engagement),4)                                              AS avg_cpe,
  ROUND(100.0*SUM(CASE WHEN er_flag='Strong' THEN 1 ELSE 0 END)/COUNT(*),1)     AS pct_strong_er
FROM analytics
GROUP BY platform, content_format, funnel_stage
ORDER BY avg_er DESC;

CREATE VIEW IF NOT EXISTS vw_tier_analysis AS
SELECT platform, tier,
  COUNT(DISTINCT creator_handle)    AS creator_count,
  COUNT(DISTINCT video_id)          AS video_count,
  ROUND(AVG(engagement_rate),5)     AS avg_er,
  ROUND(AVG(view_reach_ratio),4)    AS avg_reach_ratio,
  ROUND(AVG(cost_per_engagement),4) AS avg_cpe,
  ROUND(SUM(modeled_spend_usd),2)   AS total_spend,
  SUM(view_count)                   AS total_views,
  CASE WHEN SUM(modeled_spend_usd)>0
       THEN ROUND(SUM(view_count)/SUM(modeled_spend_usd),2) ELSE NULL END AS views_per_dollar
FROM analytics
GROUP BY platform, tier
ORDER BY platform, CASE tier WHEN 'Mega' THEN 1 WHEN 'Macro' THEN 2 WHEN 'Mid' THEN 3 WHEN 'Micro' THEN 4 ELSE 5 END;

CREATE VIEW IF NOT EXISTS vw_incrementality_proxy AS
SELECT platform,
  CASE WHEN published_date < '2025-01-15' THEN '1_Pre-Campaign'
       WHEN published_date < '2025-03-01' THEN '2_Mid-Campaign'
       ELSE '3_Late-Campaign' END AS campaign_phase,
  COUNT(DISTINCT video_id)        AS video_count,
  ROUND(AVG(engagement_rate),5)   AS avg_er,
  ROUND(AVG(view_reach_ratio),4)  AS avg_reach_ratio,
  SUM(view_count)                 AS total_views
FROM analytics
GROUP BY platform, campaign_phase
ORDER BY platform, campaign_phase;

CREATE VIEW IF NOT EXISTS vw_alerts AS
WITH trend AS (
  SELECT creator_handle, platform, period_month,
    AVG(engagement_rate) AS period_er,
    LAG(AVG(engagement_rate)) OVER (
      PARTITION BY creator_handle, platform ORDER BY period_month
    ) AS prev_er
  FROM analytics
  GROUP BY creator_handle, platform, period_month
)
SELECT creator_handle, platform, period_month,
  ROUND(period_er,5)  AS current_er,
  ROUND(prev_er,5)    AS prior_er,
  ROUND(100.0*(period_er-prev_er)/NULLIF(prev_er,0),1) AS er_pct_change,
  CASE WHEN period_er < prev_er*0.80 THEN 'Declining ER (>20% drop)'
       WHEN period_er < prev_er*0.90 THEN 'Slight ER Decline'
       ELSE 'Stable' END AS alert_status
FROM trend
WHERE prev_er IS NOT NULL
ORDER BY er_pct_change ASC;
"""

VIEWS = [
    "vw_creator_video_metrics", "vw_creator_scorecard", "vw_funnel_stage",
    "vw_platform_trend", "vw_format_performance", "vw_tier_analysis",
    "vw_incrementality_proxy", "vw_alerts",
]

def main():
    print("="*55)
    print(" HardScope — M4: SQL Views → Power BI CSVs")
    print("="*55)

    print("\n[1/3] Loading analytics table into SQLite...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_csv(ANALYTICS_CSV)
    df = df.where(pd.notnull(df), None)
    df.to_sql("analytics", conn, if_exists="replace", index=False)
    print(f"  ✓ {len(df)} rows loaded")

    print("\n[2/3] Creating SQL views...")
    for stmt in [s.strip() for s in SQL.split(";") if s.strip()]:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                vname = stmt.split("IF NOT EXISTS ")[1].split(" AS")[0].strip()
                conn.execute(f"DROP VIEW IF EXISTS {vname}")
                conn.execute(stmt)
    conn.commit()
    print(f"  ✓ {len(VIEWS)} views created")

    print("\n[3/3] Exporting CSVs for Power BI...")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for view in VIEWS:
        out = pd.read_sql(f"SELECT * FROM {view}", conn)
        path = f"{EXPORT_DIR}/{view}.csv"
        out.to_csv(path, index=False)
        print(f"  ✓ {view}: {len(out)} rows → {path}")

    conn.close()
    print(f"\n✅ All done. Load CSVs from {EXPORT_DIR}/ into Power BI.")

if __name__ == "__main__":
    main()
