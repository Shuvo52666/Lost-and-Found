# FindLoop — Community Lost & Found Platform

**FindLoop** is a community-based lost-and-found web application built with **Django**. It helps people report missing belongings, share found items, search posts within their communities, and contact post owners through an organized messaging workflow.

The platform brings together community-specific feeds, optional ownership-verification questions, contact requests, notifications, and moderation tools to make recovering lost items easier and safer.

> **Project status:** Academic/team project under active development. Some integrations and features may differ between branches. This README describes the current project design and known workflows; verify implementation details against your checked-out code.

## Features

### Accounts and profiles
- User registration and login.
- User profiles, including profile pictures where available.
- Authenticated access to posting and contact-related functionality.

### Communities
- Community-based organization of lost-and-found posts.
- Join or access communities using the application's membership workflow.
- Community profile with description, member count, and administrator information.
- Community administrators can access post management tools.

### Lost-and-found feed
- Publish **Lost** or **Found** posts with a caption, description, and optional image.
- Browse posts in a scrollable, social-style community feed.
- Search posts by keyword and filter by **Lost** or **Found**.
- See post status, author, community, and relative posting time.
- Expand/collapse comments and write new comments directly from the feed.
- Message a post owner or report an inappropriate post.

### Ownership verification and contact requests
- Add optional verification questions when creating a post.
- A person contacting the post owner can provide answers before proceeding to conversation.
- Answers are submitted as part of the initial contact-request workflow.
- Contact requests can require acceptance by the owner before unrestricted conversation.

### Messaging and notifications
- Inbox interface for contact requests and conversations.
- Unread-message and recent-request notifications.
- A notification flow for community reports and administration.

> Real-time message delivery / Socket.IO behavior is an area of development. Do not assume it is configured in every version of the repository.

### Reports and moderation
- Users can report posts created by other users.
- Community administrators can review/manage posts in their community.
- Moderation pages are intended to be restricted on the **server side**, not just by hidden buttons in the interface.

## Technology stack

| Layer | Technology |
| --- | --- |
| Backend | Python, Django 5.2.x |
| Frontend | Django templates, HTML, CSS, JavaScript |
| Database | Configured through Django settings (check your local `settings.py`) |
| Image uploads | Django media storage; Pillow may be required |
| Development | Git, GitHub, Python virtual environment |

## Project structure

The main application areas are organized approximately as follows (files can vary by branch):

```text
Lost-and-Found/
├── manage.py
├── config/                 # Django project settings and ASGI/WSGI configuration
├── accounts/               # Authentication and user profiles
├── communities/            # Communities, memberships, and administrators
├── newsfeed/               # Lost/found posts, comments, reports, moderation
├── verification/           # Verification questions and answers
├── messaging/              # Contact requests and conversations
├── notifications/          # User and administrator notifications
├── templates/              # Shared and app-specific HTML templates
│   ├── base.html
│   └── newsfeed/
│       ├── feed.html
│       └── moderate_post.html
├── static/                 # CSS, images, and other static assets
├── media/                  # Uploaded content (development; usually ignored by Git)
├── tests/                  # Tests, when present
└── requirements.txt        # Dependencies, when included
```

## Getting started

### Prerequisites
- Python installed on Windows.
- Git installed to clone the project.
- Project dependencies listed in `requirements.txt`.

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd Lost-and-Found
```

Replace `<YOUR_REPOSITORY_URL>` with your repository URL and use the cloned folder's actual name.

### 2. Setup and run (Windows PowerShell)

Run these commands from the project folder (the same folder as `manage.py`):

```powershell
# Create virtual environment (first time only)
py -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Check Django configuration
python manage.py check

# Check migrations
python manage.py showmigrations

# Apply database migrations
python manage.py migrate

# Create a superuser (first time only, if needed)
python manage.py createsuperuser

# Start server with automatic reload
python -m uvicorn config.asgi:application --reload
```

Open **http://127.0.0.1:8000/** in your browser.

## How the application works

### Post a lost or found item
1. Sign in and open a community you belong to.
2. Select **Create Post**.
3. Choose **Lost** or **Found** and enter the item information.
4. Upload an image if desired.
5. Optionally add verification questions, then publish.

### Search and interact with posts
1. Open the community feed.
2. Use search and the Lost/Found filter.
3. Expand **Comments** to read or write comments.
4. Use **Message** to begin the contact-request flow for another user's eligible post.
5. Use **Report** to flag an inappropriate post.

### Contact and verification workflow

```text
User discovers a post
        |
        v
Chooses Message / Contact
        |
        v
Answers optional verification questions
        |
        v
Contact request reaches the post owner
        |
        v
Owner reviews and accepts the request
        |
        v
Conversation can continue
```

### Community moderation workflow

```text
User reports a post
        |
        v
Community administrator receives/reviews the report
        |
        v
Administrator opens post-management or moderation view
        |
        v
Administrator decides the appropriate action
```

Administrative permissions must be enforced in Django views, even if UI controls are visible only to an administrator.

## Main Django apps

| App | Responsibility |
| --- | --- |
| `accounts` | Users, authentication, profiles |
| `communities` | Communities, memberships, administrators |
| `newsfeed` | Posts, search/filter, comments, reports, post moderation |
| `verification` | Optional post ownership-verification questions and answers |
| `messaging` | Contact requests, inbox, conversations |
| `notifications` | Unread messages, request activity, report notices |

## Common development commands

```bash
# Check project configuration
python manage.py check

# Create migration files after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test

# Start local server (ASGI with automatic reload)
python -m uvicorn config.asgi:application --reload
```

## Troubleshooting

**`TemplateDoesNotExist: newsfeed/moderate_post.html`**  
Ensure the moderation template exists at `templates/newsfeed/moderate_post.html` and that the Django `TEMPLATES` setting includes the project's template directory. The view must also render the correct template path.

**Uploaded images do not appear**  
Check `MEDIA_URL`, `MEDIA_ROOT`, image fields, and development-only media URL routing. Ensure the configured file storage backend is valid.

**`InvalidStorageError` during post creation**  
Check the `STORAGES` configuration and Django version-specific settings. Do not remove necessary storage backends.

**ASGI server fails because `SECRET_KEY` is missing**  
Configure the expected environment variable before launching the ASGI application.

**Template syntax errors**  
Check Django template tags and matching `{% if %}` / `{% endif %}` blocks. Django templates do not use Python syntax everywhere.

**Old users cannot log in after cloning**  
Check that the cloned project points to the original database and that existing users are present. Creating a new superuser does not recover your old accounts. For SQLite, back up and restore `db.sqlite3` before applying migrations. Copy `media/` separately for uploaded files.

## Security considerations

- Require authentication for protected actions.
- Confirm community membership where required.
- Validate post ownership and community-admin status **inside views**.
- Use CSRF protection on forms that change data.
- Validate uploaded files and limit upload sizes as needed.
- Avoid exposing verification answers or sensitive conversation information to unauthorized users.
- Keep production secrets out of version control.
- Set `DEBUG = False` and configure hosts, HTTPS, static/media handling, and a production-ready database before deployment.

## Team and contribution workflow

This project is developed by a **three-member team**.

A simple workflow for contributors:

1. Pull the latest changes before starting work.
2. Create a branch for the feature or fix.
3. Make focused commits with clear messages.
4. Run checks and tests for the changed parts.
5. Open a pull request or coordinate merging with the team.

Example commit messages:

```text
feat(newsfeed): add community lost and found filters
feat(messaging): add contact request approval flow
feat(verification): add optional verification questions
feat(notifications): show unread requests in inbox
fix(newsfeed): align post actions in one row
fix(moderation): restrict moderation to community admin
```

## Future improvements

Potential enhancements (not a claim that these are already implemented):

- Reliable real-time messaging and notifications.
- Better filtering, pagination, and image optimization.
- More comprehensive automated tests.
- Accessibility and mobile UI refinements.
- Deployment and CI/CD configuration.

## License

No license is specified in this README. Add a `LICENSE` file if your team decides to grant permissions for reuse or redistribution.

---

**FindLoop — Connecting communities to reunite people with their belongings.**
