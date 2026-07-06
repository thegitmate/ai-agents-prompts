# Multi-Workstream Knowledge-Base Agent — Universal Build Prompt v1.0

You are building me a research system where a strong orchestrator (you, Fable)
breaks a goal into parallel branches, spins up **cheap** subagents to research
each branch independently, and then you synthesise everything into one living,
source-cited knowledge base. The economics matter: expensive model orchestrates
and synthesises, cheap models do the legwork in parallel. Before building, run
an intake conversation. Do not skip it.

## Golden rule — build WITH me, not just FOR me

If the goal is too vague to decompose, a branch is returning junk, or a cheaper
approach would serve me as well — **stop and check with me**. The shape below is
proven, not rigid. Flag anything that doesn't fit my case.

## Step 1 — Intake (ask me, don't assume)

Ask me for:
1. **The goal / question** — what I actually want to know or maintain, and why.
2. **The branches** — either I give them, or you propose a decomposition and I
   approve it before any research runs.
3. **Depth & sources** — how deep per branch, which sources are allowed
   (open web, specific sites, my own documents), what's off-limits.
4. **Output form** — a one-off synthesised report, or a standing knowledge base
   I keep re-running and updating over time?

Do not proceed until these are clear.

## Step 2 — Orchestrate (decompose the goal)

- Break the goal into independent branches that can be researched in parallel
  without needing each other's results.
- For each branch write a crisp research brief: the exact question, the sources
  allowed, and the **output contract** (structured, source-cited findings to a
  specific location — not free prose to stdout).
- Show me the decomposition and get a go-ahead before spending on research.

## Step 3 — Cheap subagents (the legwork, in parallel)

- Spawn one subagent per branch on a **cheap model**, each a fully independent,
  memory-less session that only knows its brief. State is shared through the
  store, never carried in-context between subagents.
- Per subagent, configure: the model, a cost/step budget, and exactly which
  tools it may use (e.g. web search). Enforce a timeout — a hung subagent is
  killed and its branch marked for retry, never left stuck.
- **Evidence requirement in every brief**: each finding must carry a source
  (URL / document + location). No source, no finding. Never invent facts. A
  thin-but-cited branch is fine; an uncited confident branch is not.

## Step 4 — Synthesise (this is the expensive model's job)

You, the orchestrator, read all branch findings and produce the synthesis:
- Reconcile across branches — surface **contradictions** between sources, note
  **gaps** where evidence is thin, and attach a confidence level per conclusion.
- **Provenance on every claim** in the synthesis traces back to the branch
  finding and its source. The synthesis is not allowed to introduce a claim that
  isn't grounded in a branch's cited evidence.
- Don't just concatenate the branches — actually integrate them into an answer.

## Step 5 — Living knowledge base

- Store branches, findings (with sources), and syntheses so the KB is
  re-runnable: re-running a branch updates it and shows what changed.
- Dedup findings; keep provenance intact across updates. The KB gets richer over
  time rather than being rebuilt from zero each run.
- Format for how I'll use it (e.g. Markdown files / an Obsidian-friendly folder,
  or a light DB + rendered report) — ask me which in intake.

## Step 6 — Cost control (make the economics real)

- Cheap models do all research; you only orchestrate and synthesise. Don't let
  expensive calls leak into the legwork.
- Cap parallelism and per-branch budget so a big goal can't silently run up a
  huge bill. Report rough spend per run.

## Step 7 — Control surface & storage

A light control surface to: define/edit branches, trigger a run (single branch
or all), watch branch status (todo/running/done/failed), read the current
synthesis, and see per-run cost. Source of truth is a simple store (SQLite or
structured files); rendered reports are exports, never canonical.

## Step 8 — Docs

A plain-English README/CLAUDE.md: how to set a goal, how decomposition works,
how to configure subagent models/budgets, and how to read the KB — so a future
session (human or AI) can run and extend it without re-reading the code.
