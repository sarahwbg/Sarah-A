import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import capacity_check, classify_doors, reply_decision, threshold_watch


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
