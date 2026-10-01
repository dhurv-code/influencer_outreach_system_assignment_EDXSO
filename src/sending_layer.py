import os
import sys
import datetime
import smtplib
from email.mime.text import MIMEText
import pandas as pd

# Add project root directory to Python path FIRST
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import SENDER_EMAIL, SENDER_PASSWORD, SMTP_PORT, SMTP_SERVER

LOG_FILE = "data/outreach_log.csv"

def init_outreach_log():
    # Ensure data folder exists
    os.makedirs("data", exist_ok=True)
    
    # Check if file doesn't exist OR is empty (size == 0)
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        df_log = pd.DataFrame(columns=[
            "Influencer Name", "Email", "Platform", 
            "Message Generated", "Sent Status", "Date Sent", "Log Details"
        ])
        df_log.to_csv(LOG_FILE, index=False)
        return df_log
    
    try:
        df_log = pd.read_csv(LOG_FILE)
        return df_log
    except Exception as e:
        print(f"Warning: Could not parse log file ({e}). Re-initializing log.")
        df_log = pd.DataFrame(columns=[
            "Influencer Name", "Email", "Platform", 
            "Message Generated", "Sent Status", "Date Sent", "Log Details"
        ])
        df_log.to_csv(LOG_FILE, index=False)
        return df_log

def send_outreach_email(recipient_email: str, subject: str, body: str) -> tuple[bool, str]:
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        # Simulation Mode
        return True, "SIMULATED_SUCCESS: Credentials not configured"
        
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True, "SENT_SUCCESS"
    except Exception as e:
        return False, f"FAILED: {str(e)}"

def run_outreach_pipeline():
    enriched_file = "data/enriched_influencers.csv"
    if not os.path.exists(enriched_file):
        raise FileNotFoundError("data/enriched_influencers.csv not found. Please run personalization.py first!")

    df_influencers = pd.read_csv(enriched_file)
    df_log = init_outreach_log()
    
    already_contacted = set(df_log["Email"].dropna().tolist())
    
    new_logs = []

    for idx, row in df_influencers.iterrows():
        # Condition 1: Must pass filter
        if row["Filter Status"] != "PASSED":
            continue
            
        email = str(row["Contact Email"]).strip()
        name = row["Name"]
        email_msg = row.get("Generated Email Pitch", "")
        ig_dm = row.get("Generated Instagram DM", "")
        
        # Condition 2: Valid email check
        if email in ["Not Found", "nan", "", "None"]:
            print(f"Skipping {name}: No valid contact email.")
            continue
            
        # Condition 3: Prevent duplicate outreach
        if email in already_contacted:
            print(f"Skipping {name} ({email}): Already in outreach log.")
            continue
            
        # Send or Simulate Email
        subject = "Paid Brand Collaboration Opportunity"
        success, details = send_outreach_email(email, subject, email_msg)
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SENT" if success else "FAILED"
        
        # Record Email Log
        new_logs.append({
            "Influencer Name": name,
            "Email": email,
            "Platform": row["Platform"],
            "Message Generated": email_msg,
            "Sent Status": status,
            "Date Sent": now_str,
            "Log Details": details
        })
        
        # Simulated Instagram DM Workflow (Respecting Meta API Restrictions)
        new_logs.append({
            "Influencer Name": name,
            "Email": "N/A (Instagram DM)",
            "Platform": "Instagram DM (Simulated)",
            "Message Generated": ig_dm,
            "Sent Status": "SIMULATED_QUEUE",
            "Date Sent": now_str,
            "Log Details": "Manual IG outreach task queued for operator compliance."
        })
        
        already_contacted.add(email)

    if new_logs:
        df_new = pd.DataFrame(new_logs)
        df_updated_log = pd.concat([df_log, df_new], ignore_index=True)
        df_updated_log.to_csv(LOG_FILE, index=False)
        print(f"Outreach complete. Processed {len(new_logs)} campaign tasks.")
    else:
        print("No new influencers to process.")

if __name__ == "__main__":
    run_outreach_pipeline()