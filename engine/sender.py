import datetime

from storage import load_sent_log, save_sent_log

# Abstracted so a real provider (Twilio, Africa's Talking) can be plugged
# in later -- this only logs, nothing is actually sent in this build.


def send(visitor_id, text):
    log = load_sent_log()
    log.append(
        {
            "visitor_id": visitor_id,
            "text": text,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_sent_log(log)
    print(f"[SENT to {visitor_id}] {text}")
