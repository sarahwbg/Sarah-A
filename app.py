import datetime
import uuid

from flask import Flask, redirect, render_template, request, url_for

import message_templates as tmpl
import storage
from engine import (
    capacity_check,
    classify_doors,
    proactive_rules,
    reply_decision,
    semantic_match,
    sender,
    threshold_watch,
    timing_extract,
    translate,
)

app = Flask(__name__)


@app.route("/")
def index():
    profile = storage.load_profile()
    if not profile or not profile.get("onboarded"):
        return redirect(url_for("onboarding"))

    visitor_ids = storage.list_visitor_ids()
    threads = [storage.load_thread(v) for v in visitor_ids]
    pending = storage.load_pending_actions()
    top_item = proactive_rules.most_important_item(pending)

    return render_template(
        "index.html",
        profile=profile,
        threads=threads,
        top_item=top_item,
        pending_count=len([a for a in pending if a["status"] == "pending"]),
    )


@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if request.method == "POST":
        profile = {
            "name": "Noor",
            "onboarded": True,
            "protected_windows": (
                [
                    {
                        "label": request.form["protected_label"],
                        "start": request.form["protected_start"],
                        "end": request.form["protected_end"],
                    }
                ]
                if request.form.get("protected_label")
                else []
            ),
            "recommended_windows": (
                [
                    {
                        "label": request.form["recommended_label"],
                        "start": request.form["recommended_start"],
                        "end": request.form["recommended_end"],
                    }
                ]
                if request.form.get("recommended_label")
                else []
            ),
            "offerings": [
                o.strip() for o in request.form.get("offerings", "").split(",") if o.strip()
            ],
        }
        storage.save_profile(profile)
        return redirect(url_for("index"))

    profile = storage.load_profile() or {}
    return render_template("onboarding.html", profile=profile)


@app.route("/thread/new", methods=["POST"])
def new_thread():
    name = request.form.get("name", "").strip()
    thread = storage.new_thread(name)
    return redirect(url_for("thread_view", visitor_id=thread["visitor_id"]))


@app.route("/thread/<visitor_id>")
def thread_view(visitor_id):
    thread = storage.load_thread(visitor_id)
    pending = [a for a in storage.load_pending_actions() if a["visitor_id"] == visitor_id]
    profile = storage.load_profile()
    return render_template("thread.html", thread=thread, pending=pending, profile=profile)


@app.route("/thread/<visitor_id>/message", methods=["POST"])
def send_message(visitor_id):
    thread = storage.load_thread(visitor_id)
    text = request.form["text"].strip()
    sender_role = request.form["sender_role"]
    lang = request.form["lang"]

    tgt_lang = "en" if lang == "ar" else "ar"
    translated_text, confidence = translate.translate(text, lang, tgt_lang)

    thread["messages"].append(
        {
            "from": sender_role,
            "lang": lang,
            "original": text,
            "translated": translated_text,
            "confidence": confidence,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        }
    )
    storage.save_thread(thread)

    # Heads-up only, never a booking -- see engine/timing_extract.py. The
    # structured form in request_booking() remains the only way an actual
    # booking gets created.
    if sender_role == "visitor":
        translated_en = translated_text if tgt_lang == "en" else text
        profile = storage.load_profile()
        timing = timing_extract.extract_timing(translated_en, profile) if profile else None
        if timing:
            pending = storage.load_pending_actions()
            pending.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "type": "timing_mention",
                    "visitor_id": visitor_id,
                    "status": "pending",
                    "payload": {
                        "message_to_noor": tmpl.timing_mention_noor(thread["name"], timing),
                    },
                    "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
                }
            )
            storage.save_pending_actions(pending)

    # Noor answering a pending action is a normal text reply, not a button
    # click -- this is what makes "reply YES or NO" actually work over SMS.
    if sender_role == "noor":
        decision = reply_decision.match_decision(text)
        if decision:
            pending = storage.load_pending_actions()
            open_actions = sorted(
                (a for a in pending if a["visitor_id"] == visitor_id and a["status"] == "pending"),
                key=lambda a: a["created_at"],
            )
            if open_actions:
                apply_decision(open_actions[0], decision)
                storage.save_pending_actions(pending)

    return redirect(url_for("thread_view", visitor_id=visitor_id))


@app.route("/thread/<visitor_id>/book", methods=["POST"])
def request_booking(visitor_id):
    thread = storage.load_thread(visitor_id)
    profile = storage.load_profile()
    requested_date = request.form["date"]
    headcount = request.form["headcount"]

    result = capacity_check.check(requested_date, profile)
    message = tmpl.booking_request_noor(thread["name"], requested_date, headcount, result)

    pending = storage.load_pending_actions()
    pending.append(
        {
            "id": uuid.uuid4().hex[:8],
            "type": "booking_confirm",
            "visitor_id": visitor_id,
            "status": "pending",
            "payload": {
                "date": requested_date,
                "headcount": headcount,
                "capacity_status": result["status"],
                "message_to_noor": message,
            },
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
    )
    storage.save_pending_actions(pending)

    return redirect(url_for("thread_view", visitor_id=visitor_id))


def apply_decision(action, decision):
    """Shared by the browser YES/NO buttons and Noor's real text replies --
    one place that turns an approve/decline into the actual side effect."""
    action["status"] = "approved" if decision == "approve" else "declined"
    visitor_id = action["visitor_id"]
    if decision == "approve":
        if action["type"] == "booking_confirm":
            msg = tmpl.booking_confirmed_visitor(action["payload"]["date"], action["payload"]["headcount"])
            sender.send(visitor_id, msg)
        elif action["type"] == "referral_card":
            # Hard rule: One Thread never contacts anyone it doesn't already
            # have an opted-in relationship with. The card goes back to the
            # ORIGINAL visitor to share themselves -- never sent directly to
            # a referred friend, whose contact info this system never
            # acquires or stores in the first place.
            sender.send(visitor_id, tmpl.referral_card_for_visitor(action["payload"]["card_text"]))
        elif action["type"] == "product_proposal":
            profile = storage.load_profile()
            name = action["payload"]["proposed_offering_name"]
            if name not in profile["offerings"]:
                profile["offerings"].append(name)
                storage.save_profile(profile)
    else:
        if action["type"] == "booking_confirm":
            sender.send(visitor_id, tmpl.booking_declined_visitor(action["payload"]["date"]))


@app.route("/pending/<action_id>/decide", methods=["POST"])
def decide_pending(action_id):
    decision = request.form["decision"]
    pending = storage.load_pending_actions()
    action = next(a for a in pending if a["id"] == action_id)
    apply_decision(action, decision)
    storage.save_pending_actions(pending)
    return redirect(url_for("thread_view", visitor_id=action["visitor_id"]))


@app.route("/thread/<visitor_id>/feedback", methods=["POST"])
def submit_feedback(visitor_id):
    thread = storage.load_thread(visitor_id)
    text = request.form["text"].strip()
    lang = request.form["lang"]
    tgt_lang = "en" if lang == "ar" else "ar"
    translated_text, confidence = translate.translate(text, lang, tgt_lang)
    translated_en = translated_text if tgt_lang == "en" else text

    result = classify_doors.classify(translated_en)
    if confidence < classify_doors.LOW_CONFIDENCE_THRESHOLD:
        # Don't trust a door match built on a translation we're not
        # confident in -- fall through to the unclear-flag safety net below
        # instead of acting on it.
        result = {"door": "none", "signal_key": None}

    counters = storage.load_demand_counters()
    if result["door"] == "new_product" and not result["signal_key"]:
        result["signal_key"], counters["clusters"] = semantic_match.resolve_signal_key(
            translated_en, counters["clusters"]
        )

    thread["feedback"] = {
        "raw": text,
        "translated_en": translated_en,
        "door": result["door"],
        "confidence": confidence,
    }
    thread["visited"] = True
    storage.save_thread(thread)

    log = storage.load_feedback_log()
    log.append(
        {
            "visitor_id": visitor_id,
            "door": result["door"],
            "signal_key": result["signal_key"],
            "raw_text": text,
            "translated_text": translated_en,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        }
    )
    storage.save_feedback_log(log)

    pending = storage.load_pending_actions()

    if result["door"] == "none":
        pending.append(
            {
                "id": uuid.uuid4().hex[:8],
                "type": "unclear_flag",
                "visitor_id": visitor_id,
                "status": "pending",
                "payload": {
                    "message_to_noor": tmpl.unclear_flag_noor(translated_en),
                },
                "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
            }
        )

    if result["door"] == "referral":
        pending.append(
            {
                "id": uuid.uuid4().hex[:8],
                "type": "referral_card",
                "visitor_id": visitor_id,
                "status": "pending",
                "payload": {
                    "card_text": tmpl.referral_card_draft(thread["name"], "their friend"),
                    "message_to_noor": tmpl.referral_prompt_noor(),
                },
                "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
            }
        )

    if result["door"] == "new_product" and result["signal_key"]:
        signal_key = result["signal_key"]
        count = threshold_watch.record_signal(counters, signal_key)
        crossed = threshold_watch.check_crossed(counters, signal_key, count)
        if crossed:
            if signal_key in tmpl.KNOWN_PRODUCT_LABELS:
                proposed_name = signal_key.replace("_", " ").title()
                message_to_noor = tmpl.product_proposal_noor(signal_key, count)
            else:
                anchor_text = counters["clusters"][signal_key]["anchor_text"]
                anchor_ar, _ = translate.translate(anchor_text, "en", "ar")
                proposed_name = anchor_text.title()
                message_to_noor = tmpl.product_proposal_noor_generic(anchor_ar, count)
            pending.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "type": "product_proposal",
                    "visitor_id": visitor_id,
                    "status": "pending",
                    "payload": {
                        "signal_key": signal_key,
                        "count": count,
                        "proposed_offering_name": proposed_name,
                        "message_to_noor": message_to_noor,
                    },
                    "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
                }
            )

    storage.save_demand_counters(counters)
    storage.save_pending_actions(pending)
    return redirect(url_for("thread_view", visitor_id=visitor_id))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
