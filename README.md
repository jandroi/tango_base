# tango_base

Reusable Django scaffold for Tango projects. Spin up a new project with login, profile, landing page, and admin already wired.

Includes:

- `main_project/` — Django settings, URLs, WSGI/ASGI (config only)
- `main_users/` — email-based custom user model, login/logout/register/profile views
- `main_home/` — `base.html`, landing page, 404
- `main_media/` — project-level media root (with `default_profile_picture.jpg` only)
- `static/main_home/img/` — Tango logos
- `CLAUDE.md` — fillable harness guidance (`<...>` placeholders)
- `office/` — project office: `strategy/` lean canvas skeleton, `governance/`, `builds/backlog.md`
- `.claude/skills/` + `.claude/agents/` — 12 skills and the challenge agent
- `env.example` — every secret the settings read

## Use as a template for a new project

Full checklist (placeholders, leak check, acceptance): studio `_governance/project_office_template.md`.

```bash
# 1. Copy the folder, drop the existing git history
cp -r tango_base tango_<name>
cd tango_<name>
rm -rf .git

# 2. Replace <project> and <YYYY-MM-DD> placeholders in CLAUDE.md, env.example, office/

# 3. Secrets: copy env.example to .env and set a fresh DJANGO_SECRET_KEY
#    python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"

# 4. Install dependencies (shared tango_base conda env, or your own)
pip install -r requirements.txt

# 5. Generate the initial main_users migration and apply it
python manage.py makemigrations main_users
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Run the dev server
python manage.py runserver
```

Then open:

- Home — http://127.0.0.1:8000/
- Login — http://127.0.0.1:8000/users/login/
- Register — http://127.0.0.1:8000/users/register/
- Profile — http://127.0.0.1:8000/users/profile/
- Admin — http://127.0.0.1:8000/admin/

## Configuration

`main_project/settings.py` reads everything sensitive from the environment with safe dev fallbacks:

| Variable                    | Purpose                                | Default                              |
| --------------------------- | -------------------------------------- | ------------------------------------ |
| `DJANGO_SECRET_KEY`         | Secret key                             | dev-only insecure key (CHANGE)       |
| `DJANGO_DEBUG`              | `1` or `0`                             | `1`                                  |
| `DJANGO_ALLOWED_HOSTS`      | comma-separated hostnames              | `localhost,127.0.0.1`                |
| `DJANGO_EMAIL_BACKEND`      | email backend                          | `console.EmailBackend` (prints mail) |
| `DJANGO_EMAIL_HOST`         | SMTP host                              | `''`                                 |
| `DJANGO_EMAIL_PORT`         | SMTP port                              | `587`                                |
| `DJANGO_EMAIL_USE_TLS`      | `1` or `0`                             | `1`                                  |
| `DJANGO_EMAIL_HOST_USER`    | SMTP user                              | `''`                                 |
| `DJANGO_EMAIL_HOST_PASSWORD`| SMTP password                          | `''`                                 |
| `DJANGO_DEFAULT_FROM_EMAIL` | default sender                         | `noreply@example.com`                |

For production, set `DJANGO_DEBUG=0`, a real `DJANGO_SECRET_KEY`, the production hostnames in `DJANGO_ALLOWED_HOSTS`, and SMTP credentials.

## Adding a feature app

Per the Tango convention, feature apps go under `app_<feature_name>/` and stay self-contained.

```bash
python manage.py startapp app_my_feature
```

Then:

1. Add `'app_my_feature'` to `INSTALLED_APPS` in `main_project/settings.py`.
2. In `app_my_feature/urls.py`, set `app_name = 'my_feature'` and define routes.
3. Mount it in `main_project/urls.py`:
   ```python
   path('my_feature/', include('app_my_feature.urls')),
   ```
4. Templates go in `app_my_feature/templates/app_my_feature/` and extend `main_home/base.html`.

See `ARCHITECTURE.md` for the full convention.
"# tango_base" 
