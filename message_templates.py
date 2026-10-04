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


def referral_card_for_visitor(card_text):
    """Hard rule: One Thread never contacts anyone it doesn't already have
    an opted-in relationship with. This card is handed back to the
    ORIGINAL visitor to share themselves, through their own messaging app,
    in their own relationship -- never sent directly to a referred friend
    whose contact info this system never acquires or stores."""
    return f"Here's your invite to share with your friend:\n\n{card_text}"


def referral_prompt_noor():
    return "أحد الزوار ذكر صديقًا يريد الزيارة. دعوة جاهزة للإرسال -- هل أرسلها؟ ردي بـ نعم أو لا."


# Pre-written Arabic labels for the product categories Noor already knows
# about. A signal_key outside this dict means engine/semantic_match.py
# clustered a product that isn't on this list yet -- see
# product_proposal_noor_generic below, which translates the visitor's own
# words instead of inventing a label for it.
KNOWN_PRODUCT_LABELS = {
    "coffee_beans_for_sale": "بيع حبوب القهوة الخاصة بك",
    "harvest_day_experience": "تجربة 'يوم الحصاد' المدفوعة",
    "cooking_class": "دورة طبخ",
}


def product_proposal_noor(signal_key, count):
    label = KNOWN_PRODUCT_LABELS.get(signal_key, signal_key)
    return (
        f"{count} زوار سألوا الآن عن {label}. "
        f"هل تريدين تقديمها كخدمة حقيقية -- بسعرك وموعدك؟ ردي بـ نعم أو لا."
    )


def product_proposal_noor_generic(anchor_ar, count):
    """Same template shape as product_proposal_noor, but for a product not
    in KNOWN_PRODUCT_LABELS. anchor_ar is a straight translation of what
    visitors actually said (filled into the template, same as a name or
    date elsewhere) -- never model-generated commentary."""
    return (
        f"{count} زوار سألوا الآن عن نفس الشيء: \"{anchor_ar}\". "
        f"هل تريدين تقديمه كخدمة حقيقية -- بسعرك وموعدك؟ ردي بـ نعم أو لا."
    )


def unclear_flag_noor(translated_text):
    """Safety-net message for anything that doesn't clearly match one of
    the three defined doors, or that we're not confident we translated
    right -- never silently dropped, always surfaced for Noor to read
    herself. The visitor's own (translated) words are filled into the
    template; nothing here is model-generated commentary."""
    return (
        f"رسالة من زائر لم تندرج ضمن الفئات المعتادة: \"{translated_text}\". "
        f"يُرجى مراجعتها. ردي بـ نعم لتأكيد الاطلاع أو لا لتجاهلها."
    )


def feedback_prompt_visitor():
    return "Thanks for visiting! What's one thing you'd want a friend to know?"


def timing_mention_noor(visitor_name, timing):
    """Informational heads-up only -- never a booking. timing is the dict
    returned by engine/timing_extract.extract_timing(). Noor still has to
    use the structured booking form herself if she wants to act on it;
    this just makes sure she doesn't miss the mention."""
    if timing["kind"] == "named_window":
        when = f"حول '{timing['label']}' ({timing['start']} إلى {timing['end']})"
    else:
        when = f"حول \"{timing['matched_text']}\" (تاريخ محتمل: {timing['date']})"
    return (
        f"{visitor_name} ذكر/ت توقيتًا في رسالته/ا {when}. "
        f"هذه ليست حجزًا -- إذا أردتِ تثبيت حجز، استخدمي نموذج الحجز المعتاد. "
        f"ردي بـ نعم لتأكيد الاطلاع أو لا لتجاهلها."
    )
