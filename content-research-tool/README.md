# content-research-tool (public template)

A super-minimal, zero-dependency "content research brain" you run inside Claude Code. It
surfaces what your niche is talking about *right now* — ranked, with short-form video angles —
across two axes:

- **Trend radar** — *what's loud?* (Hacker News, GitHub, npm, HuggingFace, Lobsters, Reddit)
- **Pain radar** — *who's stuck on something nobody has answered?* (GitHub issues, HN comments, Reddit)

It's research only — it finds and ranks signal; it does not write scripts.

## Quick start

1. Open this folder in [Claude Code](https://claude.com/claude-code).
2. **Edit `niche.md`** to describe your niche and audience (a vibe-coding / AI-dev-tools example
   ships as the default — replace it with yours).
3. Optionally edit `watchlist.md` (accounts/voices to track) and `data/covered.md` (topics you've
   already made).
4. Say **"run today's research"**. On the first run, Claude asks where to write reports and saves
   that path to `config.local.md` (gitignored). See `config.example.md`.

The collector (`scripts/pull.py`) is pure Python stdlib — no `pip install`, no API keys.

## What's in here

| File | Purpose |
|------|---------|
| `CLAUDE.md` | The full operating manual Claude follows — sources, ranking formulas, output rules. |
| `niche.md` | Your niche + ideal audience. **Edit this first.** |
| `watchlist.md` | Big voices to check each run. |
| `scripts/pull.py` | The signal collector (stdlib only). |
| `data/covered.md` | Ledger of topics already turned into content, so they don't resurface. |
| `data/snapshots/` | Per-run raw pulls, for week-over-week deltas (gitignored). |
| `config.example.md` | Template for `config.local.md` (your report output path). |

## Privacy

This is a stripped, shareable copy. It contains **no personal paths, accounts, or research
output** — those live in `config.local.md`, `data/snapshots/`, and `research/*.md`, all of which
are gitignored. Keep it that way before pushing anywhere public.
