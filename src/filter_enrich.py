import json
from pathlib import Path
import re
import pandas as pd
from config import FILTER_CRITERIA

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def evaluate_influencer(record: dict) -> tuple[bool, str]:
    reasons = []
    niche = str(record.get("category_niche", "")).strip()
    if niche.casefold() != FILTER_CRITERIA["target_niche"].casefold():
        reasons.append(f"Niche mismatch: '{niche or 'Unknown'}' is not '{FILTER_CRITERIA['target_niche']}'")
    try:
        followers = int(record.get("follower_count") or 0)
    except (TypeError, ValueError):
        followers = 0
    if not (FILTER_CRITERIA["min_followers"] <= followers <= FILTER_CRITERIA["max_followers"]):
        reasons.append(f"Followers ({followers}) outside {FILTER_CRITERIA['min_followers']}-{FILTER_CRITERIA['max_followers']}")
    try:
        engagement = float(record.get("engagement_rate") or 0)
    except (TypeError, ValueError):
        engagement = 0.0
    if engagement < FILTER_CRITERIA["min_engagement_rate"]:
        reasons.append(f"Engagement proxy ({engagement:.2f}%) below {FILTER_CRITERIA['min_engagement_rate']}% threshold")
    return (not reasons, "Passed all criteria" if not reasons else "Failed: " + "; ".join(reasons))


def infer_content_themes(text: str) -> str:
    text = str(text or "").lower()
    themes = []
    for keywords, label in [
        (("skincare", "skin care", "serum", "moisturizer", "beauty", "makeup"), "Skincare/Beauty"),
        (("outfit", "fashion", "style", "dress", "lookbook"), "Fashion/Style"),
        (("routine", "daily", "vlog", "day in my life"), "Routine/Vlog"),
        (("review", "unboxing", "testing", "product"), "Product Review"),
        (("fitness", "workout", "gym", "training"), "Fitness"),
        (("tech", "phone", "laptop", "software", "gadget"), "Technology"),
    ]:
        if any(word in text for word in keywords):
            themes.append(label)
    return ", ".join(themes) if themes else ("Based on available caption: " + str(text)[:100] if text else "Not Available")


def process_and_enrich(input_file=None):
    source = Path(input_file) if input_file else DATA_DIR / "raw_influencers.json"
    if not source.is_absolute():
        source = PROJECT_ROOT / source
    if not source.exists():
        raise FileNotFoundError(f"Input file not found: {source}. Run discovery first.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with source.open(encoding="utf-8") as f:
        influencers = json.load(f)
    processed = []
    for inf in influencers:
        passed, reason = evaluate_influencer(inf)
        email = str(inf.get("contact_email") or "").strip()
        if not email or email.lower() in {"none", "nan", "not found"}:
            email = "Not Found"
        # Do not infer demographics or invent missing information.
        content = str(inf.get("recent_post_caption") or "")
        processed.append({
            "Name": inf.get("name", "Unknown"),
            "Platform": inf.get("platform", "Unknown"),
            "Profile URL": inf.get("profile_url", ""),
            "Follower Count": int(inf.get("follower_count") or 0),
            "Engagement Rate (%)": float(inf.get("engagement_rate") or 0),
            "Category / Niche": inf.get("category_niche", "Unknown"),
            "Content Themes": infer_content_themes(content),
            "Contact Email": email,
            "Filter Status": "PASSED" if passed else "FAILED",
            "Filter Reason": reason,
            "Recent Content": content,
            "Data Source": inf.get("data_source", "Source not recorded"),
        })
    df = pd.DataFrame(processed)
    output = DATA_DIR / "enriched_influencers.csv"
    df.to_csv(output, index=False)
    return df


if __name__ == "__main__":
    df = process_and_enrich()
    print(f"Processed {len(df)} records. Saved to {DATA_DIR / 'enriched_influencers.csv'}")
