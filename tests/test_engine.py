import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import capacity_check, classify_doors, reply_decision, semantic_match, threshold_watch, timing_extract


def test_capacity_protected():
    profile = {
        "protected_windows": [{"label": "pruning", "start": "2026-10-15", "end": "2026-10-25"}],
        "recommended_windows": [],
    }
    result = capacity_check.check("2026-10-20", profile)
    assert result["status"] == "protected_conflict"
    assert result["window_label"] == "pruning"


def test_capacity_ok():
    profile = {"protected_windows": [], "recommended_windows": []}
    result = capacity_check.check("2026-10-20", profile)
    assert result["status"] == "ok"


def test_classify_new_product():
    result = classify_doors.classify("I wish I could buy your coffee beans")
    assert result["door"] == "new_product"
    assert result["signal_key"] == "coffee_beans_for_sale"


def test_classify_referral():
    result = classify_doors.classify("my friend also wants to visit")
    assert result["door"] == "referral"


def test_classify_none():
    result = classify_doors.classify("thank you so much")
    assert result["door"] == "none"


def test_classify_new_product_generic_trigger_has_no_signal_key_yet():
    # Unnamed-product phrasing is still recognized as the New Product door,
    # but naming WHICH product is deferred to semantic_match, not guessed
    # here -- so signal_key comes back empty on purpose.
    result = classify_doors.classify("do you sell honey?")
    assert result["door"] == "new_product"
    assert result["signal_key"] is None


def test_semantic_match_clusters_same_product_different_phrasing():
    clusters = {}
    key1, clusters = semantic_match.resolve_signal_key("do you sell honey", clusters)
    key2, clusters = semantic_match.resolve_signal_key(
        "the honey was incredible, I'd pay for a jar", clusters
    )
    assert key1 == key2
    assert len(clusters) == 1


def test_semantic_match_splits_different_products():
    clusters = {}
    key1, clusters = semantic_match.resolve_signal_key("do you sell honey", clusters)
    key2, clusters = semantic_match.resolve_signal_key("do you sell your jam", clusters)
    assert key1 != key2
    assert len(clusters) == 2


def test_reply_decision_yes_no():
    assert reply_decision.match_decision("نعم") == "approve"
    assert reply_decision.match_decision("  Yes ") == "approve"
    assert reply_decision.match_decision("لا") == "decline"
    assert reply_decision.match_decision("no") == "decline"


def test_reply_decision_unrelated_text():
    assert reply_decision.match_decision("Can I come next week instead?") is None


def test_threshold_crosses_once():
    counters = {"counts": {}, "notified": []}
    for _ in range(2):
        count = threshold_watch.record_signal(counters, "coffee_beans_for_sale")
        assert threshold_watch.check_crossed(counters, "coffee_beans_for_sale", count) is False
    count = threshold_watch.record_signal(counters, "coffee_beans_for_sale")
    assert threshold_watch.check_crossed(counters, "coffee_beans_for_sale", count) is True
    count = threshold_watch.record_signal(counters, "coffee_beans_for_sale")
    assert threshold_watch.check_crossed(counters, "coffee_beans_for_sale", count) is False


def test_timing_extract_named_window():
    profile = {
        "protected_windows": [{"label": "pruning", "start": "2026-10-15", "end": "2026-10-25"}],
        "recommended_windows": [{"label": "coffee harvest peak", "start": "2026-11-14", "end": "2026-12-05"}],
    }
    result = timing_extract.extract_timing("is it ok to come during coffee harvest peak?", profile)
    assert result["kind"] == "named_window"
    assert result["label"] == "coffee harvest peak"


def test_timing_extract_explicit_date():
    profile = {"protected_windows": [], "recommended_windows": []}
    result = timing_extract.extract_timing("could we visit around November 20th?", profile)
    assert result["kind"] == "explicit_date"
    assert result["date"] == "2026-11-20"


def test_timing_extract_none():
    profile = {"protected_windows": [], "recommended_windows": []}
    result = timing_extract.extract_timing("just saying hello", profile)
    assert result is None
