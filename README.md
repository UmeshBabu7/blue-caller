## Blue Caller

Blue Caller is a Django-based platform for **booking verified skilled workers** (plumbers, electricians, carpenters, painters, and more).  
It supports separate **customer and worker flows**, appointment booking, ratings, and notifications, wrapped in a modern landing page.

### Features

- **Modern landing page** at `/` with Tailwind-based UI and marketing sections.
- **Authentication & accounts**
  - Custom user model (`accounts.CustomUser`) with `django-allauth` for login/signup.
  - Email-based authentication, session remembering, and account management.
- **Workers & customers**
  - Worker and customer profiles linked to users (with profile pictures, phone numbers, and optional documents).
  - Worker shift preferences and geolocation fields (latitude/longitude).
- **Services & pricing**
  - Service categories, services, and subtasks with rich metadata and images.
  - Flexible pricing types (hourly, per square foot, per unit, per inspection, shift-based, fixed).
  - Per-worker subtask pricing with experience levels and night-shift extras.
- **Appointments & workflow**
  - Customers can request appointments with workers for specific services/subtasks.
  - Status flow: pending → accepted/rejected → completed.
  - Separate worker and customer dashboards and appointment views.
- **Ratings & reviews**
  - Customers can rate workers per appointment.
  - Worker rating summary with Bayesian average, rating breakdown, and counts.
- **Notifications**
  - In-app notifications for appointment events and ratings for both workers and customers.
  - Unread notification counts per worker and per customer.
- **Location-aware features**
  - Distance and location helpers (via custom template tags and model fields) to work with user and worker locations.

### Tech Stack

- **Backend**: Django 5.1.1
- **Database**: SQLite (default, via `db.sqlite3`)
- **Auth**: `django-allauth` with a custom user model
- **Forms & UI**: `django-crispy-forms`, `crispy-tailwind`, Tailwind CSS (CDN)
- **Phone Numbers**: `django-phonenumber-field`, `phonenumbers`
- **Images & Files**: `Pillow`

### Project Structure (High Level)

- `config/` – Django project settings, URL routing, WSGI/ASGI configuration.
- `accounts/` – Custom user model and related entities (project categories, plans, user activity).
- `jobs/`
  - `models.py` – Services, workers, customers, appointments, ratings, notifications.
  - `views.py` – Landing redirection, dashboards, appointment and rating flows, notifications.
  - `urls.py` – App URLs (worker list/detail, customer/worker dashboards, appointment actions, APIs).
  - `templates/jobs/` – Worker/customer dashboards, lists, detail, forms, rating and appointment templates.
  - `templatetags/` – Custom tags and filters (distance, rating helpers, etc.).
- `templates/landing/index.html` – Main marketing/landing page.
- `templates/account/` – Login & signup templates (for `django-allauth`).
- `static/landing/` – CSS, JS, images, and fonts for the landing page.

### Getting Started (Local Development)

#### 1. Clone the repository

```bash
git clone <your-repo-url> blue-caller
cd blue-caller
```

#### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Apply migrations

```bash
python manage.py migrate
```

#### 5. (Optional) Load sample data

There is a management command under `jobs/management/commands/load_sample_data.py`.  
If configured and desired, you can run:

```bash
python manage.py load_sample_data
```

to populate example services/workers (adjust as needed based on the command implementation).

#### 6. Create a superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

#### 7. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

### Key URLs

- **Landing page**: `/` (named URL `landing-page`)
- **Get started / worker list**: `/get-started/` (named URL `worker-list`)
- **Account setup / login flow**: `/account-setup/` (named URL `handle-login`)
- **Admin**: `/admin/`
- **Allauth account routes**: `/accounts/` (login, logout, signup, etc.)
- **Customer dashboard**: `/customer/dashboard/`
- **Worker dashboard**: `/worker/dashboard/`

### Media & Static Files

- **Static files** (CSS, JS, images) live under `static/` and are served automatically in development.
- **Uploaded media** (profile pictures, certificates, citizenship images, service images, etc.) are stored under `media/`.
  - The relevant settings in `config/settings.py`:
    - `STATIC_URL = '/static/'`
    - `STATICFILES_DIRS = [BASE_DIR / "static"]`
    - `MEDIA_URL = '/media/'`
    - `MEDIA_ROOT = BASE_DIR / 'media'`

In development, media files are served via `django.conf.urls.static.static` when `DEBUG = True`.

### Authentication & Roles Overview

- **Custom user**: `accounts.CustomUser` extends Django’s `AbstractUser` with optional middle name and contact number.
- **Workers**: Represented by `jobs.Worker`, linked one-to-one to a user; store worker-specific profile info, verification, documents, and availability.
- **Customers**: Represented by `jobs.Customer`, linked one-to-one to a user; store basic profile and location.
- **Roles in the UI**:
  - After login via the handle-login flow, users are guided to create either a worker or customer profile.
  - Separate dashboards and appointment views exist for both roles.

### Environment & Configuration Notes

- Default configuration is aimed at **local development**:
  - `DEBUG = True`
  - `ALLOWED_HOSTS = ["*"]`
  - Email backend is set to console (`EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`).
- Custom authentication configuration in `config/settings.py`:
  - `AUTH_USER_MODEL = 'accounts.CustomUser'`
  - `ACCOUNT_AUTHENTICATION_METHOD = 'email'`
  - `ACCOUNT_EMAIL_REQUIRED = True`
  - `ACCOUNT_USERNAME_REQUIRED = False`
  - `ACCOUNT_UNIQUE_EMAIL = True`

For production, you should:

- Set `DEBUG = False` and configure `ALLOWED_HOSTS`.
- Use a real email backend.
- Configure static and media file hosting appropriately.
- Add proper security settings (HTTPS, secure cookies, etc.).

### Running Tests

If tests are implemented (see `accounts/tests.py`, `jobs/tests.py`), you can run them with:

```bash
python manage.py test
```

### License

Add your preferred license information here (e.g., MIT, proprietary) depending on how you intend to distribute this project.


