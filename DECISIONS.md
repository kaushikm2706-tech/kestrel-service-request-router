# Decisions I had to make, and what is still wrong

## Decisions (the brief did not say)
1. **Train on where each request ended up, not on the bot's label.** The brief calls the bot's labels the ground truth. They are not: they match the closing team in only 77.2% of 10,817 closed requests. A model trained to copy them agrees with the bot 97.7% of the time and is right only 77.8%. I used `final_team` from the resolution log.
2. **Team names.** The test rows are all from July to September 2026, after the 15 Jan 2026 renames, so `predictions.csv` uses the new names. In training I mapped Installations to Installs & Demo and Consumables to Filters & Consumables, because the policy says responsibilities did not change. If the scorer expects the old names, replace those two strings.
3. **Do not promise 90%.** About 15% of messages say nothing about the problem ("complaint about room heater"). On those, the closing team looks random (best guess right about 22% of the time). Real ceiling is about 86%.
4. **Two lanes, not a straight switch-off.** Requests where the model is at least 80% sure (83% of volume, 98% right) go straight to the team. The rest get a one-question clarification first. `predictions.csv` still contains a best guess for every row because the format needs one.
5. **No AI model inside the product.** Classic text model: no per-request cost (Finance asked for this), no API key, runs offline. I did not try a large language model; the errors come from missing information in the message, not from misunderstanding it.
6. **Multi-issue messages go to the team for the last issue mentioned.** In history, when two different issues are raised, the closing team matched the last-mentioned one in 98.8% of confident cases (259 rows).
7. **Not used:** time of day, day of week (made it slightly worse), the bot's own label as an input (it will not exist after switch-off), request/order numbers (no signal).

## Data problems I found and handled
- Zoho-era text has broken characters (e.g. "Ã©", "Ã¢â‚¬Â¦"). Cleaned before training.
- Zoho resolution times are in UTC (policy s9). 26% of them were earlier than the request was created. Adding 5.5 hours fixes it (median 9.5 h, same as CRM, zero negatives). Not needed for routing; matters for any speed report.
- 5 training rows contain pasted notes instead of customer messages. Excluded.
- 663 messages are exact repeats of another message; kept (they are real volume).

## What is wrong with this (known)
- Estimate comes from one holdout (Apr-Jun 2026, 2,133 requests) and a rolling six-month check. Real July-Sep accuracy could differ by a point or two.
- The rupee figures assume a wrong route costs the same as the bot's wrong routes did (1.44 transfers + one extra contact = Rs 698). The clarification lane assumes one question costs Rs 260 and then routes correctly. Neither is measured.
- Hosting cost (about Rs 2,000 a month) is my estimate, not a quote.
- The explanation text lists the words that pushed the model; some are odd fragments ("not turn"). Readable, not polished.
- No login, no logging, no queue integration. It is a decision service, not a CRM plug-in.
- Short messages in other languages or heavy typos are untested: none exist in the history.
- The clarification question is one fixed wording, not tailored.

## Left out on purpose
Integration with the CRM, retraining schedule, a dashboard. All need information I do not have (CRM API, who owns retraining). The memo asks for them as next steps.
