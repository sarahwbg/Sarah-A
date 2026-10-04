# Fixed, pre-written categories only -- this module NEVER generates text.
# "the complete set of things your tool is allowed to say" per the brief.

RETURNING_KEYWORDS = [
    "come back",
    "next season",
    "next year",
    "visit again",
    "return again",
    "see you again",
]

REFERRAL_KEYWORDS = [
    "my friend",
    "my brother",
    "my sister",
    "my colleague",
    "tell my",
    "bring my",
    "should visit",
    "would love this place",
]

# Fixed phrase -> signal key. Only known phrases count; anything else
# falls through to "none" rather than inventing a new category.
NEW_PRODUCT_PATTERNS = {
    "buy your coffee beans": "coffee_beans_for_sale",
    "buy the coffee beans": "coffee_beans_for_sale",
    "help pick coffee": "harvest_day_experience",
    "helping pick coffee": "harvest_day_experience",
    "harvest day": "harvest_day_experience",
    "cooking class": "cooking_class",
    "learn to cook": "cooking_class",
}

# Fixed, deterministic phrases that signal "wants to buy/pay for something"
# WITHOUT naming which product -- still a fixed keyword list, same
# discipline as everything else in this module. When one of these matches
# and no specific NEW_PRODUCT_PATTERNS phrase did, signal_key comes back
# as None and engine/semantic_match.py resolves WHICH product it is by
# comparing against previously-seen mentions, instead of this module
# guessing at a name.
GENERIC_NEW_PRODUCT_TRIGGERS = [
    "wish i could buy",
    "do you sell",
    "would pay for",
    "i'd pay for",
    "i would pay for",
    "can i buy",
    "could i buy",
    "would buy",
]

DOOR_LABELS = {
    "returning": "Returning customer",
    "referral": "Referral",
    "new_product": "New product idea",
    "none": "No signal",
}

# Matches templates/thread.html's existing low-confidence translation
# display cutoff. A translation we're not confident in shouldn't be
# trusted enough to route into a specific door either -- see app.py's
# "unclear_flag" handling.
LOW_CONFIDENCE_THRESHOLD = 0.6


def classify(translated_text_en):
    text = translated_text_en.lower()

    for phrase, signal_key in NEW_PRODUCT_PATTERNS.items():
        if phrase in text:
            return {"door": "new_product", "signal_key": signal_key}

    for phrase in GENERIC_NEW_PRODUCT_TRIGGERS:
        if phrase in text:
            return {"door": "new_product", "signal_key": None}

    for kw in REFERRAL_KEYWORDS:
        if kw in text:
            return {"door": "referral", "signal_key": None}

    for kw in RETURNING_KEYWORDS:
        if kw in text:
            return {"door": "returning", "signal_key": None}

    return {"door": "none", "signal_key": None}
