"""
arabic_toolkit.py
------------------
A small, dependency-free Arabic text-processing toolkit: normalization,
tokenization, and a transparent lexicon-based sentiment classifier.

Why this exists
================
Arabic text has a specific set of normalization problems that generic
NLP tutorials (written for English) skip entirely: alef variants
(أ إ آ ا all collapsing to ا), taa marbuta vs haa (ة vs ه), alef maksura
vs yaa (ى vs ي), diacritics (tashkeel) that add noise without changing
meaning, and tatweel/kashida elongation characters used for text
justification. Getting these wrong silently breaks matching and
classification — two spellings of the same word end up looking like
different tokens.

This module handles that normalization explicitly, then layers a
simple, auditable lexicon-based sentiment classifier on top (no
black-box model — every decision traces back to a specific word in a
specific list, which matters for explainability work).

Usage
=====
    python arabic_toolkit.py                 # runs the demo below
    python arabic_toolkit.py --interactive    # classify your own text
"""

from __future__ import annotations

import argparse
import re


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

# Arabic diacritics (tashkeel) + tatweel elongation character
_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u0640]")

_ALEF_VARIANTS = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
})
_YAA_VARIANTS = str.maketrans({"ى": "ي"})
_TAA_MARBUTA = str.maketrans({"ة": "ه"})


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for matching/classification purposes:
    - strip diacritics and tatweel
    - unify alef variants (أ إ آ ٱ -> ا)
    - unify alef maksura -> yaa (ى -> ي)
    - unify taa marbuta -> haa (ة -> ه)
    - collapse repeated whitespace

    Note: taa marbuta/alef maksura normalization is a deliberate
    simplification for matching robustness (common in search/retrieval
    pipelines). It is NOT appropriate for tasks where spelling must be
    preserved exactly, e.g. generating final output text for a user.
    """
    text = _DIACRITICS.sub("", text)
    text = text.translate(_ALEF_VARIANTS)
    text = text.translate(_YAA_VARIANTS)
    text = text.translate(_TAA_MARBUTA)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    """Extract Arabic word tokens (after normalization)."""
    return re.findall(r"[\u0621-\u064A]+", normalize_arabic(text))


# ---------------------------------------------------------------------------
# Lexicon-based sentiment classifier
# ---------------------------------------------------------------------------

# Deliberately small, readable lexicons — easy to extend, easy to audit.
# All entries are stored already normalized (see normalize_arabic above).
_POSITIVE_WORDS = {
    normalize_arabic(w) for w in [
        "ممتاز", "رائع", "جميل", "شكرا", "احسنت", "ممتازة", "سريع",
        "محترف", "احترافي", "مفيد", "عظيم", "حلو", "تمام", "موفق",
    ]
}
_NEGATIVE_WORDS = {
    normalize_arabic(w) for w in [
        "سيء", "بطيء", "مشكلة", "خطأ", "ضعيف", "سئ", "متأخر",
        "معطل", "فاشل", "رديء", "مرفوض", "محبط",
    ]
}
_NEGATION_WORDS = {
    normalize_arabic(w) for w in ["مش", "لا", "ليس", "ماهوش", "مو"]
}


def classify_sentiment(text: str) -> dict:
    """
    Classify sentiment using a transparent word-matching approach with
    basic negation handling (a negation word flips the polarity of the
    word immediately following it).

    Returns a dict with the verdict and the exact words that drove the
    decision, so the output is always auditable — this matters for any
    QA/annotation-adjacent work where you need to explain a label.
    """
    tokens = tokenize(text)
    score = 0
    matched_positive: list[str] = []
    matched_negative: list[str] = []
    negate_next = False

    for token in tokens:
        if token in _NEGATION_WORDS:
            negate_next = True
            continue

        if token in _POSITIVE_WORDS:
            if negate_next:
                score -= 1
                matched_negative.append(f"{token} (negated)")
            else:
                score += 1
                matched_positive.append(token)
        elif token in _NEGATIVE_WORDS:
            if negate_next:
                score += 1
                matched_positive.append(f"{token} (negated)")
            else:
                score -= 1
                matched_negative.append(token)

        negate_next = False

    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "neutral"

    return {
        "label": label,
        "score": score,
        "matched_positive": matched_positive,
        "matched_negative": matched_negative,
    }


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------

DEMO_TEXTS = [
    "الخدمة ممتازة وسريعة جدا شكرا",
    "التطبيق بطيء ومعطل باستمرار",
    "الموضوع مش سيء فعلا",
    "استلمت الطلب امبارح",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Arabic normalization + sentiment demo.")
    parser.add_argument("--interactive", action="store_true", help="Classify your own text.")
    args = parser.parse_args()

    if args.interactive:
        print("Enter Arabic text to classify (Ctrl+C to quit):")
        while True:
            try:
                text = input("\n> ")
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break
            if not text.strip():
                continue
            result = classify_sentiment(text)
            print(f"Label: {result['label']} (score: {result['score']})")
            print(f"Positive matches: {result['matched_positive']}")
            print(f"Negative matches: {result['matched_negative']}")
    else:
        for text in DEMO_TEXTS:
            result = classify_sentiment(text)
            print(f"Text:  {text}")
            print(f"Label: {result['label']} (score: {result['score']})")
            if result["matched_positive"]:
                print(f"  + {result['matched_positive']}")
            if result["matched_negative"]:
                print(f"  - {result['matched_negative']}")
            print()


if __name__ == "__main__":
    main()
