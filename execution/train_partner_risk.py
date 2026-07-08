"""Train the partner / lead default-risk model — the novel 'adverse selection' detector.

Predicts P(lead defaults) using customer signals PLUS the sourcing partner's
(volume-shrunk) track record. Trained only on converted/disbursed history, where
a default outcome exists. → data/partner_risk.pkl
"""
from __future__ import annotations

import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from config import load_json, DATA_DIR
from features import partner_risk_features, vectorize, PARTNER_RISK_FEATURES


def build_dataset():
    history = load_json("history.json")
    partners = {p["id"]: p for p in load_json("partners.json")}
    X, y = [], []
    for h in history:
        if not h["outcome"]["converted"]:
            continue  # default only defined for disbursed loans
        partner = partners.get(h["partner_id"])
        if not partner:
            continue
        X.append(vectorize(partner_risk_features(h, partner), PARTNER_RISK_FEATURES))
        y.append(1 if h["outcome"]["defaulted"] else 0)
    return X, y


def _importances(model, features):
    if hasattr(model, "feature_importances_"):
        raw = model.feature_importances_
    else:
        coef = abs(model[-1].coef_[0])
        raw = coef / (coef.sum() or 1.0)
    return sorted(zip(features, [float(w) for w in raw]), key=lambda t: -t[1])


def main():
    X, y = build_dataset()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    gbm = GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.05,
                                     random_state=42).fit(Xtr, ytr)
    logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(Xtr, ytr)
    scored = {"GradientBoosting": (gbm, roc_auc_score(yte, gbm.predict_proba(Xte)[:, 1])),
              "Logistic": (logit, roc_auc_score(yte, logit.predict_proba(Xte)[:, 1]))}
    best = max(scored, key=lambda k: scored[k][1])
    model, auc = scored[best]
    imp = _importances(model, PARTNER_RISK_FEATURES)

    means = {f: sum(row[i] for row in X) / len(X) for i, f in enumerate(PARTNER_RISK_FEATURES)}

    joblib.dump({"model": model, "features": PARTNER_RISK_FEATURES, "algo": best,
                 "auc": round(auc, 3), "importances": imp, "feature_means": means},
                DATA_DIR / "partner_risk.pkl")

    print(f"Partner default-risk model → data/partner_risk.pkl  (n={len(X)}, defaults={sum(y)}, selected: {best})")
    for name, (_, a) in scored.items():
        print(f"  {name:16} AUC={a:.3f}" + ("  <- selected" if name == best else ""))
    print("  Top features:", ", ".join(f"{f} ({w:.2f})" for f, w in imp[:5]))
    print(f"  Partner-history feature share: {sum(w for f, w in imp if f.startswith('partner_')):.2f}")


if __name__ == "__main__":
    main()
