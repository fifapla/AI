# arabic_toolkit.py — Arabic normalization + lexicon-based sentiment

A small, dependency-free toolkit for Arabic text: normalization
(handling alef variants, taa marbuta, alef maksura, diacritics, and
tatweel) plus a transparent, auditable sentiment classifier with
negation handling.

## Why

Arabic text normalization is a real, specific problem that most NLP
tutorials (written for English) never cover — and getting it wrong
silently breaks matching and classification, because two spellings of
the same word end up looking like different tokens.

The sentiment classifier is intentionally lexicon-based rather than a
black-box model: every label traces back to specific matched words,
which matters for any QA/annotation-adjacent work where a decision
needs to be explainable.

## Run it

```bash
python arabic_toolkit.py                 # runs demo texts
python arabic_toolkit.py --interactive    # classify your own text
```

## What it demonstrates

- Explicit Arabic normalization rules (alef unification, taa marbuta,
  alef maksura, diacritics/tatweel stripping) with documented
  trade-offs (normalization is for matching, not for final output text)
- A lexicon-based classifier with basic negation handling ("مش سيء"
  correctly flips to positive)
- Auditable output: every classification returns the exact words that
  drove the decision, not just a label

## Known limitation

The classifier matches whole tokens, so a word with an attached
conjunction prefix (e.g. `ومعطل` = "و" + "معطل") won't match the base
lexicon entry `معطل` unless the prefix is stripped first. A real
Arabic stemmer (handling prefixes/suffixes) would fix this — left out
here to keep the normalization logic readable rather than comprehensive.

## Extending it

- Add a proper Arabic stemmer/light-stemmer for prefix/suffix handling
- Grow the sentiment lexicons (currently intentionally small and
  readable)
- Swap the lexicon classifier for a real model while keeping the
  normalization layer — it's model-agnostic by design
