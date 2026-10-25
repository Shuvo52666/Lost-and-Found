
## Getting Started

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd Lost-and-Found
```

Replace `<YOUR_REPOSITORY_URL>` with your GitHub repository link.

### 2. Create and Activate Virtual Environment

Open PowerShell in the project folder.

```powershell
# Create virtual environment
py -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
# Install all required packages
python -m pip install -r requirements.txt
```

### 4. Configure the Database

FindLoop uses the database configured in `config/settings.py`.

If you are using SQLite and want to keep your previous
users, posts, communities, and messages:

1. Stop the Django server.
2. Find `db.sqlite3` in your original project.
3. Make a backup of the database.
4. Copy the original `db.sqlite3` into the cloned
   project's root directory, beside `manage.py`.
5. Copy the original `media/` folder to restore
   uploaded images.
6. Confirm that `config/settings.py` points to
   the copied database.

**Important:** Never upload a database containing real
user accounts, messages, or private data to a public
GitHub repository.

### 5. Check Django Configuration

```powershell
# Check Django configuration
python manage.py check

# Check database migrations
python manage.py showmigrations

# Apply pending migrations
python manage.py migrate
```

Do not delete existing migration files or your old
database to resolve setup errors.

### 6. Verify Previous User Accounts

```powershell
# Open Django shell
python manage.py shell
```

Inside the shell:

```python
from django.contrib.auth import get_user_model

User = get_user_model()

print("Total users:", User.objects.count())

for user in User.objects.all():
    print(user.username, user.is_active)
```

If your previous usernames appear, the cloned project
can read their records.

Exit the shell:

```python
exit()
```

### 7. Start the Development Server

```powershell
# Start ASGI server with automatic reload
python -m uvicorn config.asgi:application --reload
```

Open your browser:

http://127.0.0.1:8000/

### 8. Login

Log in using your previous username and password
if your original database has been restored.

You do not need to create another superuser when
the original superuser account already exists.

For a completely new database, you can optionally
create a superuser:

```powershell
python manage.py createsuperuser
```

### 9. Run Tests

```powershell
python manage.py test
```

## Troubleshooting

### Previous Users Cannot Log In

First, check which database Django is accessing:

```powershell
python manage.py shell
```

```python
from django.conf import settings

print(settings.DATABASES["default"])
```

Verify that the configured database is the correct
original database.

### Missing Database Tables

```powershell
python manage.py showmigrations
python manage.py migrate
```

### Missing Python Packages

```powershell
python -m pip install -r requirements.txt
```

### Missing Uvicorn

```powershell
python -m pip install uvicorn
```

Add Uvicorn to `requirements.txt` if it is required
for your project.

### Missing Uploaded Images

Copy the original `media/` folder and verify
`MEDIA_ROOT` and `MEDIA_URL` in Django settings.
