# CLAUDE.md — <project>

<!-- FILLABLE TEMPLATE. Replace every `<...>` placeholder. Delete this comment when done. -->

This file guides Claude Code when working in this repository. Domain detail lives in `office/governance/project_constitution.md`; the "why" lives in `office/strategy/`.

## Status (<YYYY-MM-DD>)

<One paragraph: what exists today, what shipped last, what is next. Update on every ship.>

Founder step before the scaffold is usable: `Copy-Item env.example .env`, fill in `DJANGO_SECRET_KEY` (generate per the comment in `env.example`), then `conda run -n tango_base python manage.py createsuperuser`.

This folder is **not** its own git repo. It lives inside the `Tango` studio repo, which tracks only `.claude/` and gitignores every product folder.

## Product

<Two sentences: what this product is and who it is for. Copy the headline from `office/strategy/00_lean_canvas/04_uvp.md` once written.>

First feature app: `app_<feature>` — <one sentence on what it does>.

## Environment

Shared `tango_base` conda environment unless a project-specific env is created. `requirements.txt` is the dependency baseline.

```powershell
conda run -n tango_base python manage.py <command>
```

## Common commands

```powershell
conda run -n tango_base python manage.py test                              # all tests
conda run -n tango_base python manage.py test app_<feature>                 # one app
conda run -n tango_base python manage.py runserver
conda run -n tango_base python manage.py makemigrations --check --dry-run   # before any migration
conda run -n tango_base python manage.py makemigrations
conda run -n tango_base python manage.py migrate
conda run -n tango_base python manage.py check
```

## Architecture — Tango Modular Django convention

Read `ARCHITECTURE.md` for the full spec. The big picture:

- **`main_project/`** — configuration only (settings, root URL routing, WSGI/ASGI). No business logic.
- **`main_*` apps** — platform layer shared across Tango projects (`main_users` auth, `main_home` shared layout, `main_media` uploads). Do not fork per project unless necessary.
- **`app_*` apps** — feature layer. Each feature app is self-contained with **no hard cross-app coupling**. The only allowed cross-app FK is `settings.AUTH_USER_MODEL`.
- **URL wiring** — `main_project/urls.py` mounts each app at a root path; each app owns its routes via `app_name = "<feature>"` in its `urls.py`.
- **Auth** — `AUTH_USER_MODEL = 'main_users.MainUser'`, email is the identifier (no username), `LOGIN_URL = '/users/login/'`. Use `LoginRequiredMixin` on every non-public view.
- **Templates** — every template extends `"main_home/base.html"`. Never duplicate layout in a feature app.
- **Views** — Class-Based Views by default. Business logic lives in models or app-local services, never in templates.
- **Models & migrations** — each app owns its migrations; PKs named general→particular.
- **Data** — user uploads go to `main_media/` (`MEDIA_ROOT`); app-internal pipeline data goes in `app_<name>/data/`.
- **Config** — all secrets read from environment variables (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, SMTP vars; see `env.example`). Never commit secrets.

## Studio office & workflow

Project office at `office/`: `strategy/` (lean canvas), `governance/`, `thinking/`, `builds/`, `decisions/`, `reference/`, `shipped/`. Dashboard: `office/index.md`.

Workflow is `office/governance/office_flow_process.md`:

- **Idea → research → challenge → promote → build → review → ship.** Pre-build ideas live in `office/thinking/<idea>/`; promoted work moves to `office/builds/<build>/` (`directive.md`, `plan.md`, `handover.md`, challenge files, `lessons_learned.md`).
- **Verdict Gate** governs every challenge loop: NEEDS WORK loops (cap N=3 → escalate to human), MINOR appends to backlog and proceeds, PASS proceeds.
- **`/challenge`** is the agent-based reviewer (source of truth: `.claude/agents/challenge.md`). Other skills: `/pm`, `/build`, `/docs`, `/foundry`, `/tester`, `/archivist`; workers `/architect`, `/dev`, `/designer`, `/standards`, `/ux`.

## Working style

- **Plan first** for any non-trivial task (3+ steps, multiple files, behavior or architecture changes). For full builds write `office/builds/<build>/plan.md`.
- **Verify before done** — run targeted app tests first; check rendered pages, redirects, forms, and changed workflows.
- **Root-cause fixes, minimal-impact edits.** Simplest complete fix; no over-engineering.
- **Capture lessons** — after a founder correction, record a reusable rule in `office/reference/lessons.md`.

## Brand

Tango is a **light** theme. Colors: `--tango-light #F2F4F2` (bg), `--tango-dark #4F4759` (ink), `--tango-accent #8097D1` (primary), `--tango-medium #7079A0` (hover). No paid web font; the system font stack is intentional.

## <Project-specific notes>

<Anything an agent must know that is not derivable from the code: legacy prototypes to preserve, external APIs, data sources, deploy target. Delete this section if empty.>
