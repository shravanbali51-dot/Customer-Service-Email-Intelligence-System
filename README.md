# Customer Service Email Intelligence System

Production-style Flask SaaS application for customer support ticket intake, local AI analysis, admin reply workflows, and admin-only analytics.

## Features

- Custom session-based authentication
- Secure password hashing with Werkzeug PBKDF2
- Public user signup and login
- Private predefined admin login only
- Strict role-based authorization
- User-owned ticket visibility
- Admin view of all tickets
- Sentiment analysis: Positive, Neutral, Negative
- Intent classification: Complaint, Refund, Delivery Issue, Product Inquiry, Technical Issue, Feedback
- Priority detection: Low, Medium, High, Critical
- Editable AI reply generation for admins
- Reply privacy: only the ticket owner can view their admin reply
- Admin-only analytics with charts
- Automatic AI replies for positive, thankful, appreciative, greeting, and non-complaint messages
- Manual admin review for complaints, refunds, delivery issues, technical/account issues, and angry language
- Spam detection with spam-only admin tab
- Corporate Bootstrap UI with dark sidebar, high-contrast cards, Chart.js charts, and responsive layouts

## Default Admin

The app seeds exactly one default admin account at startup:

```text
Username: admin_master
Password: Admin@123
```

Admin signup is not exposed publicly. Any extra admin rows are removed during startup, and only `admin_master` can authenticate as admin.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

If port 5000 is busy, run with Flask directly:

```bash
flask --app run:app run --host 127.0.0.1 --port 8001
```

## Pages

- `/` landing page
- `/admin-login`
- `/user-login`
- `/user-signup`
- `/admin-dashboard`
- `/user-dashboard`
- `/ticket/<ticket_id>`
- `/analytics`

## Database Tables

- `users`
- `admins`
- `tickets`
- `replies`
- `analytics`

The SQLite database is created automatically in `database/customer_service.db`.

## Ticket Statuses

- `AUTO_RESOLVED`: AI sent an appropriate automatic reply.
- `NEEDS_ADMIN_REVIEW`: Admin must review and reply.
- `IN_PROGRESS`: Admin generated a draft or started handling the ticket.
- `RESOLVED`: Admin sent a reply.
- `SPAM`: Hidden from the main admin queue and visible in the spam tab.

## Project Structure

```text
app/
  ai/
  models/
  services/
  __init__.py
  config.py
  extensions.py
  security.py
  routes/
database/
  schema.sql
static/
  css/
  js/
templates/
  index.html
  admin_login.html
  user_login.html
  user_signup.html
  admin_dashboard.html
  user_dashboard.html
  ticket_details.html
  analytics.html
requirements.txt
run.py
```
