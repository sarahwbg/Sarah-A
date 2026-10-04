# Deterministic yes/no matcher for Noor's plain-text SMS replies to a
# pending action -- same "fixed set, no model" pattern as classify_doors.py.
# This is what lets her just type a normal reply instead of pressing a button.

YES_WORDS = {"نعم", "ايوه", "أيوه", "ايه", "آه", "اه", "yes", "y", "ok", "okay"}
NO_WORDS = {"لا", "لأ", "no", "n"}


def match_decision(text):
    normalized = text.strip().lower()
    if normalized in YES_WORDS:
        return "approve"
    if normalized in NO_WORDS:
        return "decline"
    return None
