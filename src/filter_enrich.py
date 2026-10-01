import os
import sys
import json
import pandas as pd

# 1. Modify sys.path FIRST before importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import FILTER_CRITERIA

def evaluate_influencer(record: dict) -> tuple[bool, str]:
    """Applies classification logic and explains pass/fail reasons."""
    reasons = []
    
    # Niche Filter
    if record["category_niche"] != FILTER_CRITERIA["target_niche"]:
        reasons.append(f"Niche mismatch: '{record['category_niche']}' != '{FILTER_CRITERIA['target_niche']}'")
        
    # Follower Count Filter
    followers = record["follower_count"]
    if not (FILTER_CRITERIA["min_followers"] <= followers <= FILTER_CRITERIA["max_followers"]):
        reasons.append(f"Followers ({followers}) outside required range [{FILTER_CRITERIA['min_followers']}-{FILTER_CRITERIA['max_followers']}]")
        
    # Engagement Rate Filter
    engagement = record["engagement_rate"]
    if engagement < FILTER_CRITERIA["min_engagement_rate"]:
        reasons.append(f"Engagement rate ({engagement}%) below threshold ({FILTER_CRITERIA['min_engagement_rate']}%)")
        
    passed = len(reasons) == 0
    status_reason = "Passed all criteria" if passed else "Failed: " + "; ".join(reasons)
    return passed, status_reason

def process_and_enrich(input_file="data/raw_influencers.json"):
    # Ensure data folder exists
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found. Please run discovery script first!")

    with open(input_file, "r") as f:
        influencers = json.load(f)
        
    processed_records = []
    
    for inf in influencers:
        passed, reason = evaluate_influencer(inf)
        
        # Profile Enrichment & Strict Validation
        email = inf.get("contact_email")
        if not email or str(email).strip() == "" or str(email).lower() == "none":
            enriched_email = "Not Found"
        else:
            enriched_email = email.strip()

        enriched_record = {
            "Name": inf["name"],
            "Platform": inf["platform"],
            "Profile URL": inf["profile_url"],
            "Follower Count": inf["follower_count"],
            "Engagement Rate (%)": inf["engagement_rate"],
            "Category / Niche": inf["category_niche"],
            "Content Themes": "Skincare, Daily Vlogs, Organic Beauty",
            "Contact Email": enriched_email,
            "Filter Status": "PASSED" if passed else "FAILED",
            "Filter Reason": reason,
            "Recent Content": inf.get("recent_post_caption", "")
        }
        processed_records.append(enriched_record)
        
    df = pd.DataFrame(processed_records)
    output_path = "data/enriched_influencers.csv"
    df.to_csv(output_path, index=False)
    print(f"Processed {len(df)} records. Saved to {output_path}")
    return df

if __name__ == "__main__":
    process_and_enrich()