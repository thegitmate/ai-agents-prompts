# Auto-Leads Gen — Universal Build Prompt v1.0

You are building an autonomous B2B lead-sourcing pipeline for me. Before writing
any code, run an intake conversation — do not skip this.

## Golden rule — build WITH me, not just FOR me

This is not a spec to execute blindly. At every step below, if something doesn't
fit my actual situation, a workaround is needed, or an assumption seems wrong —
**stop and check with me** instead of silently deciding and pressing on. Adapt
the design to my specific ICP, sector, and constraints rather than forcing my
answers into the pattern below. The steps are a proven shape, not a rigid
template — flag anything that doesn't make sense for my case and we'll figure
it out together.

## Step 1 — Intake (ask me, don't assume)

Ask me for:
1. **My ICP** — who counts as a match, what disqualifies someone, company size
   range, any hard requirements (certifications, geography, etc.).
2. **Business context** — what I sell, how I currently reach customers, why I
   want this automated, roughly how many leads/week would be useful.
3. **Contact channel** — do I cold-call, cold-email, or connect on LinkedIn/other?
   This decides what data fields matter (phone vs email vs profile URL) and
   whether emails are even collected at all.
4. **Geography / scope** — countries, regions, or "wherever the ICP exists."

Do not proceed to design until you've got clear answers to all four.

## Step 2 — Decide: anchor-point strategy or direct search? (decide WITH me)

Some ICPs are too vague to search directly ("find aviation maintenance shops in
7 countries" returns nothing useful as one search). The fix is to find a proxy
list of **anchor points** — things you CAN search for directly that the real
targets cluster around or are indexed against — then search near/through each
anchor one at a time. Examples of anchors: small airports/aerodromes (for
aviation trades), industry trade-show exhibitor lists, professional-association
member directories, franchise/dealer locator pages, regional business
directories, event attendee lists, even geographic grid cells for very local
trades.

Direct search (no anchors) is better when the ICP is already specific and
searchable on its own (e.g. "SaaS companies using Shopify Plus" — a specific
BuiltWith/directory query already works).

Using my Step 1 answers, propose: (a) whether an anchor-point strategy fits,
(b) if yes, what the anchor should be and why, (c) if no, confirm direct search
and how you'll keep queries specific enough to return real results. Show me
your reasoning and wait for my go-ahead before building. Don't build both —
pick one path with me.

## Step 3 — Core architecture (build this regardless of Step 2's answer)

Two independent loops sharing one database:

- **Discover loop** (only if using anchors): find new anchors not already known,
  dedupe, add to the queue as `todo`.
- **Harvest loop**: pick the next `todo` anchor (or, if no anchors, the next
  segment/region in rotation), research it, validate, dedupe, insert leads,
  mark `done`.

Rules that make this reliable:
- **Every run is one unit of work** (one anchor, or one region/segment slice)
  and is a fully independent, memory-less agent session — no state carried
  between runs except through the database and config. This keeps runs
  reliable and stops context/drift from piling up.
- **Status + retry**: each queue item is `todo` / `done` / `failed`, with an
  attempt counter. Failed runs leave the item as `todo` for retry, up to a max
  attempts config, then it's retired to `failed`.
- **Rotation**: cycle through countries/regions/segments so coverage spreads
  out instead of exhausting one before starting the next.
- **Overlap lock**: only one run at a time. A run that's been "running" longer
  than the timeout is presumed dead and reclaimed (bump attempt, don't loop
  forever on a crashed process).
- **Dedup**: leads deduped by normalised company name + region, and by the
  primary contact key (phone/email/profile URL — whichever channel we picked).

## Step 4 — Research engine: headless OpenCode

Use **OpenCode** as the actual web-researching brain, invoked headlessly, one
subprocess call per run:

```
opencode run -m <model> "<full prompt text>"
```

Mechanics to replicate:
- Set `OPENCODE_ENABLE_EXA=1` in the subprocess env — this turns on free web
  search via Exa. Forward any provider API keys already in the parent env
  (e.g. `OPENROUTER_API_KEY`) so a key set once works without re-auth.
- Run as `subprocess.Popen` (or your language's equivalent), stream
  stdout/stderr line-by-line to a per-run console log file (strip ANSI codes)
  so a dashboard can tail it live.
- Enforce a timeout (config-driven, e.g. 600s) that kills the process if it
  hangs — a killed run must not get stuck as "running" forever; it needs to be
  reclaimed by the overlap lock on the next attempt.
- **Model fallback chain**: try a default (cheap/free) model first; only fall
  back to the next model in the chain on **auth or rate-limit errors**
  specifically (classify the output: auth error, rate limit, generic failure)
  — don't burn fallback attempts on ordinary failures, and don't confuse a
  free-search-provider rate limit (shared per IP, affects everyone regardless
  of model) with a per-model API rate limit (switching model won't help there
  — instead back off/pause automation entirely for a bit).
- **Output contract**: tell the agent in the prompt to write its result to a
  specific file path as a single JSON array, nothing else. Don't parse stdout
  for the answer — stdout is only for the live log. Parse the output file
  tolerantly (in case the agent wraps the JSON in stray prose/markdown, regex
  out the outermost `[...]`).
- **Evidence requirement in the prompt itself**: agent must include a
  source URL per lead — the page it actually opened to confirm the company is
  real and matches the ICP. Never invent companies/contacts. A lead with no
  contact info but a strong ICP match is still worth keeping (human can look
  it up); a lead with no evidence is not.
- Make the whole thing **portable to whatever machine it runs on**: check
  `opencode` is on PATH before invoking (clear error if missing/not
  installed), don't hardcode absolute paths, keep secrets in a gitignored env
  file rather than the tracked config.

## Step 5 — Manual high-quality mode (optional but recommended)

Alongside the automated OpenCode runs, support a manual mode where a
higher-quality agent (e.g. Claude, in an interactive session) can do a single
research run by hand: a small script exposes `pick` (locks the next queue item,
prints the prompt + output path) and `commit` (validates → dedupes → inserts →
rotates, identical to the automated path). Both modes share the same DB, same
dedup, same overlap lock, and are tagged by which one produced each run —
useful when you want a careful one-off on a specific anchor/segment instead of
waiting for the automated queue.

## Step 6 — Control surface

- A simple dashboard (pick whatever's fastest in your stack — e.g. Python +
  Streamlit, or a lightweight web UI) to: browse leads, mark contacted,
  export CSV, view queue status (todo/done/failed per region), trigger a
  manual run, view live run logs, and toggle automation on/off.
- A scheduler/daemon for hands-off operation: burst mode (run after run with a
  gap, optional max-runs cap) or fixed times per day. Never starts a new run
  while one is in flight (respects the overlap lock). When the harvest queue
  runs dry, auto-triggers the discover loop (if using anchors) before
  continuing.

## Step 7 — Storage

Source of truth is a simple embedded database (SQLite is a fine default) with
tables for: leads, queue items (anchors/segments), runs (history + status +
error type + model used), and a small key-value `meta` table for daemon
state/flags. CSV is only ever an export, never the source of truth.

## Step 8 — Suggested stack (adapt if you have a better fit)

Python + SQLite + Streamlit dashboard + OpenCode as the research engine is a
proven combination for this pattern — default to it unless you have a good
reason not to, but you decide the specifics (e.g. Node/Deno + a different
lightweight UI is fine too if it's genuinely a better fit for me).

## Step 9 — Docs

Produce a short plain-English "how this works" doc (no jargon) and a
CLAUDE.md/README covering setup, running, and the file/module map — so anyone
picking this up later (including a future AI session) understands it without
re-reading all the code.
