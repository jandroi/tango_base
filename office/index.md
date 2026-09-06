# <project> — Office

> Last updated: <YYYY-MM-DD> (office installed from tango_base)

## Product

<Two sentences: what this product is and who it is for. Full domain detail: `office/governance/project_constitution.md`. Why it exists: `office/strategy/`.>

See `office/builds/backlog.md` for the roadmap.

## Current State

- **Office:** installed <YYYY-MM-DD> from `tango_base` (office, governance, skills, agents).
- **Django scaffold:** installed from `tango_base`. Migrated and verified running (`/`, `/users/login/`, `/users/register/`, `/admin/` → 200).
- **Feature apps:** none yet. First will be `app_<feature>`.
- **Tests:** none yet. **Env:** `tango_base` conda env (shared).
- **Shipped builds:** none.

## Skills

**Core:**
- `/pm` — product thinking, research, directives
- `/build` — scope features into tasks, execute, ship
- `/challenge` — stress-test outputs
- `/docs` — product documentation
- `/foundry` — office structure, skill design, governance integrity
- `/tester` — quality tests, lessons learned
- `/archivist` — prunes superseded challenge files after a build ships

**Domain workers (Tango Modular Django):**
- `/architect` — data modeling, schema, migrations
- `/dev` — views, forms, URLs, tests
- `/designer` — templates, CSS, design system
- `/standards` — convention compliance, audit
- `/ux` — UX audit: pages and flows for friction, consistency, design-system compliance

## Workflow

`/pm` → `/build` → `/architect` → `/dev` → `/designer` → `/challenge` → `/tester` → `/docs` → ship

Governed by `office/governance/office_flow_process.md`. 1 full challenge round by default, delta-based follow-ups when needed.

## Office Structure

```
<project>/
├── CLAUDE.md                 ← harness guidance (env, commands, architecture)
├── env.example               ← copy to .env, fill DJANGO_SECRET_KEY
├── office/
│   ├── index.md              ← you are here
│   ├── strategy/             ← lean canvas: why this project exists (fill 01_problem first)
│   ├── governance/           ← rules; only /foundry edits
│   │   └── project_constitution.md   ← domain, stack, conventions (fill before first build)
│   ├── thinking/             ← /pm sessions, in-flight ideas
│   ├── builds/backlog.md     ← single source of truth for build status
│   ├── decisions/            ← decision logs
│   ├── reference/            ← lessons, architecture, ux notes (added as work lands)
│   └── shipped/
└── .claude/
    ├── skills/               ← 12 skills (7 core + 5 workers)
    └── agents/               ← challenge.md, ponytail.md
```

When the studio publishes governance updates, propagate to `office/governance/` and bump the version stamp.
