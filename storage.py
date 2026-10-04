import json
import os
import uuid

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
THREADS_DIR = os.path.join(DATA_DIR, "threads")


def _path(name):
    return os.path.join(DATA_DIR, name)


def load_json(name, default):
    path = _path(name)
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save_json(name, data):
    with open(_path(name), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_profile():
    return load_json("noor_profile.json", None)


def save_profile(profile):
    save_json("noor_profile.json", profile)


def list_visitor_ids():
    if not os.path.isdir(THREADS_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(THREADS_DIR) if f.endswith(".json"))


def load_thread(visitor_id):
    path = os.path.join(THREADS_DIR, f"{visitor_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_thread(thread):
    os.makedirs(THREADS_DIR, exist_ok=True)
    path = os.path.join(THREADS_DIR, f"{thread['visitor_id']}.json")
    with open(path, "w") as f:
        json.dump(thread, f, indent=2, ensure_ascii=False)


def new_thread(name):
    visitor_id = uuid.uuid4().hex[:8]
    thread = {
        "visitor_id": visitor_id,
        "name": name or f"Visitor {visitor_id}",
        "messages": [],
        "visited": False,
        "feedback": None,
    }
    save_thread(thread)
    return thread


def load_pending_actions():
    return load_json("pending_actions.json", [])


def save_pending_actions(actions):
    save_json("pending_actions.json", actions)


def load_feedback_log():
    return load_json("feedback_log.json", [])


def save_feedback_log(log):
    save_json("feedback_log.json", log)


def load_demand_counters():
    data = load_json("demand_counters.json", {"counts": {}, "notified": [], "clusters": {}})
    data.setdefault("clusters", {})
    return data


def save_demand_counters(data):
    save_json("demand_counters.json", data)


def load_sent_log():
    return load_json("sent_log.json", [])


def save_sent_log(log):
    save_json("sent_log.json", log)
