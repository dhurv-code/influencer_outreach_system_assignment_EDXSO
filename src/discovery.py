import json
import random

NICHER_LIST = ["Fashion & Beauty", "Fitness", "Tech", "Gaming", "Lifestyle"]
PLATFORMS = ["Instagram", "YouTube", "TikTok"]

def generate_mock_influencers(count=50) -> list:
    """Generates a dataset of 50 micro-influencer records for testing."""
    influencers = []
    
    # Real-world styled profile archetypes for robust testing
    sample_profiles = [
        ("Sarah Jenkins", "sarah.j.style", "Fashion & Beauty", "sarah@beautyblog.com"),
        ("Alex Rivera", "arivera_fit", "Fitness", "alex@fitlife.co"),
        ("Elena Rostova", "elena_looks", "Fashion & Beauty", "elena.rostova@gmail.com"),
        ("Marcus Vance", "vancetech", "Tech", None), # Missing email test case
        ("Chloe Bennett", "chloe_lifestyle", "Fashion & Beauty", "contact@chloebennett.com"),
    ]

    for i in range(count):
        if i < len(sample_profiles):
            name, handle, niche, email = sample_profiles[i]
        else:
            name = f"Creator {i+1}"
            handle = f"creator_{i+1}"
            niche = random.choice(NICHER_LIST)
            email = f"contact@{handle}.com" if i % 6 != 0 else None  # ~15% missing email rate

        followers = random.randint(3000, 120000)
        engagement = round(random.uniform(0.8, 6.5), 2)
        platform = random.choice(PLATFORMS)

        record = {
            "influencer_id": f"INF_{i+1:03d}",
            "name": name,
            "platform": platform,
            "profile_url": f"https://www.{platform.lower()}.com/{handle}",
            "follower_count": followers,
            "engagement_rate": engagement,
            "category_niche": niche,
            "contact_email": email,
            "recent_post_caption": f"Loved testing out these organic skincare items for the past week! What's your daily routine? #{niche.replace(' ', '').lower()}"
        }
        influencers.append(record)

    return influencers

if __name__ == "__main__":
    data = generate_mock_influencers(50)
    with open("data/raw_influencers.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Successfully generated {len(data)} influencer records.")