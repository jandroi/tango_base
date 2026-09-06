# Office Flow — Full Process

> Canonical workflow for introducing and executing builds in this office.
> Only `/foundry` can modify this file.
> Version: 2026-04-23
>
> **Companion governance:**
> - [automation_principles.md](automation_principles.md) — how to write (the authoring standard)
> - [testing_principles.md](testing_principles.md) — how to test (the quality standard)
> - This document — when to do what (the workflow)

---

## Challenge Loop Rule (universal)

Every challenge invocation in this office is a **challenge → refine** loop with **1 full review by default**. Round 2 happens only if Critical/Important findings remain after refinement, the target changed materially, or the founder explicitly asks for another pass. Round 3 is exception-only and requires a note in `office/decisions/` before it begins. A challenge round without a follow-up refinement is wasted output.

**Per round:**
1. Challenger writes findings to `<topic>_challenge_YYYYMMDD_HHMM.md` per `automation_principles.md` Principle 2 naming.
2. Author (`/pm`, `/build`, or whoever owns the target document) refines the target to address every Critical and every Important finding BEFORE the next round begins. Findings deliberately deferred are recorded in `office/decisions/` with a one-sentence rationale — they do not stay in the challenge file.
3. After refinement, the author (or loop orchestrator) deletes the round's `<topic>_challenge_*.md` via `git rm`. The file is stale: its findings are now in the target or in `office/decisions/`, and keeping it burns context on superseded evidence. Git history preserves it for recovery.
4. Review scope for the NEXT round (if needed):
   - Round 1 (the first round): read the target end-to-end.
   - Round 2+: read only the sections changed since the prior round. Deferred findings are in `office/decisions/`, not in residual challenge files.
   - Escalate back to a full reread only if the target's structure or scope changed materially.

**Exit conditions (any one):**
- Challenge verdict is PASS, OR
- No Critical/Important findings remain after refinement, OR
- Default ceiling reached (2 rounds) and unresolved blockers have been escalated to the founder instead of starting round 3, OR
- Exception ceiling reached (3 rounds with a recorded exception).

**Default ceiling vs. exception ceiling:** Round 1 is the default. Round 2 is permitted without exception (the "default ceiling"). Round 3 requires a recorded exception in `office/decisions/` before it begins.

**Applies to every challenge in the office:**
- Phase 1 Steps 2–3 (research challenge/refine).
- Phase 1 Step 4.1 (directive + plan refinement).
- Phase 2 Stage 2 (handover/code review).

---

## Verdict Gate (what each verdict triggers)

The challenger returns one of three verdicts; the verdict equals the highest-tier open finding (`challenge_rubric.md` Tier Assignment). The **Challenge Loop Rule above** governs *how many rounds*; this governs *what happens at each verdict*:

| Verdict | Trigger | Behavior |
|---|---|---|
| **NEEDS WORK** | Any Critical or Important finding open | Loop: author addresses Critical + Important, challenger re-runs (within the round ceiling above). |
| **MINOR ISSUES** | Only Minor findings open | Proceed to dev. Each Minor is appended to `office/builds/backlog.md` (one line, with source build name) and never re-challenged. |
| **PASS** | Nothing open | Proceed to dev. |

Front-load: round 1 surfaces all findings (incl. intent-level); a later-round finding that pre-existed in round 1 is logged as a round-1 failure.

---

## Phase 1: Introducing a New Build

### Trigger

The founder (human) has an **idea**.

### Step 1 — Deep Research

- **Who:** `/pm`
- **How:** Human invokes `/pm` with research ask
- **What:** Runs deep research on the idea. Can invoke researchers or workers as needed.
- **Output:** `thinking/<idea>/research.md` using this template:

```markdown
# Research: <idea>

## Scope
[1-2 sentences: what this research covers. Name at least 1 adjacent topic that is explicitly out of scope.]

## Summary
[2-3 sentences: what was researched and the key finding]

## Findings
[Minimum 3 sub-topics. Each finding follows this structure:]

### <Sub-topic>
- **Finding:** [the claim]
- **Evidence:** [source: doc URL, code file:line, specific data point with source, or code snippet. "Best practice", "commonly known", or unsourced claims are not valid evidence]
- **Implication:** [what this means for the build decision]

## Alternatives Considered
[What else was evaluated. Minimum 2 alternatives, each with strengths and weaknesses.]

## Risks
[What could go wrong if we build this. Minimum 2 risks, each with likelihood (high/med/low) and mitigation.]

## Recommendation
[Build / skip / defer. Minimum 2 numbered reasons.]

## Open Questions
[Prioritized: Blocker (must answer before build) vs. Non-blocker (can answer during build)]
- **Blocker:** [question]
- **Non-blocker:** [question]
```

### Fast Path — Narrow Build Adjustments

- **Who:** `/pm`
- **Trigger:** Existing build or well-scoped idea with no blocker-level architecture question, cross-app schema change, or external research dependency.
- **What:** Skip Deep Research. Create or refine `office/builds/<build>/directive.md` and `plan.md` directly from existing codebase evidence, then run Step 4.1 once.
- **Fallback:** If blocker questions appear while drafting, stop and return to Step 1.

### Steps 2–3 — Challenge & Refine (automated)

- **Who:** `/pm` (self-challenge loop — see Research Protocol in `/pm` skill)
- **What:** After writing `research.md`, `/pm` automatically runs 1 self-challenge round + refinement within the same invocation. Run round 2 only if Critical/Important findings remain after refinement or the founder asks for deeper review. Round 3 requires an exception note before it begins. Each round: challenge the research against standards and codebase facts, save findings to `research_challenge_YYYYMMDD_HHMM.md`, refine `research.md` to address Critical/Important findings.
- **Exit conditions:** See "Challenge Loop Rule (universal)" above.
- **Output:** Refined `research.md`. Each round's `thinking/<idea>/research_challenge_*.md` is deleted by `/pm` after that round's refinement per the Challenge Loop Rule; no research challenge file persists into Step 4.
- **Standard:** Automation Principles are followed (binary ACs, remove ambiguity). Every factual claim verified against codebase.
- **Gate:** Idea is ready when the founder says so. The founder may invoke `/challenge` separately for an independent review if desired.

### Step 4 — Promote to Build

- **Who:** `/pm`
- **What:**
  1. Create `builds/<build>/` folder
  2. Move `research.md` into `builds/<build>/`. Per the Challenge Loop Rule, no `research_challenge_*.md` should remain in `thinking/<idea>/`; if one does, `git rm` it before promotion rather than carrying it over.
  3. Delete `thinking/<idea>/` — no orphan folders
  4. Write `directive.md` — what to build and why
  5. Write `plan.md` — tasks, phases, acceptance criteria
  6. Add to `backlog.md` with priority and link to the build folder

### Step 4.1 — Refine the Directive and Plan

- **Who:** `/pm` + `/challenge`
- **What:** Reads challenge findings against the **directive and plan** (not the idea — that was Steps 2–3). Round 1 is a full read of each artifact. Follow-up rounds are delta-based unless scope changed materially.
- **How:** `/challenge` reviews `directive.md` → produces `directive_challenge_YYYYMMDD_HHMM.md`. `/challenge` reviews `plan.md` → produces `plan_challenge_YYYYMMDD_HHMM.md`. `/pm` refines using findings. On round 2+, review only sections changed since the prior round; deferred findings are in `office/decisions/` per the Challenge Loop Rule.
- **Retention rule:** `/pm` deletes each round's `directive_challenge_*.md` and `plan_challenge_*.md` via `git rm` after that round's refinement. On loop exit (PASS or MINOR), `/pm` stamps the `backlog.md` entry with `gate PASSED YYYY-MM-DD` as the durable gate record.
- **Standard:** Automation Principles are followed (binary ACs, remove ambiguity).
- **Rule:** 1 full round by default. Round 2 only if necessary. Round 3 only by recorded exception.
- **Gate:** Directive + Plan are ready when the founder says so and the loop exited PASS or MINOR — recorded in the `backlog.md` gate stamp for this build.

### Folder Structure After Phase 1

```
office/
> builds/
  > <build>/
    - research.md                           # moved from thinking/ at promotion
    - directive.md                          # official artifact
    - plan.md                               # official artifact
    # challenge files (directive_challenge_*, plan_challenge_*) live here only within
    # a single round; deleted after that round's refinement per the Challenge Loop Rule.
    # Deferred findings → office/decisions/
  backlog.md                                # status + priorities + gate stamps

> thinking/
  > <idea>/                                 # exists only during Steps 1-3
    - research.md                           # moves to builds/ at Step 4
    # research_challenge_* exists only within a round; deleted after refinement

> governance/                                # governance docs
```

---

## Phase 2: Execute Build

### Entry Criteria

The build has an approved Directive + Plan that is:
- Challenged
- Refined
- Automation-principles compliant
- If `backlog.md` has no `gate PASSED YYYY-MM-DD` stamp for this build, OR unresolved Critical/Important findings still block execution after the default ceiling, `/challenge` raises `builds/<build>/execution_blocker.md`
  - Execution blocker criteria: there is enough ambiguity that 90% quality of agentic work is not guaranteed

### Stage 1 — Development (Virtual Sprint Work)

- **Who:** Orchestrator script (`pipeline/orchestrator.py`) dispatches workers (`/architect`, `/dev`, `/designer`)
- **What:**
  1. Orchestrator reads `plan.md` and dispatches workers per task
  2. Each worker executes its task against the acceptance criteria
  3. Mechanical challenger reviews each task output (PASS/FAIL per criterion)
  4. Orchestrator loops on FAIL with challenger feedback (max 3 retries per task)
  5. Parallelize independent tasks when possible
  6. All tests pass
- **Output:** `handover.md` — summary of what was built, ready for review:

```markdown
# Handover: <build name>

> Build: [link to builds/<build>/directive.md]
> Plan: [link to builds/<build>/plan.md]
> Branch: [git branch name]
> Date: YYYY-MM-DD

## ACs Status
| # | Acceptance Criterion | Status | Evidence | Notes |
|---|---|---|---|---|
| 1 | [criterion text from plan.md] | Done / Workaround / Deferred / Not done | [file:line, test name, or screenshot] | [details if workaround or deferred — why and what's the plan] |

## Changes Made
| File | Action | AC # | What changed |
|---|---|---|---|
| `path/to/file.py` | Created / Modified / Deleted | 1, 3 | Brief description |

## Migration Status
[Single choice — pick one:]
- **No model changes** — N/A
- **Model changes made:**
  - `makemigrations --check --dry-run`: [pass/fail]
  - Migrations created: [yes/no]
  - Migrations applied: [yes/no]
  - Migration file(s): [list]

## Test Results
- **Command:** `[exact test command run]`
- **Result:** X passed, Y failed
- **New tests written:** [count and file paths]
- **Existing tests modified:** [count and file paths, or "none"]
- **Failures:** [list with file:line, or "none"]

## What Was NOT Done
[ACs that were descoped, deferred, or partially completed. Each with reason and proposed resolution.]
- AC #X — [reason] — [proposed: next build / tech debt / won't do]

## Open Questions
- [Anything unresolved that the reviewer should know. Each tagged: Blocker / Non-blocker]
```

### Stage 2 — Review (Virtual PR Review)

- **Who:** `/challenge` (code review mode — reviews handover + git diff)
- **What:**
  1. Read `handover.md` — verify every AC has a status
  2. Review code changes in git branch against `CLAUDE.md` conventions
  3. Produce findings using the standard `/challenge` output contract
  4. If findings are Critical/Important: spawn workers for corrections, then re-review only the changed files and unresolved findings unless scope changed materially
  5. Run 1 full review by default. Round 2 only if necessary. Round 3 only by recorded exception
- **Output:** `handover_challenge_YYYYMMDD_HHMM.md`
- **Retention rule:** After each round's fixes are folded into `handover.md`, `/challenge` deletes that round's `handover_challenge_*.md` via `git rm`. No handover challenge file persists into Stage 3.

### Stage 3 — Ship

- **Who:** `/tester` for tests, `/docs` for documentation
- **What:**
  1. Write tests following `testing_principles.md`
  2. Run all tests
  3. Write documentation
  4. Write `<build>_lessons_learned.md` using this template:

```markdown
# Lessons Learned: <build name>

> Build: [link to builds/<build>/directive.md]
> Date: YYYY-MM-DD
> Participants: [which skills were involved: /architect, /dev, /designer, /tester, etc.]

## What Worked
[Minimum 2 items. Each follows this structure:]
- **What:** [specific thing that went well]
- **Why it worked:** [what made it effective]
- **Keep doing:** [yes/no — is this a reusable practice?]

## What Didn't Work
[Minimum 2 items. Each follows this structure:]
- **What:** [specific problem encountered]
- **Root cause:** [why it happened — not just "it was hard"]
- **Impact:** [what it cost: time, rework, quality]

## Process Changes
[Each change is a concrete, implementable rule — not a narrative wish.]
| # | Change | Where to implement | Who implements |
|---|---|---|---|
| 1 | [specific rule or checklist item to add/modify] | [file path or skill name] | `/foundry` or `/pm` |

## Build-Specific Notes
[Anything unique to this build that doesn't generalize but is worth recording:]
- Architecture decisions that deviated from the plan and why
- Skill gaps encountered (skills that didn't have instructions for what was needed)
- Tooling issues (test runner, migrations, environment)

## Implementation Status
[Filled in by /pm during Stage 4 Admin]
| # | Change | Implemented? | Where | Date |
|---|---|---|---|---|
| 1 | [from Process Changes above] | Yes / No / Deferred | [file changed] | YYYY-MM-DD |
```

### Stage 4 — Admin

- **Who:** `/pm`
- **What:**
  1. **Reconcile `handover.md` ACs Status vs. working tree BEFORE any other step.** For every AC marked "Done" in `handover.md`, grep / read the claimed evidence (file path, URL name, test name, `data-testid`) and confirm it exists in the current working tree. Also check the `@skip` count on every test file the build touched — a non-zero skip count whose message contains "removed", "dropped", or the build's feature name is a red flag for a silent scope cut. If any mismatch is found, STOP: either re-dispatch the missing work (preferred), or rewrite the handover claim with a truthful "Workaround / Deferred / Not done" status and a rationale. The build does not move to `shipped/` while the handover and the tree disagree. Rule added 2026-04-24 after [decisions/20260424_property_management_landing_restoration.md](../decisions/20260424_property_management_landing_restoration.md).
  2. Clean backlog (mark complete, remove stale items)
  3. Link documentation
  4. Organize folders and files
  5. Implement `<build>_lessons_learned.md` (fold learnings into process)

---

## Office Folder Structure

```
<project_root>/
├── office/
│   ├── index.md           ← dashboard (status only)
│   ├── thinking/          ← /pm sessions, design rationale
│   ├── decisions/         ← what we chose and why
│   ├── governance/        ← governance docs
│   ├── builds/
│   │   ├── backlog.md     ← single source of truth
│   │   └── <build>/       ← directive + plan + log
│   └── shipped/           ← completed builds
└── .claude/
    └── skills/            ← skills for this office
```

## Build Folder Format

```
builds/<name>/
├── directive.md                          ← what to build and why
├── plan.md                               ← tasks, phases, acceptance criteria
├── handover.md                           ← dev summary for review (Phase 2)
├── <build>_lessons_learned.md            ← retrospective (Phase 2, Stage 3)
└── log.md                                ← notes as work progresses (optional)

# Challenge files (directive_challenge_*, plan_challenge_*, handover_challenge_*)
# live here only within a single active round and are deleted after that round's
# refinement per the Challenge Loop Rule. Deferred findings → office/decisions/.
```

## Decision Log Format

```markdown
# YYYY-MM-DD — Decision Title

**Context:** Why this came up
**Decision:** What we chose
**Rationale:** Why
**Consequences:** What this means going forward
```
