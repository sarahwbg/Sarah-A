"""Bounded timing-mention extraction for visitor messages.

This is NOT booking extraction. The project's existing hard rule stays
untouched: booking date/headcount are only ever created through the
structured form in request_booking() (app.py), never guessed from free
text. What this module does is narrower and strictly informational --
it notices when a visitor's ordinary message happens to mention a date
or one of Noor's own named calendar windows (e.g. "pruning",
"coffee harvest peak" -- terms she typed herself during onboarding,
not invented here), and surfaces that as a heads-up for her to read and
act on herself. It never creates a pending booking, never calls
capacity_check.check() on Noor's behalf, and returns None -- no guess
at all -- for anything that doesn't match.

Two fixed, bounded strategies, tried in order:
1. Named-window match: does the text mention one of Noor's own window
   labels (from her onboarding profile)? This is a direct string
   match against her own words, not a model's judgment.
2. Explicit date match: dateparser.search.search_dates() finds a
   literal date/month mention (e.g. "November 20th"). dateparser is a
   deterministic parser, not a generative model -- it either finds a
   date-shaped phrase or it doesn't.
If neither matches, return None.
"""

import dateparser.search


def _match_named_window(text_en, profile):
    text = text_en.lower()
    for window in profile.get("protected_windows", []) + profile.get("recommended_windows", []):
        label = window.get("label", "")
        if label and label.lower() in text:
            return {"kind": "named_window", "label": label, "start": window["start"], "end": window["end"]}
    return None


def _match_explicit_date(text_en):
    found = dateparser.search.search_dates(
        text_en, settings={"PREFER_DATES_FROM": "future"}
    )
    if not found:
        return None
    matched_text, parsed_dt = found[0]
    return {"kind": "explicit_date", "matched_text": matched_text, "date": parsed_dt.strftime("%Y-%m-%d")}


def extract_timing(text_en, profile):
    """Returns a small dict describing a timing mention, or None if the
    message doesn't contain one. Never raises, never guesses beyond what
    the two fixed strategies above actually find."""
    named = _match_named_window(text_en, profile)
    if named:
        return named
    return _match_explicit_date(text_en)
