# main_home - Architecture Documentation

## Overview

`main_home` is the Django app responsible for the public-facing landing page and brand presentation of the Tango Data Solutions Boutique platform. It serves as the entry point for visitors and provides information about the company's services, values, and offerings.

## Directory Structure

```
main_home/
├── __init__.py                    # Python package marker
├── admin.py                       # Django admin configuration (currently empty)
├── apps.py                        # App configuration
├── models.py                      # Data models (currently empty)
├── views.py                       # View functions
├── urls.py                        # URL routing
├── tests.py                       # Test suite (empty)
├── migrations/                    # Database migrations
│   └── __init__.py
└── templates/
    └── main_home/
        ├── base.html              # Base template with navbar & styling
        ├── home.html              # Landing page (standalone)
        └── 404.html               # Custom 404 error page
```

## Core Components

### 1. URL Configuration (`urls.py`)

**Purpose**: Maps URL patterns to view functions

**Current Routes**:
- `/` → `views.home` (name: 'home')

**Integration**: Included in main project via `path('', include('main_home.urls'))` in `main_project/urls.py`

---

### 2. Views (`views.py`)

**Purpose**: Handle HTTP requests and render responses

**Current Views**:

#### `home(request)`
- **Route**: `/`
- **Template**: `main_home/home.html`
- **Purpose**: Renders the main landing page
- **Authentication**: Not required
- **Context**: Uses Django's built-in `user` context for conditional rendering

---

### 3. Models (`models.py`)

**Status**: Currently empty - no data models defined

**Future Considerations**:
- Contact form submissions
- Newsletter subscriptions
- Service inquiries
- CMS content blocks

---

### 4. Admin (`admin.py`)

**Status**: Currently empty - no admin registrations

**Future Considerations**:
- Register models when added
- Custom admin views for content management

---

### 5. App Configuration (`apps.py`)

**Class**: `MainHomeConfig`
- **Name**: `main_home`
- **Auto Field**: `BigAutoField` (Django default for primary keys)

---

## Templates

### Base Template (`base.html`)

**Purpose**: Shared layout template for authenticated sections of the app

**Key Features**:
- **Meta Tags**: Open Graph and Twitter Card support for social media sharing
- **Styling**:
  - Tailwind CSS (CDN)
  - Bootstrap 5.3 (CSS + JS)
  - Custom CSS variables for brand color palette
- **Color Scheme**:
  ```css
  --color-primary: #4F4759    /* Navbar, titles */
  --color-secondary: #7079A0  /* Table headers */
  --color-accent: #8097D1     /* Submit buttons */
  --color-light: #F2F4F2      /* Light text */
  --color-green: #ACB8B2      /* Accept buttons */
  --color-red: #B2505B        /* Red buttons */
  --color-background: #F2F4F2 /* Page background */
  ```
- **Navigation**:
  - Fixed navbar with Tango branding
  - Conditional rendering based on authentication status
  - User profile dropdown (profile picture, logout)
- **Blocks**:
  - `{% block title %}` - Page title
  - `{% block og_title %}` - Open Graph title
  - `{% block og_description %}` - Open Graph description
  - `{% block og_image %}` - Open Graph image
  - `{% block twitter_title %}` - Twitter Card title
  - `{% block twitter_description %}` - Twitter Card description
  - `{% block twitter_image %}` - Twitter Card image
  - `{% block content %}` - Main page content

**JavaScript**:
- Bootstrap bundle with Popper
- Custom dropdown toggle functionality
- Click-outside to close dropdown

---

### Home Page (`home.html`)

**Purpose**: Standalone landing page (does not extend base.html)

**Structure**:

#### 1. Header/Navigation
- Dark semi-transparent fixed navbar
- Tango branding with tagline
- Conditional links based on authentication
  - Authenticated: Dashboard, Profile
  - Unauthenticated: Login, What We Do, Services, About

#### 2. Hero Section
- Full-width background image (`static/main_home/img/tango_sea_background.jpg`)
- Headline: "Calm, structured, modern data solutions"
- CTAs: "What We Do", "Work With Tango"
- Min height: 60vh
- Dark overlay for text readability

#### 3. Clarity Block
- Gray background section
- Problem statement and value proposition
- Max width: 3xl (centered)

#### 4. Three Pillars
- Grid layout (responsive)
- Icons with titles and descriptions:
  1. **Reliability**: "Give the correct number at the correct time"
  2. **One Source of Truth**: "Metrics that mean the same thing everywhere"
  3. **Time Back**: "Less tracing numbers. More decision making"

#### 5. "How Tango Works" Section
- Numbered steps (1-3):
  1. Align - Data sources working together
  2. Build the backbone - Clean structure
  3. Stable delivery - Reliable reports
- Link to full services section

#### 6. Visual Flow Diagram
- Inputs → Rules → Models → Metrics → Outputs
- SVG icons for each stage
- Visual representation of data pipeline

#### 7. Industries Section
- Four main industries:
  1. **Financial Services**: Transactions, compliance, reconciliation
  2. **Logistics, Procurement & Tendering**: Multi-source data, vendor analytics
  3. **Construction**: Project tracking, resource allocation
  4. **Energy**: Production metrics, consumption patterns
- Card layout with icons
- CTA: "Discuss your industry"

#### 8. About Section
- Company description
- Value proposition
- "What makes us different" - three differentiators

#### 9. Final CTA
- "Let's build something that lasts"
- Conditional CTAs based on authentication
  - Authenticated: "Go to Dashboard"
  - Unauthenticated: "Contact Tango"

#### 10. Footer
- Copyright notice
- Navigation links
- Profile/Login link based on authentication

**Features**:
- Smooth scroll navigation for anchor links
- Responsive design (mobile-first)
- Tailwind CSS (CDN) with custom color configuration
- All SVG icons inline (no external dependencies)

---

### 404 Error Page (`404.html`)

**Purpose**: Custom error page for missing routes

**Design**:
- Extends `base.html`
- Playful "Lost at Sea" theme
- Image: `static/main_branding/img/404_lost_at_sea.png` (note: references different static path)
- CTA: "Return to Safety" button linking to home

**Tone**: Friendly and humorous to soften the error experience

---

## Static Files

**Location**: `static/main_home/` (project-level static directory)

**Assets**:
```
static/main_home/
└── img/
    ├── tango_sea_background.jpg        # Hero section background
    ├── logo_large.png                  # Open Graph image
    ├── logo_small.png
    ├── logo_small_icon_only.png
    ├── logo_small_icon_only_inverted.png
    └── logo_white_large.png
```

**Configuration** (in `settings.py`):
```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

---

## Design System

### Typography
- Modern, clean sans-serif fonts (system defaults)
- Font weights: Regular (400), Semibold (600), Bold (700)
- Responsive text sizing (mobile-first)

### Color Palette
- **Primary Dark**: `#4F4759` - Main brand color
- **Medium**: `#7079A0` - Secondary elements
- **Accent Blue**: `#8097D1` - CTAs and highlights
- **Light**: `#F2F4F2` - Backgrounds and light text
- **Green**: `#ACB8B2` - Success actions
- **Red**: `#B2505B` - Danger/delete actions

### Spacing
- Uses Tailwind's spacing scale
- Consistent padding: sections (py-16 to py-24)
- Max widths: 3xl to 7xl depending on content

### Components
- Cards with subtle shadows and hover effects
- Rounded buttons with transition effects
- Icons using inline SVG (Heroicons style)

---

## Integration Points

### Authentication Context
- Both templates check `user.is_authenticated`
- Conditional navigation and CTAs
- Profile display for authenticated users

### Static Files
- Uses Django's `{% static %}` template tag
- All images served from `static/main_home/img/`
- Requires `STATICFILES_DIRS` configuration for development

### URL Routing
- Main project includes this app at root: `path('', include('main_home.urls'))`
- Links to other apps:
  - `/users/login/` - Login page
  - `/users/profile/` - User profile
  - `/users/logout/` - Logout
  - `/main/` - Authenticated landing (module selector)

---

## User Flows

### Anonymous Visitor
1. Lands on `/` (home page)
2. Explores sections: What We Do, Services, About
3. Clicks "Work With Tango" or "Contact Tango" → redirects to login
4. Can navigate to `/users/login/` to create account

### Authenticated User
1. Lands on `/` (home page)
2. Sees "Dashboard" link in navbar
3. Can access profile via dropdown
4. CTAs redirect to `/main/` (module selector)

---

## Dependencies

### Python Packages
- Django 5.1.5
- No additional packages required for this app

### Frontend Libraries
- **Tailwind CSS** (v3.x) - Utility-first CSS framework (CDN)
- **Bootstrap 5.3** - Component library for base.html (CDN)
- **No JavaScript frameworks** - Vanilla JS for interactions

---

## Future Enhancements

### Content Management
- Add models for dynamic content blocks
- CMS for updating homepage sections without code changes
- Blog/case studies functionality

### Forms
- Contact form submission
- Newsletter subscription
- Service inquiry form
- Integration with email service (already configured in settings.py)

### SEO
- Structured data (JSON-LD) for rich snippets
- Sitemap generation
- robots.txt configuration

### Analytics
- Google Analytics integration
- Event tracking for CTAs
- Conversion tracking

### Performance
- Image optimization (WebP format)
- Lazy loading for images
- Critical CSS inlining

---

## Testing Considerations

### Visual Tests
- Hero image loading
- Responsive breakpoints
- Browser compatibility
- Social media preview cards

### Functional Tests
- Navigation links
- Authentication-based conditional rendering
- Smooth scroll functionality
- Dropdown menu interactions

### Accessibility
- ARIA labels for interactive elements
- Keyboard navigation
- Screen reader compatibility
- Color contrast ratios

---

## Deployment Notes

### Static Files
- Run `python manage.py collectstatic` before production deployment
- Static files will be collected to `STATIC_ROOT` (`staticfiles/`)
- Configure web server (nginx/Apache) to serve from this directory

### Environment Variables
- Ensure `DEBUG = False` in production
- Update `ALLOWED_HOSTS` with production domain
- Configure proper secret key management

### CDN Considerations
- Tailwind and Bootstrap loaded from CDN
- Consider self-hosting for production reliability
- Implement fallback for CDN failures

---

## Maintenance

### Content Updates
- Homepage content currently hardcoded in template
- Updates require template edits and deployment
- Consider CMS implementation for non-technical content updates

### Brand Assets
- Logo and images in `static/main_home/img/`
- Update references if changing directory structure
- Maintain multiple logo versions for different contexts

---

## Contact

For questions about this app's architecture or to request features, contact the development team or refer to the main project documentation.

---

**Last Updated**: December 2025
**Django Version**: 5.1.5
**Python Version**: 3.12+
