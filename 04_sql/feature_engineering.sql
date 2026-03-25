-- ============================================================
-- HardScope Challenge — M4: SQL Feature Engineering
-- Brand: GlowMetric Q1 2025 Creator Campaign
-- Engine: SQLite (run via Python) | Also valid in BigQuery/Snowflake
-- Input:  glowmetric_analytics_table.csv  (loaded as table `analytics`)
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- 1. CORE ANALYTICS VIEW
--    Base table with all engineered features + benchmark flags
-- ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_creator_video_metrics AS
SELECT
    platform,
    campaign,
    brand,
    creator_handle,
    tier,
    video_id,
    title,
    published_date,
    period_month,
    content_format,
    funnel_stage,
    audience_size,
    view_count,
    like_count,
    comment_count,
    share_count,
    duration_sec,
    total_engagements,
    engagement_rate,
    view_reach_ratio,
    watch_through_rate,
    watch_time_index,
    modeled_spend_usd,
    cost_per_engagement,
    er_flag,
    reach_flag,

    -- Cost per view (CPV)
    CASE 
        WHEN view_count > 0 AND modeled_spend_usd IS NOT NULL 
        THEN ROUND(modeled_spend_usd / view_count, 6)
        ELSE NULL 
    END AS cost_per_view,

    -- Share rate (TikTok only meaningful)
    CASE 
        WHEN platform = 'TikTok' AND view_count > 0 
        THEN ROUND(CAST(share_count AS FLOAT) / view_count, 5)
        ELSE NULL 
    END AS share_rate,

    -- Duration bucket
    CASE
        WHEN duration_sec < 60  THEN 'Short (<1 min)'
        WHEN duration_sec < 180 THEN 'Medium (1-3 min)'
        WHEN duration_sec < 600 THEN 'Long (3-10 min)'
        ELSE 'Deep (10+ min)'
    END AS duration_bucket,

    -- Composite performance flag
    CASE
        WHEN er_flag = 'Strong' AND reach_flag = 'Strong' THEN 'Top Performer'
        WHEN er_flag = 'Strong' OR  reach_flag = 'Strong' THEN 'Strong'
        WHEN er_flag = 'Average' AND reach_flag = 'Average' THEN 'Average'
        WHEN er_flag = 'Weak' AND reach_flag = 'Weak' THEN 'Underperformer'
        ELSE 'Mixed'
    END AS overall_performance

FROM analytics;


-- ─────────────────────────────────────────────────────────────
-- 2. CREATOR SCORECARD
--    One row per creator per platform — sortable table for dashboard
-- ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_creator_scorecard AS
SELECT
    creator_handle,
    platform,
    tier,
    MAX(audience_size)                              AS audience_size,
    COUNT(DISTINCT video_id)                        AS video_count,
    SUM(view_count)                                 AS total_views,
    SUM(total_engagements)                          AS total_engagements,
    ROUND(AVG(engagement_rate), 5)                  AS avg_er,
    ROUND(AVG(view_reach_ratio), 4)                 AS avg_reach_ratio,
    ROUND(SUM(modeled_spend_usd), 2)                AS total_spend,
    ROUND(AVG(cost_per_engagement), 4)              AS avg_cpe,
    ROUND(AVG(watch_time_index), 3)                 AS avg_wti,

    -- Best performing format
    (
        SELECT content_format
        FROM analytics a2
        WHERE a2.creator_handle = a.creator_handle
          AND a2.platform = a.platform
        GROUP BY content_format
        ORDER BY AVG(engagement_rate) DESC
        LIMIT 1
    ) AS best_format,

    -- % of videos that are Strong ER
    ROUND(
        100.0 * SUM(CASE WHEN er_flag = 'Strong' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS pct_strong_er,

    -- CPE efficiency vs benchmark ($0.03 = good)
    CASE
        WHEN AVG(cost_per_engagement) <= 0.03 THEN 'Efficient'
        WHEN AVG(cost_per_engagement) <= 0.05 THEN 'Average'
        ELSE 'Expensive'
    END AS cpe_efficiency,

    -- Scale / Optimize / Cut
    CASE
        WHEN AVG(engagement_rate) >= (
            CASE platform WHEN 'YouTube' THEN 0.030 ELSE 0.060 END
        )
        AND AVG(view_reach_ratio) >= (
            CASE platform WHEN 'YouTube' THEN 0.15 ELSE 0.50 END
        )
        THEN 'Scale'
        WHEN AVG(engagement_rate) >= (
            CASE platform WHEN 'YouTube' THEN 0.018 ELSE 0.040 END
        )
        THEN 'Optimize'
        ELSE 'Cut'
    END AS recommendation

FROM analytics a
GROUP BY creator_handle, platform, tier
ORDER BY avg_er DESC;


-- ─────────────────────────────────────────────────────────────
-- 3. FUNNEL VIEW
--    Content volume and engagement by funnel stage
-- ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_funnel_stage AS
SELECT
    funnel_stage,
    platform,
    COUNT(DISTINCT video_id)        AS video_count,
    SUM(view_count)                 AS total_views,
    SUM(total_engagements)          AS total_engagements,
    ROUND(AVG(engagement_rate), 5)  AS avg_er,
    ROUND(SUM(modeled_spend_usd), 2)AS total_spend,
    ROUND(AVG(cost_per_engagement), 4) AS avg_cpe
FROM analytics
GROUP BY funnel_stage, platform
ORDER BY 
    CASE funnel_stage 
        WHEN 'Awareness'     THEN 1 
        WHEN 'Engagement'    THEN 2 
        WHEN 'Consideration' THEN 3 
    END,
    platform;


-- ─────────────────────────────────────────────────────────────
-- 4. PLATFORM TIME SERIES
--    Week-over-week trend for key KPIs
-- ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_platform_trend AS
SELECT
    platform,
    period_month,
    COUNT(DISTINCT creator_handle)  AS active_creators,
    COUNT(DISTINCT video_id)        AS video_count,
    SUM(view_count)                 AS total_views,
    SUM(total_engagements)          AS total_engagements,
    ROUND(AVG(engagement_rate), 5)  AS avg_er,
    ROUND(SUM(modeled_spend_usd), 2)AS total_spend
FROM analytics
GROUP BY platform, period_month
ORDER BY platform, period_month;


-- ─────────────────────────────────────────────────────────────
-- 5. FORMAT PERFORMANCE
--    Best / worst content formats by ER and cost efficiency
-- ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_format_performance AS
SELECT
    platform,
    content_format,
    funnel_stage,
    COUNT(DISTINCT video_id)            AS video_count,
    ROUND(AVG(engagement_rate), 5)      AS avg_er,
    ROUND(AVG(view_reach_ratio), 4)     AS avg_reach_ratio,
    ROUND(AVG(watch_time_index), 3)     AS avg_wti,
    ROUND(AVG(cost_per_engagement), 4)  AS avg_cpe,
    ROUND(
        100.0 * SUM(CASE WHEN er_flag = 'Strong' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS pct_strong_er
FROM analytics
GROUP BY platform, content_format, funnel_stage
ORDER BY avg_er DESC;


-- ─────────────────────────────────────────────────────────────
-- 6. TIER ANALYSIS
--    Does creator tier explain performance? (classic debate in influencer)
-- ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_tier_analysis AS
SELECT
    platform,
    tier,
    COUNT(DISTINCT creator_handle)      AS creator_count,
    COUNT(DISTINCT video_id)            AS video_count,
    ROUND(AVG(engagement_rate), 5)      AS avg_er,
    ROUND(AVG(view_reach_ratio), 4)     AS avg_reach_ratio,
    ROUND(AVG(cost_per_engagement), 4)  AS avg_cpe,
    ROUND(SUM(modeled_spend_usd), 2)    AS total_spend,
    SUM(view_count)                     AS total_views,

    -- Efficiency: views per dollar
    CASE
        WHEN SUM(modeled_spend_usd) > 0
        THEN ROUND(SUM(view_count) / SUM(modeled_spend_usd), 2)
        ELSE NULL
    END AS views_per_dollar

FROM analytics
GROUP BY platform, tier
ORDER BY platform,
    CASE tier WHEN 'Mega' THEN 1 WHEN 'Macro' THEN 2 WHEN 'Mid' THEN 3 
              WHEN 'Micro' THEN 4 WHEN 'Nano' THEN 5 END;


-- ─────────────────────────────────────────────────────────────
-- 7. INCREMENTAL LIFT PROXY
--    Pre/post comparison using campaign week buckets
--    "Pre-campaign" = videos published before Jan 15 (ramp-up period)
--    "Mid-campaign" = Jan 15 – Feb 28
--    "Late-campaign" = Mar 1 – Mar 31 (consideration phase)
-- ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_incrementality_proxy AS
SELECT
    platform,
    CASE
        WHEN published_date < '2025-01-15' THEN '1_Pre-Campaign'
        WHEN published_date < '2025-03-01' THEN '2_Mid-Campaign'
        ELSE '3_Late-Campaign'
    END AS campaign_phase,
    COUNT(DISTINCT video_id)            AS video_count,
    ROUND(AVG(engagement_rate), 5)      AS avg_er,
    ROUND(AVG(view_reach_ratio), 4)     AS avg_reach_ratio,
    SUM(view_count)                     AS total_views
FROM analytics
GROUP BY platform, campaign_phase
ORDER BY platform, campaign_phase;


-- ─────────────────────────────────────────────────────────────
-- 8. ALERT FLAGS
--    Creators to watch / act on
-- ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_alerts AS
WITH creator_trend AS (
    SELECT
        creator_handle,
        platform,
        period_month,
        AVG(engagement_rate) AS period_er,
        LAG(AVG(engagement_rate)) OVER (
            PARTITION BY creator_handle, platform 
            ORDER BY period_month
        ) AS prev_period_er
    FROM analytics
    GROUP BY creator_handle, platform, period_month
)
SELECT
    ct.creator_handle,
    ct.platform,
    ct.period_month,
    ROUND(ct.period_er, 5)      AS current_er,
    ROUND(ct.prev_period_er, 5) AS prior_er,
    ROUND(
        100.0 * (ct.period_er - ct.prev_period_er) / NULLIF(ct.prev_period_er, 0),
        1
    ) AS er_pct_change,
    CASE
        WHEN ct.period_er < ct.prev_period_er * 0.80 THEN '🔴 Declining ER (>20% drop)'
        WHEN ct.period_er < ct.prev_period_er * 0.90 THEN '🟡 Slight ER Decline'
        ELSE '🟢 Stable'
    END AS alert_status
FROM creator_trend ct
WHERE ct.prev_period_er IS NOT NULL
ORDER BY er_pct_change ASC;
