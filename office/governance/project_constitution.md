# Project Constitution: <project>

> Founding document for this project. Read by `/foundry` when designing project skills, and by all project skills for domain context.
> This is NOT `CLAUDE.md`. CLAUDE.md handles the Claude Code harness (env, commands, routing). This document handles the domain (what we're building, how, and why).
> Only `/foundry` can modify this file.
> Version: YYYY-MM-DD

---

## 1. Product Identity

**What is this product?**
[1-2 sentences. What it does, who it's for.]

**What problem does it solve?**
[1-2 sentences. The pain point, not the feature list.]

**Who is the user?**
[Role/persona. e.g., "Operations managers who oversee 10-50 sites."]

---

## 2. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | [e.g., Python] | [e.g., 3.11] |
| Framework | [e.g., Django] | [e.g., 5.1] |
| Database | [e.g., SQLite → PostgreSQL] | [e.g., 3.45 / 16] |
| Frontend | [e.g., Django templates + HTMX] | [e.g., HTMX 2.0] |
| CSS | [e.g., Bootstrap] | [e.g., 5.3] |
| Package manager | [e.g., conda] | |
| Test framework | [e.g., Django TestCase] | |

**Environment setup command:**
```bash
[e.g., conda run -n tango_base python manage.py <command>]
```

---

## 3. Domain Model

The core concepts and how they relate. Every model name used in code should appear here.

### Entities

| Entity | What it represents | Key relationships |
|---|---|---|
| [e.g., Customer] | [e.g., Organization buying the service] | Has many Orders, has many Contacts |
| [e.g., Order] | [e.g., Individual purchase] | Belongs to Customer, has many LineItems |

### Hierarchy

```
[e.g.,
Customer → Order → LineItem → Fulfilment
Customer → Contract
Order → Invoice → Payment
]
```

### Domain Terminology

| Term | Meaning in this project | Do NOT confuse with |
|---|---|---|
| [e.g., Order] | [A confirmed customer purchase] | [Quote — pre-confirmation pricing] |
| [e.g., Unit] | [A single LineItem on an Order] | [Django unit test] |

---

## 4. App Architecture

How the codebase is organized. Every app folder should appear here.

### App Map

| App | Responsibility | URL root |
|---|---|---|
| [e.g., app_customer_core] | [Customer and contact management] | [/customers/] |
| [e.g., app_orders] | [Order processing and line items] | [/orders/] |
| [e.g., main_users] | [Custom email-based auth] | [/users/] |
| [e.g., main_home] | [Shared layout and landing pages] | [/] |

### Architectural Rules

| Rule | Rationale |
|---|---|
| [e.g., `main_` apps hold shared infrastructure, `app_` apps hold features] | [Separation of concerns — features don't depend on each other] |
| [e.g., No cross-app imports (only FK relationships)] | [Apps must be independently testable] |
| [e.g., Business logic in models or services, never in templates or views] | [Testability — templates can't be unit tested] |
| [e.g., All views are CBVs with LoginRequiredMixin first] | [Consistency — every view follows the same pattern] |

---

## 5. Coding Conventions

Specific rules that project skills must follow. Each rule must be binary-checkable (Principle 1: Zero Ambiguity).

### Naming

| What | Convention | Example |
|---|---|---|
| [e.g., Model PKs in URLs] | [e.g., Model-specific names: `customer_id`, `order_id`] | [e.g., `path('<int:customer_id>/', ...)`] |
| [e.g., URL namespacing] | [e.g., `app_name` + `name` for every route] | [e.g., `reverse('customers:customer_detail', args=[pk])`] |
| [e.g., Template naming] | [e.g., `<app>/<model>_<action>.html`] | [e.g., `app_customer_core/customer_detail.html`] |

### Patterns

| Pattern | When to use | Example |
|---|---|---|
| [e.g., ListView with pagination] | [Any list that could grow beyond 25 items] | [e.g., `paginate_by = 25`] |
| [e.g., select_related/prefetch_related] | [Any queryset that traverses FK/M2M] | [e.g., `Order.objects.select_related('customer')`] |
| [e.g., Form clean methods] | [Any validation beyond field-level] | [e.g., `def clean_name(self): ...`] |

### Anti-Patterns (things that are NOT allowed)

| Anti-pattern | Why it's banned | What to do instead |
|---|---|---|
| [e.g., Business logic in templates] | [Can't be unit tested] | [Put in model method or service function] |
| [e.g., Raw SQL] | [SQL injection risk, not portable] | [Use Django ORM] |
| [e.g., `|safe` filter without justification] | [XSS risk] | [Escape by default, document exceptions] |

---

## 6. UI/UX Principles

Rules that `/designer` and `/dev` follow for user-facing work.

| Principle | Rule |
|---|---|
| [e.g., Read-only vs. edit separation] | [Detail pages are read-only. Mutations happen in dedicated edit/manage views.] |
| [e.g., Empty states] | [Every list view shows a message when empty, not a blank page.] |
| [e.g., Navigation] | [Every page has breadcrumbs and a back link to its parent.] |
| [e.g., Feedback] | [Every form submission shows a success/error message via Django messages framework.] |

---

## 7. Testing Expectations

What "tested" means in this project (supplements `testing_principles.md` with project-specific rules).

| Rule | Detail |
|---|---|
| [e.g., Auth on every view] | [Every view test includes: authenticated access, unauthenticated redirect, wrong-user 403] |
| [e.g., Test command] | [`conda run -n tango_base python manage.py test`] |
| [e.g., Test data] | [Use obviously fake data: "Test Acme Co", "user@test.com". Never use real names or emails.] |
| [e.g., Fixture strategy] | [Each test class creates its own data in setUp. No shared fixtures across classes.] |

---

## 8. Current State Snapshot

A point-in-time summary to orient new agents. Update when significant changes land.

| Metric | Value | Last updated |
|---|---|---|
| [e.g., Total tests] | [e.g., 47] | [YYYY-MM-DD] |
| [e.g., Migration count] | [e.g., 12] | [YYYY-MM-DD] |
| [e.g., Active apps] | [e.g., 6] | [YYYY-MM-DD] |
| [e.g., Deploy target] | [e.g., PythonAnywhere] | [YYYY-MM-DD] |
| [e.g., Auth model] | [e.g., MainUser with email as USERNAME_FIELD] | [YYYY-MM-DD] |
