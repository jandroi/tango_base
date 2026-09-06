# main_home

Public pages and shared base templates.

## Owns

- Public views: `home`, `what_we_do`, `how_it_works`, `about`, `contact`
- Authenticated landing: `main_distributor` at `/main/` (module selector); `/dashboard/` redirects to it
- Shared templates used across apps (`base.html`, `base_landing.html`)

## Routes

- `/`
- `/what_we_do/`
- `/how_it_works/`
- `/about/`
- `/contact/`
- `/main/` (login required)
- `/dashboard/` → redirects to `/main/`

## Notes

- Views are class-based (`TemplateView`) and intentionally simple.
- Feature apps extend templates from this app.
