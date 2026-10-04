import os
import re

# ---------------------------------------------------------------------------
# Translation is the ONLY place a neural model is allowed to run in this app.
# Everything that states a fact (counts, dates, matches) comes from
# deterministic code elsewhere -- never from this module's output.
# ---------------------------------------------------------------------------

BACKEND = os.environ.get("TRANSLATOR_BACKEND", "mock")

# Curated Arabic/English pairs so the demo translates reliably without
# needing the real model loaded. Real upgrade path: facebook/m2m100_418M.
PHRASE_PAIRS = [
    ("مرحبا، هل يمكنني زيارة المزرعة؟", "Hello, can I visit the farm?"),
    ("متى أفضل وقت للزيارة؟", "When is the best time to visit?"),
    ("أريد الحجز لخمسة أشخاص", "I want to book for five people"),
    ("سأعود السنة القادمة بالتأكيد", "I will definitely come back next year"),
    ("صديقي يريد زيارة المزرعة أيضا", "My friend also wants to visit the farm"),
    ("أتمنى لو كان بإمكاني شراء حبوب القهوة الخاصة بكم", "I wish I could buy your coffee beans"),
    (
        "أحببت المساعدة في قطف القهوة، أتمنى لو كان هذا نشاطا متاحا دائما",
        "I loved helping pick coffee, I wish that was always available",
    ),
    ("شكرا جزيلا، كانت زيارة رائعة", "Thank you so much, it was a wonderful visit"),
    ("نعم، هذا يناسبني", "Yes, that suits me"),
]


def _normalize(text):
    return re.sub(r"[\s\u200f\u200e]+", " ", text).strip().lower()


class MockTranslator:
    """Dictionary lookup for demo phrases, naive passthrough otherwise.
    Confidence is a heuristic, not a real log-probability -- see README."""

    def translate(self, text, src_lang, tgt_lang):
        norm = _normalize(text)
        for ar, en in PHRASE_PAIRS:
            if norm == _normalize(ar):
                return en, 0.95
            if norm == _normalize(en):
                return ar, 0.95
        # Unknown text: can't translate reliably -- flag low confidence
        # rather than invent a translation.
        return text, 0.3


class M2M100Translator:
    """Real model, loaded lazily. Opt-in via TRANSLATOR_BACKEND=m2m100."""

    def __init__(self):
        from transformers import pipeline

        self._pipe = pipeline("translation", model="facebook/m2m100_418M")

    def translate(self, text, src_lang, tgt_lang):
        out = self._pipe(text, src_lang=src_lang, tgt_lang=tgt_lang)
        translated = out[0]["translation_text"]
        # m2m100's pipeline doesn't expose sequence log-prob by default;
        # using a fixed placeholder until wired to real generation scores.
        confidence = 0.8
        return translated, confidence


_instance = None


def get_translator():
    global _instance
    if _instance is None:
        _instance = M2M100Translator() if BACKEND == "m2m100" else MockTranslator()
    return _instance


def translate(text, src_lang, tgt_lang):
    return get_translator().translate(text, src_lang, tgt_lang)
