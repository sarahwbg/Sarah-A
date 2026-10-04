# One Thread -- Noor's Farm (Small AI for Development prototype)

A single bilingual message thread per visitor that handles discovery,
booking, feedback, and follow-up for a smallholder farm-tourism host,
built around a calendar-aware conversation and a fixed-category
feedback classifier -- not a general-purpose chatbot.

## Honesty notes (read before demoing)

- **Translation is mocked by default.** `engine/translate.py` ships with
  a curated Arabic/English phrase dictionary so the demo is reliable.
  The real model (`facebook/m2m100_418M`) is wired in and can be enabled
  with `TRANSLATOR_BACKEND=m2m100` (requires `pip install transformers
  torch sentencepiece` and a ~1.9GB download on first run). Confidence
  scores are currently a heuristic placeholder, not the model's real
  sequence log-probability -- that's the next real step, not pretended.
- **Nothing is actually sent.** `engine/sender.py` logs outbound
  messages to `data/sent_log.json` and prints to console. It's a
  one-method interface so a real provider (Twilio, Africa's Talking) is
  a drop-in swap, not a rewrite.
- **"Offline" claim is precise, not blanket.** Translation and
  classification run locally without a live connection once the model
  is loaded. The messaging layer itself (SMS/thread transport) is
  natively store-and-forward at the telecom level in a real deployment
  -- not "fully on-device" messaging, the same honest framing the
  brief's own Health annex (Mwana, mTrac) uses.
- **Booking date/headcount are entered via a small form in the thread
  UI, not extracted from free text.** Full NLP entity extraction from
  natural conversation was cut for time; a structured quick-entry point
  achieves the same guardrail goal (no hallucinated dates) more
  reliably. Real entity extraction is a named upgrade path.
- **That form only exists because this prototype's "thread" is a web
  page standing in for both phones.** Over real SMS there is no screen
  to show a form on, so this specific piece doesn't carry over as-is.
  A real deployment would replace it with structured plain-text replies
  (e.g. the thread asks for a date, then a headcount, one short question
  at a time) parsed the same deterministic way `reply_decision.py`
  parses "نعم"/"لا" -- still no free-text NLP, just more of the same
  guardrail pattern applied to two more fields.
- **Every fact-stating message is a filled template**
  (`message_templates.py`), never model output. The only model calls in
  this codebase are translation and (if swapped in) speech-to-text.
- **The feedback classifier is fixed-keyword matching, not a trained
  model.** This is partly deliberate (no hallucinated categories, fully
  auditable) and partly a scope call given hackathon time -- a trained
  classifier (e.g. on MASSIVE) was out of reach in the time available.
  One consequence: in real-AI translation mode, the model's phrasing can
  drift from the fixed keyword list, so a trigger (referral, product
  proposal) can be missed even when the visitor's intent is there. Mock
  mode's curated phrases are tuned to match the keywords, which is why
  it's the reliable one for a live demo.

## Architecture

- `storage.py` -- JSON file read/write helpers (threads, profile,
  pending actions, feedback log, demand counters, sent log)
- `engine/translate.py` -- translation interface, mock + real m2m100 backend
- `engine/classify_doors.py` -- fixed three-door classifier (returning /
  referral / new product), modeled on MASSIVE's fixed-intent-set
  approach (51 languages incl. ar-SA); a hand-written matcher here is
  the MVP substitute, MASSIVE is the named upgrade path
- `engine/capacity_check.py` -- pure function: date vs. Noor's stated
  protected/recommended windows
- `engine/threshold_watch.py` -- pure function: counts a repeat demand
  signal, fires exactly once when it first crosses a threshold (3)
- `engine/proactive_rules.py` -- transparent priority rule over pending
  actions (referral > product proposal > booking), not a model's
  judgment call
- `engine/sender.py` -- mocked/logged outbound sender, swappable
- `message_templates.py` -- every outbound/fact-stating string, filled
  not generated
- `app.py` -- Flask routes tying it together
- `templates/`, `static/` -- the thread UI

## Run it

```
pip install -r requirements.txt
python app.py
# open http://localhost:5050
```

## Run tests

```
pytest tests/
```

## Suggested demo flow

1. Onboarding: set a protected window (pruning) and a recommended window
   (harvest peak), plus offerings.
2. New visitor thread, send a message as "Visitor" in English
   (try: `Hello, can I visit the farm?`) -- see it arrive on Noor's
   phone translated live into Arabic.
3. Request a booking inside the protected window -- see the Arabic
   warning message queued for Noor's approval, not an auto-confirm.
4. Submit post-visit feedback mentioning coffee beans
   (`I wish I could buy your coffee beans`) from three different
   visitor threads -- the third one crosses the threshold and a
   product proposal (in Arabic, for Noor) appears.
5. Submit feedback mentioning a friend
   (`My friend also wants to visit the farm`) -- a referral prompt (in
   Arabic, for Noor) appears for approval.

## Upgrade paths (named, not built)

- Real translation: facebook/m2m100_418M (already wired, flag-gated)
- Speech-to-text: Mozilla Common Voice (Arabic coverage) for voice
  onboarding/feedback
- Classifier: train/fine-tune on MASSIVE instead of hand-written patterns
- Less-supported languages: fine-tune on Masakhane's African-language corpora
- SMS delivery: Twilio or Africa's Talking behind `engine/sender.py`
- Discoverability: real OpenStreetMap batch registration via the cooperative
- Longitudinal "season vs. season" comparison: needs accumulated
  history, moonshot item
