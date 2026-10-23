# FindLoop — Community Lost & Found (Django)

A community-based Lost & Found web app based on the project proposal. Django templates, SQLite (local), Pillow image uploads, QR invite codes, moderated contact requests, approved messaging, and in-app notifications.

## Requirements
- Python 3.10+ (prefer Python 3.12 or 3.13)
- pip, Git

## Quick start — macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DJANGO_SECRET_KEY to a random secret
python manage.py makemigrations accounts communities newsfeed verification messaging notifications
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Quick start — Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set DJANGO_SECRET_KEY
python manage.py makemigrations accounts communities newsfeed verification messaging notifications
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
If PowerShell blocks activation, open Command Prompt and run `.venv\Scripts\activate.bat` instead.

Visit http://127.0.0.1:8000/ and log into /admin/ using your superuser account.

**Before your first migration**, keep `AUTH_USER_MODEL='accounts.User'`. After running `makemigrations` on the shared project, **commit the generated migration files to Git**. Other team members should run `migrate` only after pulling the committed migrations.

## Test
```bash
python manage.py check
python manage.py test
```

## Demo walkthrough
1. Sign up as person A, create a community, share its community ID or QR invite.
2. Sign up as person B in a different browser/incognito window, join the community.
3. Person A creates a found-item post and optionally adds verification questions.
4. Person B opens the post and submits a contact request with private ownership details.
5. Person A reviews and approves the request at **Requests**.
6. Both can now talk via **Inbox**. Notifications appear in **Alerts**.
7. Person A marks the post as **Returned** once the item is returned.

## Team conventions
- `main` stays stable; each task gets a `feature/...` branch.
- Create Pull Requests, have another team member review, then merge.
- Never commit `.env`, `db.sqlite3`, `media/`, or `.venv/`.
- Commit `requirements.txt` and **generated migrations**.
- One member should coordinate changes to `models.py` and migrations during integration.

## Known limitations / next improvements
This is a **local demo/MVP**, not a production-hardened release. No email verification, password reset, anti-spam/rate limiting, audit logging, media moderation, multi-image uploads, moderation dashboard, real-time WebSockets, or mobile app. Invitations by code/QR allow anyone holding the code to join. Verification is **manual review by the poster**, not automated proof of ownership. QR code redirects to a join confirmation route; share codes carefully. Messages refresh when the page reloads. There is no integrated object storage or production PostgreSQL configuration. The in-app UI uses the project name **FindLoop** as a replaceable brand. Uploaded media is served by Django *only in DEBUG mode*, not by WhiteNoise.

### Deployment checklist (additional work required)
Use PostgreSQL, protected object storage for user media, HTTPS, a strong secret, trusted CSRF origins, email authentication flows, secure logging, access control review, backups, admin moderation procedures, and deployment smoke tests. Set `DJANGO_DEBUG=False` in production. This starter uses SQLite by default, so do **not** directly deploy it as a public production service without configuring a hosted DB/media storage.
