"""Production entrypoint — exports `app` for gunicorn."""
import os
from dotenv import load_dotenv

load_dotenv()

from bhv.full_app import create_app
from bhv.db import get_user_by_email, create_user
from werkzeug.security import generate_password_hash

app = create_app()

# ── Auto-seed default admin on first startup ──────────────────────────────────
# Safe to run on every deploy: does nothing if admin already exists.
_admin_email = os.environ.get('ADMIN_EMAIL', 'admin@bhv.com')
_admin_pass  = os.environ.get('ADMIN_PASSWORD', 'Admin@1234')

with app.app_context():
    if not get_user_by_email(_admin_email):
        create_user(_admin_email, generate_password_hash(_admin_pass), role='admin')
        print(f'[startup] Admin created: {_admin_email}')
    else:
        print(f'[startup] Admin already exists: {_admin_email}')
