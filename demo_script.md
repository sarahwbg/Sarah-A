# Demo video outline (2-5 min)

## 1. Problem statement (one sentence)
Because of One Thread, Noor will steer visitor timing around her real
agricultural calendar and turn repeat requests into priced offerings,
that she'd otherwise miss, collide with farm work, or under-price; we
know because GSMA's Mobile Gender Gap Report shows the device-ownership
pattern her persona reflects, and Global Findex (World Bank) shows the
mobile-money usage pattern her phone already supports.

## 2. AI capabilities + why a simpler tool wouldn't do the job
- A spreadsheet or SMS template can't translate both directions in one
  thread, can't match free-text feedback to a fixed, checkable
  category, and can't notice a demand threshold crossing on its own.
- State the guardrails explicitly: nothing auto-sent/auto-booked, every
  fact comes from deterministic logic and templates, the model only
  ever runs for translation.

## 3. Tool demo -- one visitor's journey, end to end
- Visitor messages in Arabic asking to visit -- translated instantly
- Requests a booking during the pruning window -- Noor sees the warning
  phrasing, not an auto-confirm
- Visit happens, feedback mentions "buy your honey" for the 3rd time
  this season -- threshold crosses -- product proposal appears for
  Noor to approve
- A referral mention -- bilingual card drafted for Noor to approve

## 4. The gap being addressed + tech stack
- Named workflows from the brief, built as one engine, not six
  disconnected features
- facebook/m2m100_418M, MASSIVE (classifier grounding), OpenStreetMap,
  Common Voice, Masakhane -- named as the upgrade paths, not oversold
  as already built

## 5. Your take
The AI's job here isn't answering Noor's question, it's knowing which
question she should have asked -- and SMS/voice should be the
permanent interface for someone like her, not a stepping stone to
"upgrade" her into an app later.
