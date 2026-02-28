"""
Text feature extraction for fake profile detection.
Uses TF-IDF + spam keywords + repetition metrics.
No external model required (fallback-friendly).
"""
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


SPAM_KEYWORDS = [
    "buy now", "click link", "earn money", "guaranteed profit", "work from home",
    "crypto", "bitcoin", "pump", "dm for", "follow back", "f4f", "like4like",
    "promo", "giveaway", "free", "win", "cash", "investment", "forex",
    "100x", "get rich", "passive income", "onlyfans", "adult",
]


def _count_spam_keywords(text: str) -> int:
    text_lower = text.lower()
    return sum(1 for kw in SPAM_KEYWORDS if kw in text_lower)


def _repetition_score(texts: list[str]) -> float:
    """Fraction of posts that are near-duplicates (simple exact match)."""
    if not texts:
        return 0.0
    unique = len(set(t.strip().lower() for t in texts))
    return round(1 - unique / len(texts), 4)


def extract_text_features(
    profiles_df: pd.DataFrame,
    posts_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Returns text feature DataFrame indexed by profile_id.
    If posts_df is None, uses bio_text from profiles only.
    """
    records = []

    # Aggregate posts per profile if available
    post_map: dict[str, list[str]] = {}
    if posts_df is not None and "profile_id" in posts_df.columns:
        for pid, grp in posts_df.groupby("profile_id"):
            post_map[pid] = grp["content"].fillna("").tolist()

    for _, row in profiles_df.iterrows():
        pid = row["profile_id"]
        bio = str(row.get("bio_text", "") or "")
        posts = post_map.get(pid, [])
        all_text = " ".join([bio] + posts)

        bio_spam = _count_spam_keywords(bio)
        all_spam = _count_spam_keywords(all_text)
        rep_score = _repetition_score(posts) if posts else 0.0
        url_count = len(re.findall(r"http[s]?://\S+", all_text))
        hashtag_count = len(re.findall(r"#\w+", all_text))
        mention_count = len(re.findall(r"@\w+", all_text))
        caps_ratio = sum(1 for c in all_text if c.isupper()) / max(len(all_text), 1)
        avg_post_len = np.mean([len(p) for p in posts]) if posts else 0.0

        records.append({
            "profile_id": pid,
            "bio_spam_keywords": bio_spam,
            "total_spam_keywords": all_spam,
            "post_repetition_score": rep_score,
            "url_count_in_posts": url_count,
            "hashtag_count": hashtag_count,
            "mention_count": mention_count,
            "caps_ratio": round(caps_ratio, 4),
            "avg_post_length": round(avg_post_len, 2),
            "num_posts_sampled": len(posts),
        })

    return pd.DataFrame(records).set_index("profile_id")


Optional = pd.DataFrame  # re-export type alias
