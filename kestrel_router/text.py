"""Text cleaning and clause handling for Kestrel service requests."""
import re

GREETINGS = ("hi", "good morning", "namaste", "hello team")
RENAMES = {"Installations": "Installs & Demo", "Consumables": "Filters & Consumables"}
TEAMS = ["Billing", "Filters & Consumables", "Installs & Demo", "Product Advice",
         "Repairs", "Returns & Replacement", "Warranty Claims"]

# Zoho migration damaged some characters (UTF-8 read as Latin-1/cp1252).
_MOJIBAKE = [("Ã¢â‚¬Â¦", " "), ("Ã¢â‚¬â€œ", " - "), ("Ã©", "e"), ("Ã¢â‚¬â„¢", "'")]


def fix_encoding(t: str) -> str:
    for bad, good in _MOJIBAKE:
        t = t.replace(bad, good)
    return t


def normalise(t: str) -> str:
    t = fix_encoding(str(t)).lower()
    t = re.sub(r"\b(sr|ko)\d+", " ", t)       # request / order numbers carry no routing signal
    return re.sub(r"[^a-z ]", " ", t)


def clauses(raw: str):
    """Split a message into content clauses (greeting removed, split on commas)."""
    t = fix_encoding(str(raw)).lower().strip()
    parts = [p.strip() for p in t.split(", ")]
    if len(parts) > 1 and parts[0] in GREETINGS:
        parts = parts[1:]
    return [normalise(p) for p in parts if p.strip()]


def features_text(raw: str) -> str:
    """Bag-of-words with position tags: whole text + LAST clause + EARLIER clauses.

    In the history, when a message raises two different issues, the team that closes
    it is almost always the one for the LAST issue mentioned, so position matters.
    """
    cl = clauses(raw) or [""]
    last, earlier = cl[-1], cl[:-1]
    toks = ["a_" + w for w in " ".join(cl).split()]
    toks += ["L_" + w for w in last.split()]
    toks += ["L2_" + a + "_" + b for a, b in zip(last.split(), last.split()[1:])]
    toks += ["E_" + w for c in earlier for w in c.split()]
    toks.append("ncl_%d" % min(len(cl), 4))
    return " ".join(toks)
