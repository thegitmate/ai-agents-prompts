#!/usr/bin/env python3
"""
Collector for content-research-tool. Pure stdlib — no pip install, no API keys.

    python3 scripts/pull.py data/raw-today.json          # full run (~4 min)
    python3 scripts/pull.py out.json --no-reddit         # skip the slow part
    python3 scripts/pull.py out.json --no-pain           # trend signal only

Two axes:
  TREND  — what's loud.     HN points, GitHub stars/day, npm curves, HF, Lobsters.
  PAIN   — who's hurting.   GitHub issue reactions/day, HN comments, Reddit pain search.

Fetches raw signal ONLY. Ranking, filtering and the write-up are Claude's job —
see CLAUDE.md. Failures are recorded in out["failures"] rather than raised, so a
blocked source never silently looks like "no signal".

Verified working 09/07/2026. If something starts failing, check the
"Known-dead sources" section of CLAUDE.md before debugging.
"""
import html, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
NOW = int(time.time())
ago = lambda days: NOW - days * 86400

# ---- trend config ----------------------------------------------------------
MIN_HN_POINTS = 40            # Algolia rejects numericFilters=points>N; filter here.
HN_QUERIES = ["AI", "Claude", "coding agent", "LLM", "vibe coding", "AI startup"]
HN_WINDOWS = {"0-2d": (ago(2), NOW), "2-7d": (ago(7), ago(2)), "7-14d": (ago(14), ago(7))}
NPM_PKGS = ["@anthropic-ai/claude-code", "@openai/codex", "@google/gemini-cli",
            "opencode-ai", "@sourcegraph/amp"]

# ---- pain config -----------------------------------------------------------
# Repos whose issue trackers are the ICP's tools. NOTE: sst/opencode does NOT exist.
PAIN_REPOS = ["anthropics/claude-code", "openai/codex", "google-gemini/gemini-cli",
              "anomalyco/opencode"]
PAIN_HN_QUERIES = ["claude code", "coding agent", "vibe coding", "AI agent", "LLM coding"]

# The linguistic fingerprint of someone stuck. Tuned 09/07/2026 — adding vague words
# ("limit", "problem") floods this with false positives like "limits were reset, thanks!".
PAIN_LEXICON = [
    "how do i", "how can i", "can't figure", "cant figure", "why does", "why is",
    "frustrat", "gave up", "wasted", "struggling", "anyone else", "am i the only",
    "context limit", "runs out of context", "rate limit", "usage limit", "too expensive",
    "burning through", "burned through", "forgets", "keeps breaking", "stuck",
    "broke my", "no idea how", "doesn't work", "hallucinat", "can't get", "cant get",
    "no users", "no customers", "no traction", "nobody uses", "churn", "not converting",
]

# ---- Reddit: ONE paced queue for every call ---------------------------------
# Reddit rate-limits per-IP across the whole domain, so trend and pain calls must share
# one pacer. Ordered by importance: what we lose first should be what matters least.
# `top` returns wins and memes (0 pain matches in testing) — pain lives in `search`.
REDDIT_GAP_S = 20             # 15s still 429'd on 09/07/2026
REDDIT_MAX_CONSECUTIVE_429 = 2  # bail out instead of burning minutes on a dead quota
#
# Order matters: a mid-run abort truncates the tail, so INTERLEAVE trend and pain.
# (Grouping them means one axis gets everything and the other gets nothing.)
_q = lambda s: ('search.rss?q=' + urllib.parse.quote(s) + '&sort=new&t=month&limit=15')
REDDIT_QUEUE = [
    # (kind, label, url_path)  — most valuable first, alternating axes
    ("trend", "ClaudeAI",      "r/ClaudeAI/top/.rss?t=week"),
    ("pain",  "ClaudeAI/tool", _q('subreddit:ClaudeAI ("usage limit" OR "rate limit" OR "burning through")')),
    ("trend", "LocalLLaMA",    "r/LocalLLaMA/top/.rss?t=week"),
    ("pain",  "vibecoding/tool", _q('subreddit:vibecoding ("how do i" OR "stuck" OR "keeps breaking")')),
    ("trend", "AI_Agents",     "r/AI_Agents/top/.rss?t=week"),
    ("pain",  "indiehackers/business", _q('subreddit:indiehackers ("no users" OR "nobody" OR "no traction")')),
    ("pain",  "SaaS/business", _q('subreddit:SaaS ("no users" OR "no customers" OR "not converting")')),
    ("trend", "vibecoding",    "r/vibecoding/top/.rss?t=week"),
]

failures = []


def log(m):
    print(m, file=sys.stderr, flush=True)


def get(url, raw=False):
    """Fetch. Never retries a 429 — the retry burns quota and blocks the next call."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
        return body.decode("utf-8", "replace") if raw else json.loads(body)
    except urllib.error.HTTPError as e:
        failures.append(f"{url[:90]} -> HTTP {e.code}")
        log(f"  !! HTTP {e.code}  {url[:64]}")
        return f"__ERR_{e.code}" if raw else None
    except Exception as e:
        failures.append(f"{url[:90]} -> {type(e).__name__}")
        log(f"  !! {type(e).__name__}  {url[:64]}")
    return None


def dated(iso):
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - d).total_seconds() / 86400
    return d.strftime("%d/%m/%Y"), f"{days:.1f}d ago", days


def pain_phrases(text):
    t = text.lower()
    return [p for p in PAIN_LEXICON if p in t]


# ============================ TREND =========================================

def hacker_news():
    """Three time windows -> velocity on the first run, with no stored history."""
    log("== HN (trend) ==")
    out = {w: [] for w in HN_WINDOWS}
    for q in HN_QUERIES:
        for w, (lo, hi) in HN_WINDOWS.items():
            nf = urllib.parse.quote(f"created_at_i>{lo},created_at_i<{hi}")
            d = get("https://hn.algolia.com/api/v1/search?tags=story"
                    f"&query={urllib.parse.quote(q)}&numericFilters={nf}&hitsPerPage=25")
            if not d:
                continue
            for h in d.get("hits", []):
                pts = h.get("points") or 0
                if pts < MIN_HN_POINTS:
                    continue
                out[w].append({"title": h["title"], "points": pts,
                               "comments": h.get("num_comments") or 0,
                               "date": h["created_at"][:10], "query": q,
                               "url": f"https://news.ycombinator.com/item?id={h['objectID']}",
                               "link": h.get("url")})
            time.sleep(0.35)
    for w in out:
        seen, keep = set(), []
        for x in sorted(out[w], key=lambda z: -z["points"]):
            if x["title"] not in seen:
                seen.add(x["title"]); keep.append(x)
        out[w] = keep[:15]
        log(f"  {w}: {len(out[w])}")
    return out


def github_repos():
    """API gives created_at + total stars but NOT stars-today -> stars/day is the proxy."""
    log("== GitHub repos (trend) ==")
    since = datetime.fromtimestamp(ago(21), timezone.utc).strftime("%Y-%m-%d")
    rows = []
    for q in [f"created:>{since} stars:>40", f"created:>{since} stars:>25 topic:ai-agent"]:
        d = get("https://api.github.com/search/repositories?"
                f"q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page=12")
        if d:
            for r in d.get("items", []):
                dt, rel, days = dated(r["created_at"])
                rows.append({"name": r["full_name"], "stars": r["stargazers_count"],
                             "per_day": round(r["stargazers_count"] / max(days, 1), 1),
                             "date": dt, "ago": rel, "url": r["html_url"],
                             "desc": (r["description"] or "")[:100]})
        time.sleep(2)
    seen, keep = set(), []
    for g in sorted(rows, key=lambda z: -z["per_day"]):
        if g["name"] not in seen:
            seen.add(g["name"]); keep.append(g)
    log(f"  {len(keep[:12])} repos")
    return keep[:12]


def npm():
    """Measured adoption, the hype detector. NOTE: installs, not people. CI inflates."""
    log("== npm (trend) ==")
    rows = []
    for p in NPM_PKGS:
        d = get("https://api.npmjs.org/downloads/range/last-month/"
                + urllib.parse.quote(p, safe="@/"))
        if not d or "downloads" not in d:
            continue
        dl = [x["downloads"] for x in d["downloads"]]
        wks = [sum(dl[i:i + 7]) for i in range(0, 28, 7)]
        if len(wks) == 4 and wks[-2] and wks[0]:
            rows.append({"pkg": p, "weeks": wks, "last_week": wks[-1],
                         "wow_pct": round((wks[-1] / wks[-2] - 1) * 100, 1),
                         "mom_pct": round((wks[-1] / wks[0] - 1) * 100, 1)})
        time.sleep(0.4)
    log(f"  {len(rows)} packages")
    return sorted(rows, key=lambda z: -z["wow_pct"])


def huggingface():
    log("== HuggingFace (trend) ==")
    d = get("https://huggingface.co/api/models?sort=trendingScore&limit=15") or []
    return [{"id": m["modelId"], "likes": m.get("likes"), "downloads": m.get("downloads"),
             "created": m.get("createdAt", "")[:10],
             "url": f"https://huggingface.co/{m['modelId']}"} for m in d][:10]


def lobsters():
    log("== Lobsters (trend) ==")
    d = get("https://lobste.rs/hottest.json") or []
    return [{"title": s["title"], "points": s["score"], "date": s["created_at"][:10],
             "tags": s.get("tags", []), "url": s["comments_url"]} for s in d[:20]]


# ============================ PAIN ==========================================

def github_issues():
    """A reaction is a person clicking 'me too' — a quantified pain counter.

    Reactions accumulate FOREVER, so the raw total is a level, not a slope. Rank on
    reactions_per_day, and only consider issues still active (updated in last 90d).
    """
    log("== GitHub issues (pain) ==")
    rows = []
    recent = datetime.fromtimestamp(ago(90), timezone.utc).strftime("%Y-%m-%d")
    for r in PAIN_REPOS:
        q = f"repo:{r} is:issue is:open updated:>{recent}"
        d = get(f"https://api.github.com/search/issues?q={urllib.parse.quote(q)}"
                "&sort=reactions&order=desc&per_page=15")
        time.sleep(3)
        if not d or "items" not in d:
            continue
        for i in d["items"]:
            age, created = dated(i["created_at"])[2], dated(i["created_at"])[0]
            upd_days = dated(i["updated_at"])[2]
            react = i["reactions"]["total_count"]
            rows.append({"repo": r, "title": i["title"], "reactions": react,
                         "reactions_per_day": round(react / max(age, 1), 2),
                         "comments": i["comments"], "created": created,
                         "age_days": round(age), "updated_days_ago": round(upd_days, 1),
                         "labels": [l["name"] for l in i.get("labels", [])],
                         "url": i["html_url"],
                         "body": re.sub(r"\s+", " ", (i.get("body") or ""))[:260]})
        log(f"  {r}: {len(d['items'])}")
    return sorted(rows, key=lambda z: -z["reactions_per_day"])


def hn_comments():
    """Verbatim pain, in their own words. tags=comment searches INSIDE comment bodies."""
    log("== HN comments (pain) ==")
    rows, seen = [], set()
    for q in PAIN_HN_QUERIES:
        d = get("https://hn.algolia.com/api/v1/search?tags=comment"
                f"&query={urllib.parse.quote(q)}"
                f"&numericFilters=created_at_i>{ago(14)}&hitsPerPage=60")
        if d:
            for h in d.get("hits", []):
                txt = html.unescape(re.sub("<[^>]+>", "", h.get("comment_text") or ""))
                m = pain_phrases(txt)
                if not m or h["objectID"] in seen or len(txt) < 60:
                    continue
                seen.add(h["objectID"])
                rows.append({"author": h.get("author"), "date": dated(h["created_at"])[0],
                             "matched": m, "text": re.sub(r"\s+", " ", txt)[:400],
                             "story": h.get("story_title"), "query": q,
                             "url": f"https://news.ycombinator.com/item?id={h['objectID']}"})
        time.sleep(0.4)
    log(f"  {len(rows)} pain comments")
    return rows


def _parse_reddit_atom(x):
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", x, re.S):
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        up = re.search(r"<updated>(.*?)</updated>", e)
        u = re.search(r'<link href="(.*?)"', e)
        c = re.search(r'<content type="html">(.*?)</content>', e, re.S)
        if not (t and up):
            continue
        body = html.unescape(re.sub("<[^>]+>", " ", html.unescape(c.group(1)))) if c else ""
        title = html.unescape(t.group(1).strip())
        dt, rel, _ = dated(up.group(1))
        out.append({"title": title, "date": dt, "ago": rel,
                    "url": u.group(1) if u else "",
                    "snippet": re.sub(r"\s+", " ", body)[:300],
                    "matched": pain_phrases(title + " " + body[:600])})
    return out


def reddit(want_pain=True):
    """One paced queue for EVERY reddit call — the rate limit is per-IP, domain-wide."""
    log("== Reddit (trend + pain, one paced queue) ==")
    out, consecutive_429, first = {"trend": {}, "pain": {}}, 0, True
    for kind, label, path in REDDIT_QUEUE:
        if kind == "pain" and not want_pain:
            continue
        if consecutive_429 >= REDDIT_MAX_CONSECUTIVE_429:
            failures.append(f"reddit: aborted after {consecutive_429} consecutive 429s "
                            f"(skipped {label} and the rest)")
            log(f"  ABORT reddit — quota exhausted, skipping remaining calls")
            break
        if not first:
            time.sleep(REDDIT_GAP_S)
        first = False
        x = get(f"https://www.reddit.com/{path}", raw=True)
        if isinstance(x, str) and x.startswith("__ERR_429"):
            consecutive_429 += 1
            out[kind][label] = None
            log(f"  {label}: 429")
            continue
        if not x or "<entry>" not in x:
            out[kind][label] = None
            log(f"  {label}: BLOCKED/empty")
            continue
        consecutive_429 = 0
        rows = _parse_reddit_atom(x)[:12]
        if kind == "pain":
            rows = [r for r in rows if r["matched"]]   # search.rss is fuzzy; filter locally
        out[kind][label] = rows
        log(f"  {label}: {len(rows)}")
    return out


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        sys.exit(__doc__)
    dest = args[0]
    want_pain = "--no-pain" not in args
    want_reddit = "--no-reddit" not in args

    out = {"pulled_at": datetime.now(timezone.utc).isoformat(),
           "run_date": datetime.now().strftime("%d/%m/%Y")}
    out["hn"] = hacker_news()
    out["github"] = github_repos()
    out["npm"] = npm()
    out["hf"] = huggingface()
    out["lobsters"] = lobsters()
    if want_pain:
        out["pain_github"] = github_issues()
        out["pain_hn"] = hn_comments()
    r = reddit(want_pain) if want_reddit else {"trend": {}, "pain": {}}
    out["reddit"] = r["trend"]
    out["pain_reddit"] = r["pain"]
    out["failures"] = failures

    json.dump(out, open(dest, "w"), indent=1)
    log(f"\nwrote {dest}")
    if failures:
        log(f"{len(failures)} failure(s) — these MUST appear in the report:")
        for f in failures:
            log("  - " + f)


if __name__ == "__main__":
    main()
