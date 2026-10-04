# Transparent scoring over real data -- never a model's free judgment.
# Priority order IS the rule: referrals first (time-sensitive by nature),
# then newly-crossed demand thresholds, then plain booking confirmations.
# Month-over-month comparison is out of scope for a new operator with no
# history yet -- see README (moonshot item).


def most_important_item(pending_actions):
    pending = [a for a in pending_actions if a["status"] == "pending"]

    referrals = [a for a in pending if a["type"] == "referral_card"]
    if referrals:
        return referrals[0]

    proposals = [a for a in pending if a["type"] == "product_proposal"]
    if proposals:
        return proposals[0]

    bookings = [a for a in pending if a["type"] == "booking_confirm"]
    if bookings:
        return bookings[0]

    return None
