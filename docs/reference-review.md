# Backend Reference Review

## Scope

This review selected three mature AI application backends and extracted patterns that fit the existing Flask application without forcing a framework rewrite.

## 1. Dify — `langgenius/dify`

Useful patterns:

- secret templates leave signing keys empty instead of shipping reusable values
- documentation gives an explicit strong-key generation command
- service URLs, token lifetimes, databases, and integrations are controlled through environment variables
- configuration behavior is covered by dedicated tests

Applied here:

- `SECRET_KEY` and `JWT_SECRET_KEY` are mandatory and validated
- placeholders and short keys fail before Flask starts
- the environment example contains blank credential fields
- token expiry and database URL are environment-driven

## 2. Langflow — `langflow-ai/langflow`

Useful patterns:

- CORS behavior receives dedicated security tests
- comma-separated origin configuration is normalized consistently
- wildcard origins and credentialed requests are treated as a high-risk combination
- middleware configuration is checked rather than assumed

Applied here:

- `CORS_ORIGINS` is parsed into an explicit allowlist
- wildcard CORS is rejected in production
- wildcard plus credentialed CORS is rejected in every environment
- configuration tests cover secure and insecure cases

## 3. Open WebUI — `open-webui/open-webui`

Useful patterns:

- runtime services are configured through environment variables
- user capabilities and public-facing features have explicit boolean gates
- permissive user capabilities default to disabled
- database configuration is separated from application logic

Applied here:

- public registration defaults to disabled
- public registration can create only team accounts, never admin accounts
- demo users and tasks require an explicit development-only flag
- integrations expose only configured/not-configured health state, never credential values

## Deliberate non-adoptions

- no migration from Flask to FastAPI or another framework
- no new secret-management dependency
- no large authentication rewrite
- no database migration in this security slice

The chosen implementation keeps the current product operational while closing the highest-risk configuration and authorization gaps first.
