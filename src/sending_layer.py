import datetime
import re
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
import pandas as pd
from config import SENDER_EMAIL, SENDER_PASSWORD, SMTP_PORT, SMTP_SERVER

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
LOG_FILE = DATA_DIR / "outreach_log.csv"
LOG_COLUMNS = ["Influencer Name", "Email", "Platform", "Message Generated", "Sent Status", "Date Sent", "Log Details"]
EMAIL_RE = re.compile(r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$", re.I)


def init_outreach_log():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size:
        try:
            df = pd.read_csv(LOG_FILE).fillna("")
            for col in LOG_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[LOG_COLUMNS]
        except Exception:
            pass
    df = pd.DataFrame(columns=LOG_COLUMNS)
    df.to_csv(LOG_FILE, index=False)
    return df


def send_outreach_email(recipient_email: str, subject: str, body: str) -> tuple[bool, str]:
    # Safe by default: no configured credentials means simulation, not a fake SENT status.
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return False, "SIMULATED_ONLY: SMTP credentials are not configured; no email was sent."
    if not EMAIL_RE.match(str(recipient_email).strip()):
        return False, "FAILED: invalid email address format."
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=25) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True, "SMTP_ACCEPTED: email submitted to SMTP server; delivery is not guaranteed."
    except Exception as exc:
        return False, f"FAILED: {exc}"


def run_outreach_pipeline():
    enriched_file = DATA_DIR / "enriched_influencers.csv"
    if not enriched_file.exists():
        raise FileNotFoundError("Run discovery, filtering, and personalization first.")
    df = pd.read_csv(enriched_file).fillna("")
    log = init_outreach_log()
    already_contacted = {str(x).strip().lower() for x in log["Email"] if EMAIL_RE.match(str(x).strip())}
    new_rows = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for _, row in df.iterrows():
        if str(row.get("Filter Status", "")) != "PASSED":
            continue
        email = str(row.get("Contact Email", "")).strip()
        name = str(row.get("Name", "Unknown"))
        email_message = str(row.get("Generated Email Pitch", "")).strip()
        dm_message = str(row.get("Generated Instagram DM", "")).strip()
        if not EMAIL_RE.match(email):
            continue
        if email.lower() in already_contacted:
            continue
        success, details = send_outreach_email(email, "Paid Brand Collaboration Opportunity", email_message)
        status = "SMTP_ACCEPTED" if success else ("SIMULATED" if details.startswith("SIMULATED_ONLY") else "FAILED")
        new_rows.append({"Influencer Name": name, "Email": email, "Platform": row.get("Platform", ""), "Message Generated": email_message, "Sent Status": status, "Date Sent": now, "Log Details": details})
        new_rows.append({"Influencer Name": name, "Email": "N/A (Instagram DM)", "Platform": "Instagram DM (Manual Queue)", "Message Generated": dm_message, "Sent Status": "MANUAL_REVIEW", "Date Sent": now, "Log Details": "Manual review only; no Instagram DM was sent."})
        already_contacted.add(email.lower())
    if new_rows:
        updated = pd.concat([log, pd.DataFrame(new_rows)], ignore_index=True)
        updated.to_csv(LOG_FILE, index=False)
    return pd.DataFrame(new_rows, columns=LOG_COLUMNS)


if __name__ == "__main__":
    result = run_outreach_pipeline()
    print(f"Added {len(result)} outreach log rows. Check Sent Status and Log Details; simulated records were not sent.")
