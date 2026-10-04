THRESHOLD = 3


def record_signal(counters, signal_key):
    counters["counts"][signal_key] = counters["counts"].get(signal_key, 0) + 1
    return counters["counts"][signal_key]


def check_crossed(counters, signal_key, count):
    already_notified = signal_key in counters["notified"]
    if count >= THRESHOLD and not already_notified:
        counters["notified"].append(signal_key)
        return True
    return False
