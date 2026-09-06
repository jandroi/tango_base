# Deployment Readiness

> Pre-deploy checklist for <project>. Every item is binary-checkable: a reviewer answers YES or NO without judgment.
> Run top-to-bottom before a production deploy or external handover.
> Version: 2026-04-28
> Only `/foundry` may modify this file.

---

## How to use

- Walk every item in order. Stop at the first NO; do not deploy with open items.
- Record evidence (command output, screenshot, file path) next to each YES.
- For an external handover, the receiving engineer signs each section after independent verification.

---

## 1. Code state

- [ ] `git status` reports a clean working tree on the deploy branch
- [ ] Deploy branch is fast-forward of `main` with no diverged commits
- [ ] `conda run -n tango_base python manage.py test` returns 0 failures, 0 errors
- [ ] `conda run -n tango_base python manage.py makemigrations --check --dry-run` returns no model changes
- [ ] `conda run -n tango_base python manage.py check --deploy` returns no issues at WARNING level or higher
- [ ] No `print(`, `pdb.set_trace`, `breakpoint(`, or `TODO: remove` in any `app_*` or `main_*` Python file
- [ ] No `console.log` in any committed JS or template

## 2. Configuration

- [ ] `DEBUG = False` resolved from env in `main_project/settings.py`
- [ ] `ALLOWED_HOSTS` driven by env, includes the production hostname, excludes `*`
- [ ] `SECRET_KEY` read from env; the placeholder/dev key in repo is not the production value
- [ ] `DATABASES` reads from env; SQLite default is dev-only
- [ ] `STATIC_ROOT` and `MEDIA_ROOT` resolve to writable paths on the target host
- [ ] All env vars used by the app are listed in a `.env.example` at the repo root with one-line descriptions
- [ ] `git ls-files | grep -Ei '\.(env|pem|key)$'` returns empty (no secrets tracked)

## 3. Security

- [ ] `SECURE_SSL_REDIRECT = True` in production settings
- [ ] `SESSION_COOKIE_SECURE = True` and `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS >= 31536000` with `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- [ ] `X_FRAME_OPTIONS = "DENY"` (or `"SAMEORIGIN"` only with a written reason in `office/decisions/`)
- [ ] Password reset flow tested end-to-end against the production email backend
- [ ] No superuser accounts seeded in fixtures or migrations
- [ ] Admin URL is moved off `/admin/`; if kept at `/admin/`, the exception is logged in `office/decisions/`

## 4. Database and data

- [ ] Production database migrated to latest: `manage.py migrate --plan` shows no unapplied migrations
- [ ] Fresh DB can be built from migrations alone: `manage.py migrate` on an empty DB succeeds
- [ ] No fixture or migration contains real customer data, real names, real emails, or real property addresses
- [ ] Backup procedure documented in a runbook, with restore tested at least once on a non-production copy
- [ ] HESB seed data restorable via migration `0004_backfill_hesb_sample_data` on an empty DB

## 5. Static, media, and file storage

- [ ] `manage.py collectstatic --noinput` runs without warnings
- [ ] Media storage backend (S3 / GCS / disk) is configured and write-tested from a Python shell on the target host
- [ ] `BrandStandardsCatalogFile` and `PropertyStandardsCatalogFile` upload + download tested against the configured backend

## 6. Operations

- [ ] WSGI server (gunicorn or equivalent) and process manager (systemd / supervisor / container orchestrator) chosen and documented in a runbook
- [ ] Application logs land somewhere persistent and queryable (rotated file, journald, or cloud log sink)
- [ ] Error tracking (Sentry or equivalent) is wired; a forced exception from a deploy-time view appears in the dashboard
- [ ] Health endpoint returns 200 for "app up" and exercises the database
- [ ] Runbook covers: deploy, roll back, rotate secrets, restore from backup

## 7. Dependencies and runtime

- [ ] `requirements.txt` is fully version-pinned (`==`, no `>=`, no commented-out packages)
- [ ] Python version is recorded (in `runtime.txt`, `Dockerfile`, or `README.md`) and matches the `tango_base` env
- [ ] `pip-audit` (or equivalent) reports zero High or Critical CVEs against pinned versions
- [ ] All dependency licenses reviewed and compatible with redistribution

## 8. Legal and IP

- [ ] Repo includes a `LICENSE` file at the root
- [ ] No third-party assets (logos, icons, photos) without a documented license
- [ ] Brand names visible in the UI (Hyatt, Hilton, etc.) limited to seed/demo data; no real-customer artifacts ship in the repo

## 9. Documentation handover

- [ ] `README.md` covers: prereqs, install, env vars, run dev server, run tests, deploy
- [ ] `office/index.md` "Current State" reflects the actual deploy SHA
- [ ] `office/reference/project_architecture.md` matches the running models (no orphaned references)
- [ ] `office/reference/lessons.md` exists and is non-empty
- [ ] All open items in `office/builds/backlog.md` either resolved or explicitly deferred in `office/decisions/`

## 10. Smoke tests on the deployed instance

Run as a freshly created superuser, against the production URL:

- [ ] Login at `/users/login/` succeeds
- [ ] `/` renders the authenticated landing page without 500
- [ ] TODO (<project> domain): primary feature page renders without 500
- [ ] TODO (<project> domain): core user flow completes end-to-end
- [ ] TODO (<project> domain): per-user data saves and reloads for the logged-in user
- [ ] Logout returns to `/users/login/`

---

## Sign-off

| Section | Verifier | Date | Notes |
|---|---|---|---|
| 1. Code state | | | |
| 2. Configuration | | | |
| 3. Security | | | |
| 4. Database | | | |
| 5. Static / media | | | |
| 6. Operations | | | |
| 7. Dependencies | | | |
| 8. Legal / IP | | | |
| 9. Documentation | | | |
| 10. Smoke tests | | | |

All ten sections signed -> safe to deploy.
