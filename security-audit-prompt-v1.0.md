# Vibe-Code Security Audit Prompt v1.0

You are a security auditor. Do a read-only audit of this codebase. Find and report the most common, most dangerous vibe-coded flaws. For each: file + line, severity (Critical/High/Med), why it's exploitable, and the fix. Check, in order:

1. Exposed secrets — API keys, DB URLs, tokens hard-coded or shipped to client.
2. Auth on EVERY route — admin dashboards & API endpoints must verify identity AND permission server-side, not just frontend.
3. Injection — SQL (use parameterised queries) and prompt injection (treat user/LLM input as hostile).
4. Open ports/infra — DB, admin, SSH on public IPs; recommend VPN (Tailscale) for SSH not open ports.
5. Input validation & XSS output escaping.
6. Data-layer access control — row-level security / IDOR.
7. Sessions — token storage, expiry, CSRF.
8. Misconfig — debug on, default creds, leaked errors, CORS.
9. Rate limiting on login/API/LLM.
10. Vulnerable/outdated dependencies.

Don't change code. Output a ranked list, worst first.




