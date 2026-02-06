import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, Response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from .db import init_db, create_user, get_user_by_email, create_entry, list_entries_for_patient, list_all_entries, get_entry, delete_entry, update_entry
from .storage.git_adapter import GitAdapter
import difflib

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def create_app():
    templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # init DB
    init_db()

    # storage adapter (use GitAdapter under uploads)
    storage = GitAdapter(UPLOAD_FOLDER)


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
            email = request.form['email']
            password = request.form['password']
            role = request.form.get('role', 'patient')
            if get_user_by_email(email):
                flash('User already exists')
                return redirect(url_for('signup'))
            pw = generate_password_hash(password)
            create_user(email, pw, role=role)
            session['user_email'] = email
            return redirect(url_for('index'))
        return render_template('signup.html')


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = get_user_by_email(email)
            if not user or not check_password_hash(user.get('password'), password):
                flash('Invalid credentials')
                return redirect(url_for('login'))
            session['user_email'] = user.get('email')
            return redirect(url_for('index'))
        return render_template('login.html')


    @app.route('/logout')
    def logout():
        session.pop('user_email', None)
        return redirect(url_for('index'))


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
