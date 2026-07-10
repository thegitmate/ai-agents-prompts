# content-research-tool (v1)

Super-minimal content research brain. Run it and it surfaces what my niche is talking about *right now*, ranked, with Instagram Reel angles. Research only — no script writing.

## Two axes: what's LOUD, and who's HURTING

The **trend radar** asks *"what is everyone talking about?"* The **pain radar** asks *"what is someone stuck on right now that nobody has answered?"* These find different things, and the second one is where the content is.

Proven on 09/07/2026: Reddit's `top/week` for r/ClaudeAI returned 12 posts and **zero** pain matches — top posts are wins and memes. Every real complaint was in `search.rss`. **Hot ≠ painful.** Run both axes; the report has a section for each.

## Core idea: a trend is a *derivative*, not a *level*

Every source gives you a **level** (points, stars, likes, downloads). "Biggest thing today" is a level — and everyone else can see it too, so you'd be the 50th Reel on it. What you want is the **slope**: what was small last week and is big this week.

Two ways to get slope, both used here:
1. **Time-sliced queries** — ask the same source for `0–2d`, `2–7d`, `7–14d` separately, then compare a topic's share of voice across the windows. Works on the very first run, no stored history needed.
2. **Snapshots** — every run writes its raw pull to `data/snapshots/DD-MM-YYYY.md`. After ~2 weeks these give true week-over-week deltas and reveal *recurring/structural* themes (a topic appearing in 5 of the last 8 runs) as opposed to one-day spikes.

## How to run
Open this folder in Claude Code and say: **"run today's research"**. Then:

0. **First run only:** read `config.local.md`. If it's missing, ask the user for the report output path and create it (see **Output** below). This is where reports get written — never hardcode a path.
1. Read `niche.md` and `watchlist.md`.
2. Read the last 2–3 files in `data/snapshots/` (if any) — needed for week-over-week and to avoid re-surfacing stale topics.
3. Read `data/covered.md` — topics already made into Reels. Don't resurface them unless there's genuinely new signal.
4. **Pull today's signal:**
   ```bash
   python3 scripts/pull.py data/raw-today.json
   ```
   Pure stdlib, no keys, no install. Takes ~4 min (most of it Reddit's mandatory pacing).
   Pulls **both axes**: trend (`hn`, `github`, `npm`, `hf`, `lobsters`, `reddit`) and
   pain (`pain_github`, `pain_hn`, `pain_reddit`).
   `--no-reddit` skips the slow part; `--no-pain` runs the trend axis only.
   It fetches raw signal only — **ranking and write-up are yours.** It records failures in
   `out["failures"]` instead of crashing; those failures **must** appear in the report.
   The endpoint details are documented below so the run still works if the script breaks.
5. WebSearch the **saturation check** for each candidate topic (the script can't do this).
6. For each candidate **pain**, judge **answeredness** — is there already a good public
   answer? — and discard anything you couldn't solve in a 60-second Reel.
7. Filter against `niche.md`. Drop off-niche noise.
8. Rank with the two scoring formulas (below).
9. Write the report to the configured report output path (see **Output**), and the raw pull to `data/snapshots/DD-MM-YYYY.md`.

### ⚠️ Use `curl` via Bash, NOT `WebFetch`

**The single most important operational rule.** `WebFetch` runs from Anthropic's servers, which many sites block outright. `curl` runs from this Mac's residential IP, which they don't. Reddit depends entirely on this: `WebFetch` on reddit.com returns "unable to fetch," while `curl` returns a clean 200.

Always send a browser User-Agent:
`-A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"`

Prefer raw JSON APIs over `WebFetch`'s page summaries — you get exact numbers and timestamps instead of a small model's paraphrase.

## Sources (all verified working, 09/07/2026)

Run in parallel where possible, **except Reddit** (see pacing).

### Hacker News — hard engagement signal
Use the **`search`** index (relevance/points-ranked), **not** `search_by_date` (pure chronological → returns 1-point junk).

```
https://hn.algolia.com/api/v1/search?tags=story&query=<Q>&numericFilters=created_at_i>{LO},created_at_i<{HI}&hitsPerPage=25
```
- ❌ **`numericFilters=points>100` is DEAD.** Algolia returns `400 invalid numeric attribute(points)`. Filter points **client-side** instead (keep `≥40`).
- `created_at_i` is a Unix timestamp and **does** work. Build the three windows from it.
- Queries: `AI`, `Claude`, `coding agent`, `LLM`, `vibe coding`, `AI startup`.
- Keep `title`, `points`, `num_comments`, `created_at`, `objectID` → thread URL is `https://news.ycombinator.com/item?id=<objectID>`.
- **A high comment-to-points ratio means the topic is contentious** — good emotional hook.

### Reddit — where the ICP actually lives
Public RSS works: no OAuth, no captcha (the v0 "impossible" gap).
```
https://www.reddit.com/r/<sub>/top/.rss?t=week     (also t=day)
```
- Subs: `ClaudeAI`, `vibecoding`, `LocalLLaMA`, `indiehackers`, `SaaS`, `AI_Agents`.
- ⚠️ **Rate-limits hard.** 2.5s spacing still produced HTTP 429 on 3 of 6 subs. **Wait ≥10s between subs, and never retry a 429 immediately** — the retry burns the quota and blocks the next sub. If short on time, pull the 3 most on-niche (`ClaudeAI`, `LocalLLaMA`, `AI_Agents`) rather than failing 6.
- ⚠️ **RSS has titles + timestamps but NO upvote scores.** Reddit *confirms* a topic across sources; it cannot *rank* one. Don't invent scores.

### GitHub — what builders are shipping
Use the Search API (unauthenticated is fine), not the trending page.
```
https://api.github.com/search/repositories?q=created:>{21d ago}+stars:>40&sort=stars&order=desc
```
- The API exposes `created_at` + total stars but **not "stars today"** — so compute **stars/day = stars ÷ age_in_days** as the velocity proxy. Rank on that, not on total stars.
- ~10 req/min unauthenticated. Space calls ~2s.

### npm — real adoption curves (the hype detector)
```
https://api.npmjs.org/downloads/range/last-month/<pkg>
```
- Packages: `@anthropic-ai/claude-code`, `@openai/codex`, `@google/gemini-cli`, `opencode-ai`, `@sourcegraph/amp`.
- Sum into 4 weekly buckets → week-over-week and month-over-month percentages.
- **The most differentiated signal available**, because it's measured rather than asserted. Loud on HN + flat downloads = noise. Quiet + rising curve = the real story.
- ⚠️ **Always state the caveat**: these are *installs*, not people. CI pipelines and mirrors inflate them heavily. Never say "N million developers."

### HuggingFace — on-niche model trends
`https://huggingface.co/api/models?sort=trendingScore&limit=15` → `modelId`, `likes`, `downloads`, `createdAt`.

### Lobsters — HN complement, less noise
`https://lobste.rs/hottest.json` → `title`, `score`, `created_at`, `tags` (watch the `vibecoding` and `ai` tags).

### Saturation check — the arbitrage signal
For each candidate top topic, WebSearch whether **Instagram Reels / YouTube Shorts / TikTok already cover it**. High dev signal + zero short-form coverage = your opening. Heavy short-form coverage = skip, you're late.

### PyPI — optional
`https://pypistats.org/api/packages/<pkg>/recent`. Rate-limits (429); back off, and skip rather than block the run.

### X / big voices
Read `watchlist.md`. X is login-walled; WebSearch each name + recent niche terms. Best-effort and secondhand — **timestamp everything**.

## Pain radar sources

The same derivative rule applies to pain. **Reaction counts accumulate forever**, so a raw total is a *level*. An issue with 200 reactions gathered this month is hotter than one with 5,000 gathered over a year.

### GitHub Issues — reactions are a quantified "me too"
```
https://api.github.com/search/issues?q=repo:<repo>+is:issue+is:open+updated:>{90d ago}&sort=reactions&order=desc
```
- Repos: `anthropics/claude-code`, `openai/codex`, `google-gemini/gemini-cli`, `anomalyco/opencode`.
  ⚠️ **`sst/opencode` does not exist** (HTTP 422). The real repo is `anomalyco/opencode`.
- **Rank on `reactions ÷ age_in_days`**, never on the raw total, and require activity in the last 90 days so you surface *live* pain.
- A very high **comments-to-reactions** ratio means people are arguing/guessing in the thread — i.e. **nobody has answered it**. That's the opportunity.
- Skews to power users. Treat it as a **leading indicator**: what power users complain about today, beginners hit in ~3 months.

### HN comments — the pain in their own words
```
https://hn.algolia.com/api/v1/search?tags=comment&query=<Q>&numericFilters=created_at_i>{14d ago}
```
- `tags=comment` searches *inside* comment bodies. Filter results locally against the **pain lexicon** in `scripts/pull.py`.
- ⚠️ **Keep the lexicon specific.** Vague words (`limit`, `problem`, `loops`) flood it with false positives — `"limits were reset, thanks Anthropic!"` is *relief*, not pain.
- This is where **verbatim quotes** come from. A quote is the Reel hook.

### Reddit — beginner pain and business pain
```
https://www.reddit.com/search.rss?q=subreddit:<sub> ("how do i" OR "stuck" OR ...)&sort=new&t=month
```
- ⚠️ **Never use `top/.rss` for pain.** It returns wins and memes (0/12 matched). Pain lives in `search.rss` and `new`.
- `search.rss` is **fuzzy** — it returns near-matches. Always re-filter locally against the lexicon.
- Tool pain: `ClaudeAI`, `vibecoding`. Business pain: `SaaS`, `indiehackers`.
- ⚠️ **All Reddit calls share one per-IP rate limit, domain-wide.** `scripts/pull.py` runs every Reddit call — trend *and* pain — through **one paced queue** (20s gaps) that **interleaves the two axes** and **aborts after 2 consecutive 429s**. Never add a second, separate Reddit pacer; they'll starve each other.

## Ranking

### Trend radar
```
score = velocity × cross_source_count × (1 − saturation)
```
- **velocity** — is it accelerating across the `0–2d` / `2–7d` / `7–14d` windows? (stars/day and download WoW feed this too)
- **cross_source_count** — how many independent sources surfaced it. **Cross-source topics win.** A single-source spike is usually noise.
- **saturation** — already covered in short-form? Then it's worth much less.
- Also flag **recurring/structural** themes (present across many snapshots): slower, but they make evergreen content that doesn't rot in 3 days.

Report the top 5, plus a short "Also rising" list for anything that narrowly missed.

### Pain radar
```
pain_score = frequency × intensity × (1 − answeredness)
```
- **frequency** — how many *distinct people* hit it (reactions, distinct threads, distinct subs). Cross-source pain wins, same as trends.
- **intensity** — reactions/day, comment counts, and the heat of the language.
- **answeredness** — is there already a good public answer? **This is the pain-side equivalent of saturation.** An unresolved problem with thousands of "me too"s is the whole game; a problem with ten thousand existing Reels is worthless no matter how much it hurts.

**Then apply the hard filter: only report pains you can solve in 60 seconds.** Discard the rest — but **state how many you discarded and name the biggest ones in one line**, so the filter's aggressiveness stays visible and tunable.

Report the top 5 pains. For each:
- **The pain in their own words** — a verbatim quote, blockquoted, with a link and date. This is the single most valuable output; the quote *is* the Reel hook.
- **Frequency / intensity / answeredness**, with the hard numbers.
- **2–3 Reel angles that actually solve it.**

**Audience weighting:** rank on *beginner* pain (Reddit, HN comments) — that's the ICP. Include power-user pain (GitHub issues) as a leading indicator, clearly labelled.

**Cross-reference the two axes.** The best Reels sit where they meet: on 09/07/2026 the trend axis found Slopfix charging $10k/week to delete AI code, and the pain axis found beginners asking *"I vibe-coded an app, now what?"* — the same problem at two price points. Call these pairings out explicitly.

## Output

Reports are written to a **notes directory of your choosing** (the single source of truth) — e.g. an Obsidian vault, a Notion export folder, or any local directory you sync.

**First-run setup (do this before the first write):**
1. Read `config.local.md`. If it doesn't exist, this is a first run.
2. **Ask the user** for the absolute path to the folder where reports should be written (the "report output path"). Do **not** guess or hardcode it.
3. Write that path into `config.local.md` (which is gitignored — it never gets committed) so future runs read it instead of asking again. See `config.example.md` for the format.
4. On every later run, read the report output path from `config.local.md`.

Reports are written to `<report output path>/DD-MM-YYYY.md`.

- **Never overwrite an existing report for today.** Read it first. If one exists, write `DD-MM-YYYY-v2.md` and say so.
- **Fallback only:** if the write to the configured path fails (path missing, sync issue, or `config.local.md` not yet set up), write to `research/DD-MM-YYYY.md` and flag it in your reply. When the configured path succeeds, do **not** keep a local copy.
- Also write the raw pull to `data/snapshots/DD-MM-YYYY.md` every run, so future runs have history.

## Report format

Two sections: **Top topics** (5, what's loud) and **Pain radar** (5, who's hurting).

Each topic: name, score line, **plain-English explainer**, why it's hot (with numbers), source(s), and 2–3 concrete Reel angles.
Each pain: name, score line, **verbatim quote(s)** with links + dates, hard numbers, and 2–3 Reel angles that solve it.

Put a jump link to the pain radar at the top, next to the ad-hoc anchor:
`> 🩹 **[[#Pain radar|↓ Jump to the Pain radar]]**`

"Today's pick" must weigh **both** axes — a live, unanswered pain usually beats an interesting trend, because it gets saved and sent to a friend.

### Explainer rule (non-negotiable)
Every topic MUST open with a **`📖 What this actually means:`** section (2–4 short paragraphs) placed **before** the sources, written for someone with **no prior context**:
- Spell out every piece of jargon in ordinary words the first time it appears — *prompt injection*, *open-weight*, *margin*, *agentic workflow*, *npm*, *skills*. Assume the reader has never met the term.
- Explain **why the thing works the way it does**, not just what happened. ("The agent can't tell the difference between instructions from you and text it happens to read.")
- Say **why it matters to this specific audience** (solo founders early in their AI journey), and why it's Reel-able.
- Use an analogy when it genuinely clarifies (Linux vs. paid Unix), not for decoration.
- If a number is tempting to misread, **say so here** with a ⚠️ and give the honest reading.

A topic the reader has to Google is a topic they will not film.

### Sourcing rule (non-negotiable)
Every topic MUST cite its source as a clickable link (HN thread, GitHub repo, article URL, the API endpoint). No claim or number goes in without a source next to it. Include a "Sources (raw pulls)" section at the bottom listing exact endpoints used. If something can't be sourced, drop it or flag it as unverified — never present it as fact.

### Recency rule (non-negotiable)
Every source MUST show WHEN it was posted: an absolute date **and** its age relative to the run date (e.g. "03/07/2026 — 1 day ago"). Sort/flag by freshness; explicitly call out anything older than ~2 weeks so it's never mistaken for current. If a date can't be determined, say "date unknown" rather than implying it's recent.

### Honesty rule (non-negotiable)
Record what **failed** in the report's sources section — blocked subs, 429s, dead endpoints. A silent gap looks like an absence of signal, which is a lie. Also surface caveats that weaken your own headline (npm counts bots; correlation isn't causation) — the audience trusts the person who volunteers the caveat.

## Formatting conventions
- **Dates: DD/MM/YYYY** everywhere in report *content* (e.g. `03/07/2026`). Filenames use `DD-MM-YYYY.md` (slashes aren't allowed in filenames).
- **Ad-hoc research goes at the bottom.** Off-cycle research during the day (script fact-checks, verifying a claim) is appended to that day's report under a single `## Ad-hoc research & fact-checks` section, below a `---` separator, newest entry first. Each entry: a `### <title> — DD/MM/YYYY` heading, with sources + dates like any topic.
- **Anchor at the top.** Just under the report intro, add an Obsidian jump link:
  `> 🔖 **[[#Ad-hoc research & fact-checks|↓ Jump to ad-hoc research & fact-checks]]**`

## Known-dead sources — don't retry these blindly
Verified broken on **09/07/2026**. Re-test occasionally, but don't burn a run on them.

- **HN `numericFilters=points>100`** → `400 invalid numeric attribute(points)`. Use the workaround above. *(This silently broke v0.)*
- **Reddit `.json`** → 403, unauthenticated access gated. **Use `.rss`.**
- **Reddit via `WebFetch`** → blocked. **Use local `curl`.**
- **Bluesky `searchPosts`** → 403 from `public.api.bsky.app`. `getAuthorFeed` works, but **@karpathy's Bluesky has been dormant since 2023** — dead end for this niche.
- **Redlib mirrors** (to recover Reddit scores) → `redlib.catsarch.com` 403s; `safereddit.com` is behind an Anubis browser-check wall.
- **Google Trends RSS** → works, but US-geo returns mainstream noise (sports, celebrities). Useless here.
- **Product Hunt** → homepage 403s to non-browser clients; API v2 needs OAuth.
- **Reddit OAuth** → abandoned in v0, app-creation captcha wouldn't complete. Unnecessary now that RSS works.
- **Reddit `top/.rss` as a PAIN source** → works, but yields ~0 pain (wins and memes). Use `search.rss`.
- **`sst/opencode`** → HTTP 422, no such repo. Use `anomalyco/opencode`.
- **Stack Overflow** (`api.stackexchange.com`) → works, free, has an `/unanswered` endpoint, but for this niche it returns enterprise plumbing (Bedrock, Vertex AI). Wrong audience. Dropped.

## Known-fragile
- **Reddit rate limits are the weakest link.** On 09/07/2026, `r/SaaS` returned 429 even after a 120s cooldown and 22s spacing. Business pain depends on `r/SaaS` + `r/indiehackers`, so it's the first thing to degrade. If a sub is missing, **say so in the report** and mark any single-sourced pain as provisional.
- Reddit's limit is per-IP and domain-wide, and it persists for a while. **Don't test Reddit repeatedly** — you'll poison the real run.

## Roadmap (only if the simple version proves useful)
- Snapshots need ~3 runs before week-over-week means anything. Be patient.
- `data/covered.md` ledger so filmed topics stop resurfacing.
- No scheduling, no HTML viewer, no voice/script layer.
