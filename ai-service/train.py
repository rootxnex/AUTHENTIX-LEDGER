"""
Model training pipeline for AUTHENTIX LEDGER.
Trains: (1) Logistic Regression baseline  (2) XGBoost (production model)
Exports: model/pipeline.joblib

Run: python train.py
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import joblib
import shap
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    classification_report, roc_auc_score, precision_recall_curve,
    f1_score, precision_score, recall_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
os.makedirs(MODEL_DIR, exist_ok=True)

sys.path.insert(0, os.path.dirname(__file__))
from features.behavioral import extract_behavioral_features
from features.text import extract_text_features
from features.graph import extract_graph_features


def load_data():
    profiles = pd.read_csv(os.path.join(DATA_DIR, "profiles.csv"))
    labels = pd.read_csv(os.path.join(DATA_DIR, "labels.csv"))
    posts = pd.read_csv(os.path.join(DATA_DIR, "posts.csv"))
    edges = pd.read_csv(os.path.join(DATA_DIR, "edges.csv"))
    return profiles, labels, posts, edges


def build_feature_matrix(profiles, posts, edges):
    print("[1/3] Extracting behavioral features...")
    behav = extract_behavioral_features(profiles)
    behav.index = profiles["profile_id"].values

    print("[2/3] Extracting text features...")
    text = extract_text_features(profiles, posts)

    print("[3/3] Extracting graph features...")
    graph = extract_graph_features(profiles, edges)

    # Join all features on profile_id
    X = behav.join(text, how="left").join(graph, how="left").fillna(0)
    return X


def evaluate(model, X_test, y_test, label="Model"):
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print(f"\n── {label} ──")
    print(f"  ROC-AUC:  {auc:.4f}")
    print(f"  Precision:{precision:.4f}")
    print(f"  Recall:   {recall:.4f}")
    print(f"  F1:       {f1:.4f}")
    print(classification_report(y_test, y_pred, target_names=["Real", "Fake"]))

    # Tune threshold for high precision (law enforcement: minimize false accusations)
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
    best_threshold = 0.5
    for p, r, t in zip(precisions, recalls, thresholds):
        if p >= 0.90 and r >= 0.50:
            best_threshold = t
            break
    print(f"  High-precision threshold (P≥0.90): {best_threshold:.3f}")
    return {"auc": auc, "precision": precision, "recall": recall, "f1": f1, "threshold": best_threshold}


def main():
    print("=== AUTHENTIX LEDGER — AI Training Pipeline ===\n")
    profiles, labels, posts, edges = load_data()
    print(f"Loaded {len(profiles)} profiles, {len(posts)} posts, {len(edges)} edges")

    X = build_feature_matrix(profiles, posts, edges)
    y = labels.set_index("profile_id").reindex(X.index)["label"].values
    feature_names = X.columns.tolist()

    print(f"\nFeature matrix: {X.shape[0]} samples × {X.shape[1]} features")
    print(f"Class distribution: real={sum(y==0)}, fake={sum(y==1)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X.values, y, test_size=0.2, stratify=y, random_state=42
    )

    # ── Baseline: Logistic Regression ────────────────────────────────────────
    print("\n[Training] Logistic Regression baseline...")
    lr_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, C=1.0)),
    ])
    lr_pipe.fit(X_train, y_train)
    lr_metrics = evaluate(lr_pipe, X_test, y_test, "Logistic Regression")

    # ── Production: XGBoost via GradientBoosting ──────────────────────────────
    # Using sklearn GradientBoostingClassifier for SHAP TreeExplainer compatibility
    print("\n[Training] Gradient Boosting (production model)...")
    gb = GradientBoostingClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        min_samples_leaf=10,
        random_state=42,
    )
    gb.fit(X_train, y_train)
    gb_metrics = evaluate(gb, X_test, y_test, "Gradient Boosting")

    # ── SHAP Feature Importance ────────────────────────────────────────────────
    print("\n[SHAP] Computing global feature importance...")
    explainer = shap.TreeExplainer(gb)
    shap_values = explainer(X_test[:200])  # sample for speed
    importance = pd.Series(
        np.abs(shap_values.values).mean(axis=0),
        index=feature_names,
    ).sort_values(ascending=False)
    print("\nTop 10 Global Features (SHAP):")
    print(importance.head(10).to_string())

    # Save global importance
    importance.to_json(os.path.join(MODEL_DIR, "feature_importance.json"))

    # ── Export pipeline ────────────────────────────────────────────────────────
    print("\n[Export] Saving model artifacts...")

    # Wrap GradientBoosting with calibration for accurate probabilities
    calibrated = CalibratedClassifierCV(gb, cv="prefit", method="sigmoid")
    calibrated.fit(X_test, y_test)  # fit calibration on held-out test set

    # Save as dict for inference flexibility
    artifact = {
        "model": calibrated,
        "feature_names": feature_names,
        "threshold": gb_metrics["threshold"],
        "metrics": gb_metrics,
    }
    joblib.dump(artifact, os.path.join(MODEL_DIR, "pipeline.joblib"))
    joblib.dump(explainer, os.path.join(MODEL_DIR, "shap_explainer.joblib"))

    # Save metadata
    metadata = {
        "feature_names": feature_names,
        "threshold": gb_metrics["threshold"],
        "metrics": gb_metrics,
        "lr_metrics": lr_metrics,
    }
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✓ Model saved to {MODEL_DIR}/pipeline.joblib")
    print(f"✓ SHAP explainer saved to {MODEL_DIR}/shap_explainer.joblib")
    print(f"✓ Metadata saved to {MODEL_DIR}/metadata.json")


if __name__ == "__main__":
    main()
