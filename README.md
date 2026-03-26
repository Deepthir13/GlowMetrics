# GlowMetric Q1 2025 : Creator Campaign Measurement Workspace
### HardScope Lead Analyst Challenge Submission

**Brand:** GlowMetric (fictional DTC skincare brand)  
**Platforms:** YouTube + TikTok  
**Creators:** 10 beauty/skincare creators  
**Campaign Period:** Q1 2025 (Jan–Mar)  
**Submitted by:** Deepth Ramesh

**Summary PDF:** https://github.com/Deepthir13/GlowMetrics/blob/main/GlowMetric_Challenge_Summary.pdf

**Metrics PDF:** https://github.com/Deepthir13/GlowMetrics/blob/main/03_framework/GlowMetric_Measurement_Framework.pdf


**Executive readout:** https://github.com/Deepthir13/GlowMetrics/blob/main/GlowMetric_Executive_Readout.pdf

---
 
## What This Is
 
A complete creator campaign measurement workspace built for a fictional GlowMetric SPF serum launch. It pulls real YouTube data via API, generates benchmark-grounded TikTok data, normalizes both into a unified analytics schema, runs SQL feature engineering, and delivers a 3-page Power BI dashboard with an executive QBR readout.
 
**Headline finding:** TikTok Nano/Micro creators delivered 14%+ engagement rates at $0.01 CPE — 22.6× more cost-efficient than YouTube ($0.55 CPE). The data makes a clear case for reallocating $130K from underperforming YouTube creators to TikTok Nano/Micro for Q2.
 
---
 
## How to Run Everything Locally
 
### Prerequisites
 
**Mac / Linux**
```bash
pip3 install pandas numpy google-api-python-client
```
 
**Windows**
```bash
pip install pandas numpy google-api-python-client
```
 
---
 
### Step 1 — Get your YouTube Data API v3 key
 
1. Go to [console.cloud.google.com](https://console.cloud.google.com) and sign in
2. Click **Select a project → New Project** → name it anything → Create
3. Go to **APIs & Services → Library**
4. Search **YouTube Data API v3** → click it → click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **+ Create Credentials → API Key**
7. Copy the key shown
 
Open `01_data_pull/youtube_pull_v2.py` and paste your key on line 10:
 
```python
API_KEY = "PASTE_YOUR_KEY_HERE"
```
 
---
 
### Step 2 — Pull data
 
**Mac / Linux**
```bash
python3 01_data_pull/youtube_pull_v2.py
python3 01_data_pull/tiktok_synthetic.py
```
 
**Windows**
```bash
python 01_data_pull/youtube_pull_v2.py
python 01_data_pull/tiktok_synthetic.py
```
 
**Expected output:**
```
✅ Saved 138 records → data/raw/youtube_raw_[timestamp].csv
✅ Generated 150 TikTok records → data/raw/tiktok_synthetic_[timestamp].csv
```
 
---
 
### Step 3 — Build the analytics table
 
**Mac / Linux**
```bash
python3 02_modeling/data_model.py
```
 
**Windows**
```bash
python 02_modeling/data_model.py
```
 
**Expected output:**
```
✅ Analytics table:   288 rows × 26 cols  → data/clean/glowmetric_analytics_table.csv
✅ Creator scorecard: 20 rows             → data/clean/creator_scorecard.csv
✅ Platform summary:  36 rows             → data/clean/platform_summary.csv
 
🏆 Creator Scorecard (ranked by performance score):
  creator_handle  platform  tier   avg_er  performance_score  recommendation
       HouseOfCB    TikTok  Nano  0.14175              123.1           Scale
    LisaHeldmann    TikTok  Nano  0.14506              121.1           Scale
         ...
```
 
---
 
### Step 4 — Run SQL feature engineering
 
**Mac / Linux**
```bash
python3 04_sql/run_sql.py
```
 
**Windows**
```bash
python 04_sql/run_sql.py
```
 
**Expected output:**
```
✅ vw_creator_video_metrics: 288 rows → data/powerbi/vw_creator_video_metrics.csv
✅ vw_creator_scorecard:      20 rows → data/powerbi/vw_creator_scorecard.csv
✅ vw_funnel_stage:            5 rows → data/powerbi/vw_funnel_stage.csv
✅ vw_platform_trend:         36 rows → data/powerbi/vw_platform_trend.csv
✅ vw_format_performance:     13 rows → data/powerbi/vw_format_performance.csv
✅ vw_tier_analysis:          10 rows → data/powerbi/vw_tier_analysis.csv
✅ vw_incrementality_proxy:    6 rows → data/powerbi/vw_incrementality_proxy.csv
✅ vw_alerts:                 72 rows → data/powerbi/vw_alerts.csv
```
 
---
 
### Step 5 — Open Power BI dashboard
 
1. Open `05_powerbi/GlowMetric_Dashboard.pbix` in Power BI Desktop
2. When prompted about data source errors, click **Transform Data → Data Source Settings**
3. Update each file path to point to your local `data/powerbi/` folder
4. Click **Close & Apply** — all visuals will populate
 
---
 
### Step 6 — Read the executive readout
 
The executive readout lives at `GlowMetric_Executive_Readout.pdf` or scroll up and click on the link

 
---
 
### Step 7 — Review the measurement framework
 
The full measurement framework document is at `GlowMetric_Measurement_Framework.pdf`or scroll up and click on the link
 
It defines the three-tier funnel (Awareness → Engagement → Consideration), all metric definitions, YouTube and TikTok benchmarks sourced from industry reports, cost efficiency thresholds, creator tier framework, incrementality logic, alerting rules, and known measurement gaps. It is designed as a reusable playbook — swap the brand name and update the benchmarks to deploy it for a different client in under 2 hours.
 
---
 
## Project Structure
 
```
hardscope/
├── README.md
├── .gitignore
├── 01_data_pull/
│   ├── youtube_pull_v2.py          # YouTube Data API v3 — 10 creators, 15 videos each
│   └── tiktok_synthetic.py         # Benchmark-grounded TikTok dataset generator
├── 02_modeling/
│   └── data_model.py               # Clean, normalize, join → unified analytics table
├── 03_framework/
│   └── GlowMetric_Measurement_Framework.pdf
├── 04_sql/
│   ├── feature_engineering.sql     # 8 SQL views
│   └── run_sql.py                  # Execute SQL via SQLite, export Power BI CSVs
├── 05_powerbi/
│   └── GlowMetric_Dashboard.pbix
├── 06_readout/
│   └── generate_readout_numbers.py        # generates readout numbers
├── screenshots/
│   ├── page1_overview.png
│   ├── page2_scorecard.png
│   └── page3_funnel.png
└── data/
    ├── raw/                        # API outputs + synthetic data (.gitignored)
    ├── clean/                      # Normalized analytics tables (.gitignored)
    └── powerbi/                    # Power BI-ready CSVs (.gitignored)
```
 
---
 
## Data Sources
 
### YouTube — Real Data
 
- **Source:** YouTube Data API v3 (Google Cloud)
- **Why:** Free, no approval required, returns real channel + video metrics
- **What we pull:** Subscriber count, view count, likes, comments, video duration, tags for 10 beauty/skincare creators (15 most recent videos each)
- **API quota used:** ~600 units of the 10,000/day free limit
- **Limitations:**
  - No audience demographic breakdown — requires Creator Studio access or third-party tool
  - No click or conversion data — not exposed by the platform API
  - Watch time is approximated via Watch Time Index proxy (duration × ER), not actual minutes watched
 
### TikTok — Benchmark-Grounded Synthetic Data
 
- **Why synthetic:** TikTok Research API requires formal application and 4–6 week approval. Using it without approval violates TOS.
- **Why not skip TikTok:** TikTok is the dominant platform for beauty creator content. Excluding it would make the measurement framework incomplete and the recommendations unrealistic.
- **Benchmark sources used:**
  - Influencer Marketing Hub: TikTok Engagement Benchmarks 2024
  - CreatorIQ: Beauty Category Creator Report 2024
  - Social Insider: TikTok Benchmark Report Q4 2024
- **How it's modeled:** ER by creator tier, view/follower ratio, watch-through rate, share rate — all with realistic variance using log-normal noise seeded for reproducibility
- **Clearly labeled** throughout all outputs and the dashboard
 
---
 
## Measurement Framework & Key Assumptions
 
### Three-tier funnel
 
| Tier | Key Metrics | Lift Definition |
|---|---|---|
| **Awareness** | Views, VSR, VFR | VSR >15% (YT) or VFR >50% (TT) = algorithmic amplification signal |
| **Engagement** | ER%, WTR, Watch Time Index | ER above benchmark + product-specific comment signal |
| **Consideration** | Search interest, Share rate, Profile visits | +15% branded search lift during campaign window |
 
### Benchmarks used
 
| Platform | Strong ER | Average ER | Good Reach Ratio |
|---|---|---|---|
| YouTube (beauty) | ≥ 3.0% | 1.0%–3.0% | VSR ≥ 15% |
| TikTok (beauty) | ≥ 6.0% | 4.0%–6.0% | VFR ≥ 50% |
 
*Source: CreatorIQ 2024, Social Insider Q4 2024, Influencer Marketing Hub 2024*
 
### Key assumptions
 
1. **Spend is modeled** from public creator rate card benchmarks. Actual contracted rates would replace these.
2. **Engagement rate formula:** (Likes + Comments) ÷ Followers/Subscribers. Shares included in TikTok total_engagements but not ER numerator — preserves cross-platform comparability.
3. **Watch Time Index** is a proxy engineered from duration and ER — not platform-reported watch minutes.
4. **Incrementality** is estimated via pre/post phase comparison — not a controlled holdout experiment.
5. **No cross-platform audience de-duplication** — views are treated as additive across platforms.
 
---
### Power BI Dashboards
![Page1](https://github.com/user-attachments/assets/ffb65f81-1f81-4d18-91d2-83dc950b0c06)
![Page2](https://github.com/user-attachments/assets/f1749c53-67d4-4f7c-99ab-59982b87ff59)
![Page3](https://github.com/user-attachments/assets/f8c7bc0d-ffae-40a4-849d-6b6f93e55a06)

---
## Architecture & Analysis Decisions
 
| Decision | Why | Tradeoff |
|---|---|---|
| **YouTube Data API v3 for real data** | Free, no approval, real metrics | No demographic or conversion data available |
| **Benchmark-grounded synthetic TikTok** | TikTok API requires 4–6 week approval | Not real data — clearly labeled; replace when API approved |
| **SQLite for SQL layer** | Zero setup, runs locally, same syntax as BigQuery/Snowflake | Not scalable past ~10M rows; production would use BigQuery |
| **Pandas for normalization** | Matches resume stack, readable, fast for this volume | Spark/Databricks for production at 100M+ row scale |
| **Modeled creator spend** | Enables CPE/CPV analysis without actual media plan | Directional only; replace with contracted rates in production |
| **Power BI for dashboard** | Strongest tool in stack; best for stakeholder sharing | Requires license; Looker Studio is a free-share alternative |
| **One row per video schema** | Enables video-level, creator-level, and program-level aggregation from one table | Slightly denormalized but maximizes Power BI flexibility |
 
---
 
## What I'd Do With Another Week
 
1. **Build an agentic scraper for TikTok**: instead of waiting months for API approval, use an AI agent with browser automation to scrape public TikTok profile pages (views, likes, comments, captions) for the specific creators in the program. Scrape on a schedule, parse with an LLM for caption themes and product mentions, and feed it into the same pipeline. Faster than any API and richer than raw metrics alone.
 
2. **Stitch YouTube and TikTok posting schedules together**: right now the two platforms are analyzed independently. A creator who posts a YouTube tutorial on Monday and a TikTok GRWM on Wednesday about the same product might be driving compounding lift. Cross-platform sequencing analysis: does a YouTube post followed by TikTok within 7 days lift engagement on both? is something I'd want to model.
 
3. **Wire in Google Trends as a live consideration signal**: pull branded search volume for "GlowMetric serum" weekly using the pytrends library, overlay it with creator posting dates, and build a simple lag-correlation model. Not a causal claim, but a directional signal that tells you whether the content is moving brand interest or just platform metrics.

4. **Incrementality holdout**: Randomly pause 2 creators for 4 weeks in Q2. Compare branded search volume vs. active creators to estimate true incremental lift.

5. **Audience demographic validation**: Run top 5 Scale creators through CreatorIQ or StatSocial API to confirm 18–34 beauty buyer alignment before increasing budgets.

6. **Productionize the pipeline**: Apache Airflow DAG with weekly scheduled refresh, Slack alerting when any creator's ER drops >20%, and a parameterized playbook template deployable for a new brand in under 2 hours.

 
---
 
## Tools Used
 
| Tool | Purpose |
|---|---|
| Python (pandas, numpy) | Data pull, cleaning, normalization, feature engineering |
| YouTube Data API v3 | Real video + channel metrics |
| SQLite | SQL feature engineering layer |
| Power BI (DAX, Power Query) | Dashboard + scorecard |
| Markdown | Framework documentation + executive readout |
| GitHub | Version control + submission |
 
---
