# Stock Deep Analysis — Universal Build Prompt v1.0

You are building a deep equity-analysis tool for me. I feed it primary
documents — 10-Ks, 10-Qs, earnings transcripts, investor decks — and it returns
ranked, evidence-cited investment theses and a red-flags register. You are a
research analyst's engine, **not an advisor**. Before building, run an intake
conversation. Do not skip it.

## Golden rule — build WITH me, not just FOR me

This is not a spec to execute blindly. If something doesn't fit how I actually
invest, an assumption seems wrong, or a shortcut would hide uncertainty from me
— **stop and check with me**. The passes below are a proven shape, not a rigid
template. Flag anything that doesn't make sense for my case.

## Hard guardrail — this is analyst input, not financial advice

Bake this into the system's behaviour, not just a disclaimer:
- Never state a buy/sell/hold as fact. Frame everything as *analysis for me to
  judge*.
- **Cite everything.** Every claim traces to a source document with a quote and
  a location (page / section / transcript timestamp). A claim with no citation
  does not get made.
- **Never invent numbers.** If a figure isn't in the documents, say so — don't
  estimate silently. If you estimate, mark it loudly as an estimate with method.
- Always surface uncertainty and the disconfirming evidence, not just the clean
  story.

## Step 1 — Intake (ask me, don't assume)

Ask me for:
1. **My style** — value, growth, quality-at-a-price, income, event-driven?
2. **Scope** — sectors I care about / avoid, market-cap range, geographies.
3. **Horizon and risk tolerance** — am I holding years or trading a catalyst?
4. **What *I* count as a red flag** — dilution, aggressive accounting, customer
   concentration, governance, leverage? Get my personal disqualifiers.

Do not proceed to design until these are clear.

## Step 2 — Ingestion

- Accept messy inputs: PDFs, HTML filings, transcript text, pasted tables.
- Parse and chunk with **location metadata preserved** (page, section heading,
  speaker/timestamp) so every downstream claim can cite exactly where it came
  from. Losing provenance at ingestion breaks the whole guardrail — don't.
- Normalise financials into a small structured store (revenue, margins, cash
  flow, debt, share count over time) so trends can be computed, not just quoted.

## Step 3 — Analysis passes (discrete, each evidence-cited)

Run separate, focused passes rather than one mega-prompt. At minimum:
1. **Financial health** — growth, margins, cash generation, balance-sheet
   strength, share-count trend (dilution/buybacks).
2. **Moat / competitive position** — what protects the economics, and is it
   widening or narrowing.
3. **Management & capital allocation** — track record, incentives, what they do
   with cash, candour in their own words (quote them).
4. **Valuation** — where it trades vs history and vs the fundamentals; state the
   assumptions explicitly, don't smuggle them in.
5. **Risks** — feeding the red-flags register in Step 5.

Each pass outputs claims with citations. No pass gets to hand-wave.

## Step 4 — Theses (steelman both sides)

- Produce a ranked set of theses. For each: the bull case AND a genuinely
  **steelmanned bear case** — argue against yourself properly, don't strawman
  the downside.
- Attach a confidence level and state what would change your mind (the specific
  evidence that would break the thesis).

## Step 5 — Red-flags register

A standing list of concerns, each tagged severity + citation, separated into
"confirmed in the documents" vs "worth checking, not confirmed." My personal
disqualifiers from intake get flagged loudest.

## Step 6 — Output format

- Per-name: a structured memo (thesis, the five passes, red flags, confidence,
  what-would-change-my-mind) with citations inline.
- Across names: a comparative ranking table (score/confidence per dimension) so
  I can line up candidates at a glance.
- Re-runnable: re-feeding updated filings refreshes the memo and shows what
  changed since last time.

## Step 7 — Stack & storage

Pick whatever's fastest and reliable for document parsing + LLM orchestration
(Python is a fine default). Store parsed documents, the normalised financials,
and generated memos so analysis is reproducible and diffable over time. Keep any
API keys in a gitignored env file.

## Step 8 — Docs

A plain-English README/CLAUDE.md: how to add documents, run an analysis, read
the output, and — importantly — a clear statement of the tool's limits (it
analyses what you feed it, it is not advice, it can be wrong) so future-me and
anyone else uses it with the right expectations.
