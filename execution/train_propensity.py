"""Train the customer conversion-propensity model.

Gradient-boosted classifier over the labeled history → data/propensity.pkl.
Reports holdout AUC + a logistic baseline + feature importances for the deck.
"""
from __future__ import annotations

import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from config import load_json, DATA_DIR
from features import prospect_features, vectorize, PROPENSITY_FEATURES


def build_dataset():
    history = load_json("history.json")
    X, y = [], []
    for h in history:
        X.append(vectorize(prospect_features(h), PROPENSITY_FEATURES))
        y.append(1 if h["outcome"]["converted"] else 0)
    return X, y


def _importances(model, features):
    """Uniform importance vector for either a tree or a scaled-logistic pipeline."""
    if hasattr(model, "feature_importances_"):
        raw = model.feature_importances_
    else:  # pipeline(StandardScaler, LogisticRegression) -> |standardized coef|
        coef = abs(model[-1].coef_[0])
        raw = coef / (coef.sum() or 1.0)
    return sorted(zip(features, [float(w) for w in raw]), key=lambda t: -t[1])


def main():
    X, y = build_dataset()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    gbm = GradientBoostingClassifier(n_estimators=180, max_depth=3, learning_rate=0.06,
                                     random_state=42).fit(Xtr, ytr)
    logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(Xtr, ytr)

    scored = {
        "GradientBoosting": (gbm, roc_auc_score(yte, gbm.predict_proba(Xte)[:, 1])),
        "Logistic": (logit, roc_auc_score(yte, logit.predict_proba(Xte)[:, 1])),
    }
    best_name = max(scored, key=lambda k: scored[k][1])
    model, auc = scored[best_name]
    acc = accuracy_score(yte, model.predict(Xte))
    imp = _importances(model, PROPENSITY_FEATURES)

    # population means per feature — the baseline for per-decision (occlusion) explanations
    means = {f: sum(row[i] for row in X) / len(X) for i, f in enumerate(PROPENSITY_FEATURES)}

    joblib.dump({"model": model, "features": PROPENSITY_FEATURES, "algo": best_name,
                 "auc": round(auc, 3), "importances": imp, "feature_means": means},
                DATA_DIR / "propensity.pkl")

    print(f"Propensity model → data/propensity.pkl  (selected: {best_name})")
    for name, (_, a) in scored.items():
        print(f"  {name:16} AUC={a:.3f}" + ("  <- selected" if name == best_name else ""))
    print(f"  Selected ACC={acc:.3f}")
    print("  Top features:", ", ".join(f"{f} ({w:.2f})" for f, w in imp[:5]))


if __name__ == "__main__":
    main()
