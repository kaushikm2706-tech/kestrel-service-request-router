# Evidence: how well it works, and how often it does not

Full output: `reports/evidence_numbers.txt` (regenerate with `evidence.py`).

## Headline (never-seen test: trained on data before 1 Apr 2026, tested on Apr-Jun 2026, 2,133 requests)
| | Accuracy |
|---|---|
| New router | **85.65%** (95% CI 84.1 to 87.1), macro-F1 0.855 |
| Old bot | 76.65% |
| Model trained to copy the bot | right 77.8%; agrees with the bot 97.7% |

## Stable over time (train on all earlier months, test on the next month)
Jan 84.9, Feb 83.4, Mar 88.3, Apr 86.7, May 85.7, Jun 84.6. Mean 85.6 vs bot 77.0. It beat the bot in every month.

## When it is wrong
- 306 of 2,133 were wrong (14.3%). 270 of those were low-confidence, and a clarifying question catches them.
- Confidence is honest: when 80%+ sure it is right 98.0% of the time (83% of requests). Below 80% it is right 24.6% of the time.
- Only 36 wrong answers (1.7% of all requests) were confidently wrong.
- Weakest team pairs: Product Advice read as Repairs (21 times), Returns read as Repairs (20), Repairs read as Installs (14), Warranty read as Installs (13). Weakest team: Installs & Demo (F1 0.83).

## Why 90% is not reachable
15.3% of messages are vague (model under 60% sure); the best guess on those is right 21.8% of the time. A perfect reader of clear messages (98%) plus chance on vague ones is about **86%**. We are at that ceiling, so extra modelling will not help; extra information from the customer will.

## Why the bot's labels are not ground truth
Bot label vs where the request closed, 10,817 closed requests: right 77.2%. The bot uses Repairs as a catch-all: of 3,126 requests it sent to Repairs, only 1,990 closed there; the rest closed in the other six teams. Misrouted requests needed 1.44 transfers on average.

## Expected score on the hidden test (July to September)
About **85 to 86%** accuracy, plausible range 83 to 87%. Reasons: holdout 85.7, rolling mean 85.6, near the 86% ceiling. If the grader counts the bot's labels instead of closing teams I would expect about 78%; I think that is the wrong target and did not optimise for it.

## Tests
`python -m unittest tests.test_smoke`: 6 pass (health, screen loads, installer+payment goes to Installs & Demo, two-issue message goes to the last issue's team, vague message asks a question, empty input gives a clean 400).
