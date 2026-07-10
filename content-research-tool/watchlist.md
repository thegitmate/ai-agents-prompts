# X / Big-Voice Watchlist

Accounts to check each run for what the influential people in the niche are talking about.
X can't be scraped directly (login-walled), so the run searches the web for each name +
recent niche terms — best-effort, secondhand, **always timestamp what you find** so stale
takes are obvious.

## Accounts
- Andrej Karpathy (@karpathy) — AI, agentic coding, "Software 3.0"
- (add more here: founders, AI builders, vibe-coding voices you want to track)

## How the run uses this
For each account: WebSearch `"<name> <recent niche term> <current month/year>"`, pull anything
from the last ~2 weeks, note the date + how old it is. Fold notable items into the report as a
"Big voices" section. Anything older than ~2 weeks: include only if still clearly relevant, and
label its age.

## Upgrades (later, only if this proves useful)
- ~~Bluesky open API~~ — **tested 09/07/2026, dead end.** `searchPosts` returns 403 from
  `public.api.bsky.app`; `getAuthorFeed` works but @karpathy's Bluesky has been dormant
  since **2023**. The AI/tech crowd did not, in fact, migrate. Don't retry without checking
  first whether the accounts you care about are actually posting there.
- Paid X scraper API (Apify etc.) — real-time verbatim tweets, costs money. Currently the
  only way to get X properly.
- **In the meantime**, the best secondhand X signal is Hacker News and Reddit *discussing*
  what these people said — which the main run already captures, with real timestamps.
