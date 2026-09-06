# TANGO_CONTEXT.md

## 1. System Overview

This document defines the Tango Modular Django scaffold used across Tango projects.

It is project-agnostic and separates:

- `main_` apps: shared platform and infrastructure layers
- `app_` apps: client or micro-SaaS feature modules

The architecture enforces:

- strict project vs app responsibilities
- reusable and portable apps
- zero hidden cross-app coupling. 
  - rerferencing (fks) are accepted
  - no hard referencing (nulls are permitted when developing)
- clean app-level isolation
- predictable structure for AI-assisted development

## 2. Architectural Principles (Non-Negotiable)

### 2.1 Project vs App Separation

- `main_project/` is configuration only.
- No business logic inside `main_project/`.
- Domain logic must live inside apps.

### 2.2 Apps Are Portable Units

Each app must be self-contained and include:

- `models.py`
- `views.py` (CBVs by default)
- `urls.py` (with `app_name`)
- `templates/<app_name>/`
- optional `static/<app_name>/`
- optional app-local `data/` or `media/` (internal, app-owned)

Allowed dependencies for feature apps:

- Django
- `settings.AUTH_USER_MODEL` (when user relation is needed)
- app-local models/services/helpers

Feature apps must not depend directly on other feature apps.

## 3. Core `main_` Apps (Platform Layer)

These are reusable across Tango deployments.

### 3.1 `main_users`

Purpose: authentication and user lifecycle.

Rules:

- custom user model (email login)
- `AUTH_USER_MODEL = 'main_users.MainUser'`
- no username field
- CBVs only
- templates under `templates/main_users/`
- admin-ready configuration

Must support:

- login
- logout
- password reset
- profile management

### 3.2 `main_home`

Purpose: shared UI shell and layout.

Responsibilities:

- provides `base.html`
- shared navbar/layout/brand tokens
- optional shared CSS/JS

Path:

- `main_home/templates/main_home/base.html`

Feature templates should extend:

```django
{% extends "main_home/base.html" %}
```

Branding logic belongs in `main_home`, not in feature apps.

### 3.3 `main_project`

Purpose: Django settings, URL entrypoint, WSGI/ASGI only.

No feature-domain logic is allowed here.

## 4. Feature `app_` Apps (Micro-SaaS Layer)

Feature apps implement business capabilities (for example: `app_customer_core`, `app_orders`, `app_survey_portal`).

Rules:

- must remain independent
- must not assume other feature apps exist
- must not hardcode project-level URLs
- must define `app_name = "<app_name>"`
- must use CBVs
- templates must live in `templates/<app_name>/`

## 5. Data Management Philosophy

Two storage classes are allowed:

### 5.1 Project Media (User Uploads)

- stored in `MEDIA_ROOT`
- served through `MEDIA_URL`
- used for user-uploaded assets
- centralized by project policy (for example `main_media/`)

### 5.2 App-Local Internal Data

If an app runs ETL, API snapshots, CSV workflows, or batch pipelines, keep data inside the app:

```text
app_example/
  data/
    data_input/
    data_lake/
```

This preserves app portability and pipeline isolation.

## 6. URL Wiring Pattern

In `main_project/urls.py`, the project mounts apps and each app owns internal routes.

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("main_users.urls")),
    path("<feature>/", include("<feature>.urls")),
]
```

## 7. View Philosophy

Default to Class-Based Views:

- `TemplateView`
- `ListView`
- `DetailView`
- `CreateView`
- `UpdateView`
- `DeleteView`

Avoid:

- function-based views unless justified
- business logic in templates

Business logic belongs in models and app-local services/helpers.

## 8. Template Philosophy

- always extend the shared base template
- do not duplicate layout across apps
- feature templates should avoid injecting global CSS rules
- keep presentation separate from business logic

## 9. Model and Migration Discipline

- each app manages its own migrations
- avoid cross-app FKs (except `settings.AUTH_USER_MODEL`)
- avoid circular dependencies
- keep models normalized unless denormalization is intentional

Naming conventions:

- primary keys should be model-specific (`standard_id`, `brand_id`, `property_id`) instead of generic `id`
- naming should go from general to particular

## 10. Deployment Baseline

Default target is PythonAnywhere (or equivalent Django hosting).

Implications:

- static files handled via `collectstatic`
- WSGI entry via `main_project/wsgi.py`
- secrets via environment variables
- never commit hardcoded API keys

## 11. Agent Behavior Rules

When generating code for Tango projects:

- never place feature logic in `main_project/`
- never tightly couple feature apps
- always use `settings.AUTH_USER_MODEL` for user relations
- always namespace URLs
- keep templates inside their app
- default to CBVs
- follow folder conventions strictly

If unsure:

- favor modularity over convenience
- favor explicit structure over shortcuts

## 12. Design Goal

The scaffold should support growth into:

- multi-tenant SaaS platforms
- survey engines
- data-ingestion apps
- AI-assisted analysis modules
- reporting systems
- client-specific vertical solutions

The architecture must remain:

- predictable
- reusable
- replaceable
- testable
- AI-friendly

## 13. Base Scaffold (Reference)

```text
project_root/
  main_project/
  main_users/
  main_home/
  main_media/              # optional central media policy
  app_<feature_a>/
  app_<feature_b>/
```

Use this as the default baseline for all new Tango projects.
