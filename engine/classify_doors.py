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

DOOR_LABELS = {
    "returning": "Returning customer",
    "referral": "Referral",
    "new_product": "New product idea",
    "none": "No signal",
}


def classify(translated_text_en):
    text = translated_text_en.lower()

    for phrase, signal_key in NEW_PRODUCT_PATTERNS.items():
        if phrase in text:
            return {"door": "new_product", "signal_key": signal_key}

    for kw in REFERRAL_KEYWORDS:
        if kw in text:
            return {"door": "referral", "signal_key": None}

    for kw in RETURNING_KEYWORDS:
        if kw in text:
            return {"door": "returning", "signal_key": None}

    return {"door": "none", "signal_key": None}
