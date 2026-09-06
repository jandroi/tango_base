# Challenge Rubric

> The challenger's exact checks as a binary list. Every line is answered YES or NO by reading the target — no judgment.
> Used by: the `challenge` agent (the check), `/build` (self-audit before handoff), the loop orchestrator (automated gate).
> Only `/foundry` can modify this file.
>
> **How to read this:** YES on a check = compliant. A finding is raised for every NO. The finding's tier comes from the Tier Assignment rule at the bottom. The overall verdict equals the highest-tier open finding.
> **Principle references are by name** (Zero Ambiguity, File Naming, Security, Lean Output / Clean Workspace) because principle *numbers* differ across offices.

---

## Group 1 — Ambiguity words

Per the **Zero Ambiguity** principle. A word counts only if it appears **outside backticks/quotes** and is **used as an instruction** (not as data — e.g., a line defining this rubric may name the word).

- Is the artifact free of "good" used as an instruction?
- Is it free of "clean", "thorough", "ensure", "appropriate"?
- Is it free of "as needed", "improve", "relevant", "properly", "comprehensive"?
- Count of ambiguity-word instruction-uses = 0?

## Group 2 — Line caps

- Is every modified/created SKILL.md ≤ 80 lines?
- Does each SKILL.md front-load its critical rules (First Steps / Output Contract before "What You Do NOT Do")?
- Is each acceptance criterion a single checkable statement (not a paragraph bundling 3+ checks)?

## Group 3 — Banned words / unverifiable claims

- Is the artifact free of unverifiable status claims ("works", "done", "everything passes") stated **without** a file:line, test name, or count as evidence?
- Does every "done/passed" claim cite specific evidence (file:line, test name, or count)?
- Is the artifact free of the office's banned bloat words (the challenge agent's Lean-output list)?

## Group 4 — Test-coverage categories (code artifacts only)

Per `testing_principles.md` (Exhaustive Interaction Coverage). For any AC or handover that claims tests:

- Does each view/endpoint name **Access** tests (auth, unauth, wrong-permission, superuser)?
- Does it name **Action** tests (every button, link, form submit, filter, sort)?
- Does it name **Form-input** tests (valid, empty, special chars `<script>`/`'; DROP`/unicode, max/min length)?
- Does it name **State** tests (empty list, single item, many, paginated, filtered-to-zero)?
- Does it name **Error-path** tests (404, 403, 405, validation errors)?
- Does it name **Redirect** tests (correct destination after create/delete/login)?
- Is the test count stated as a number, not "several/many"?

## Group 5 — Anti-patterns

- Does each task in the artifact list its anti-patterns (what NOT to do)?
- Is the artifact free of every anti-pattern its own anti-pattern list names?
- For skills: does the artifact avoid overlapping scope with an existing skill (no two skills owning one task)?

## Group 6 — Convention checks

- Does every produced filename follow the **File Naming** principle (`<topic>.md`, or `<topic>_<reference>_YYYYMMDD_HHMM.md`)?
- Does every SKILL.md have valid frontmatter (`name`, `description`, `user_invocable`)?
- Is the file saved in its correct office location (per `office_flow_process.md`)?
- Does every acceptance criterion reference a specific file, line, count, or condition (verifiable by reading the output)?
- **Isolated-reader / intent check:** Could a reader with zero build-conversation context misread the **intent** of this artifact (not just an AC)? Answer NO to pass.

---

## Tier Assignment (binary — assign every finding a tier by rule, not feel)

- **Critical** — the finding breaks a stated AC, violates a **Zero Ambiguity** or **Security** rule, OR makes the artifact misbuildable by an isolated reader.
- **Important** — the finding weakens a binary AC (makes it judgment-dependent) OR omits required coverage (a test category, an anti-pattern list, a named worker).
- **Minor** — the artifact still passes every AC and every principle with the finding unaddressed; it is a refinement, not a gap.

**Overall verdict = the highest-tier open finding.** Any open Critical → NEEDS WORK. No Critical but an open Important → NEEDS WORK. Only Minor open → MINOR ISSUES. Nothing open → PASS.
</content>
