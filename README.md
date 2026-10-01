Markdown
# Automated Micro-Influencer Outreach System

An AI-powered end-to-end pipeline designed to discover, filter, enrich, and personalize collaboration outreach for micro-influencers.

---

## 🛠️ Technology Stack & Tools Used
- **Language**: Python 3.10+
- **Environment Management**: Python `venv`
- **Data Processing**: Pandas, JSON
- **AI/LLM Engine**: Google Gemini API (`gemini-2.5-flash`) for dynamic message generation
- **Sending Layer**: Python `smtplib` + MIME for email dispatch & simulated IG DM queue
- **Storage**: CSV / Structured JSON logs

---

## 🏗️ System Architecture & Workflow

1. **Discovery (`src/discovery.py`)**: Fetches / generates 50 influencer records across social platforms (Instagram, YouTube, TikTok). Saved to `data/raw_influencers.json`.
2. **Filtering & Enrichment (`src/filter_enrich.py`)**:
   - Evaluates candidates based on Niche (`Fashion & Beauty`), Follower Count (5,000–100,000), and Engagement Rate (>= 2.0%).
   - Explicitly records pass/fail rationale.
   - Enriches records with content themes and marks missing emails as `"Not Found"` (without guessing or generating fake data).
   - Saved to `data/enriched_influencers.csv`.
3. **AI Personalization (`src/personalization.py`)**:
   - Generates a **60–90 word Email Pitch** referencing content context and campaign offer.
   - Generates a **15–30 word Instagram DM** that is short, natural, and customized.
4. **Sending & Tracking Layer (`src/sending_layer.py`)**:
   - Filters out candidates marked `"Not Found"` or failed.
   - Prevents duplicate outreach using historical tracking.
   - Sends emails via SMTP or runs in simulation mode if credentials are omitted.
   - Queues Instagram DMs in compliance with Meta API restrictions.
   - Maintained in `data/outreach_log.csv`.

---

## 🚀 Complete Step-by-Step Execution Guide

Follow these exact steps from your terminal inside the root project directory (`influencer_outreach_system/`).

### Step 1: Create & Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
On Windows (Command Prompt):

DOS
python -m venv venv
.\venv\Scripts\activate.bat
On macOS / Linux:

Bash
python3 -m venv venv
source venv/bin/activate
Step 2: Install Dependencies
With the virtual environment activated, install all required Python packages:

Bash
pip install -r requirements.txt
Step 3: Configure Environment Variables
Create a file named .env in the root folder of the project:

Code snippet
GEMINI_API_KEY="your_actual_gemini_api_key_here"
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SENDER_EMAIL="your_email@gmail.com"
SENDER_PASSWORD="your_app_password"
Note: If GEMINI_API_KEY or SMTP credentials are omitted, the system gracefully defaults to simulation and template fallback modes so you can test the pipeline safely.

Step 4: Run the Pipeline Step-by-Step
Run each module sequentially from the root directory:

1. Generate / Fetch Raw Discovery Data
Bash
python src/discovery.py
Output: Successfully generated 50 influencer records.

Generated File: data/raw_influencers.json

2. Execute Filtering & Profile Enrichment
Bash
python src/filter_enrich.py
Output: Processed 50 records. Saved to data/enriched_influencers.csv

Generated File: data/enriched_influencers.csv

3. Generate Personalized AI Messages
Bash
python src/personalization.py
Output: Personalized messages successfully generated.

Updated File: data/enriched_influencers.csv (Populates Generated Email Pitch and Generated Instagram DM columns)

4. Execute Sending Layer & Log Outreach
Bash
python src/sending_layer.py
Output: Outreach complete. Processed X campaign tasks.

Generated File: data/outreach_log.csv

5. Verify Deduplication
Re-run the sending layer script to verify that duplicate emails are automatically skipped:

Bash
python src/sending_layer.py
Output: Skipping [Name] ([Email]): Already in outreach log. followed by No new influencers to process.

📊 Dataset & Log Outputs
data/raw_influencers.json: Raw dataset containing 50 initial influencer records.

data/enriched_influencers.csv: Complete structured dataset containing follower counts, engagement rates, pass/fail status, filter rationale, enriched contact details, and generated outreach messages.

data/outreach_log.csv: Log tracking email delivery statuses, timestamping, details, and queued Instagram DM tasks.

📌 Limitations & Production Scaling
Instagram API Restrictions: Meta Graph API prohibits programmatic cold DM dispatch to personal accounts. The system queues these as operator tasks in outreach_log.csv to ensure compliance.

Scaling to 500+ Creators: The system's modular architecture allows replacing src/discovery.py with an automated web scraper (e.g., Apify actors or YouTube Data API) and replacing CSV storage with a PostgreSQL or MongoDB database.