# Database Operations

> How to operate the productive database safely. Covers backup, migration, branch-switch hygiene, and the eventual SQLite→Postgres cutover.
> Only `/foundry` can modify this file.
> Version: 2026-05-13
>
> **Companion governance:**
> - [automation_principles.md](automation_principles.md) — authoring standard
> - [office_flow_process.md](office_flow_process.md) — build workflow
> - [testing_principles.md](testing_principles.md) — test quality standard
> - This document — database operations standard

---

## Scope

Applies to the productive SQLite file (`db.sqlite3`) today and to the eventual Postgres instance after L5 cutover. Out of scope: replication, multi-tenant DB partitioning, encrypted-at-rest storage.

**Read this doc before:**
- Planning any migration (`/architect`)
- Running `manage.py migrate` against the prod DB (`/dev`, humans)
- Switching branches whose migration history differs
- Untracking, restoring, or rotating `db.sqlite3`

---

## L1 — Untrack `db.sqlite3` from git

**Policy:** the productive SQLite file must not be tracked. Every commit and branch switch otherwise mutates prod DB state by overwriting the working blob.

**Pre-action checklist (mandatory before any untrack operation):**

1. Confirm working tree is clean — no uncommitted schema changes.
2. Take a binary backup AND a SQL dump (see L3 for the verbatim command).
3. Confirm both backup files exist and are non-zero bytes.
4. Get founder go on the untrack operation.

**Reference command sequence — do not run during governance authoring:**

```bash
# Reference only — do not execute as part of governance authoring
git rm --cached db.sqlite3
# in .gitignore, un-comment the `#db.sqlite3` line; commit both changes together
```

**Acceptance:** after L1 lands, `git ls-files db.sqlite3` returns nothing and `db.sqlite3` still exists in the working tree.

---

## L2 — Per-environment DB convention

**Policy:** one filename per role. Roles do not share files.

| Role | Filename | Notes |
|---|---|---|
| Production | `db.sqlite3` | Untracked after L1. Single live copy. |
| Migration rehearsal | `db.sqlite3.rehearsal` | Gitignored. Throwaway. Copy from prod before each rehearsal. |
| Django test DB | `test_db.sqlite3` (auto) | Created and destroyed by `manage.py test`. Do not collapse with rehearsal DB. |

**Rehearsal protocol:**
1. Copy `db.sqlite3` → `db.sqlite3.rehearsal` (binary).
2. Point Django at the rehearsal DB. The project currently hardcodes `DATABASES['default']['NAME']` in `main_project/settings.py:94`; the supported method is a temporary edit to that line (`BASE_DIR / 'db.sqlite3.rehearsal'`) that is reverted before the prod migrate runs. A proper env-var override is unscheduled work and not required for L2.
3. Run the planned migration against rehearsal.
4. On success, revert the settings.py edit and run the same migration against prod. On failure, discard rehearsal file and revise the migration.

---

## L3 — Backup before migrate (single source of truth)

**Policy:** every `manage.py migrate` invocation against `db.sqlite3` is preceded by a backup. Not only destructive ones. Not only "risky-looking" ones.

**Naming:** `backups/<reason>_<YYYYMMDD>_<HHMM>.sqlite3` (binary) plus optional `backups/<reason>_<YYYYMMDD>_<HHMM>.sql` (human-readable).

**Retention:**
- Keep the last 20 binary backups; older ones may be deleted.
- Archive `.sql` dumps older than 12 months into `backups/archive/<YYYY>/`.

**Reference backup command — do not run during governance authoring:**

```bash
# Reference only — do not execute as part of governance authoring
cp db.sqlite3 backups/pre_<build>_$(date +%Y%m%d_%H%M).sqlite3
sqlite3 db.sqlite3 .dump > backups/pre_<build>_$(date +%Y%m%d_%H%M).sql
```

**Acceptance:** before invoking `migrate` against prod, `ls backups/pre_<build>_<YYYYMMDD>_<HHMM>.sqlite3` returns a file ≥ the size of `db.sqlite3` at that moment.

This is the **only** location in the office where the verbatim backup command lives. Skills, CLAUDE.md, and other governance docs point here.

---

## L4 — Migration discipline

**Pre-migrate gates (in order):**

1. `makemigrations --check --dry-run` — no unstaged model drift.
2. `migrate --plan` — preview the operation set; eyeball for destructive ops.
3. L3 backup taken and verified.
4. For destructive migrations: plan task carries a checkbox; `handover.md` Migration Status section names the signing-off agent or human.

**Destructive operation = any of:** `RemoveField`, `DeleteModel`, `AlterField` with data loss, `RenameField`, `RenameModel`.

**SQLite caveat:** every `AlterField` / `RenameField` / `RenameModel` triggers Django's `_remake_table` (full table rebuild). Partial-failure recovery requires the L3 backup regardless of how cosmetic the change looks.

**Rollback path:** restore from L3 backup. Do **not** rely on `migrate <previous>` for rollback; reverse migrations are unreliable on SQLite under `_remake_table`.

**Branch-switch hygiene (interim — L1 untrack is unscheduled work, not currently in `office/builds/backlog.md`):**
- Before `git checkout <other-branch>` from a branch with newer migrations: L3 backup first.
- After the checkout: `migrate` against the target branch's migration head before resuming work.

---

## L5 — Postgres cutover plan (deferred)

**Tripwire** (recorded in `office/builds/backlog.md` as a watcher item, not a build):
- Fires when **any single Django model exceeds 100,000 rows**, OR
- when a buyer Letter of Intent is signed.
- Whichever fires first triggers a concrete plan; not before.

**Tooling candidates** (chosen at tripwire time, not pre-decided):
- `pgloader` for full data + schema in one shot.
- Django `dumpdata` / `loaddata` for small datasets where a slow load is acceptable.

**Pre-cutover acceptance** (to be detailed when the tripwire fires):
- Rehearsed against a copy of prod twice without data loss.
- Read-only freeze window agreed with stakeholders.
- L3 backup taken inside the freeze window, before cutover.
- Rollback = restore SQLite from L3 backup; no in-place Postgres rollback.

Until the tripwire fires, L5 stays a one-paragraph contract. Do not preemptively install Postgres tooling.

---

## Compliance

**Trigger:** the surface that makes agents and humans aware of this doc is the one-line pointer in `CLAUDE.md` Common Commands, placed immediately above the `# Model change checks` block. Anyone reading `CLAUDE.md` for the `migrate` command sees the pointer first.

**Roles:**
- `/foundry` — the only role that may revise this doc.
- Everyone else (`/architect`, `/dev`, humans) — read this doc on the trigger above before planning or running a migration.

**Enforcement:** there is no mechanical enforcement of L3 backups in this build's scope. Compliance relies on the self-check below. If a stronger gate is needed later (pre-commit hook, `safe_migrate` wrapper, Tier-1 deny), it is a separate build.

**Self-check before every prod migrate:**

1. Have I taken the L3 backup with the correct naming?
2. Have I run `migrate --plan` and read every operation?
3. Is the migration destructive? If yes, is the sign-off recorded?
4. Do I know where the rollback file is?

If any answer is "no" or "I'm not sure," stop and resolve before running `migrate`.
