"""python -m kestrel_router.train --train train.csv --resolution resolution_log.csv --out model.joblib"""
import argparse, json
import numpy as np, pandas as pd
from . import model as M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--resolution", required=True)
    ap.add_argument("--out", default="model.joblib")
    a = ap.parse_args()
    d = M.load_training_frame(a.train, a.resolution)
    cut = "2026-04-01"
    A, B = d[d.created_at_ist < cut], d[d.created_at_ist >= cut]
    b = M.fit(A)
    P = M.predict_proba(b, B)
    pred = np.array(b["classes"])[P.argmax(1)]
    print("time-split check (train before %s, test on the last 3 months): n=%d  accuracy vs where it ended up = %.4f"
          % (cut, len(B), (pred == B.final_team).mean()))
    print("old bot on the same rows: %.4f" % (B.team_label == B.final_team).mean())
    full = M.fit(d)
    M.save(full, a.out)
    print("trained on %d rows, saved %s" % (len(d), a.out))


if __name__ == "__main__":
    main()
