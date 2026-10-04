from datetime import date, datetime


def _parse(d):
    return datetime.strptime(d, "%Y-%m-%d").date()


def _in_window(check_date, window):
    return _parse(window["start"]) <= check_date <= _parse(window["end"])


def check(requested_date_str, profile):
    requested = _parse(requested_date_str)

    for window in profile.get("protected_windows", []):
        if _in_window(requested, window):
            return {"status": "protected_conflict", "window_label": window["label"]}

    suggestion = None
    for window in profile.get("recommended_windows", []):
        if not _in_window(requested, window):
            start = _parse(window["start"])
            if start > date.today():
                weeks = (start - date.today()).days // 7
                suggestion = {
                    "label": window["label"],
                    "start": window["start"],
                    "weeks_away": weeks,
                }
            break

    return {"status": "ok", "suggestion": suggestion}
