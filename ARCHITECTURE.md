# Tango Base — Architecture

This scaffold follows the Tango Modular Django convention. This file describes how `tango_base` implements that convention.

## Layering

- **`main_project/`** — configuration only (settings, URLs, WSGI, ASGI). No business logic.
- **`main_*` apps** — platform layer, shared across all Tango projects:
  - `main_users` — email-based auth, profile
  - `main_home` — shared `base.html`, landing page, 404
  - `main_media` — project media root (`MEDIA_ROOT`)
- **`app_*` apps** — feature/micro-SaaS layer. Each one self-contained, no hard cross-app coupling.

> Note: this scaffold uses `main_home` for the shared layout role. Keep that choice consistent inside a project.

## What lives in each app

```
my_app/
  __init__.py
  apps.py
  models.py
  views.py            # CBVs by default
  urls.py             # app_name = "<app_name>"
  forms.py            # if needed
  admin.py
  migrations/
  templates/<app_name>/
  static/<app_name>/  # optional
  data/               # optional, app-local pipeline data
```

## URL wiring

`main_project/urls.py` mounts apps; each app owns its internal routes.

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('main_users.urls')),
    path('', include('main_home.urls')),
    # path('<feature>/', include('app_<feature>.urls')),
]
```

## Auth

- `AUTH_USER_MODEL = 'main_users.MainUser'`
- Email is the unique identifier. There is no username field.
- `LOGIN_URL = '/users/login/'`, `LOGIN_REDIRECT_URL = '/'`, `LOGOUT_REDIRECT_URL = '/'`

## Templates

- All templates extend `"main_home/base.html"`.
- `base.html` provides a Tailwind+Bootstrap layout with a fixed top navbar (login link or user dropdown depending on auth state) and exposes blocks: `title`, `content`, `brand`, `tagline`, `og_title`, `og_description`, `og_image`.
- Don't duplicate layout in feature apps — extend the base.

## Views

- Default to Class-Based Views: `TemplateView`, `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`.
- Function views only if there's a clear reason.
- Business logic belongs in models / app-local services, not in templates.

## Models & migrations

- Each app owns its migrations.
- Avoid cross-app foreign keys except `settings.AUTH_USER_MODEL`.
- Naming: model-specific PKs (`brand_id`, `property_id`) when applicable, general → particular.

## Media vs app-local data

- User uploads → project `MEDIA_ROOT` (`main_media/`).
- App-internal pipeline data (CSV inputs, ETL artifacts) → inside the app: `app_<name>/data/`.

## When you start a new project from this scaffold

1. Copy the folder, drop `.git`, init a fresh repo.
2. Run `makemigrations main_users` then `migrate` (no migrations are committed — see `main_users/migrations/` is empty by design).
3. Create your first feature app with `python manage.py startapp app_<feature>` and follow the app structure above.
4. Replace `main_home/templates/main_home/home.html` with your landing copy.
5. Replace logos in `static/main_home/img/` with your brand assets if not Tango-branded.
