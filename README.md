# One Thread -- Noor's Farm (Small AI for Development prototype)

A single bilingual message thread per visitor that handles discovery,
booking, feedback, and follow-up for a smallholder farm-tourism host,
built around a calendar-aware conversation and a fixed-category
feedback classifier -- not a general-purpose chatbot.

**Deployment status: working local prototype, not yet deployed live.**
Everything described here runs and is testable on `localhost` today.
It has not been deployed to a public host or wired to a real SMS
number/provider -- that step (hosting + a Twilio/Africa's Talking
number) is straightforward but was deprioritized given limited time
to focus on getting the core logic right first. It's a planned next
step once the approach is reviewed/approved, not a technical blocker.

## Honesty notes (read before demoing)

- **Translation is mocked by default.** `engine/translate.py` ships with
  a curated Arabic/English phrase dictionary so the demo is reliable.
  The real model (`facebook/m2m100_418M`) is wired in and can be enabled
  with `TRANSLATOR_BACKEND=m2m100` (requires `pip install transformers
  torch sentencepiece` and a ~1.9GB download on first run). Confidence
  scores are currently a heuristic placeholder, not the model's real
  sequence log-probability -- that's the next real step, not pretended.
- **"Arabic support" means Modern Standard Arabic, not a specific
  spoken dialect.** `facebook/m2m100_418M` is trained predominantly on
  MSA (the written/formal register), which is what a text-based tool
  like this mostly sees -- but a visitor texting in a strong regional
  dialect (Gulf, Levantine, Egyptian, Moroccan, etc.) can get a lower-
  quality or lower-confidence translation than a visitor writing in
  more standard Arabic. That's exactly what the existing confidence
  score and low-confidence safety net are for -- this isn't a new
  gap, just a more precise description of the one the confidence
  mechanism already covers.
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
- **New Product demand is now de-duplicated by meaning, not just by exact
  phrase -- but only after a fixed keyword flags intent first.**
  `classify_doors.py` still only recognizes a fixed list of "wants to buy
  something" phrases (e.g. "do you sell X", "wish I could buy X") -- it
  never guesses that a message is product-interest out of nothing.  What
  changed: when that phrase doesn't also name one of Noor's three known
  products, the door no longer discards it. `engine/semantic_match.py`
  pulls out the short product phrase (e.g. "honey" out of "do you sell
  honey"), embeds it with
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (118M
  params, runs locally, offline after a one-time ~460MB download -- same
  pattern as the translation model), and compares it by cosine similarity
  against products already logged this season. Above a fixed, visible
  threshold (0.55) it's counted as the same repeated demand; below it, a
  new one starts. The threshold is a config constant anyone can read and
  change -- never a model's free judgment call, same discipline as the
  door classifier and the demand counter itself. The model only measures
  similarity between things visitors already said; the message Noor
  eventually sees is still a filled template, with the product name
  translated into Arabic, never model-generated commentary.
- **Nothing that doesn't fit a door is silently dropped anymore.** Earlier,
  feedback that didn't match Returning/Referral/New Product (or that we
  translated with low confidence) was logged but never surfaced to Noor.
  Now both cases route to a fourth, catch-all outcome -- an "unclear, please
  review" flag that always appears in her queue with the translated text
  included, same "not sure, ask a person" principle already used for
  low-confidence translations, just extended to the classifier. This isn't
  a smarter category -- it's a safety net, so something that matters (like
  a visitor flagging something felt unsafe) never disappears just because
  it didn't match one of the three known patterns.
- **The referral card is never sent to the referred friend directly.** One
  Thread never acquires, stores, or messages a third party's contact
  info -- a referred friend's number is never collected. The card is
  generated FOR the original visitor and handed back TO that same
  visitor, to share themselves through their own messaging app, in their
  own relationship. (An earlier version of this code sent the card
  straight to a placeholder "referred_hint" value as if it were a real
  recipient -- that was a bug, not an intended design, and has been
  fixed.) Hard rule, enforced in code and here: One Thread never contacts
  anyone it doesn't already have an opted-in relationship with.
- **A visitor mentioning a date doesn't create a booking.** The existing
  rule stands: an actual booking is only ever created through the
  structured form in `request_booking()`. What's new is a narrower,
  purely informational heads-up (`engine/timing_extract.py`) -- if a
  visitor's ordinary message happens to name one of Noor's own
  onboarding-defined calendar windows (e.g. "pruning") or an explicit
  date ("November 20th"), via the deterministic `dateparser` library,
  Noor gets a flagged note in her queue so she doesn't miss it. It never
  calls the capacity check itself, never guesses a headcount, and
  returns nothing at all for a message with no date-shaped content in
  it. If she wants to actually book it, she still uses the same form as
  always.
- **Visitor opt-out (STOP) is a named upgrade path, not yet built.** A
  real SMS deployment needs a visitor to be able to text STOP and be
  permanently removed from future messages -- that's a consent
  requirement, not an optional nicety. This prototype doesn't implement
  it yet (there's no SMS carrier opt-out registry to integrate with in
  a browser demo), but it's called out here explicitly rather than
  silently assumed away. See Upgrade paths below.

## How this works in real life (no app, on either end)

Neither Noor nor a visitor installs anything. Here's what that actually
means, mechanically:

**1. Where does "the system" live?**
Nowhere on either phone. It lives on a server in the cloud -- a computer
somewhere else, always on. Both sides just text a normal phone number;
that number is connected to our server behind the scenes.

**2. How does it know who's who?**
Their phone number *is* the identity -- no login, no account. A visitor
texts Noor's business number for the first time → the server has never
seen that number before → it starts a new thread automatically. They
text again next week → same number → same thread, continued. (In this
browser prototype we fake that by clicking "new thread" with a made-up
ID; in real life the ID is just the phone number, created the moment
someone texts in, not by anyone clicking anything.)

**3. Where does translation happen, if there's no app?**
On the server, in the middle -- invisible to both sides. A message comes
in, the server translates it, and forwards the translation on. Neither
person ever sees "untranslated" text or knows a server is involved. To
Noor, it just looks like a visitor who happens to text her in Arabic. To
the visitor, it looks like a host who happens to reply in English. The
translation happens mid-conversation, server-side -- never on-device.

**4. Who does onboarding, if she never opens an app?**
It's a one-time setup, done once, by someone else, before any visitor
ever texts her -- not something her phone does. Realistically: a
cooperative staff member, an NGO fieldworker, or a volunteer with a
laptop sits with her once (or calls and asks her questions over the
phone) and enters her calendar and offerings into the `/onboarding` form
this prototype already has. She never needs data, a smartphone, or to
touch a screen. After that one conversation, she only ever just texts,
like always.

**5. If there's a server, how is any of this "offline"?**
"Offline" was never a claim that no server exists anywhere -- it's a
claim about what Noor's and the visitor's own phones need. A basic
phone sending a text only needs enough cell signal for an SMS -- the
same 2G signal that's worked for decades, no data plan, no wifi, no
app. That's genuinely different from needing a smartphone with an
internet connection and a chat app installed, which is the bar most
"digital" tourism tools actually require.

Separately, "offline" also describes how the AI itself runs: once a
message reaches the server, translation happens using a model loaded
directly on that server's own hardware -- not by calling out to a
separate AI company's API over the live internet for every message.
That matters because the system isn't fragile to a third-party API
going down, and the server could realistically live somewhere closer
to home (the cooperative's own office, a regional telecom partner)
instead of depending on a distant hyperscale cloud.

So: the server is always-on and connected -- same as any telecom
infrastructure already is today. What's "offline" is everything on
Noor's and the visitor's end, and the AI model's own execution. This is
the same honest framing real deployed SMS health systems (Mwana,
mTrac) use: not "nothing is connected anywhere," but "the person at
the edge of the network doesn't need to be."

## Architecture

- `storage.py` -- JSON file read/write helpers (threads, profile,
  pending actions, feedback log, demand counters, sent log)
- `engine/translate.py` -- translation interface, mock + real m2m100 backend
- `engine/classify_doors.py` -- fixed three-door classifier (returning /
  referral / new product), modeled on MASSIVE's fixed-intent-set
  approach (51 languages incl. ar-SA); a hand-written matcher here is
  the MVP substitute, MASSIVE is the named upgrade path. Anything that
  doesn't match, or that we translated with low confidence, routes to a
  fourth "unclear -- flag for Noor" outcome in `app.py` rather than being
  dropped
- `engine/semantic_match.py` -- for New Product mentions the fixed
  keyword list can't name, clusters similarly-worded repeats of the same
  product together via sentence-transformers embeddings + cosine
  similarity against a fixed, visible threshold; never names a product
  itself, only measures similarity between what visitors already said
- `engine/capacity_check.py` -- pure function: date vs. Noor's stated
  protected/recommended windows
- `engine/timing_extract.py` -- bounded, informational-only timing-mention
  detector for visitor messages: matches Noor's own named calendar
  windows or an explicit date (via `dateparser`), never creates a
  booking itself, returns nothing for messages with no date-shaped
  content
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

- **"Enables hiring" means it removes a visibility bottleneck, not the
  other barriers to actually hiring someone.** Each recurring revenue
  signal (a referral, a repeat visit, a new paid offering crossing
  threshold) gives Noor a reason to bring on local help she wouldn't
  otherwise have known she could afford or justify -- that's a real,
  specific thing this tool does. It does not supply the capital to pay
  that person, establish the trust/reputation needed to hire from her
  own community, or handle the liability of taking someone on. Those
  remain hers (and a cooperative's/NGO's) to solve; this tool only
  removes "I didn't realize the demand was there" as a reason not to.
- **"This generalizes to other industries" means the engine, not the
  three doors as they stand.** `classify_doors.py`, the threshold
  watcher, and the proactive-rules priority order are all
  domain-agnostic plumbing -- but "returning visitor," "referral," and
  "new product" are tourism-specific categories, and
  `message_templates.py`'s Arabic wording is written for a farm-stay
  host specifically. Applying this to a different small business (a
  market vendor, a repair shop) means re-authoring the keyword lists
  and templates for that business's own doors -- a content rewrite,
  not a code rewrite, but a real one, not a flag flip.

## Upgrade paths (named, not built)

- Visitor consent/opt-out: a real deployment needs a STOP keyword that
  permanently unsubscribes a visitor's number from future messages --
  a hard consent requirement for live SMS, not implemented in this
  prototype (no carrier opt-out registry to integrate with in a
  browser demo)
- Real translation: facebook/m2m100_418M (already wired, flag-gated)
- Speech-to-text: Mozilla Common Voice (Arabic coverage) for voice
  onboarding/feedback
- Classifier: train/fine-tune on MASSIVE instead of hand-written patterns
- Less-supported languages: fine-tune on Masakhane's African-language corpora
- SMS delivery: Twilio or Africa's Talking behind `engine/sender.py`
- Discoverability: real OpenStreetMap batch registration via the cooperative
- Longitudinal "season vs. season" comparison: needs accumulated
  history, moonshot item
