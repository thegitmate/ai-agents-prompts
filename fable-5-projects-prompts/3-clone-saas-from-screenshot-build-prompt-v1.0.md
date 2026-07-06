# Clone-a-SaaS-From-a-Screenshot — Universal Build Prompt v1.0

You are building me a private version of a tool I already pay for, starting from
a screenshot. The goal is **not** to replicate the entire product — it's to
rebuild the specific workflow I actually use, as a private tool I own and can
run myself. Before writing code, run an intake conversation. Do not skip it.

## Golden rule — build WITH me, not just FOR me

This is not a spec to execute blindly. If the screenshot is ambiguous, my
workflow doesn't match what the UI implies, or a simpler design would serve me
better — **stop and check with me**. Don't guess a whole app from one image.

## Step 0 — Ethics & scope check (do this out loud)

This is for building a private tool for my own workflow, or a clearly original
reimplementation — not for cloning someone's product to resell, and not for
copying their proprietary code, trademarks, or brand assets. If what I'm asking
drifts toward reselling a competitor's product, say so and we'll reshape it. Use
the screenshot to understand *structure and workflow*, not to lift their assets.

## Step 1 — Intake (ask me, don't assume)

Ask me for:
1. **Which tool and screenshot(s)** — get more than one shot if the workflow
   spans screens.
2. **The workflow I actually use** — walk me through what I click and why. This
   is the real spec. Most of the product's features I probably never touch;
   don't build those.
3. **Where it runs & who sees it** — local only, self-hosted, just me, or a
   small team? Any data-privacy constraint (data must stay on my machine)?
4. **Constraints** — stack I prefer, anything it must integrate with, budget for
   hosting (ideally free/local).

Do not proceed to build until these are clear.

## Step 2 — Vision analysis

From the screenshot(s), infer and write down: the UI layout and components, the
implied data model (what entities exist, their fields, their relationships), the
core actions, and the state that must persist. Produce this as a short,
readable spec — not code yet.

## Step 3 — Confirm the spec WITH me before building

Show me the inferred spec and my described workflow side by side. Get my
corrections. **Only build once I've confirmed** — a wrong data model discovered
after building is expensive; discovered now it's a sentence.

## Step 4 — Build (workflow-first)

- Pick a fast, boring, self-hostable default stack unless I said otherwise
  (e.g. a single React/Next front end + a light local DB like SQLite or
  Supabase-local). Optimise for "runs on my machine today," not scale.
- Build the **core workflow end to end first** — the thing I do every day —
  before any secondary feature. I'd rather have one real workflow working than
  ten half-built screens.
- Iterate with me: get the core usable, show me, then add the next slice.

## Step 5 — Private & portable

- My data stays mine: local-first by default, no phoning home, secrets in a
  gitignored env file.
- Make it genuinely runnable on my machine — check prerequisites, no hardcoded
  absolute paths, one clear "how to start it" command.

## Step 6 — Docs

A plain-English README/CLAUDE.md: what it does, how to run it, the file/module
map, and how to extend it — so I (or a future AI session) can add the next
feature without reverse-engineering the whole thing.
