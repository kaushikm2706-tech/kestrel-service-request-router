"""python -m kestrel_router.predict --test test_unlabelled.csv --out predictions.csv"""
import argparse
import numpy as np, pandas as pd
from . import model as M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--model", default="model.joblib")
    ap.add_argument("--out", default="predictions.csv")
    a = ap.parse_args()
    b = M.load(a.model)
    t = pd.read_csv(a.test)
    P = M.predict_proba(b, t)
    out = pd.DataFrame({"request_id": t.request_id, "team": np.array(b["classes"])[P.argmax(1)]})
    out.to_csv(a.out, index=False)
    conf = P.max(1)
    print("wrote %s (%d rows). Share the model is >=%.0f%% sure about: %.1f%%"
          % (a.out, len(out), 100 * b["threshold"], 100 * (conf >= b["threshold"]).mean()))


if __name__ == "__main__":
    main()
