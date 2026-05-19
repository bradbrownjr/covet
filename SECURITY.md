# Security

Tangible is designed for self-hosted, single-household or small-team use. This document describes the security controls built into the application and how to report vulnerabilities.

## Reporting Vulnerabilities

Please **do not** open a public GitHub issue for security vulnerabilities. Instead, use [GitHub's private security advisory feature](https://github.com/bradbrownjr/tangible/security/advisories/new) or email the maintainer directly (address on the GitHub profile). Expect a response within 5 business days.

---

## Security Architecture

### Authentication

| Control | Detail |
|---|---|
| Password hashing | Argon2id (via `argon2-cffi`), rehash-on-login when parameters change |
| Password policy | Minimum 12 characters, maximum 255 characters enforced at the API boundary |
| Session tokens | Cryptographically random (`secrets.token_urlsafe(32)`), stored `HttpOnly`/`Secure`/`SameSite` cookies |
| API tokens | Opaque random tokens for scripting and mobile use; stored as hashed values |
| Two-factor auth | TOTP (RFC 6238) with QR provisioning; 8 single-use backup codes (SHA-256 hashed at rest); time-limited signed ticket between password and TOTP steps |
| OIDC/SSO | Configurable external identity providers for organisations that prefer federated auth |
| Rate limiting | Login, registration, and TOTP confirmation limited to 5 requests/minute per IP; global API cap of 300 requests/minute |

### CSRF Protection

`OriginCsrfMiddleware` blocks cross-origin state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) that carry a session cookie. The `Origin` (or `Referer`) host is compared against the request host. Bearer-token-authenticated requests (mobile app, scripts) are exempt because they cannot be triggered by a cross-site form.

### Security Headers

Every response includes:

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'`; images/media allow `data:` and `blob:`; no external script sources |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Camera, microphone, geolocation, payment, USB all denied |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` (when HTTPS is enabled) |

### Input Validation

- All API payloads are validated by Pydantic v2 schemas before reaching the database.
- String fields have explicit `min_length` / `max_length` constraints at the schema layer.
- Numeric fields have `ge` / `le` guards where applicable.
- Category slugs, sort directions, and enum-style query parameters are validated against allowlists before use.
- File uploads (photos, documents) enforce size limits and MIME-type allowlists server-side.

### SQL Injection

All database access uses SQLAlchemy's ORM and Core expression API with parameterized queries. No raw SQL strings or f-string-interpolated queries exist in the application code.

### XSS

The SvelteKit web UI escapes all dynamic content by default. The single use of `{@html}` (the What's New modal) renders only server-controlled CHANGELOG content through a custom Markdown renderer that calls `escapeHtml()` on all text before emitting any markup, and restricts link URLs to `https?://` schemes.

### SSRF Protection

The URL metadata scraper (`POST /api/metadata/scrape`) and photo-from-URL ingestion resolve hostnames to IP addresses and reject private (`RFC 1918`), loopback, link-local, and reserved ranges before making any outbound HTTP request.

### File Storage

Uploaded photos and documents are stored by content-addressed SHA-256 hash, not by user-supplied filenames. Filenames are stored in the database and used only for `Content-Disposition` download headers (sanitized — see [Audit History](#audit-history) below).

### Access Control

Every collection resource endpoint checks the caller's role (`viewer`, `editor`, or `owner`) before performing any read or mutation. There is no reliance on obscurity or client-supplied role claims.

### Audit Log

All item creates, updates, deletes, archives, member changes, and loan operations are written to an append-only `audit_log` table, accessible to collection owners via `GET /api/audit`.

---

## Recommended Production Configuration

- Run behind HTTPS (Caddy, Nginx, Traefik) — HSTS is enabled automatically when `TANGIBLE_SESSION_COOKIE_SECURE=true`.
- Set `TANGIBLE_SECRET_KEY` to a strong random value (or let the server generate and persist one to `/config/secret.key`).
- Use Docker Secrets or a `_FILE` companion variable for all credentials rather than plain environment variables.
- Restrict the container's network exposure; Tangible does not need to be internet-facing for household use.
- Enable TOTP on all admin accounts.
- Keep the container image updated — `ghcr.io/bradbrownjr/tangible:latest` tracks the current release.

---

## Audit History

### May 2026 — Internal audit (v0.25.70)

A full read of the server and web source was performed covering OWASP Top 10 categories. The following was confirmed clean without changes required:

- SQL injection (ORM/parameterized queries throughout)
- XSS (Svelte default escaping; single `{@html}` usage verified safe)
- Authentication strength (Argon2id, secure cookies, TOTP)
- CSRF (Origin/Referer middleware)
- Security headers (CSP, nosniff, DENY framing, HSTS, Permissions-Policy)
- SSRF (IP allowlist guard on all outbound fetches)
- Access control (role checks on every endpoint)

Three issues were identified and fixed in **v0.25.70**:

**1. LoginRequest unbounded fields (DoS amplifier)**
`POST /auth/login` accepted arbitrarily long `username` and `password` values. Because Argon2 is intentionally CPU/memory-intensive, even a rate-limited attacker could craft multi-megabyte payloads to amplify CPU burn. Fixed by adding `max_length=64` (username) and `max_length=1024` (password) to `LoginRequest`, matching limits already in place on the registration schema.

**2. Content-Disposition header injection**
Collection names and usernames were interpolated directly into `Content-Disposition` response headers without sanitization (e.g. `attachment; filename=bom-{collection.name}.txt`). A name containing `\r\n` could inject arbitrary HTTP response headers. Fixed by adding a `_safe_filename()` helper that strips `\r`, `\n`, `"`, and `\` from user-supplied strings before header insertion. All four affected download endpoints now use quoted RFC 6266-style filenames.

**3. Unbounded `notes` fields (storage DoS)**
`notes` fields on `Item`, maintenance tasks, chores, contacts, loans, and inventory lot schemas had no `max_length` constraint. An authenticated user could submit arbitrarily large notes, consuming unbounded database and backup storage. Fixed by adding `Field(max_length=65535)` (64 KB) to all affected input schemas. Read schemas are unaffected.
