"""python evidence.py train.csv resolution_log.csv > reports/evidence_numbers.txt
Rolling-origin evaluation, error analysis, confidence bands and the cost arithmetic used in the memo."""
import sys, numpy as np, pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from kestrel_router import model as M

d = M.load_training_frame(sys.argv[1], sys.argv[2])
d["month"] = d.created_at_ist.str[:7]
months = sorted(d.month.unique())

print("== Rolling-origin: train on everything before month m, test on month m (last 6 months)")
rows = []
for m in months[-6:]:
    A, B = d[d.month < m], d[d.month == m]
    b = M.fit(A); P = M.predict_proba(b, B); pred = np.array(b["classes"])[P.argmax(1)]
    rows.append((m, len(B), (pred == B.final_team).mean(), (B.team_label == B.final_team).mean()))
r = pd.DataFrame(rows, columns=["month", "n", "model_acc", "old_bot_acc"]); print(r.round(3).to_string(index=False))
print("mean model %.3f  mean old bot %.3f" % (r.model_acc.mean(), r.old_bot_acc.mean()))

print("\n== Final holdout: train before 2026-04-01, test on Apr-Jun 2026")
A, B = d[d.created_at_ist < "2026-04-01"], d[d.created_at_ist >= "2026-04-01"]
b = M.fit(A); P = M.predict_proba(b, B); cls = np.array(b["classes"]); pred = cls[P.argmax(1)]; conf = P.max(1)
ok = pred == B.final_team.values
n = len(B); acc = ok.mean(); se = np.sqrt(acc * (1 - acc) / n)
z = 1.96; lo = (acc + z*z/(2*n) - z*np.sqrt(acc*(1-acc)/n + z*z/(4*n*n))) / (1 + z*z/n)
hi = (acc + z*z/(2*n) + z*np.sqrt(acc*(1-acc)/n + z*z/(4*n*n))) / (1 + z*z/n)
print("n=%d  model accuracy=%.4f (95%% CI %.3f-%.3f)   old bot=%.4f" % (n, acc, lo, hi, (B.team_label == B.final_team).mean()))
bot_only = M.fit(A.assign(final_team=A.team_label))
Pb = M.predict_proba(bot_only, B); pb = np.array(bot_only["classes"])[Pb.argmax(1)]
print("A model trained to copy the bot's labels: agrees with bot %.4f but right only %.4f" % ((pb == B.team_label).mean(), (pb == B.final_team).mean()))
print("Macro-F1: ", end=""); from sklearn.metrics import f1_score; print(round(f1_score(B.final_team, pred, average="macro"), 4))
print(classification_report(B.final_team, pred, digits=3))
print(pd.DataFrame(confusion_matrix(B.final_team, pred, labels=cls), index=cls, columns=[c[:8] for c in cls]).to_string())

print("\n== Confidence bands (holdout)")
bands = pd.cut(conf, [0, .4, .6, .8, .9, 1.0])
t = pd.DataFrame({"band": bands, "ok": ok}).groupby("band").ok.agg(["size", "mean"]); t["share"] = t["size"] / n
print(t.round(3).to_string())
auto = conf >= 0.80
print("auto-route (>=0.80): %.1f%% of requests, %.1f%% right;  needs clarification: %.1f%% of requests, %.1f%% right"
      % (100*auto.mean(), 100*ok[auto].mean(), 100*(~auto).mean(), 100*ok[~auto].mean()))
print("wrong answers that are auto-routed: %d of %d wrong (%.0f%%)" % ((~ok & auto).sum(), (~ok).sum(), 100*(~ok & auto).sum()/(~ok).sum()))

print("\n== Ceiling: what any tool could do")
vague = conf < 0.6
print("vague requests (model <60%% sure): %.1f%% of rows; best guess right %.1f%% of the time" % (100*vague.mean(), 100*ok[vague].mean()))
print("Even a perfect reader on clear rows (assume 98%%) + chance on vague => about %.1f%%" %
      (100*((1-vague.mean())*0.98 + vague.mean()*0.22)))

print("\n== Why not copy the bot: bot vs real outcome (all history)")
x = d
print("bot right on %.1f%% of all %d closed requests; transfers per request %.3f; share needing >=1 transfer %.1f%%"
      % (100*(x.team_label == x.final_team).mean(), len(x), x.transfers.mean(), 100*(x.transfers > 0).mean()))
mis = x[x.team_label != x.final_team]
print("bot-misrouted: %d (%.1f%%), mean transfers when misrouted %.2f" % (len(mis), 100*len(mis)/len(x), mis.transfers.mean()))
print(pd.crosstab(x.team_label, x.final_team).to_string())

print("\n== Money (policy s4: Rs 305 per transfer, Rs 260 extra contact per misrouted request)")
per_year = len(pd.read_csv(sys.argv[1].replace("train", "test_unlabelled"))) * 4 if False else None
vol_q = 2178                      # test file rows = Jul-Sep 2026 (one quarter)
vol_y = vol_q * 4
bot_mis = (B.team_label != B.final_team).mean()
t_per_mis = mis.transfers.mean()
cost_mis = t_per_mis * 305 + 260
def annual(rate): return vol_y * rate * cost_mis
mod_mis = 1 - acc
print("requests per year (Jul-Sep x4): %d;  cost of one misrouted request = %.2f x 305 + 260 = Rs %.0f" % (vol_y, t_per_mis, cost_mis))
print("bot misroute rate (Apr-Jun) %.3f -> Rs %.1f lakh/yr" % (bot_mis, annual(bot_mis)/1e5))
print("model misroute rate %.3f -> Rs %.1f lakh/yr (if every wrong one costs the same)" % (mod_mis, annual(mod_mis)/1e5))
print("handling saving vs bot: Rs %.1f lakh/yr; plus licence Rs 3.2 lakh; hosting ~ Rs 0.2-0.3 lakh (estimate)" % ((annual(bot_mis)-annual(mod_mis))/1e5))
lo_rate = 1 - hi; hi_rate = 1 - lo
print("saving range using the 95%% CI of accuracy: Rs %.1f to Rs %.1f lakh/yr (handling only)" % ((annual(bot_mis)-annual(hi_rate))/1e5, (annual(bot_mis)-annual(lo_rate))/1e5))
# if the unclear 17% get one clarifying contact (Rs 260) instead of a wrong route
unclear = (~auto).mean()
wrong_auto = (~ok & auto).mean()
hyb = vol_y * (wrong_auto * cost_mis + unclear * 260)
print("hybrid (auto-route >=0.80, ask the rest one question at Rs 260): Rs %.1f lakh/yr -> saving vs bot Rs %.1f lakh/yr"
      % (hyb/1e5, (annual(bot_mis)-hyb)/1e5))

print("\n== Workload by team: bot's queue vs where requests actually closed (all history, per month)")
w = pd.DataFrame({"bot_queue": x.team_label.value_counts(), "closed_by": x.final_team.value_counts()}) / 15
w["diff_%"] = 100 * (w.closed_by / w.bot_queue - 1); print(w.round(1).sort_values("closed_by", ascending=False).to_string())

print("\n== Zoho resolution-time check")
rs = pd.read_csv(sys.argv[2]); full = pd.read_csv(sys.argv[1]).merge(rs, on="request_id")
full["hrs"] = (pd.to_datetime(full.resolved_at) - pd.to_datetime(full.created_at_ist)).dt.total_seconds()/3600
print(full.groupby("source").hrs.agg(["count", "median", lambda s: (s < 0).mean()]).rename(columns={"<lambda_0>": "share_negative"}).round(2))
full.loc[full.source == "legacy_zoho", "hrs"] += 5.5
print("after adding 5.5h to Zoho rows (UTC->IST):"); print(full.groupby("source").hrs.agg(["median", lambda s: (s < 0).mean()]).round(2))
