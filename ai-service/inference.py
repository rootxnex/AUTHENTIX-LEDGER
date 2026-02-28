"""
Inference script — accepts a profile JSON and outputs risk score + SHAP explanations.
Can be used as a CLI or imported as a module.

Usage:
  python inference.py '{"follower_count": 50, "following_count": 5000, ...}'
"""
import json
import sys
import os
import numpy as np
import joblib
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")


def load_artifacts():
    pipeline_path = os.path.join(MODEL_DIR, "pipeline.joblib")
    explainer_path = os.path.join(MODEL_DIR, "shap_explainer.joblib")
    meta_path = os.path.join(MODEL_DIR, "metadata.json")

    if not os.path.exists(pipeline_path):
        raise FileNotFoundError(f"Model not found: {pipeline_path}. Run train.py first.")

    artifact = joblib.load(pipeline_path)
    model = artifact["model"]
    feature_names = artifact["feature_names"]
    threshold = artifact.get("threshold", 0.5)

    explainer = joblib.load(explainer_path) if os.path.exists(explainer_path) else None

    with open(meta_path) as f:
        metadata = json.load(f)

    return model, feature_names, threshold, explainer, metadata


def profile_to_features(profile: dict, feature_names: list) -> pd.DataFrame:
    """
    Convert a raw profile dict to a feature row matching training feature names.
    Missing features default to 0.
    """
    import re

    follower = profile.get("follower_count", 0) or 0
    following = profile.get("following_count", 0) or 0
    posts = profile.get("post_count", 0) or 0
    age = profile.get("account_age_days", 365) or 365
    bio = str(profile.get("bio_text", "") or "")
    username = str(profile.get("username", "") or "")

    SPAM_KEYWORDS = [
        "buy now", "click link", "earn money", "guaranteed profit", "work from home",
        "crypto", "bitcoin", "pump", "dm for", "follow back", "f4f",
        "promo", "giveaway", "free", "win", "cash", "investment",
    ]

    ff_ratio = following / max(follower, 1)
    posts_per_day = posts / max(age, 1)
    digit_ratio = sum(c.isdigit() for c in username) / max(len(username), 1)
    bio_length = len(bio)
    spam_count = sum(1 for kw in SPAM_KEYWORDS if kw in bio.lower())

    row = {
        "ff_ratio": ff_ratio,
        "posts_per_day": posts_per_day,
        "like_to_follower_ratio": profile.get("avg_likes_per_post", 0) / max(follower, 1),
        "engagement_rate": 0.0,
        "is_new_account": int(age < 30),
        "log_account_age": np.log1p(age),
        "digit_ratio_username": digit_ratio,
        "username_length": len(username),
        "has_bot_keywords": int(bool(re.search(r"bot|auto|spam|fake|promo", username.lower()))),
        "bio_length": bio_length,
        "empty_bio": int(bio_length == 0),
        "verified": int(profile.get("verified", False) or False),
        "burst_activity_score": int(posts_per_day > 10) * int(age < 30),
        "ghost_follower_score": int(follower < 10 and following > 200),
        "duplicate_posts_ratio": profile.get("duplicate_posts_ratio", 0.0) or 0.0,
        "spam_keyword_count": spam_count,
        "reply_ratio": profile.get("reply_ratio", 0.5),
        "retweet_ratio": profile.get("retweet_ratio", 0.3),
        "profile_pic_changes": profile.get("profile_pic_changes", 0),
        # text features (defaults)
        "bio_spam_keywords": spam_count,
        "total_spam_keywords": spam_count,
        "post_repetition_score": profile.get("duplicate_posts_ratio", 0.0) or 0.0,
        "url_count_in_posts": 0,
        "hashtag_count": len(re.findall(r"#\w+", bio)),
        "mention_count": len(re.findall(r"@\w+", bio)),
        "caps_ratio": sum(c.isupper() for c in bio) / max(len(bio), 1),
        "avg_post_length": 0.0,
        "num_posts_sampled": 0,
        # graph (defaults — no graph context for single-profile inference)
        "pagerank": 0.0,
        "clustering_coeff": 0.0,
        "in_degree": 0,
        "out_degree": 0,
        "io_degree_ratio": 0.0,
        "degree_centrality": 0.0,
        "component_size": 1,
        "is_isolated_node": 1,
        "is_hub_node": 0,
    }

    # Build DataFrame with only the features the model expects
    df = pd.DataFrame([{k: row.get(k, 0) for k in feature_names}])
    return df


def predict(profile: dict) -> dict:
    """
    Main inference function.
    Returns: { risk_score, risk_level, probability, threshold_used, top_factors }
    """
    model, feature_names, threshold, explainer, metadata = load_artifacts()
    X = profile_to_features(profile, feature_names)

    proba = model.predict_proba(X)[0][1]
    risk_score = round(proba * 100, 2)
    flagged = proba >= threshold

    risk_level = (
        "CRITICAL" if risk_score >= 75 else
        "HIGH" if risk_score >= 50 else
        "MEDIUM" if risk_score >= 25 else
        "LOW"
    )

    # SHAP explanation
    top_factors = []
    if explainer is not None:
        try:
            # TreeExplainer expects raw model input (base estimator)
            base_model = model.calibrated_classifiers_[0].estimator if hasattr(model, "calibrated_classifiers_") else None
            if base_model and hasattr(explainer, "__call__"):
                shap_values = explainer(X)
                sv = shap_values.values[0]
                for name, val in sorted(zip(feature_names, sv), key=lambda x: abs(x[1]), reverse=True)[:5]:
                    top_factors.append({
                        "name": name,
                        "contribution": round(float(val), 4),
                        "direction": "increases_risk" if val > 0 else "decreases_risk",
                        "description": f"SHAP contribution of '{name}' to fake probability",
                    })
        except Exception:
            pass

    if not top_factors:
        # Heuristic explanation fallback
        top_factors = [
            {"name": "ff_ratio", "contribution": round(X["ff_ratio"].iloc[0] * 0.1, 4), "direction": "increases_risk" if X["ff_ratio"].iloc[0] > 2 else "decreases_risk", "description": "Following/Follower ratio"},
            {"name": "posts_per_day", "contribution": round(X["posts_per_day"].iloc[0] * 0.05, 4), "direction": "increases_risk" if X["posts_per_day"].iloc[0] > 10 else "decreases_risk", "description": "Posting frequency"},
        ]

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "probability_fake": round(proba, 4),
        "flagged": flagged,
        "threshold_used": threshold,
        "top_factors": top_factors,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inference.py '<profile JSON>'")
        print("Example:")
        print('  python inference.py \'{"follower_count": 5, "following_count": 5000, "account_age_days": 3}\'')
        sys.exit(1)

    profile_json = json.loads(sys.argv[1])
    result = predict(profile_json)
    print(json.dumps(result, indent=2))
