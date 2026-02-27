"""
AI Risk Scoring Client.
Loads the pre-trained joblib pipeline from ai-service/model/
and provides synchronous + async inference.
Falls back to a heuristics-only scorer if model file is absent.
"""
import json
import math
import os
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "ai-service", "model", "pipeline.joblib"
)

_pipeline = None


def _load_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    try:
        import joblib
        _pipeline = joblib.load(os.path.abspath(_MODEL_PATH))
        logger.info("ai.pipeline_loaded", path=_MODEL_PATH)
    except Exception as e:
        logger.warning("ai.pipeline_unavailable", error=str(e), fallback="heuristics")
        _pipeline = None
    return _pipeline


def _heuristic_score(profile_data: dict) -> tuple[float, list[dict]]:
    """
    Rule-based fallback scorer when ML model is unavailable.
    Returns (score 0-100, factors list).
    """
    score = 30.0  # baseline
    factors = []

    follower_count = profile_data.get("follower_count", 0) or 0
    following_count = profile_data.get("following_count", 0) or 0
    post_count = profile_data.get("post_count", 0) or 0
    account_age_days = profile_data.get("account_age_days", 365) or 365
    bio_text = profile_data.get("bio_text", "") or ""
    username = profile_data.get("username", "") or ""

    # High following/follower ratio (bot signal)
    ff_ratio = following_count / max(follower_count, 1)
    if ff_ratio > 5:
        delta = min(25, ff_ratio * 2)
        score += delta
        factors.append({
            "name": "high_following_ratio",
            "contribution": round(delta, 2),
            "direction": "increases_risk",
            "description": f"Following/Follower ratio {ff_ratio:.1f}x — typical of bot accounts",
        })

    # New account with many posts (astroturfing)
    if account_age_days < 30 and post_count > 100:
        score += 20
        factors.append({
            "name": "new_account_high_activity",
            "contribution": 20.0,
            "direction": "increases_risk",
            "description": "Account less than 30 days old but >100 posts — burst activity pattern",
        })

    # Near-zero followers (unused/bot)
    if follower_count < 10 and following_count > 200:
        score += 15
        factors.append({
            "name": "ghost_follower_pattern",
            "contribution": 15.0,
            "direction": "increases_risk",
            "description": "<10 followers but 200+ following — ghost/bot pattern",
        })

    # Empty bio
    if not bio_text.strip():
        score += 5
        factors.append({
            "name": "empty_bio",
            "contribution": 5.0,
            "direction": "increases_risk",
            "description": "Profile has no bio text",
        })

    # Numeric-heavy username (bot naming pattern: user12345678)
    import re
    digit_ratio = len(re.findall(r'\d', username)) / max(len(username), 1)
    if digit_ratio > 0.5:
        score += 10
        factors.append({
            "name": "numeric_username",
            "contribution": 10.0,
            "direction": "increases_risk",
            "description": f"Username is {digit_ratio*100:.0f}% digits — common bot naming pattern",
        })

    score = min(max(score, 0), 100)
    return round(score, 2), factors


def score_profile(profile_data: dict) -> dict:
    """
    Score a profile. Returns dict with:
      - risk_score: float 0–100
      - risk_level: str (LOW/MEDIUM/HIGH/CRITICAL)
      - risk_factors: list[dict]
    """
    pipeline = _load_pipeline()

    if pipeline is not None:
        try:
            import pandas as pd
            df = pd.DataFrame([profile_data])
            proba = pipeline.predict_proba(df)[0][1]  # probability of fake
            score = round(proba * 100, 2)

            # SHAP explanation
            factors = []
            try:
                import shap
                explainer = pipeline.get("explainer")
                if explainer:
                    shap_values = explainer(df)
                    feature_names = df.columns.tolist()
                    sv = shap_values.values[0]
                    for i, (name, val) in enumerate(zip(feature_names, sv)):
                        factors.append({
                            "name": name,
                            "contribution": round(float(val), 4),
                            "direction": "increases_risk" if val > 0 else "decreases_risk",
                            "description": f"Feature '{name}' SHAP contribution",
                        })
                    factors = sorted(factors, key=lambda x: abs(x["contribution"]), reverse=True)[:5]
            except Exception:
                pass

            if not factors:
                score, factors = _heuristic_score(profile_data)
        except Exception as e:
            logger.error("ai.model_inference_failed", error=str(e))
            score, factors = _heuristic_score(profile_data)
    else:
        score, factors = _heuristic_score(profile_data)

    # Risk level mapping
    if score < 25:
        level = "LOW"
    elif score < 50:
        level = "MEDIUM"
    elif score < 75:
        level = "HIGH"
    else:
        level = "CRITICAL"

    return {"risk_score": score, "risk_level": level, "risk_factors": factors}
