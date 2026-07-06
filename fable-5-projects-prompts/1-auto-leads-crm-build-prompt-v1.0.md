# Auto-Leads + CRM — Universal Build Prompt v1.0

You are extending an autonomous B2B lead-sourcing pipeline for me. This prompt
assumes a working discover/harvest sourcing engine already exists (see the
`auto-leads-gen-build-prompt` in this same registry). Your job is to bolt three
things on top of it — **scoring, cold-email drafting, and CRM sync** — without
rebuilding the parts that already work. Before writing any code, run an intake
conversation. Do not skip it.

## Golden rule — build WITH me, not just FOR me

This is not a spec to execute blindly. At every step, if something doesn't fit
my actual situation, a workaround is needed, or an assumption seems wrong —
**stop and check with me** instead of silently deciding and pressing on. The
steps below are a proven shape, not a rigid template. Flag anything that doesn't
make sense for my case and we'll figure it out together.

## Step 0 — Locate what already exists

If a sourcing pipeline is already in the repo, read it first and reuse its
database, dedup, queue, and run-loop as-is. If there is no existing pipeline,
tell me — we'll build the sourcing engine from the base prompt first, then come
back here. Do not silently reimplement sourcing from scratch.

## Step 1 — Intake (ask me, don't assume)

Ask me for:
1. **My ICP + channel** — reuse whatever's already configured; only ask for
   what's missing.
2. **What "qualified" means to me** — the difference between a lead worth an
   email and one worth binning. Give me examples of both if I'm vague.
3. **Which CRM** — HubSpot, Pipedrive, Airtable, Notion, a Google Sheet, or
   something else. Get the exact object/table structure I want leads to land in.
4. **Email posture** — cold email, or drafts I review before sending? Tone,
   length, language, any legal footer (GDPR/CAN-SPAM), and hard don'ts.

Do not proceed to design until all four are clear.

## Step 2 — Scoring layer (build the rubric WITH me)

- Design a scoring rubric together: positive fit signals, disqualifiers, and
  rough weighting. Don't invent weights silently — propose, show me, adjust.
- Every score is **stored and explainable**: alongside the number, record the
  signals that produced it (e.g. "employs 12 staff ✓, no relevant cert ✗").
  A score with no reasoning is useless to me later.
- Score at harvest time so ranking is available immediately, but make it
  **re-runnable** — if I change the rubric, I can rescore the existing table
  without re-sourcing.
- Keep scoring model-cheap: a rubric applied to already-collected fields beats
  a fresh LLM call per lead where a rule will do. Use an LLM pass only for the
  judgement calls a rule can't make, and cache the result.

## Step 3 — Cold-email drafting

- One draft per qualified lead, **grounded in that lead's real evidence** (the
  source page/fields we already collected) — reference something specific and
  true about them, never a generic mail-merge.
- **No hallucination**: the writer may only use facts already in the database
  for that lead. If it wants a fact it doesn't have, it leaves a clearly marked
  gap rather than inventing one.
- **Anti-spam guardrails**: no fake personalisation, no false urgency, honour
  the tone/length/legal rules from intake, include unsubscribe/footer if
  required.
- **Drafts, not sends, by default.** Store drafts against the lead; sending is a
  separate, explicit, opt-in action. If I later want auto-send, that's a
  deliberate switch with rate limits and a suppression list — never the default.

## Step 4 — CRM sync (adapter pattern)

- One internal `CRMAdapter` interface (upsert lead, update status, check exists)
  with a concrete implementation per CRM. Swapping CRM = swapping the adapter,
  not touching the pipeline.
- **Idempotent upsert**: syncing the same lead twice never creates a duplicate.
  Match on a stable key (email / domain / phone — whichever channel we picked).
- **Dedup against the CRM, not just our DB**: before insert, check the lead
  doesn't already live in the CRM under a different capitalisation/format.
- Sync carries the score, the score's reasoning, and the email draft into the
  CRM record so I can act on it where I already work.
- Keep secrets (CRM API keys) in a gitignored env file, never in tracked config.

## Step 5 — Control surface

Extend the existing dashboard (or build a light one if none exists) to: view
leads ranked by score with the reasoning visible, read/edit the email draft per
lead, trigger a rescore, push-to-CRM (single or batch), and see sync status
(synced / pending / failed) per lead.

## Step 6 — Storage

Reuse the existing embedded DB (SQLite is fine). Add columns/tables for: score,
score reasoning, email draft, draft status, and CRM sync state + external CRM
id. CRM is a destination, never the source of truth — our DB stays canonical.

## Step 7 — Docs

Update the existing README/CLAUDE.md (or write one) covering the new scoring,
email, and CRM pieces: how to configure a rubric, how to swap CRM adapter, and
how the draft→review→sync flow works — in plain English, so a future session
(human or AI) can run it without re-reading all the code.
