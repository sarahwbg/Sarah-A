# All outbound text is a filled template -- never model-generated.


def booking_request_noor(visitor_name, requested_date, headcount, capacity_result):
    if capacity_result["status"] == "protected_conflict":
        message = (
            f"طلب حجز من {visitor_name}: {requested_date}، "
            f"{headcount} ضيوف. هذا الأسبوع عادة "
            f"'{capacity_result['window_label']}'. هل ما زلتِ تريدين الاستضافة، "
            f"أم تقترحين تاريخًا آخر؟"
        )
    else:
        suggestion = capacity_result.get("suggestion")
        message = f"طلب حجز من {visitor_name}: {requested_date}، {headcount} ضيوف. هل توافقين؟"
        if suggestion:
            message += (
                f" (ملاحظة: {suggestion['label']} يبدأ خلال حوالي "
                f"{suggestion['weeks_away']} أسابيع، في حال أردتِ اقتراح ذلك بدلاً من هذا.)"
            )
    return message + " ردي بـ نعم أو لا."


def booking_confirmed_visitor(requested_date, headcount):
    return f"Confirmed! See you on {requested_date} for {headcount}."


def booking_declined_visitor(requested_date):
    return f"Unfortunately {requested_date} doesn't work -- let's find another date."


def referral_card_draft(visitor_name, referred_hint):
    return (
        f"{visitor_name} thought you'd enjoy a visit to Noor's farm in the Ondera "
        f"highlands -- coffee tasting, farm walks, and homestay stays. "
        f"Message this number to plan your visit."
    )


def referral_prompt_noor():
    return "أحد الزوار ذكر صديقًا يريد الزيارة. دعوة جاهزة للإرسال -- هل أرسلها؟ ردي بـ نعم أو لا."


def product_proposal_noor(signal_key, count):
    labels = {
        "coffee_beans_for_sale": "بيع حبوب القهوة الخاصة بك",
        "harvest_day_experience": "تجربة 'يوم الحصاد' المدفوعة",
        "cooking_class": "دورة طبخ",
    }
    label = labels.get(signal_key, signal_key)
    return (
        f"{count} زوار سألوا الآن عن {label}. "
        f"هل تريدين تقديمها كخدمة حقيقية -- بسعرك وموعدك؟ ردي بـ نعم أو لا."
    )


def feedback_prompt_visitor():
    return "Thanks for visiting! What's one thing you'd want a friend to know?"
