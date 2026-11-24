"""Train / load / apply the Kestrel routing model (no external API, no paid key)."""
import json, re, joblib
import numpy as np, pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from .text import features_text, clauses, RENAMES, TEAMS

META = ["product_family", "warranty_status", "channel"]
AUTO_THRESHOLD = 0.80        # at/above this the request is routed automatically
# Rows that are not customer messages (stray operator annotations pasted into the export).
_NOT_CUSTOMER = re.compile(r"gold-routed|human-verified|automated tools|for ai assistants|ops remark|assistant/reviewer", re.I)

CLARIFY = {
    "default": "Ask the customer one question: is this (a) something broken, (b) an installation/demo visit, "
               "(c) a spare part or filter, (d) a payment/invoice problem, (e) a return/exchange of a delivery, "
               "(f) a warranty/Shield question, or (g) a how-to question?",
}


def load_training_frame(train_csv, resolution_csv):
    tr = pd.read_csv(train_csv)
    rs = pd.read_csv(resolution_csv)
    d = tr.merge(rs[["request_id", "final_team", "transfers"]], on="request_id", how="inner")
    d["final_team"] = d["final_team"].replace(RENAMES)          # two teams were renamed on 15 Jan 2026
    d["team_label"] = d["team_label"].replace(RENAMES)
    d = d[~d["request_text"].str.contains(_NOT_CUSTOMER)].reset_index(drop=True)
    return d


def _design(df, vec, enc, fit=False):
    ft = df["request_text"].map(features_text)
    meta = df[META].fillna("unknown").astype(str)
    if fit:
        return hstack([vec.fit_transform(ft), enc.fit_transform(meta)]).tocsr()
    return hstack([vec.transform(ft), enc.transform(meta)]).tocsr()


def fit(df, C=10.0):
    vec = TfidfVectorizer(token_pattern=r"\S+", min_df=2, sublinear_tf=True, lowercase=False)
    enc = OneHotEncoder(handle_unknown="ignore")
    X = _design(df, vec, enc, fit=True)
    clf = LogisticRegression(C=C, max_iter=5000).fit(X, df["final_team"])
    return {"vec": vec, "enc": enc, "clf": clf, "classes": list(clf.classes_), "threshold": AUTO_THRESHOLD}


def predict_proba(bundle, df):
    return bundle["clf"].predict_proba(_design(df, bundle["vec"], bundle["enc"]))


def save(bundle, path):
    joblib.dump(bundle, path, compress=3)


def load(path):
    return joblib.load(path)


# ---------------------------------------------------------------- single record, with reasons
_STOP = set("a an and the is are was were am be to of in on at for from by with as it its my me i we our you your this that these those which what when where who why how up did do does not no so if or but have has had will would can could just also than then there here about after before into out over again very pls please sir hi hello team thanks asap".split())
_PAY = re.compile(r"\b(paid|payment done|payment|upi|emi|card)\b")


def _top_phrases(bundle, row_df, cls_idx, k=4):
    vec, enc, clf = bundle["vec"], bundle["enc"], bundle["clf"]
    x = _design(row_df, vec, enc)
    nt = len(vec.vocabulary_)
    contrib = x[:, :nt].multiply(clf.coef_[cls_idx][:nt]).toarray()[0]
    inv = np.array(vec.get_feature_names_out())
    out = []
    for i in np.argsort(-contrib):
        if contrib[i] <= 0 or len(out) >= k:
            break
        tok = inv[i]
        if tok.startswith(("a_", "L_", "E_")):
            w = tok.split("_", 1)[1]
        elif tok.startswith("L2_"):
            w = tok[3:].replace("_", " ")
        else:
            continue
        if all(t in _STOP for t in w.split()):
            continue
        if w not in out and not any(w in o for o in out):
            out.append(w)
    return out


def explain(bundle, record):
    text = str(record.get("request_text", "")).strip()
    if not text:
        raise ValueError("request_text is required")
    row = pd.DataFrame([{"request_text": text,
                         "product_family": record.get("product_family") or "unknown",
                         "warranty_status": record.get("warranty_status") or "unknown",
                         "channel": record.get("channel") or "unknown"}])
    p = predict_proba(bundle, row)[0]
    classes = bundle["classes"]
    order = np.argsort(-p)
    top = classes[order[0]]
    conf = float(p[order[0]])
    action = "auto_route" if conf >= bundle["threshold"] else "needs_clarification"
    reasons = []
    cl = [c for c in clauses(text) if c.strip()]
    phrases = _top_phrases(bundle, row, int(order[0]))
    if action == "auto_route":
        if phrases:
            reasons.append("Key words behind this: " + ", ".join('"%s"' % w for w in phrases) + ".")
        if len(cl) > 1:
            # which team would each clause alone go to?
            per = []
            for c in cl:
                r1 = row.assign(request_text=c)
                pc = predict_proba(bundle, r1)[0]
                per.append((c, classes[int(np.argmax(pc))], float(pc.max())))
            teams = [t for _, t, pr in per if pr >= 0.6]
            if len(set(teams)) > 1:
                reasons.append("The customer raised more than one issue (" + "; ".join(
                    '"%s" -> %s' % (c, t) for c, t, pr in per if pr >= 0.6) +
                    "). In past requests the team that closed it was nearly always the one for the LAST issue mentioned, "
                    "so it goes to " + top + ".")
        if _PAY.search(text.lower()) and top != "Billing":
            reasons.append("The customer mentions paying, but per policy section 3 it is Billing only when the payment "
                           "itself is the problem. Here the real issue is something else.")
    else:
        reasons.append("The message does not say what is actually wrong, so no tool can route it reliably. "
                       "In the past, requests worded like this ended up with all seven teams.")
        reasons.append(CLARIFY["default"])
    return {
        "recommended_team": top,
        "confidence": round(conf, 3),
        "action": action,
        "alternatives": [{"team": classes[i], "probability": round(float(p[i]), 3)} for i in order[1:3]],
        "reasons": reasons,
        "model": "tf-idf + logistic regression trained on where requests actually ended up (no external API)",
    }
