"""Shared helpers for the dub: text normalisation for QA and for the forced aligner."""
import re

from num2words import num2words

BRANDS = {
    "minichat": "manychat",
    "manychats": "manychat",
    "manysetters": "manysetter",
    "minisetter": "manysetter",
    "calendlys": "calendly",
    "calumly": "calendly",
    "econ": "ecom",
    "ecommerce": "ecommerce",
}


def _num(m: re.Match) -> str:
    raw = m.group(0)
    cur = ""
    if raw.startswith("$"):
        cur, raw = " dollars", raw[1:]
    elif raw.startswith("€"):
        cur, raw = " euros", raw[1:]
    k = ""
    if raw[-1:] in "kK":
        k, raw = " k", raw[:-1]
    raw = raw.replace(",", "")
    try:
        n = float(raw) if "." in raw else int(raw)
    except ValueError:
        return m.group(0)
    return f" {num2words(n)}{k}{cur} "


def spoken(text: str) -> str:
    """Text as it is pronounced (numbers, currencies, a.m., brands, domains)."""
    t = text.replace("’", "'").replace("…", " ")
    t = re.sub(r"(?i)\bmany\s?setter\.com\b", "many setter dot com", t)
    t = re.sub(r"(?i)\bmanysetter\b", "many setter", t)
    t = re.sub(r"(?i)\bmanychat\b", "many chat", t)
    t = re.sub(r"(?i)\bwhatsapp\b", "whats app", t)
    t = re.sub(r"(?i)\ba\.m\.", "a m", t)
    t = re.sub(r"(?i)\bAPI\b", "a p i", t)
    t = re.sub(r"(?i)\bPDFs\b", "p d fs", t)
    t = re.sub(r"(?i)\bAI\b", "a i", t)
    t = re.sub(r"[$€]?\d[\d,]*(?:\.\d+)?[kK]?", _num, t)
    t = t.replace("-", " ")
    return re.sub(r"\s+", " ", t).strip()


def norm_words(text: str) -> list[str]:
    """Comparable word list for QA (both the script and whisper's transcript go through it)."""
    t = spoken(text).lower()
    t = re.sub(r"\b(dollar|euro)\b", r"\1s", t)
    # casual spoken forms are fine in a YouTube voice
    t = re.sub(r"\bgonna\b", "going to", t)
    t = re.sub(r"\bwanna\b", "want to", t)
    t = re.sub(r"\bgotta\b", "got to", t)
    for a, b in ((r"\ba i\b", "ai"), (r"\bmany chat\b", "manychat"), (r"\bmany setter\b", "manysetter"),
                 (r"\bwhats app\b", "whatsapp"), (r"\be com\b", "ecom"), (r"\be commerce\b", "ecommerce"), (r"\ba m\b", "am"), (r"\bp m\b", "pm"),
                 (r"\bset up\b", "setup")):
        t = re.sub(a, b, t)
    ws = re.findall(r"[a-z0-9']+", t)
    ws = [w.strip("'") for w in ws]
    return [BRANDS.get(w, w) for w in ws if w]
