import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, Response
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .db import init_db, create_user, get_user_by_email, create_entry, list_entries_for_patient, list_all_entries, get_entry, delete_entry, update_entry
from .storage.git_adapter import GitAdapter
import difflib

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def create_app(testing: bool = False, upload_folder: str = None):
    templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
    # allow tests or callers to override upload folder
    chosen_upload = upload_folder or UPLOAD_FOLDER
    app.config['UPLOAD_FOLDER'] = chosen_upload
    # testing config toggles
    if testing:
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days
    
    csrf = CSRFProtect(app)
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')

    # init DB
    init_db()

    # storage adapter (use GitAdapter under uploads)
    storage = GitAdapter(app.config['UPLOAD_FOLDER'])


    def current_user():
        uid = session.get('user_email')
        if not uid:
            return None
        return get_user_by_email(uid)


    @app.route('/')
    def index():
        user = current_user()
        if user:
            if user.get('role') == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('my_entries'))
        return render_template('index.html')


    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            email = request.form['email'].strip()
            password = request.form['password']
            if not is_valid_email(email):
                flash('Invalid email format')
                return redirect(url_for('signup'))
            if len(password) < 6:
                flash('Password must be at least 6 characters')
                return redirect(url_for('signup'))
            role = request.form.get('role', 'patient')
            if get_user_by_email(email):
                flash('User already exists')
                return redirect(url_for('signup'))
            pw = generate_password_hash(password)
            create_user(email, pw, role=role)
            session.permanent = True
            session['user_email'] = email
            return redirect(url_for('index'))
        return render_template('signup.html')


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email'].strip()
            password = request.form['password']
            user = get_user_by_email(email)
            if not user or not check_password_hash(user.get('password'), password):
                flash('Invalid email or password')
                return redirect(url_for('login'))
            session.permanent = True
            session['user_email'] = user.get('email')
            return redirect(url_for('index'))
        return render_template('login.html')


    @app.route('/logout')
    def logout():
        session.pop('user_email', None)
        return redirect(url_for('index'))


    @app.route('/auth/google', methods=['POST'])
    @csrf.exempt  # Google token in POST body, not CSRF token
    def auth_google():
        """Handle Google OAuth token from frontend (implicit/token flow)."""
        token = request.form.get('token') or request.json.get('token')
        if not token or not google_client_id:
            flash('Google authentication not configured')
            return redirect(url_for('login'))
        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), google_client_id)
            email = idinfo.get('email')
            user = get_user_by_email(email)
            if not user:
                # Auto-create patient account on first Google login
                create_user(email, '', role='patient')  # empty password for OAuth
            session.permanent = True
            session['user_email'] = email
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Google login failed: {str(e)}')
            return redirect(url_for('login'))



    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        if request.method == 'POST':
            f = request.files.get('file')
            narrative = request.form.get('narrative', '')
            if not f:
                flash('File required')
                return redirect(url_for('upload'))
            filename = secure_filename(f.filename)
            patient_id = user.get('email') if user.get('role')=='patient' else request.form.get('patient_id')
            rel_path = os.path.join(patient_id, filename)
            data = f.read()
            # use storage adapter to save (creates commit)
            storage.save(rel_path, data, user_id=user.get('email'), action='upload')
            # record in DB
            create_entry(patient_id, filename, narrative)
            flash('Uploaded')
            return redirect(url_for('my_entries'))
        return render_template('upload.html')


    @app.route('/my')
    def my_entries():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        patient_id = user.get('email') if user.get('role')=='patient' else request.args.get('patient_id')
        entries = list_entries_for_patient(patient_id)
        return render_template('patient.html', entries=entries, patient_id=patient_id)


    @app.route('/admin')
    def admin():
        user = current_user()
        if not user or user.get('role')!='admin':
            return redirect(url_for('login'))
        entries = list_all_entries()
        return render_template('admin.html', entries=entries)


    @app.route('/uploads/<path:filename>')
    def uploads(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


    @app.route('/entry/<entry_id>/delete', methods=['POST'])
    def entry_delete(entry_id):
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        delete_entry(entry_id)
        flash('Deleted')
        return redirect(url_for('admin') if user.get('role')=='admin' else url_for('my_entries'))


    @app.route('/history/<patient_id>/<filename>')
    def history(patient_id, filename):
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        # basic access check: patients can view their own history; admins can view all
        if user.get('role') != 'admin' and user.get('email') != patient_id:
            flash('Forbidden')
            return redirect(url_for('index'))
        rel = os.path.join(patient_id, filename)
        commits = storage.history(rel)
        return render_template('history.html', commits=commits, patient_id=patient_id, filename=filename)


    @app.route('/diff/<patient_id>/<filename>/<old_sha>/<new_sha>')
    def diff(patient_id, filename, old_sha, new_sha):
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        if user.get('role') != 'admin' and user.get('email') != patient_id:
            flash('Forbidden')
            return redirect(url_for('index'))
        rel = os.path.join(patient_id, filename)
        old_bytes = storage.get(rel, old_sha)
        new_bytes = storage.get(rel, new_sha)
        try:
            old_text = old_bytes.decode('utf-8').splitlines()
        except Exception:
            old_text = old_bytes.decode('latin-1', errors='ignore').splitlines()
        try:
            new_text = new_bytes.decode('utf-8').splitlines()
        except Exception:
            new_text = new_bytes.decode('latin-1', errors='ignore').splitlines()
        ud = difflib.unified_diff(old_text, new_text, fromfile=old_sha, tofile=new_sha, lineterm='')
        diff_text = '\n'.join(list(ud))
        return render_template('diff.html', diff=diff_text, patient_id=patient_id, filename=filename, old=old_sha, new=new_sha)


    @app.route('/file/<patient_id>/<filename>')
    @app.route('/file/<patient_id>/<filename>/<version>')
    def file_version(patient_id, filename, version=None):
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        if user.get('role') != 'admin' and user.get('email') != patient_id:
            flash('Forbidden')
            return redirect(url_for('index'))
        rel = os.path.join(patient_id, filename)
        data = storage.get(rel, version)
        return Response(data, mimetype='application/octet-stream', headers={'Content-Disposition': f'attachment; filename="{filename}"'})


    return app
