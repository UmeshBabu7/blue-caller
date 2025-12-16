## Blue Caller

Blue Caller is a Django-based platform for **booking verified skilled workers** (plumbers, electricians, carpenters, painters, and more).  
It supports separate **customer and worker flows**, appointment booking and ratings in a modern landing page.

### Features

- **Modern landing page** at `/` with Tailwind-based UI and marketing sections.
- **Authentication & accounts**
  - Custom user model (`accounts.CustomUser`) with `django-allauth` for login/signup.
  - Session remembering, and account management.
- **Workers & customers**
  - Worker and customer profiles linked to users (with profile pictures, phone numbers, and optional documents).
  - Worker shift preferences and geolocation fields (latitude/longitude).
- **Appointments & workflow**
  - Customers can request appointments with workers.
  - Status flow: pending → accepted/rejected → completed.
  - Separate worker and customer dashboards and appointment views.
- **Ratings & reviews**
  - Customers can rate workers per appointment.
  - Worker rating summary with Bayesian average, rating breakdown, and counts.
- **Location-aware features**
  - Distance and location helpers (via custom template tags and model fields) to work with user and worker locations.

### Tech Stack

- **Backend**: Django 5.1.1
- **Database**: SQLite (default, via `db.sqlite3`)
- **Auth**: `django-allauth` with a custom user model
- **Forms & UI**: `django-crispy-forms`, `crispy-tailwind`, Tailwind CSS (CDN)
- **Phone Numbers**: `django-phonenumber-field`, `phonenumbers`
- **Images & Files**: `Pillow`

### Project Structure

- `config/` – Django project settings, URL routing, WSGI/ASGI configuration.
- `accounts/` – Custom user model and related entities (project categories, plans, user activity).
- `jobs/`
  - `models.py` – Services, workers, customers, appointments, ratings, notifications.
  - `views.py` – Landing redirection, dashboards, appointment and rating flows.
  - `urls.py` – App URLs (worker list/detail, customer/worker dashboards, appointment actions).
  - `templates/jobs/` – Worker/customer dashboards, lists, detail, forms, rating and appointment templates.
  - `templatetags/` – Custom tags and filters (distance, rating helpers, etc.).
- `templates/landing/index.html` – Main marketing/landing page.
- `templates/account/` – Login & signup templates (for `django-allauth`).
- `static/landing/` – CSS, JS, images, and fonts for the landing page.
