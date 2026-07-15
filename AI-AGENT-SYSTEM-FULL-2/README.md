# AI Agent System

A Flask and React task-management application with JWT authentication, AI-assisted task generation, optional Telegram notifications, and team performance tracking.

## Security notice

A Telegram bot credential was previously committed to this public repository. Removing it from the current branch does not remove it from Git history. The bot token must be revoked and replaced in BotFather before Telegram integration is used again. Any deployment that used the previous JWT or application secret should also receive newly generated secrets.

The backend now fails closed when required secrets are missing, short, or obvious placeholders. It also rejects wildcard CORS in production, keeps public registration disabled by default, blocks public creation of admin accounts, and disables demo data unless explicitly enabled in development.

## Features

### Backend

- Flask REST API and SQLAlchemy persistence
- JWT access and refresh tokens
- Admin and team-member roles
- Task CRUD, statistics, and performance tracking
- Optional OpenAI and Telegram integrations
- Environment-validated security configuration
- Restricted CORS allowlist
- Explicit development-only demo-data mode
- Dependency-free secret and unsafe-default checks

### Frontend

- React dashboard
- Authentication and protected routes
- Task management and performance views
- Responsive Tailwind CSS interface

## Requirements

- Python 3.10 or later
- Node.js 16 or later
- SQLite for the default local setup
- Optional OpenAI API key
- Optional Telegram bot token and user ID

## Backend setup

```powershell
cd AI-AGENT-SYSTEM-FULL-2\backend
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Generate two independent secrets:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put one generated value in `SECRET_KEY` and the other in `JWT_SECRET_KEY`. The populated `.env` file is ignored by Git and must remain local.

Start the backend:

```powershell
python app.py
```

The API is available at `http://127.0.0.1:5000`, with health information at `http://127.0.0.1:5000/api/health`.

## Frontend setup

```powershell
cd AI-AGENT-SYSTEM-FULL-2\frontend
npm install
npm run dev
```

Set the frontend API address in its local environment:

```env
VITE_API_URL=http://127.0.0.1:5000/api
```

## Backend configuration

Start from `backend/.env.example`.

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Yes | Flask application signing secret; at least 32 characters |
| `JWT_SECRET_KEY` | Yes | Independent JWT signing secret; at least 32 characters |
| `JWT_ACCESS_TOKEN_EXPIRES` | No | Access-token lifetime in seconds; default `3600` |
| `DATABASE_URL` | No | SQLAlchemy database URL |
| `CORS_ORIGINS` | Yes in production | Comma-separated frontend origin allowlist |
| `CORS_SUPPORTS_CREDENTIALS` | No | Enables credentialed CORS; default `false` |
| `ALLOW_PUBLIC_REGISTRATION` | No | Enables team-only public signup; default `false` |
| `ALLOW_DEMO_DATA` | No | Enables local sample users and tasks; forbidden in production |
| `DEMO_ADMIN_PASSWORD` | Demo mode only | Local demo admin password, at least 12 characters |
| `DEMO_USER_PASSWORD` | Demo mode only | Local demo member password, at least 12 characters |
| `OPENAI_API_KEY` | No | Enables OpenAI-backed features |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot credential; configure with user ID |
| `TELEGRAM_USER_ID` | No | Telegram destination user/chat identifier |
| `HOST` | No | Bind address; default `127.0.0.1` |
| `PORT` | No | Server port; default `5000` |

### Production rules

- Use unique application and JWT secrets.
- Never use `*` in `CORS_ORIGINS`.
- Keep `ALLOW_DEMO_DATA=false`.
- Keep public registration off unless it is a deliberate product requirement.
- Store OpenAI and Telegram credentials in the hosting provider's secret manager.
- Configure both Telegram values together or leave both blank.

## Optional local demo data

Demo accounts are no longer created automatically. To create sample users and tasks locally:

```env
FLASK_ENV=development
ALLOW_DEMO_DATA=true
DEMO_ADMIN_PASSWORD=choose-a-strong-local-password
DEMO_USER_PASSWORD=choose-another-strong-local-password
```

The backend refuses demo mode in production. Passwords are not printed to logs or stored in repository files.

## Registration behavior

`POST /api/auth/register` is disabled by default. When `ALLOW_PUBLIC_REGISTRATION=true`, the endpoint may create only `team` accounts. An unauthenticated caller cannot request the `admin` role.

## Main API endpoints

### Authentication

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/register` when explicitly enabled

### Tasks

- `GET /api/tasks`
- `POST /api/tasks`
- `PUT /api/tasks/{id}`
- `DELETE /api/tasks/{id}`
- `GET /api/tasks/stats`

### AI and notifications

- `POST /api/chat/generate-tasks`
- `POST /api/chat/suggest-assignment`
- `POST /api/telegram/send-notification`
- `GET /api/telegram/status`

## Verification

The security checks do not require the full backend dependency set:

```powershell
python -m unittest discover -s AI-AGENT-SYSTEM-FULL-2/backend/tests -v
python scripts/check_repository_security.py
python -m compileall AI-AGENT-SYSTEM-FULL-2/backend/src AI-AGENT-SYSTEM-FULL-2/backend/app.py
```

The repository CI runs these checks on Python 3.10, 3.11, and 3.12.

## Render deployment

`backend/render.yaml` contains no credentials. In the Render dashboard, provide at least:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`

Add `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_USER_ID` only when those integrations are required. Keep demo data and public registration disabled for production.

## Security limitations

- The exposed credential remains in old Git commits until history is rewritten, so rotation is mandatory.
- Existing route handlers still need broader input-schema validation and consistent non-sensitive error responses.
- SQLite is suitable for local and small single-instance deployments; a managed database is recommended for multi-instance production use.

See `docs/security-audit.md` and `docs/reference-review.md` for the implementation review and remaining work.
