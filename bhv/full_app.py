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
    # Allow overriding secure cookie behavior for local testing.
    # If SESSION_COOKIE_SECURE is set in the environment, honor it (1/true/yes = True).
    env_secure = os.environ.get('SESSION_COOKIE_SECURE')
    if env_secure is not None:
        app.config['SESSION_COOKIE_SECURE'] = str(env_secure).lower() in ('1', 'true', 'yes')
    else:
        app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days

    # Optional verbose request logging for debugging upload/CSRF issues.
    # Enable with `BHV_REQUEST_DEBUG=1`.
    app.config['REQUEST_DEBUG'] = str(os.environ.get('BHV_REQUEST_DEBUG', '')).lower() in ('1', 'true', 'yes')
    
    if app.config['REQUEST_DEBUG']:
        # Install a small WSGI middleware to log raw request headers and cookies
        # BEFORE other Flask before_request handlers (CSRFProtect registers a before_request).
        original_wsgi = app.wsgi_app

        def _logging_middleware(environ, start_response):
            try:
                method = environ.get('REQUEST_METHOD')
                path = environ.get('PATH_INFO', '')
                if method == 'POST' and path.startswith('/upload'):
                    print('---MW /upload START---')
                    # print some useful request metadata available at WSGI level
                    print('REQUEST_METHOD:', method)
                    print('PATH_INFO:', path)
                    print('CONTENT_TYPE:', environ.get('CONTENT_TYPE'))
                    print('CONTENT_LENGTH:', environ.get('CONTENT_LENGTH'))
                    print('HTTP_COOKIE:', environ.get('HTTP_COOKIE'))
                    # print a few header-like env vars
                    for k, v in environ.items():
                        if k.startswith('HTTP_'):
                            print(f"{k}: {v}")
                    print('---MW /upload END---')
            except Exception as _e:
                print('Logging middleware error:', _e)
            return original_wsgi(environ, start_response)

        app.wsgi_app = _logging_middleware
    csrf = CSRFProtect(app)
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    # Expose Google client id to templates so the Google Identity button gets the client id
    app.config['GOOGLE_CLIENT_ID'] = google_client_id or ''

    # init DB
    init_db()

    # storage adapter (use GitAdapter under uploads)
    storage = GitAdapter(app.config['UPLOAD_FOLDER'])

    # Inject current year into all templates for footer
    from datetime import datetime as _dt, timezone as _tz
    @app.context_processor
    def inject_year():
        return {'current_year': _dt.now(_tz.utc).year}


    def current_user():
        uid = session.get('user_email')
        if not uid:
            return None
        return get_user_by_email(uid)


    @app.route('/')
    def index():
        return render_template('home.html')


    @app.route('/dashboard')
    def dashboard():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        if user.get('role') == 'admin':
            return redirect(url_for('admin'))
        return redirect(url_for('my_entries'))


    @app.route('/features')
    def features():
        return render_template('features.html')


    @app.route('/how-it-works')
    def how_it_works():
        return render_template('how_it_works.html')


    @app.route('/testimonials')
    def testimonials():
        return render_template('testimonials.html')


    @app.route('/contact')
    def contact():
        return render_template('contact.html')


    @app.route('/profile')
    def profile():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        entries = _normalize_entries(list_entries_for_patient(user.get('email')))
        return render_template('profile.html', user=user, entries=entries)


    @app.route('/ask_me', methods=['GET', 'POST'])
    def ask_me():
        """AI assistant for querying patient data."""
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        
        answer = None
        results = []
        question = None
        
        if request.method == 'POST':
            question = request.form.get('question', '').strip()
            if question:
                # Get user's entries
                patient_id = user.get('email') if user.get('role') == 'patient' else None
                if patient_id:
                    entries = list_entries_for_patient(patient_id)
                elif user.get('role') == 'admin':
                    entries = list_all_entries()
                else:
                    entries = []
                
                # Simple keyword-based search and response
                q_lower = question.lower()
                
                # Count queries
                if any(word in q_lower for word in ['how many', 'count', 'total']):
                    answer = f"You have {len(entries)} entries in your vault."
                    results = entries[:5]  # Show first 5
                
                # List all queries
                elif any(word in q_lower for word in ['show all', 'list all', 'all entries', 'all uploaded']):
                    answer = f"Here are all {len(entries)} entries from your vault:"
                    results = entries
                
                # Keyword search
                elif 'mention' in q_lower or 'about' in q_lower or 'find' in q_lower:
                    # Extract potential keywords after common search terms
                    keywords = []
                    for term in ['mention', 'mentioning', 'about', 'find', 'regarding', 'contains']:
                        if term in q_lower:
                            idx = q_lower.index(term) + len(term)
                            remaining = question[idx:].strip()
                            keywords.extend([w.strip('\"\\\',.;:!?') for w in remaining.split() if len(w) > 3])
                    
                    if keywords:
                        matching = []
                        for e in entries:
                            narrative = (e.get('narrative') or '').lower()
                            filename = (e.get('filename') or '').lower()
                            if any(kw.lower() in narrative or kw.lower() in filename for kw in keywords):
                                matching.append(e)
                        
                        if matching:
                            answer = f"Found {len(matching)} entries matching your query."
                            results = matching
                        else:
                            answer = f"No entries found matching '{', '.join(keywords)}'."
                    else:
                        answer = "Please specify keywords to search for (e.g., 'Find entries mentioning anxiety')."
                
                # Summary
                elif 'summar' in q_lower or 'overview' in q_lower:
                    answer = f"Recovery Journey Summary:\\n\\nTotal Entries: {len(entries)}\\n"
                    if entries:
                        recent = entries[-5:] if len(entries) >= 5 else entries
                        answer += f"\\nMost Recent Uploads:\\n"
                        for e in reversed(recent):
                            answer += f"• {e.get('filename')} - {e.get('narrative', 'No description')[:50]}...\\n"
                    results = entries[-10:]  # Show last 10
                
                # Default response
                else:
                    answer = f"I found {len(entries)} entries in your vault. Try asking:\\n"
                    answer += "• 'Show me all my entries'\\n"
                    answer += "• 'Find entries mentioning [keyword]'\\n"
                    answer += "• 'How many entries do I have?'\\n"
                    answer += "• 'Summarize my recovery journey'"
                    results = entries[:5]
                
                # Normalize results for template
                normalized_results = []
                for e in results:
                    obj = type('Entry', (), {})()
                    obj.filename = e.get('filename')
                    obj.narrative = e.get('narrative', '')
                    obj.patient_id = e.get('patient_id')
                    obj.timestamp = e.get('timestamp', '')
                    normalized_results.append(obj)
                results = normalized_results
        
        return render_template('ask_me.html', question=question, answer=answer, results=results)


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



    def _normalize_entries(raw_entries):
        """Normalize DB results (TinyDB dicts or Mongo docs) into objects
        with consistent attributes: .id, .filename, .narrative, .timestamp, .patient_id"""
        norm = []
        for e in raw_entries:
            elem = type('E', (), {})()
            elem.filename = e.get('filename')
            elem.narrative = e.get('narrative')
            elem.timestamp = e.get('timestamp')
            elem.patient_id = e.get('patient_id')
            # TinyDB Document objects have a .doc_id attribute (int)
            # MongoDB documents have an '_id' field (ObjectId)
            if hasattr(e, 'doc_id'):
                elem.id = e.doc_id
            elif e.get('_id'):
                elem.id = str(e['_id'])
            else:
                elem.id = None
            norm.append(elem)
        return norm


    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        if request.method == 'POST':
            if app.config.get('REQUEST_DEBUG'):
                # DEBUG: print headers/cookies/form to help diagnose missing CSRF/session issues
                try:
                    print('---DEBUG /upload START---')
                    print('Request Headers:')
                    for k, v in request.headers.items():
                        print(f"{k}: {v}")
                    print('Request Cookies:')
                    for k, v in request.cookies.items():
                        print(f"{k}: {v}")
                    print('Form keys:', list(request.form.keys()))
                    print('---DEBUG /upload END---')
                except Exception as _e:
                    print('DEBUG logging failed:', _e)
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
        is_admin = user.get('role') == 'admin'
        return render_template('upload.html', is_admin=is_admin)


    @app.route('/my')
    def my_entries():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        patient_id = user.get('email') if user.get('role')=='patient' else request.args.get('patient_id')
        entries = _normalize_entries(list_entries_for_patient(patient_id))
        return render_template('patient.html', entries=entries, patient_id=patient_id)


    @app.route('/admin')
    def admin():
        user = current_user()
        if not user or user.get('role')!='admin':
            return redirect(url_for('login'))
        entries = _normalize_entries(list_all_entries())
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


    @app.route('/entry/<entry_id>/edit', methods=['GET', 'POST'])
    def entry_edit(entry_id):
        """Edit an existing entry's narrative and optionally replace the file."""
        user = current_user()
        if not user:
            return redirect(url_for('login'))

        # Fetch the entry
        raw = get_entry(entry_id)
        if not raw:
            flash('Entry not found')
            return redirect(url_for('my_entries'))

        # Normalize for consistent access
        entry = _normalize_entries([raw])[0]

        # Access check: patients can only edit their own, admins can edit any
        is_admin = user.get('role') == 'admin'
        if not is_admin and user.get('email') != entry.patient_id:
            flash('Access denied')
            return redirect(url_for('my_entries'))

        if request.method == 'POST':
            new_narrative = request.form.get('narrative', '')
            f = request.files.get('file')

            update_fields = {'narrative': new_narrative}

            # If a new file was provided, replace the stored file
            if f and f.filename:
                new_filename = secure_filename(f.filename)
                rel_path = os.path.join(entry.patient_id, new_filename)
                data = f.read()
                storage.save(rel_path, data, user_id=user.get('email'), action='edit')
                update_fields['filename'] = new_filename

            update_entry(entry_id, **update_fields)
            flash('Entry updated')
            return redirect(url_for('admin') if is_admin else url_for('my_entries'))

        return render_template('edit_entry.html', entry=entry, is_admin=is_admin)


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
