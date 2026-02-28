"""Behavioral feature engineering from profiles.csv."""
import pandas as pd
import numpy as np


def extract_behavioral_features(profiles_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract behavioral aggregates from raw profile metadata.
    Returns a DataFrame with feature columns ready for model training.
    """
    df = profiles_df.copy()

    # Core ratio features
    df["ff_ratio"] = df["following_count"] / (df["follower_count"] + 1)
    df["posts_per_day"] = df["post_count"] / (df["account_age_days"] + 1)
    df["like_to_follower_ratio"] = df.get("avg_likes_per_post", pd.Series(0, index=df.index)) / (df["follower_count"] + 1)
    df["engagement_rate"] = (
        df.get("avg_likes_per_post", pd.Series(0, index=df.index)) +
        df.get("avg_comments_per_post", pd.Series(0, index=df.index))
    ) / (df["follower_count"] + 1)

    # Account age features
    df["is_new_account"] = (df["account_age_days"] < 30).astype(int)
    df["log_account_age"] = np.log1p(df["account_age_days"])

    # Username features
    if "username" in df.columns:
        df["digit_ratio_username"] = df["username"].apply(
            lambda u: sum(c.isdigit() for c in str(u)) / max(len(str(u)), 1)
        )
        df["username_length"] = df["username"].apply(lambda u: len(str(u)))
        df["has_bot_keywords"] = df["username"].str.lower().str.contains(
            r"bot|auto|spam|fake|promo", regex=True, na=False
        ).astype(int)
    else:
        df["digit_ratio_username"] = 0.0
        df["username_length"] = 10
        df["has_bot_keywords"] = 0

    # Bio features
    df["bio_length"] = df.get("bio_text", pd.Series("", index=df.index)).fillna("").apply(len)
    df["empty_bio"] = (df["bio_length"] == 0).astype(int)

    # Verified
    df["verified"] = df.get("verified", pd.Series(0, index=df.index)).fillna(0).astype(int)

    # Activity anomaly
    df["burst_activity_score"] = (df["posts_per_day"] > 10).astype(int) * df["is_new_account"]
    df["ghost_follower_score"] = ((df["follower_count"] < 10) & (df["following_count"] > 200)).astype(int)

    BEHAVIORAL_FEATURES = [
        "ff_ratio", "posts_per_day", "like_to_follower_ratio", "engagement_rate",
        "is_new_account", "log_account_age", "digit_ratio_username", "username_length",
        "has_bot_keywords", "bio_length", "empty_bio", "verified",
        "burst_activity_score", "ghost_follower_score",
        "duplicate_posts_ratio", "spam_keyword_count", "reply_ratio", "retweet_ratio",
        "profile_pic_changes",
    ]

    # Fill any missing columns with 0
    for col in BEHAVIORAL_FEATURES:
        if col not in df.columns:
            df[col] = 0

    return df[BEHAVIORAL_FEATURES]
