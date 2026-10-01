import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import google.generativeai as genai
import pandas as pd
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

PROMPT_TEMPLATE = """
You are an expert Influencer Marketing Specialist. Generate two personalized outreach messages for the following influencer:

Influencer Name: {name}
Niche: {niche}
Platform: {platform}
Recent Content Context: {recent_content}

Generate JSON matching this schema strictly:
{{
  "email_pitch": "An email collaboration pitch referencing their content style. Length MUST be strictly between 60 and 90 words. Proposed collaboration: Paid UGC campaign.",
  "instagram_dm": "A short, natural IG DM referencing their recent post. Length MUST be strictly between 15 and 30 words."
}}

Do not include any Markdown wrapper code blocks like ```json. Return raw JSON string only.
"""

def generate_personalized_messages(name: str, niche: str, platform: str, recent_content: str) -> dict:
    if not GEMINI_API_KEY:
        # Fallback simulation if API key is not configured
        return {
            "email_pitch": f"Hi {name}, I loved your recent post about skincare! Your {niche} content resonated with us, and we would love to collaborate on a UGC campaign for our organic skincare line. We offer competitive compensation and free premium products for review. Let us know if you'd be interested in reviewing the collaboration details!",
            "instagram_dm": f"Hi {name}, loved your latest post on skincare! Your audience would be perfect for our upcoming UGC campaign. Sent you an email!"
        }

    prompt = PROMPT_TEMPLATE.format(
        name=name,
        niche=niche,
        platform=platform,
        recent_content=recent_content
    )
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"LLM Generation Error for {name}: {e}")
        return {
            "email_pitch": f"Hi {name}, loved your content on {platform}. Your profile in {niche} is fantastic and matches our target brand aesthetic. We are running a UGC sponsorship campaign and would love to partner up. Please let us know if you are open to receiving a product package and details!",
            "instagram_dm": f"Hey {name}, adore your {niche} content! Would love to collaborate on an upcoming project. Let us know if interested!"
        }

def run_personalization():
    df = pd.read_csv("data/enriched_influencers.csv")
    
    email_pitches = []
    ig_dms = []
    
    for idx, row in df.iterrows():
        if row["Filter Status"] == "PASSED":
            msgs = generate_personalized_messages(
                row["Name"], row["Category / Niche"], row["Platform"], row["Recent Content"]
            )
            email_pitches.append(msgs["email_pitch"])
            ig_dms.append(msgs["instagram_dm"])
        else:
            email_pitches.append("N/A - Filter Failed")
            ig_dms.append("N/A - Filter Failed")
            
    df["Generated Email Pitch"] = email_pitches
    df["Generated Instagram DM"] = ig_dms
    df.to_csv("data/enriched_influencers.csv", index=False)
    print("Personalized messages successfully generated.")

if __name__ == "__main__":
    run_personalization()