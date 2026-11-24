# Kestrel Home: service-request router

Routes a customer's opening message to the team that will actually close it, says how sure it is, and explains why in plain English.
It does **not** use any paid API, API key or internet connection. Everything runs on a normal laptop.

## Run it (clean machine, about 2 minutes)
Needs Python 3.10 or newer.

```bash
git clone <this repo> && cd <this repo>
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open **http://127.0.0.1:5000** (the screen). Check it works: `python -m unittest tests.test_smoke`.

### Call the endpoint
```bash
curl -s -X POST http://127.0.0.1:5000/route -H "Content-Type: application/json" \
  -d '{"request_text":"installer did not turn up for cooktop i paid extra for this","product_family":"Induction Cooktop","warranty_status":"in_warranty","channel":"chat"}'
```
Only `request_text` is required. Reply fields: `recommended_team`, `confidence`, `action` (`auto_route` or `needs_clarification`), `alternatives`, `reasons`.
If the model file is missing it answers politely with HTTP 503 instead of crashing. Bad input gives HTTP 400 with a message.

## Re-create the files from the data (optional)
The customer data is **not** in this repository (policy s10: it must not be published). To rebuild with your copy of the pack:
```bash
python -m kestrel_router.train   --train train.csv --resolution resolution_log.csv --out model.joblib
python -m kestrel_router.predict --test test_unlabelled.csv --model model.joblib --out predictions.csv
python evidence.py train.csv resolution_log.csv > reports/evidence_numbers.txt
```

## What is in here
| File | What it is |
|---|---|
| `predictions.csv` | One row per test request. Team names are the current ones ("Installs & Demo", "Filters & Consumables"). |
| `memo_to_ritu.md` / `.pdf` | One-page memo for Ritu |
| `EVIDENCE.md`, `reports/evidence_numbers.txt` | How I know it works and how often it does not |
| `DECISIONS.md` | The calls I made where the brief was unclear, and the known problems |
| `app.py`, `templates/index.html` | The endpoint and the screen |
| `kestrel_router/` | Cleaning, training, prediction and the explanations |

## The one-line summary
The old bot's labels agree with where requests really ended up only **77%** of the time, so "match the labels at 90%" would copy the bot's mistakes.
This model learns from where requests actually ended up. On the last three months of history (never used for training) it is **85.7% right** versus the bot's **76.7%**,
and for the 83% of requests where it is confident it is **98% right**. About 15% of messages carry no information about what is wrong ("someone contact me about my mixer"), which caps any tool at roughly 86%.

## Expected score on the hidden outcomes
About **85.5% accuracy** against the team that closed each request (plausible range 83% to 87%). Macro-F1 about 0.85.
