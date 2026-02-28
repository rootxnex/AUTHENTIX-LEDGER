"""
Synthetic Dataset Generator for AUTHENTIX LEDGER AI pipeline.
Generates realistic fake/real profile data for demo and testing.
Run: python generate_dataset.py
"""
import os
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

PLATFORMS = ["twitter", "instagram", "facebook", "telegram"]
REAL_BIO_SAMPLES = [
    "Journalist covering technology and policy",
    "Software engineer | Open source contributor",
    "Photographer based in Mumbai",
    "Sports analyst and cricket lover",
    "Teacher | Education reformer",
    "Startup founder | FinTech",
    "Government employee | Public servant",
    "PhD researcher in AI ethics",
]
FAKE_BIO_SAMPLES = [
    "", "", "",  # empty bio is a bot signal
    "Follow back! DM for promo",
    "Crypto expert 100x gains guaranteed",
    "Online marketer | work from home",
]
BOT_USERNAME_PATTERNS = ["user{}", "acc{}", "bot{}", "auto{}"]
REAL_USERNAME_PATTERNS = ["{}singh", "{}sharma", "{}kumar", "the_real_{}", "{}_india"]

SPAM_PHRASES = [
    "buy now", "click link", "earn money fast", "guaranteed profit",
    "follow for follow", "dm for collab", "crypto pump",
]


def gen_profile(fake: bool, idx: int) -> dict:
    platform = random.choice(PLATFORMS)
    account_age_days = random.randint(1, 20) if fake else random.randint(180, 3000)

    if fake:
        follower_count = random.randint(0, 200)
        following_count = random.randint(500, 5000)
        post_count = random.randint(50, 2000)
        bio_text = random.choice(FAKE_BIO_SAMPLES)
        pattern = random.choice(BOT_USERNAME_PATTERNS)
        username = pattern.format(random.randint(100000, 999999))
        avg_likes = random.randint(0, 5)
        avg_comments = random.randint(0, 2)
        verified = False
        profile_pic_changed = random.randint(3, 20)
        duplicate_posts_ratio = random.uniform(0.4, 0.95)
        spam_keyword_count = random.randint(3, 15)
        reply_ratio = random.uniform(0.0, 0.05)
        retweet_ratio = random.uniform(0.7, 1.0)
    else:
        follower_count = random.randint(50, 50000)
        following_count = random.randint(50, 2000)
        post_count = random.randint(10, 3000)
        bio_text = random.choice(REAL_BIO_SAMPLES)
        pattern = random.choice(REAL_USERNAME_PATTERNS)
        username = pattern.format(random.choice(["raj", "priya", "arjun", "ananya", "vikram"]))
        avg_likes = random.randint(10, 5000)
        avg_comments = random.randint(2, 500)
        verified = random.random() < 0.05
        profile_pic_changed = random.randint(0, 3)
        duplicate_posts_ratio = random.uniform(0.0, 0.15)
        spam_keyword_count = random.randint(0, 2)
        reply_ratio = random.uniform(0.3, 0.8)
        retweet_ratio = random.uniform(0.1, 0.4)

    ff_ratio = following_count / max(follower_count, 1)
    bio_length = len(bio_text)
    digit_ratio = sum(c.isdigit() for c in username) / max(len(username), 1)
    posts_per_day = post_count / max(account_age_days, 1)

    return {
        "profile_id": f"{'fake' if fake else 'real'}_{idx:05d}",
        "platform": platform,
        "username": username,
        "follower_count": follower_count,
        "following_count": following_count,
        "post_count": post_count,
        "account_age_days": account_age_days,
        "bio_text": bio_text,
        "bio_length": bio_length,
        "verified": int(verified),
        "avg_likes_per_post": avg_likes,
        "avg_comments_per_post": avg_comments,
        "ff_ratio": round(ff_ratio, 4),
        "posts_per_day": round(posts_per_day, 4),
        "digit_ratio_username": round(digit_ratio, 4),
        "profile_pic_changes": profile_pic_changed,
        "duplicate_posts_ratio": round(duplicate_posts_ratio, 4),
        "spam_keyword_count": spam_keyword_count,
        "reply_ratio": round(reply_ratio, 4),
        "retweet_ratio": round(retweet_ratio, 4),
    }


def gen_posts(profile_id: str, fake: bool, post_count: int) -> list[dict]:
    rows = []
    n = min(post_count, 20)
    for i in range(n):
        if fake:
            content = random.choice(SPAM_PHRASES) + " " + random.choice(["http://bit.ly/xyz", ""] * 3)
            sentiment = random.choice([-1, 0])
        else:
            content = f"Sample post content #{i} about current events"
            sentiment = random.choice([-1, 0, 1])
        rows.append({
            "profile_id": profile_id,
            "post_id": f"{profile_id}_p{i}",
            "content": content,
            "like_count": random.randint(0, 500),
            "comment_count": random.randint(0, 50),
            "sentiment": sentiment,
        })
    return rows


def gen_edges(profile_ids: list[str], n_edges: int = 2000) -> list[dict]:
    """Generate follow/mention graph edges for network analysis."""
    rows = []
    for _ in range(n_edges):
        src = random.choice(profile_ids)
        dst = random.choice(profile_ids)
        if src != dst:
            rows.append({"source": src, "target": dst, "edge_type": random.choice(["follow", "mention"])})
    return rows


def main():
    n_real = 700
    n_fake = 700

    profiles = [gen_profile(False, i) for i in range(n_real)] + [gen_profile(True, i) for i in range(n_fake)]
    random.shuffle(profiles)
    profile_df = pd.DataFrame(profiles)

    labels_df = profile_df[["profile_id"]].copy()
    labels_df["label"] = profile_df["profile_id"].apply(lambda x: 1 if x.startswith("fake") else 0)

    posts = []
    for row in profiles:
        posts.extend(gen_posts(row["profile_id"], row["profile_id"].startswith("fake"), row["post_count"]))

    profile_ids = profile_df["profile_id"].tolist()
    edges = gen_edges(profile_ids, n_edges=3000)

    profile_df.to_csv(os.path.join(DATA_DIR, "profiles.csv"), index=False)
    labels_df.to_csv(os.path.join(DATA_DIR, "labels.csv"), index=False)
    pd.DataFrame(posts).to_csv(os.path.join(DATA_DIR, "posts.csv"), index=False)
    pd.DataFrame(edges).to_csv(os.path.join(DATA_DIR, "edges.csv"), index=False)

    print(f"Generated {len(profiles)} profiles ({n_real} real, {n_fake} fake)")
    print(f"  → data/profiles.csv, labels.csv, posts.csv, edges.csv")


if __name__ == "__main__":
    main()
