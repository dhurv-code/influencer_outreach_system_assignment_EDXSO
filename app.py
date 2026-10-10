from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
# Existing modules use project-relative data paths. Keep those paths stable on local and cloud runs.
import os
os.chdir(ROOT)
DATA_DIR = ROOT / "data"
RAW_FILE = DATA_DIR / "raw_influencers.json"
ENRICHED_FILE = DATA_DIR / "enriched_influencers.csv"
LOG_FILE = DATA_DIR / "outreach_log.csv"

# Existing project modules are reused; no second backend is introduced.
from src.discovery import generate_mock_influencers
from src.filter_enrich import process_and_enrich
from src.personalization import run_personalization

st.set_page_config(
    page_title="Micro-Influencer Outreach",
    page_icon="",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {background: #f6f8fb; padding: 14px; border-radius: 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_enriched() -> pd.DataFrame:
    if ENRICHED_FILE.exists():
        try:
            return pd.read_csv(ENRICHED_FILE).fillna("")
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def read_log() -> pd.DataFrame:
    columns = ["Influencer Name", "Email", "Platform", "Message Generated", "Sent Status", "Date Sent", "Log Details"]
    if LOG_FILE.exists():
        try:
            df = pd.read_csv(LOG_FILE).fillna("")
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            return df[columns]
        except Exception:
            pass
    return pd.DataFrame(columns=columns)


def generate_sample_dataset(count: int = 50):
    """Generate clearly-labelled synthetic data for testing only."""
    ensure_data_dir()
    records = generate_mock_influencers(count)
    with RAW_FILE.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    process_and_enrich(str(RAW_FILE))


def simulate_outreach(df: pd.DataFrame) -> tuple[int, int]:
    """Record a demo only. This function never sends real email or DMs."""
    ensure_data_dir()
    log_df = read_log()
    contacted = {
        str(value).strip().lower()
        for value in log_df.get("Email", pd.Series(dtype=str)).tolist()
        if str(value).strip() and str(value).strip().lower() not in {"n/a (instagram dm)", "nan", "none"}
    }
    new_rows = []
    skipped = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, row in df.iterrows():
        if str(row.get("Filter Status", "")) != "PASSED":
            continue
        email = str(row.get("Contact Email", "")).strip()
        name = str(row.get("Name", "Unknown"))
        email_message = str(row.get("Generated Email Pitch", "")).strip()
        dm_message = str(row.get("Generated Instagram DM", "")).strip()
        if not email or email.lower() in {"not found", "nan", "none"}:
            skipped += 1
            continue
        if email.lower() in contacted:
            skipped += 1
            continue

        new_rows.append({
            "Influencer Name": name,
            "Email": email,
            "Platform": str(row.get("Platform", "")),
            "Message Generated": email_message,
            "Sent Status": "SIMULATED",
            "Date Sent": now,
            "Log Details": "Demo mode only. No email was sent.",
        })
        # Instagram outreach is queued for manual review; it is not sent automatically.
        new_rows.append({
            "Influencer Name": name,
            "Email": "N/A (Instagram DM)",
            "Platform": "Instagram DM (Manual Queue)",
            "Message Generated": dm_message,
            "Sent Status": "MANUAL_REVIEW",
            "Date Sent": now,
            "Log Details": "Draft queued for manual review. No DM was sent.",
        })
        contacted.add(email.lower())

    if new_rows:
        updated = pd.concat([log_df, pd.DataFrame(new_rows)], ignore_index=True)
        updated.to_csv(LOG_FILE, index=False)
    return len(new_rows), skipped


st.title("🎯 Micro-Influencer Outreach System")
st.caption("Discover sample profiles, apply filtering, generate outreach drafts, and track simulated outreach.")
st.warning(
    "Demo-data notice: the current discovery module creates synthetic sample profiles. "
    "Names, emails, URLs, and metrics are not verified real influencers. Use this mode to test the workflow only."
)

with st.sidebar:
    st.header("Workflow")
    st.write("Run each stage in order. Your existing Python modules and CSV files are reused.")
    if st.button("1 · Generate 50 sample profiles", use_container_width=True, type="primary"):
        try:
            generate_sample_dataset(50)
            st.session_state["notice"] = "Generated 50 synthetic sample profiles and applied filtering."
            st.rerun()
        except Exception as exc:
            st.error(f"Discovery/filtering failed: {exc}")

    if st.button("2 · Generate personalized messages", use_container_width=True):
        try:
            if not ENRICHED_FILE.exists():
                st.error("Generate the sample profiles first.")
            else:
                run_personalization()
                st.session_state["notice"] = "Message generation completed. Check the Messages tab."
                st.rerun()
        except Exception as exc:
            st.error(f"Personalization failed: {exc}")

    if st.button("3 · Simulate outreach", use_container_width=True):
        try:
            df_now = read_enriched()
            if df_now.empty:
                st.error("Generate profiles first.")
            else:
                count, skipped = simulate_outreach(df_now)
                st.session_state["notice"] = f"Simulation recorded {count} log rows; skipped {skipped} missing/duplicate email records. No messages were sent."
                st.rerun()
        except Exception as exc:
            st.error(f"Outreach simulation failed: {exc}")

    st.divider()
    st.caption("Email and Instagram sending are disabled in this dashboard. It is safe to demo without sending real messages.")

if st.session_state.get("notice"):
    st.success(st.session_state.pop("notice"))

df = read_enriched()
log_df = read_log()

if df.empty:
    st.info("Start with **1 · Generate 50 sample profiles** in the sidebar. This creates test data and runs the filtering stage.")
    st.stop()

passed_count = int((df.get("Filter Status", pd.Series(dtype=str)) == "PASSED").sum())
failed_count = int((df.get("Filter Status", pd.Series(dtype=str)) == "FAILED").sum())
email_count = int((df.get("Contact Email", pd.Series(dtype=str)).astype(str).str.strip().str.lower().isin(["", "not found", "none", "nan"]) == False).sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Profiles in dataset", len(df))
m2.metric("Passed filters", passed_count)
m3.metric("Failed filters", failed_count)
m4.metric("Profiles with email field", email_count)

tab_overview, tab_profiles, tab_messages, tab_log = st.tabs(["Overview", "Influencer Profiles", "Personalized Messages", "Outreach Tracker"])

with tab_overview:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Filter results")
        summary = pd.DataFrame({"Result": ["Passed", "Failed"], "Count": [passed_count, failed_count]})
        st.bar_chart(summary.set_index("Result"))
    with right:
        st.subheader("Current filtering rules")
        st.markdown("- **Niche:** Fashion & Beauty\n- **Followers:** 5,000–100,000\n- **Engagement rate:** at least 2%")
        st.caption("These are rules from config.py. The dataset is synthetic until a verified discovery source is integrated.")
    st.subheader("Recent profiles")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)

with tab_profiles:
    st.subheader("Filter and inspect profiles")
    status_options = ["All"] + sorted([str(x) for x in df.get("Filter Status", pd.Series(dtype=str)).unique() if str(x)])
    chosen_status = st.selectbox("Filter status", status_options)
    search_text = st.text_input("Search name, niche, or platform")
    view = df.copy()
    if chosen_status != "All":
        view = view[view["Filter Status"].astype(str) == chosen_status]
    if search_text.strip():
        mask = pd.Series(False, index=view.index)
        for col in ["Name", "Category / Niche", "Platform"]:
            if col in view.columns:
                mask |= view[col].astype(str).str.contains(search_text, case=False, na=False)
        view = view[mask]
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button("Download profiles CSV", data=view.to_csv(index=False).encode("utf-8"), file_name="influencer_profiles.csv", mime="text/csv")

with tab_messages:
    st.subheader("Generated outreach drafts")
    if "Generated Email Pitch" not in df.columns:
        st.info("Click **2 · Generate personalized messages** in the sidebar.")
    else:
        qualified = df[df.get("Filter Status", "") == "PASSED"].copy()
        if qualified.empty:
            st.info("No profiles passed the current filters. Generate a new sample dataset to test again.")
        else:
            names = qualified["Name"].astype(str).tolist()
            selected_name = st.selectbox("Choose a qualified profile", names)
            selected = qualified[qualified["Name"].astype(str) == selected_name].iloc[0]
            st.markdown(f"**{selected.get('Name', '')}** · {selected.get('Platform', '')} · {selected.get('Category / Niche', '')}")
            st.text_input("Contact email", value=str(selected.get("Contact Email", "")), disabled=True)
            st.markdown("**Email pitch**")
            st.text_area("Email draft", value=str(selected.get("Generated Email Pitch", "")), height=180, key="email_preview")
            st.markdown("**Instagram DM (manual draft)**")
            st.text_area("Instagram DM draft", value=str(selected.get("Generated Instagram DM", "")), height=100, key="dm_preview")
            st.caption("Review all details before use. Sample data and fallback messages are not evidence of real influencer activity.")

with tab_log:
    st.subheader("Outreach tracker")
    if log_df.empty:
        st.info("No outreach records yet. Use **3 · Simulate outreach** to create a demo log. This will not send emails or DMs.")
    else:
        st.dataframe(log_df.sort_values("Date Sent", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("Download outreach log CSV", data=log_df.to_csv(index=False).encode("utf-8"), file_name="outreach_log.csv", mime="text/csv")
