"""Semantic de-duplication for the New Product door.

classify_doors.py only detects THAT a message expresses interest in an
unnamed new product (generic phrases like "do you sell X" or "wish I
could buy X"). It deliberately does NOT try to name X -- that would mean
guessing at free text, which this project's whole architecture avoids.

This module resolves WHAT product, by comparing the already-translated
English text against previously-seen mentions and clustering similar
ones together -- so "do you sell honey" and "the honey was incredible,
I'd pay for a jar" count as the same repeated demand instead of two
separate, uncounted signals.

Uses sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (118M
params), loaded once and cached in-process. Runs fully offline after the
model's one-time download, same pattern as engine/translate.py's m2m100
backend. This module NEVER generates text -- it only measures similarity
between text visitors already said, and the threshold below is a fixed,
visible config value, not a model's free judgment call -- same
discipline as the door classifier and the demand threshold itself.
"""

import math
import re
import uuid

from engine import classify_doors

SIMILARITY_THRESHOLD = 0.55

_FILLER_LEAD = re.compile(r"^(the|a|an|your|my|some)\s+")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def embed(text):
    return _get_model().encode(text).tolist()


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def extract_anchor(message_text):
    """Strip the matched generic trigger phrase (and leading filler words)
    from a New Product door message, isolating the product noun-phrase
    before embedding. Whole-sentence comparison alone wasn't precise
    enough in testing: two different products wrapped in the same trigger
    phrase (e.g. "do you sell honey" vs "do you sell jam") scored too
    similar to each other, because the shared wrapper phrase dominated the
    sentence embedding. This is deterministic string trimming only -- it
    never guesses or invents the product name, just removes the part of
    the sentence that isn't it.
    """
    t = message_text.lower().strip("? .!")
    for trig in classify_doors.GENERIC_NEW_PRODUCT_TRIGGERS:
        if trig in t:
            t = t.replace(trig, " ")
    t = re.sub(r"\s+", " ", t).strip(" ,.")
    t = _FILLER_LEAD.sub("", t)
    return t if t else message_text


def resolve_signal_key(message_text, clusters):
    """clusters: dict of signal_key -> {"anchor_text": str, "embedding": [float, ...]}

    Returns (signal_key, clusters). If message_text's extracted anchor is
    similar enough (>= SIMILARITY_THRESHOLD) to an existing cluster's
    anchor, that cluster's key is reused and the count against it keeps
    growing. Otherwise a new cluster is created and clusters is updated in
    place.
    """
    anchor_text = extract_anchor(message_text)
    new_embedding = embed(anchor_text)
    best_key, best_score = None, 0.0
    for key, data in clusters.items():
        score = _cosine(new_embedding, data["embedding"])
        if score > best_score:
            best_key, best_score = key, score
    if best_key is not None and best_score >= SIMILARITY_THRESHOLD:
        return best_key, clusters
    new_key = f"demand_{uuid.uuid4().hex[:8]}"
    clusters[new_key] = {"anchor_text": anchor_text, "embedding": new_embedding}
    return new_key, clusters
