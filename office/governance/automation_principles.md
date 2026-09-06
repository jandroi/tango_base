# Automation Principles

> Canonical governance for how skills, documents, and processes are written in this office.
> Binding for: `/foundry` (office structure), `/pm` (research, directives), `/build` (plans), `/challenge` (reviews).
> Only `/foundry` can modify this file.
> Version: 2026-04-23
>
> **Companion governance:**
> - [office_flow_process.md](office_flow_process.md) — when to do what (the workflow)
> - [testing_principles.md](testing_principles.md) — how to test (the quality standard)
> - This document — how to write (the authoring standard)

---

## Office Rules

1. **Certainty and accuracy are #1 priority**

2. **Naming conventions are the base of success**. We organize from general to particular. From ideas to unit tests. Everything needs the correct sequencing to track anything through its names. Any output should have the topic first (to group all topics together) and then the YYYYMMDD_HHMM format to have the chronological order.

3. **Boundary test.** Before any action: "Am I following the office flow, or inventing a process?" If inventing, raise it to `/foundry`.

4. **Clean Workspace**. Bloat and fluff are not welcome. Any unuseful document or stale file should be cleaned. The content in the files must be precise, concrete and optimized for the execution.

---

## Principle 1: Zero Ambiguity

Every instruction an agent receives — in a skill, a directive, a plan, a handover, a review, or a lesson learned — must be precise enough that the agent cannot misinterpret it. Ambiguity is the root cause of agent drift, hallucination, and low-quality output.

### The Standard: Binary-Checkable

Every deliverable, task, acceptance criterion, and instruction must be **binary-checkable**: a reviewer (human or `/challenge`) can answer YES or NO without judgment. The end goal is to be able to work without the challenger.

| Type | Bad (ambiguous) | Good (binary-checkable) |
|---|---|---|
| **Research task** | "Research authentication" | "Produce a comparison of 3+ auth approaches, each with: setup complexity (low/med/high), Django compatibility (yes/no/partial), and a recommendation with 2+ reasons" |
| **Skill instruction** | "Write good tests" | "Every view has access tests (auth, unauth, 403, 404, 405), action tests (every form submit, filter, sort), and state tests (empty list, single item, paginated)" |
| **Acceptance criterion** | "Clean implementation" | "All views are CBVs with LoginRequiredMixin listed first in inheritance" |
| **Directive** | "Improve the build process" | "Rewrite `/build` to produce Directive.md + Plan.md instead of scope.md, add a challenge gate with 1 full round by default, delta-based follow-up review, and `execution_blocker.md` awareness" |
| **Handover** | "Everything works" | "ACs 1–5 implemented. AC 3 required a workaround (see line 42 of views.py). All 12 tests pass. No migrations needed." |
| **Lesson learned** | "Tests were hard" | "State tests for empty lists were missing because the test fixture always created 3 objects. Fix: add a dedicated test class with empty setUp for zero-state tests." |
| **Review finding** | "Code needs improvement" | "[MAJOR] app_&lt;feature&gt;/views.py:45 — &lt;Model&gt;ListView has no pagination. Queryset returns all rows unbounded. Suggested AC: ListView has paginate_by = 25" |

### Where Zero Ambiguity Applies

This principle governs **every document agents read or produce**. If ambiguity is introduced by the human to foundry or pm, the first hard rule is to make it less ambiguous.

| Document | Who writes it | Ambiguity check |
|---|---|---|
| **SKILL.md** | `/foundry` | Every instruction is an action with a verifiable output. No "be thorough" or "ensure quality." |
| **Directive.md** | `/pm` | The "what" and "why" are specific enough that `/build` can produce a plan without asking questions. |
| **Plan.md** | `/build` | Every task has: worker, files, binary ACs, anti-patterns, references. |
| **handover.md** | `/dev` or orchestrator | Lists every AC with status (done/not done/workaround), test results, and open questions. |
| **challenge findings** | `/challenge` | Every finding has file:line, severity, and a suggested AC that closes the gap. |
| **lessons_learned.md** | `/tester` | Every lesson is a reusable rule, not a narrative. States what happened, why, and the specific process change. |
| **research.md** | `/pm` | Findings are structured with evidence. Recommendations have numbered reasons. |
| **testing_principles.md** | `/foundry` | Test categories are enumerated, not described. |

### The Ambiguity Test

Before any document ships, ask:

1. **Could two different agents read this and produce different outputs?** If yes, it's ambiguous. Add constraints until there's only one valid interpretation.
2. **Could `/challenge` verify this criterion by reading the code/output?** If no, rewrite it with a specific file, line, count, or condition.
3. **Does this instruction contain any of these words?** If yes, replace them:

| Ambiguous word | Replace with |
|---|---|
| "good" | specific quality criteria |
| "clean" | specific conventions to follow |
| "thorough" | enumerated checklist |
| "ensure" | specific check with pass/fail |
| "appropriate" | exact value or condition |
| "as needed" | explicit trigger condition |
| "improve" | specific before → after state |
| "relevant" | named files, sections, or artifacts |
| "properly" | specific convention or standard |
| "comprehensive" | enumerated categories with minimum counts |

### How This Governs Skill Writing

When `/foundry` writes or updates a skill:

1. **No vague scope.** "Your Scope" lists specific actions with specific outputs.
2. **No subjective quality gates.** "Review Checklist" items are binary.
3. **No open-ended instructions.** "First Steps" names exact files to read, in order.
4. **No implicit knowledge.** If a skill depends on a convention, it references the specific document.
5. **Output contracts are templates, not descriptions.** The skill shows the exact markdown structure the agent must fill in.

---

## Principle 2: File Naming Convention

All files produced by any skill follow ONE format. No exceptions.

Official Artifact: **Format:** `<topic>.md`
	Example: idea1/directive.md, idea2/plan.md
Reference document: Format: `<topic>_<reference>_YYYYMMDD_HHMM.md`
	Example: idea1/directive_challenge_20260101_0921.md, thinking/idea2/research_audit_20260101_0921
Build-scoped artifact: **Format:** `<build>_<artifact>.md`
	Example: <project>_office_setup_lessons_learned.md, automation_pipeline_lessons_learned.md

Rules:
- `<topic>` comes first — this is what the file is about
- Build-scoped artifacts prefix with the build name to group related files
- Skill-specific suffixes are part of the topic: `_challenge`, `_audit`, `_research`
- Timestamp is `YYYYMMDD_HHMM` — no dashes in the date, 24h time
- All lowercase, underscores only, no spaces

This replaces all per-skill naming formats. Skills reference this principle, they do not define their own format.

---

## Principle 3: Security — Two-Tier Model

Agent operations are secured by two independent layers. Both must be maintained.

### Tier 1 — Hard Boundary (settings.json deny list)

Mechanically enforced by Claude Code before the agent sees the result. An agent cannot bypass a deny rule regardless of what any skill, prompt, or instruction says.

**Deny list covers blast-radius patterns:**
- Network access (curl, wget, ssh, git push)
- Catastrophic file deletion (rm -rf /, ~, C:, $VAR)
- Arbitrary code execution (python -c, py -c)
- Database destruction (manage.py flush, manage.py reset_db)
- Destructive git operations (reset --hard, clean)
- Credential file writes (.env, .pem, .key, credentials, secrets)

**Ask tier covers operations that need oversight but aren't catastrophic:**
- Package installation (pip install, npm install)
- Database queries (sqlite3)
- Selective file discards (git checkout --)

The deny list lives in `settings.local.json`. It is reviewed when new tools are added to the workflow.

### Tier 2 — Soft Boundary (skill instructions + automation principles)

Agent-enforced. Covers context-dependent rules that can't be expressed as command patterns:
- Scope limits: don't modify files outside your task
- Process rules: follow the office flow
- Quality gates: run tests before handover
- Data safety: don't UPDATE without WHERE, don't delete production data

### The Rule

**Anything truly dangerous must be in the deny list (Tier 1). Skill instructions reinforce — they do not replace.**

---

## Principle 4: Lean Output

Agents over-produce by default. Every artifact has hard caps and banned words to force signal over volume.

### Line caps

| Artifact | Cap | Shape |
|---|---|---|
| `directive.md` | ≤ 50 lines | Purpose (2 lines) · Scope (in + out bullets) · Done (≤ 5 bullets) |
| `plan.md` | ≤ 6 lines per task | Worker · Files · ACs (≤ 3) · Ref (≤ 1) |
| `research.md` | ≤ 150 lines | Scope · Summary (≤ 3 lines) · ≤ 5 findings · Decisions · Open questions |
| Challenge file | 1 line per finding + 1-line AC | No context paragraphs, no cross-round citations |

Exceeding a cap requires a 1-sentence rationale in `office/decisions/`. Never quietly.

### Banned words

Grep-verifiable. If any saved artifact contains these, lint fails:

`canonical` · `vocab` · `vocabulary` · `orthogonal` · `umbrella` · `posture` · `cliff edge` · `defense in depth` · `self-describing` · `first-class` · `blast radius` · `load-bearing`

Replace with the concrete thing (a field name, a table name, a specific behavior). If you can't, you don't understand it yet.

### No meta-refs

Artifacts do not cite other artifacts inside their body.

- Bad: "Per B7 answer, create model X" · "Per challenge round 2 C1, use nullable FK"
- Good: "Create model X" · "Add FK as nullable; backfill in next migration."

Rationale lives in `research.md`. Downstream artifacts state decisions, not their history.

### Self-audit before save

Every skill writing an artifact checks, before save:

1. Line count ≤ cap for that artifact type
2. `grep -i` for banned words returns 0
3. No "per X" meta-refs

Fails any check → trim before save. Do not save and fix later.

---

## Compliance

- `/foundry` must apply all principles when maintaining office structure, reference docs, and skills.
- `/pm` must apply Principle 1 and Principle 4 when producing research, directives, and recommendations.
- `/challenge` must check for Principle 1 and Principle 4 violations when reviewing any document — ambiguous instructions and bloated ACs are findings.
- `/build` must apply Principle 1 and Principle 4 when writing plans and acceptance criteria.
- All skills must respect Principle 3 — dangerous operations belong in the deny list, not only in skill text.
- When in doubt, apply the ambiguity test AND the line-cap check. If the document fails either, it's not ready.
