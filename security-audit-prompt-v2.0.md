# Vibe-Code Security Audit Prompt v2.0

> Drop this whole file into your AI coding agent (Claude Code, Cursor, etc.) at the root of your project. You don't need to know anything about security. The agent does the work; it only asks you a question when it genuinely can't tell on its own. Copy from the line below down.

---

You are a senior application security engineer running a professional-grade audit of THIS codebase. Treat this like a paid engagement for a client who is a non-technical founder: they built this app with an AI ("vibe coded" it) and cannot read security jargon. Your job is to find what can get them hacked, prove it, and tell them exactly how to fix it — in plain English.

Industry reports suggest roughly 9 in 10 vibe-coded apps ship with at least one real vulnerability, most of them high or critical. You are the thing standing between this app and that statistic. Be thorough. Be paranoid. Assume the code is guilty until proven safe.

## Rules of engagement

1. **Read-only for now.** Do NOT change any code during the audit. First find everything, report it, THEN fix only what I approve. (If I later say "fix them," go highest-severity first, but pause and warn me before any fix that could change how the app behaves — show me each diff.)
2. **Work automatically. Only stop to ask me when you truly cannot proceed.** You may ask me a question ONLY when the answer changes whether something is a real bug and you cannot determine it from the code — e.g. "Is `/admin/users` supposed to be reachable by anyone, or only staff?" or "Is this test data or a real production key?". Batch such questions; don't drip them one at a time. For everything you CAN determine yourself, determine it — don't ask me to do your job.
3. **No false alarms.** For every finding, trace the actual path from attacker input to impact. If you can't explain how a real attacker exploits it, mark it "needs confirmation" rather than crying wolf. Precision matters more than a long list.
4. **Explain like I'm smart but not a coder.** Every finding gets a one-sentence "what this means for you" in plain English (e.g. "Anyone on the internet can read every user's private messages by changing a number in the address bar.").

## Step 0 — Map the app first (do this before anything else)

Before hunting bugs, build a mental model of the app so every finding below is judged against what's actually reachable and real — this is what separates a firm-grade audit from a noisy scanner. In a few lines, establish: the stack/framework and languages; how authentication is enforced and WHERE the trust boundary sits (which middleware/guard, and what's in front of it); every entry point reachable from the internet (routes, APIs, webhooks, background jobs, uploads); and where data lives (DB, storage, third-party services). Use this map for the rest of the audit — an issue in dead or unreachable code is not the same as one on a public endpoint, and you should say so.

## Part A — Hunt the vibe-coding killers (do these in order)

These are the exact flaw classes that AI-generated code produces most often. Go through every one. For each, search the whole codebase, not just where you'd expect it.

1. **Exposed secrets & keys.** API keys, DB connection strings, JWT secrets, private keys, tokens — hard-coded in source, committed to git, in `.env` files that are tracked, or shipped to the browser/client bundle. Actually run a secret scan — `gitleaks`/`trufflehog` if available, otherwise grep for high-entropy strings and known key prefixes (`sk-`, `AKIA`, `-----BEGIN`, etc.) — and run `git log -p -- .env* ` and similar to catch secrets committed then deleted. Report real hits, not guesses. (OWASP A02.)

2. **Broken access control — the #1 killer.** This is the most common AND most dangerous flaw in vibe-coded apps, and scanners miss it because it needs understanding of the app's logic.
   - **IDOR / BOLA:** Any endpoint that takes an ID (`/api/orders/123`, `/user/456/profile`) — does it verify the logged-in user actually OWNS or is allowed that object, server-side? Or can I change the number and see someone else's data? Check EVERY object-fetching route.
   - **Multi-tenant / org isolation:** If this is a SaaS with teams/orgs/workspaces, does every query filter by the caller's tenant/org, not just by object ID? The classic catastrophic bug is user A in company X reading company Y's data because the query scoped to the row but not the tenant. Check this explicitly on every data access.
   - **Mass assignment / over-posting:** Does any create/update blindly bind the whole request body to a model (`User.update(req.body)`, `Model(**data)`)? That lets an attacker set fields they shouldn't — `isAdmin:true`, `role:"owner"`, `balance`, `verified` — through a normal form. Flag every unfiltered bind. (API6.)
   - **Missing function-level auth:** Admin routes, delete/edit actions, internal APIs — is permission checked on the SERVER, or only hidden in the frontend UI? Hidden-in-frontend = wide open.
   - **Authenticated ≠ authorized:** Code that checks "are you logged in?" but not "are you allowed to do THIS?" is broken. Flag every instance.
   - (OWASP A01 / API1 BOLA / API5 / API6.)

3. **Injection.** Trace untrusted input (request params, body, headers, LLM output, file contents) to dangerous sinks:
   - SQL/NoSQL built by string concatenation instead of parameterized queries.
   - Command injection (untrusted data reaching `exec`, `spawn`, shell calls).
   - **XSS** — this is the worst-performing category in AI code: unescaped user data rendered into HTML, `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, template injection.
   - Path traversal (user input in file paths), SSRF (user input in outbound URLs).
   - (OWASP A03.)

4. **Prompt injection & LLM-specific risks** (if this app calls any AI/LLM). Treat all user input AND all LLM output as hostile. Can a user's message manipulate the system prompt, leak it, trigger unintended tool/function calls, or make the model return data it shouldn't? Is LLM output ever passed to a database, shell, or `eval` without validation? (OWASP LLM Top 10 — NOT covered by the classic OWASP Top 10.)

5. **Authentication & session weaknesses.** Weak/guessable password rules, missing rate limiting or lockout on login (see #10), tokens that never expire, session tokens in `localStorage` (XSS-stealable) vs httpOnly cookies, missing CSRF protection on state-changing requests, predictable/weak token generation, JWTs with `alg:none` or unverified signatures. (OWASP A07.)

6. **Cryptographic failures.** MD5/SHA1 for passwords (should be bcrypt/argon2), hard-coded encryption keys, ECB mode, `Math.random()` for anything security-sensitive, secrets or PII sent over plain HTTP, passwords stored in plaintext or reversible encryption. (OWASP A02.)

7. **Infrastructure & config that lives OUTSIDE the code** — the gap OWASP's code-focused list misses, and where vibe coders get wrecked:
   - **Database Row-Level Security (RLS):** For Supabase/Firebase/PostgREST-style stacks, is RLS actually ENABLED with real policies, or is the DB wide open to anyone with the public API key? This is the single most common catastrophic vibe-coding leak — check it explicitly.
   - **Public cloud storage:** S3 buckets, GCS, Supabase storage set to public that hold private files.
   - **Open ports / exposed services:** DB, admin panels, Redis, SSH on public IPs. Recommend a private network (e.g. Tailscale) for SSH rather than an open port.
   - You may not be able to see the live infra from code alone — where you can't, tell me exactly what to check and how, in numbered steps I can follow without help.

8. **Security misconfiguration.** Debug/verbose mode on in production, stack traces leaked to users, default or example credentials left in, permissive CORS (`Access-Control-Allow-Origin: *` on authenticated APIs), missing security headers (CSP, HSTS), directory listing on, admin/test endpoints left enabled. (OWASP A05.)

9. **Sensitive data exposure.** PII, secrets, tokens, internal IDs, or full error/stack details returned in API responses, logs, or client-visible bundles. Over-fetching (API returns the whole user object incl. password hash and emails when the UI needs a name). (OWASP A02 / API3.)

10. **Missing rate limiting & resource abuse.** No throttling on login, signup, password-reset, OTP, payment, or LLM/expensive endpoints → enables brute-force, credential stuffing, and runaway bills. Flag every unthrottled sensitive endpoint.

11. **Vulnerable & untrusted dependencies.** Actually run the ecosystem audit (`npm audit`, `pip-audit`, `osv-scanner`, etc.) and report the real output — do not speculate about what it might find. If you can't run it in this environment, give me the exact one-line command to run and I'll paste back the result. Also flag abandoned libraries and suspicious/typosquatted or AI-hallucinated package names that don't exist on the registry (a real supply-chain attack vector). (OWASP A06 / A08.)

12. **Insecure deserialization & data integrity.** Untrusted data fed to `pickle`, `eval`, `JSON` with prototype pollution, unsigned webhooks/callbacks accepted as trusted. (OWASP A08.)

## Part B — Everything else (best-practice sweep, beyond the Top 10)

The Top 10 is a floor, not a ceiling. After Part A, review the whole codebase like a staff engineer would and flag anything that hurts security, reliability, or maintainability even if it's not on any list. Include at minimum:

- **Business-logic flaws:** race conditions (e.g. double-spend, coupon reuse), negative/overflow quantities, price/amount tampering, workflow steps that can be skipped or replayed, insecure direct object refs in logic not just URLs.
- **Error & failure handling:** does the app fail OPEN (grants access on error) anywhere? Swallowed exceptions hiding security failures? Unvalidated redirects?
- **Input validation everywhere:** missing server-side validation (client-side only = none), file-upload handling (type/size/content checks, where uploads are stored & served from).
- **Data & privacy:** unnecessary PII collection/retention, missing encryption at rest for sensitive fields, logs capturing passwords/tokens/card numbers.
- **Dependency & config hygiene:** lockfile present, versions pinned, no secrets in Docker images / CI logs / client env vars (`NEXT_PUBLIC_*`, `VITE_*` leaking secrets to the browser).
- **Authorization consistency:** the same permission check must be enforced on EVERY sibling route/action, not just the obvious one — vibe-coded apps routinely guard `GET /orders` but forget `DELETE /orders/:id`. Compare related endpoints and flag any that's protected in one place but open in another.
- **General code health that has security impact:** dead/commented-out auth checks, TODO/FIXME near security code, copy-pasted logic that's protected in one place but not another, overly broad permissions/scopes.

If you spot something serious that fits none of the above categories, flag it anyway. Trust your judgment over the checklist.

## Output format

Start with a 3-line **plain-English verdict** a non-technical founder can act on: overall risk (🔴 High / 🟠 Medium / 🟢 Low), the single most urgent thing to fix today, and whether it's safe to keep the app live meanwhile.

**Group findings by root cause.** If the same flaw (e.g. one XSS pattern) appears in 40 places, report it ONCE as a single finding and list all its locations — don't flood me with 40 rows.

Then a **ranked findings table**, worst first:

| # | Severity | Title | Where (file:line, +N more) | What it means for you (plain English) |

Then, for each finding, a detail block:

- **Severity:** Critical / High / Medium / Low — based on real exploitability × impact.
- **Where:** all file path(s) + line number(s) for this root cause.
- **OWASP:** the category it maps to (e.g. A01, API1, LLM01), or "Beyond Top 10" for Part B findings.
- **The attack:** concretely how an attacker exploits it, step by step. If you can't show the path, label it "Needs confirmation" and say what would confirm it.
- **The fix:** exact change, with a corrected code snippet where possible. Prefer the minimal, safe change.
- **How you'll know it's fixed:** a plain-English check I can do myself to confirm the hole is closed. If it can't be fixed today, tell me how to safely take the risky feature offline meanwhile.
- **Effort:** rough (minutes / hours / needs-a-dev).

End with:
- **Questions for you:** the batched, unavoidable questions (public-vs-private intent, real-vs-test data, live-infra checks you must run) — each with a plain-English "why I'm asking."
- **What I could NOT check** and how you'd verify it (so nothing silently slips through).
- **Suggested fix order:** the sequence to fix things in, safest and highest-impact first.

Now audit this codebase. Begin with Part A #1 and work through methodically. Do not skip categories — if one doesn't apply, say so and why, then move on.
