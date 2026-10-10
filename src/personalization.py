import json
import re
from pathlib import Path
import pandas as pd
from config import GEMINI_API_KEY

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", str(text or "")))


def _topic(recent_content: str) -> str:
    text = str(recent_content or "").strip().strip(".!\n")
    # Keep the personalization signal concise so required message word limits remain valid.
    words = text.split()[:6]
    return " ".join(words) if words else "your recent content"


def fallback_messages(name: str, niche: str, platform: str, recent_content: str) -> dict:
    topic = _topic(recent_content)
    email = (
        f"Hi {name}, I came across your {platform} content about {topic} and appreciated how you share "
        f"{niche} ideas with your audience. We are exploring a paid UGC collaboration for an upcoming campaign "
        "and think your content could be a relevant fit. The partnership would include a clear brief, agreed "
        "deliverables, and compensation discussed upfront. If you are interested, I would be happy to share the "
        "campaign details and answer your questions. Would you be open to a quick conversation?"
    )
    dm = f"Hi {name}, I saw your {platform} post about {topic}. Your {niche} content may suit our paid creator campaign. Open to details?"
    return {"email_pitch": email, "instagram_dm": dm}


def _valid_lengths(data: dict) -> bool:
    return 60 <= word_count(data.get("email_pitch", "")) <= 90 and 15 <= word_count(data.get("instagram_dm", "")) <= 30


def generate_personalized_messages(name: str, niche: str, platform: str, recent_content: str) -> dict:
    fallback = fallback_messages(name, niche, platform, recent_content)
    if not GEMINI_API_KEY:
        return fallback
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""Create two truthful personalized outreach drafts using only these supplied facts.
Name: {name}
Niche: {niche}
Platform: {platform}
Recent content title/caption: {recent_content}

Return only valid JSON with keys email_pitch and instagram_dm. Email must be 60-90 words; DM must be 15-30 words. Do not invent audience demographics, results, personal experience, or details not provided. Suggest a paid UGC collaboration and avoid exaggerated claims."""
        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        if _valid_lengths(result):
            return {"email_pitch": result["email_pitch"].strip(), "instagram_dm": result["instagram_dm"].strip()}
    except Exception as exc:
        print(f"Gemini personalization unavailable; using validated fallback: {exc}")
    # Keep a reliable working path even if Gemini is unavailable or output violates limits.
    if not _valid_lengths(fallback):
        # Use a neutral caption so long titles cannot break required word limits.
        fallback = fallback_messages(name, niche, platform, "your recent creator content")
    return fallback


def run_personalization():
    path = DATA_DIR / "enriched_influencers.csv"
    if not path.exists():
        raise FileNotFoundError("Run discovery and filtering first.")
    df = pd.read_csv(path).fillna("")
    emails, dms = [], []
    for _, row in df.iterrows():
        if str(row.get("Filter Status", "")) == "PASSED":
            msgs = generate_personalized_messages(str(row.get("Name", "Creator")), str(row.get("Category / Niche", "")), str(row.get("Platform", "")), str(row.get("Recent Content", "")))
            emails.append(msgs["email_pitch"])
            dms.append(msgs["instagram_dm"])
        else:
            emails.append("N/A - Filter Failed")
            dms.append("N/A - Filter Failed")
    df["Generated Email Pitch"] = emails
    df["Generated Instagram DM"] = dms
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    run_personalization()
    print("Personalized messages saved to data/enriched_influencers.csv")
