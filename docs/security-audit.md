# Security Audit — 2026-07-15

## Scope

Security hardening for the Flask backend configuration, deployment files, registration boundary, demo-data initialization, and repository hygiene.

## Confirmed findings before remediation

- **Critical:** a live-looking Telegram bot token and destination identifier were committed in `.env`, `.env.example`, `render.yaml`, and README documentation
- **High:** Flask CORS accepted every origin
- **High:** public registration accepted a caller-selected `admin` role
- **High:** application and JWT secrets had reusable fallback values
- **High:** predictable demo account passwords were seeded automatically
- **Medium:** the populated `.env` file was tracked and no repository secret regression gate existed

## Remediation implemented

- removed the tracked `backend/.env` file
- removed credential values from documentation, templates, and Render configuration
- added mandatory independent application and JWT secrets
- reject missing, short, or placeholder secrets before application startup
- replaced wildcard CORS with an environment-controlled allowlist
- reject wildcard CORS in production and wildcard-plus-credentials everywhere
- disabled public registration by default
- block public registration requests that attempt to create non-team roles
- disabled demo seeding by default and prohibited it in production
- require explicit strong local demo passwords
- removed password output from application logs
- added baseline browser security headers
- added `.gitignore`, configuration tests, a dependency-free repository security check, and least-privilege CI

## Verification evidence

Local-equivalent checks completed before commit:

- Python compile check passed for the new configuration, application, tests, and security-check script
- `6/6` configuration unit tests passed
- repository security check passed on the sanitized candidate tree
- no new runtime dependency was introduced

## Required operator action

Deleting a credential from the current branch does not invalidate it or remove it from Git history. The repository owner must:

1. revoke the exposed Telegram bot token in BotFather
2. issue a replacement token
3. update the hosting provider's secret store
4. replace any application or JWT secrets used by a deployment based on the previous repository state
5. consider a coordinated Git-history rewrite after rotation if repository history must be sanitized

## Residual risk

- old commits still contain the exposed values until history is rewritten
- many existing route handlers return raw exception text and need a consistent safe-error layer
- request validation remains manual and should move toward reusable schemas
- login rate limiting and token revocation are not yet implemented
- the dependency list is broad and should receive a separate minimization and vulnerability-audit slice
- production SQLite deployment has availability and concurrency limitations

## Next recommended security slice

Add request schemas, centralized non-sensitive error responses, login rate limiting, and tests proving authorization behavior on user and task routes.
