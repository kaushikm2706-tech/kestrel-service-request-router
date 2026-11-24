# Memo to Ritu: what to do about request routing

**From:** Kaushik M  **Re:** Service-request routing, Variant B

## Decision
**Do not switch the old bot off and copy its labels. Replace it with the new router, run it alongside the bot for two weeks, then switch.** Do not set a 90% target. It cannot be reached.

## Why not 90%
The old bot's label agrees with the team that actually closed the request only **77 times in 100**. Anything trained to copy the bot copies those mistakes (I tested it: it matches the bot 98% of the time and is right 78%). About 15 in 100 customer messages say nothing about the problem ("someone contact me about my mixer"). On those, nobody, human or machine, does better than about 22%. That caps any tool at roughly **86%**.

## The number
On the last three months of history, which the router never saw: **86 right in 100 (range 84 to 87), against the bot's 77.**
When it is at least 80% sure, which is **83 in 100 requests, it is right 98 times in 100.** For the other 17 in 100, it should ask the customer one question before routing, instead of guessing.

## The rupees (per year, at about 8,700 requests)
| | Rs lakh a year |
|---|---|
| Bot's wrong routes today | about 14.2 |
| New router, guessing on everything | about 8.7. **Saving about 5.5** |
| New router + one question on unsure ones | about 4.8. **Saving about 9.4** |
| Bot licence no longer needed | 3.2 |
| Hosting (my estimate, not a quote) | 0.2 to 0.3 |
| Per-request AI charges | 0. It runs on our own machine and needs no paid service |

Based on policy: Rs 305 per transfer, Rs 260 per extra customer contact. A wrong route costs about Rs 698 (1.44 transfers plus one extra contact). **Not measured:** whether one clarifying question really costs Rs 260. The Rs 9.4 lakh figure depends on it. The Rs 5.5 lakh figure does not.

## One more finding
The bot sends about 29% of requests to Repairs as a catch-all, but only about 23% actually close there. Staff teams by where requests close, not by the bot's queue: Installs & Demo, Returns and Warranty are each 31 to 35% busier than the bot's counts suggest, Product Advice 18% busier. Repairs, Billing and Filters are 19 to 27% quieter.

## Next week
1. **Mon:** you approve a two-week shadow run: router and bot both label every request, nothing changes for customers.
2. **Tue to Fri:** IT connects the router to the helpdesk and the "ask one question" step. I need the helpdesk's connection details.
3. **End of week 2:** compare against where requests actually closed. If it is at least 84%, switch over and cancel the bot licence. If lower, tell me before switching.

## What could be wrong
My accuracy comes from one three-month test plus a six-month rolling check; July to September could differ by a point or two. The tool has not been tested on other languages or very short messages.
