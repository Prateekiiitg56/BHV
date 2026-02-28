import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, Response
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .db import (
    init_db, create_user, get_user_by_email, create_entry, list_entries_for_patient,
    list_all_entries, get_entry, delete_entry, update_entry,
    create_disease_template, get_disease_templates, get_disease_template,
    create_disease_stage, get_stages_for_template, clone_disease_template,
    assign_patient_journey, get_patient_journeys, update_patient_journey_stage,
    complete_patient_journey, delete_patient_journey,
    list_all_users, list_all_journeys, admin_delete_journey, admin_rename_journey, delete_user
)
from .storage.git_adapter import GitAdapter
import difflib
from datetime import datetime

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
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', '')

    # Optional verbose request logging for debugging upload/CSRF issues.
    # Enable with `BHV_REQUEST_DEBUG=1`.
    app.config['REQUEST_DEBUG'] = str(os.environ.get('BHV_REQUEST_DEBUG', '')).lower() in ('1', 'true', 'yes')
    
    csrf = CSRFProtect(app)
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    app.config['GOOGLE_CLIENT_ID'] = google_client_id

    # init DB
    init_db()

    # storage adapter (use GitAdapter under uploads)
    storage = GitAdapter(app.config['UPLOAD_FOLDER'])

    # Inject current year into all templates for footer
    @app.context_processor
    def inject_year():
        return {'current_year': datetime.utcnow().year}


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
                patient_id = user.get('email') if user.get('role') == 'patient' else None
                entries = list_entries_for_patient(patient_id) if patient_id else (list_all_entries() if user.get('role') == 'admin' else [])
                
                # Setup OpenRouter client
                api_key = os.environ.get("OPENROUTER_API_KEY")
                
                if not api_key:
                    answer = "Please configure your `OPENROUTER_API_KEY` in the `.env` file first!"
                    # Show some recent entries as fallback
                    results = entries[:5] 
                else:
                    try:
                        from openai import OpenAI
                        client = OpenAI(
                            base_url="https://openrouter.ai/api/v1",
                            api_key=api_key
                        )
                        
                        # Get active journey context
                        journeys = get_patient_journeys(patient_id) if patient_id else []
                        journey_context = f"The patient currently has {len(journeys)} active recovery journeys.\\n"
                        
                        # Format the context for the LLM
                        context = "Here are the patient's journal entries:\\n"
                        for i, e in enumerate(entries):
                            narrative = e.get('narrative', 'No narrative provided')
                            date = e.get('timestamp', 'Unknown date')
                            filename = e.get('filename', 'Unknown document')
                            context += f"Entry {i+1} ({date}) - File: {filename}: {narrative}\\n"
                            
                        prompt = f"{journey_context}\\n{context}\\n\\nBased on these journal entries and context, answer the following question as a helpful assistant. Be engaging, empathetic, and encouraging. Use markdown formatting (like bolding and bullet points) to make the text easy to read.\\n\\nQuestion: {question}"
                        
                        response = client.chat.completions.create(
                            model="liquid/lfm-2.5-1.2b-instruct:free",
                            messages=[
                                {"role": "system", "content": "You are an empathetic, engaging, and highly intelligent AI assistant for the Behavioral Health Vault. Speak directly to the patient. Answer their questions based ONLY on the provided journal entries and context. Use HTML-friendly markdown formatting."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        
                        answer = response.choices[0].message.content
                        
                        # Still do a basic keyword match to populate related records purely for UI linking
                        q_lower = question.lower()
                        matching = [e for e in entries if any(word in (e.get('narrative') or '').lower() or word in (e.get('filename') or '').lower() for word in q_lower.split() if len(word) > 3)]
                        results = matching if matching else entries[:3] # show matching or just some recent ones
                        
                    except Exception as e:
                        print(f"OpenAI/OpenRouter error: {e}")
                        answer = f"Sorry, there was an error communicating with the AI. Error details: {str(e)}"
                        results = entries[:3]
                
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
            if get_user_by_email(email):
                flash('User already exists')
                return redirect(url_for('signup'))
            pw = generate_password_hash(password)
            create_user(email, pw, role='patient')
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
            if user.get('role') == 'admin':
                return redirect(url_for('admin'))
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
        google_client_id = app.config.get('GOOGLE_CLIENT_ID')
        token = request.form.get('token') or request.json.get('token')
        if not token or not google_client_id:
            flash('Google authentication not configured')
            return redirect(url_for('login'))
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                google_client_id,
                clock_skew_in_seconds=60
            )
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



    @app.route('/auth/google/redirect')
    def auth_google_redirect():
        """Standard OAuth2 redirect — sends user to Google consent page. No FedCM."""
        client_id = app.config.get('GOOGLE_CLIENT_ID', '')
        if not client_id:
            flash('Google Sign-In is not configured.')
            return redirect(url_for('login'))
        import urllib.parse
        callback_url = url_for('auth_google_callback', _external=True)
        params = {
            'client_id': client_id,
            'redirect_uri': callback_url,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'online',
            'prompt': 'select_account',
        }
        auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
        return redirect(auth_url)


    @app.route('/auth/google/callback')
    @csrf.exempt
    def auth_google_callback():
        """Receives the OAuth2 authorization code and signs the user in."""
        import urllib.parse, urllib.request, json as _json, base64
        code = request.args.get('code')
        error = request.args.get('error')
        if error or not code:
            flash(f'Google login cancelled: {error or "no code"}')
            return redirect(url_for('login'))
        client_id = app.config.get('GOOGLE_CLIENT_ID', '')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        callback_url = url_for('auth_google_callback', _external=True)
        token_data = urllib.parse.urlencode({
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': callback_url,
            'grant_type': 'authorization_code',
        }).encode()
        try:
            req = urllib.request.Request(
                'https://oauth2.googleapis.com/token',
                data=token_data, method='POST'
            )
            with urllib.request.urlopen(req) as resp:
                token_resp = _json.loads(resp.read())
            id_tok = token_resp.get('id_token', '')
            # Decode JWT payload (Google already verified the code — safe for prototype)
            payload_b64 = id_tok.split('.')[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            user_info = _json.loads(base64.urlsafe_b64decode(payload_b64))
            email = user_info.get('email')
            if not email:
                flash('Could not get email from Google.')
                return redirect(url_for('login'))
            if not get_user_by_email(email):
                create_user(email, '', role='patient')
            session.permanent = True
            session['user_email'] = email
            return redirect(url_for('index'))
        except Exception as exc:
            flash(f'Google login error: {str(exc)}')
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
            elem.stage_id = e.get('stage_id')
            elem.journey_id = e.get('journey_id')
            # TinyDB Document objects have a .doc_id attribute (int)
            # MongoDB documents have an '_id' field (ObjectId)
            if hasattr(e, 'doc_id'):
                elem.id = str(e.doc_id)
            elif e.get('_id'):
                elem.id = str(e['_id'])
            else:
                elem.id = None
            norm.append(elem)
        return norm


    @app.route('/api/journeys')
    def api_journeys():
        user = current_user()
        if not user or user.get('role') != 'admin':
            return {"error": "Unauthorized"}, 403
            
        email = request.args.get('email')
        if not email:
            return []
            
        journeys = get_patient_journeys(email)
        templates = get_disease_templates()
        template_map = {str(t.get('doc_id', t.get('_id', getattr(t, 'id', '')))): t.get('name', 'Journey') for t in templates}
        
        result = []
        for j in journeys:
            if j.get('completed'):
                continue
            jid = str(j.get('id', j.get('_id', getattr(j, 'doc_id', None))))
            tid = str(j.get('template_id'))
            tname = template_map.get(tid, 'Journey')
            result.append({
                'id': jid,
                'name': tname,
                'started_at': j.get('started_at', '')
            })
        return result

    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
            
        patient_email = user.get('email')
        all_journeys = get_patient_journeys(patient_email) if user.get('role') == 'patient' else []
        journeys = [j for j in all_journeys if not j.get('completed')]
        for j in journeys:
            j['id_str'] = str(j.get('id', j.get('_id', getattr(j, 'doc_id', ''))))
        
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
            
            # Simplified routing: User selects a Journey ID, we auto-find the stage.
            journey_id = request.form.get('journey_id')
            stage_id = None
            
            if journey_id:
                active_journeys = get_patient_journeys(patient_id)
                for j in active_journeys:
                    jid = str(j.get('id', j.get('_id', getattr(j, 'doc_id', None))))
                    if jid == journey_id:
                        stage_id = str(j.get('current_stage_id'))
                        break
                
            rel_path = os.path.join(patient_id, filename)
            data = f.read()
            
            # Prepare contextual commit message
            action_desc = f"upload [Stage: {stage_id}]" if stage_id else "upload"

            # use storage adapter to save (creates commit)
            storage.save(rel_path, data, user_id=user.get('email'), action=action_desc)
            # record in DB
            create_entry(patient_id, filename, narrative, stage_id=stage_id, journey_id=journey_id)
            flash('Uploaded')
            return redirect(url_for('my_entries') if user.get('role') == 'patient' else url_for('admin'))
        is_admin = user.get('role') == 'admin'
        templates = get_disease_templates()
        # Pass active journeys to the template for the dropdown menu
        return render_template('upload.html', is_admin=is_admin, journeys=journeys, templates=templates)


    @app.route('/my')
    def my_entries():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        patient_id = user.get('email') if user.get('role')=='patient' else request.args.get('patient_id')
        entries = _normalize_entries(list_entries_for_patient(patient_id))
        now_hour = datetime.now().hour
        return render_template('patient.html', entries=entries, patient_id=patient_id, now_hour=now_hour)


    @app.route('/admin')
    def admin():
        user = current_user()
        if not user or user.get('role') != 'admin':
            return redirect(url_for('login'))
        entries = _normalize_entries(list_all_entries())
        all_users = list_all_users()
        all_journeys = list_all_journeys()
        return render_template('admin.html', entries=entries, all_users=all_users, all_journeys=all_journeys)


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


    @app.route('/admin/templates', methods=['GET', 'POST'])
    def admin_templates():
        user = current_user()
        if not user or user.get('role') != 'admin':
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            desc = request.form.get('description', '')
            if name:
                create_disease_template(name, desc)
                flash('Template created')
            return redirect(url_for('admin_templates'))
        
        raw_templates = get_disease_templates()
        # Inject doc_id as a plain dict key so Jinja can access it as t.id
        templates = []
        for t in raw_templates:
            td = dict(t)
            td['id'] = getattr(t, 'doc_id', None) or td.get('_id', '?')
            templates.append(td)
        return render_template('admin_templates.html', templates=templates)

    @app.route('/admin/templates/<template_id>/stages', methods=['GET', 'POST'])
    def admin_template_stages(template_id):
        user = current_user()
        if not user or user.get('role') != 'admin':
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            desc = request.form.get('description', '')
            order = request.form.get('order_index', 0)
            if name:
                create_disease_stage(template_id, name, order, desc)
                flash('Stage added')
            return redirect(url_for('admin_template_stages', template_id=template_id))
        
        stages = get_stages_for_template(template_id)
        return render_template('admin_stages.html', template_id=template_id, stages=stages)

    @app.route('/admin/assign_journey', methods=['POST'])
    def assign_journey():
        user = current_user()
        if not user or user.get('role') != 'admin':
            return redirect(url_for('login'))
        
        patient_email = request.form.get('patient_email')
        template_id = request.form.get('template_id')
        
        if patient_email and template_id:
            # Clone global admin template into a personal patient copy
            cloned_template_id = clone_disease_template(template_id, patient_email)
            if cloned_template_id:
                cloned_stages = get_stages_for_template(cloned_template_id)
                initial_stage = str(cloned_stages[0].get('id', cloned_stages[0].get('_id', getattr(cloned_stages[0], 'doc_id', None)))) if cloned_stages else None
                assign_patient_journey(patient_email, cloned_template_id, initial_stage)
                flash('Journey assigned and cloned for patient.')
            else:
                flash('Failed to clone timeline.')
        return redirect(url_for('admin'))


    @app.route('/admin/journey/<journey_id>/delete', methods=['POST'])
    def admin_delete_journey_route(journey_id):
        user = current_user()
        if not user or user.get('role') != 'admin':
            return redirect(url_for('login'))
        admin_delete_journey(journey_id)
        flash('Journey deleted.')
        return redirect(url_for('admin') + '#journeys')


    @app.route('/admin/journey/<journey_id>/rename', methods=['POST'])
    def admin_rename_journey_route(journey_id):
        user = current_user()
        if not user or user.get('role') != 'admin':
            return redirect(url_for('login'))
        new_name = request.form.get('new_name', '').strip()
        if new_name:
            admin_rename_journey(journey_id, new_name)
            flash('Journey renamed.')
        return redirect(url_for('admin') + '#journeys')


    @app.route('/admin/user/<user_id>/delete', methods=['POST'])
    def admin_delete_user_route(user_id):
        user = current_user()
        if not user or user.get('role') != 'admin':
            return redirect(url_for('login'))
        # Prevent admin from deleting themselves
        target = list_all_users()
        target_user = next((u for u in target if str(u.get('id')) == str(user_id)), None)
        if target_user and target_user.get('email') == user.get('email'):
            flash('You cannot delete your own admin account.')
            return redirect(url_for('admin') + '#users')
        delete_user(user_id)
        flash('User account deleted.')
        return redirect(url_for('admin') + '#users')


    @app.route('/journey/start', methods=['POST'])
    def start_journey():
        """Patient-facing route to self-serve creating a custom timeline."""
        user = current_user()
        if not user:
            return redirect(url_for('login'))
            
        patient_email = user.get('email')
        template_id = request.form.get('template_id')
        
        if template_id == 'custom':
            try:
                custom_name = request.form.get('custom_journey_name', '').strip() or "My Custom Journey"
                custom_stage = request.form.get('custom_stage_name', '').strip() or "Starting Point"
                
                # Create a brand new custom template for the patient
                new_template_id = create_disease_template(
                    name=custom_name,
                    description="A personalized path created by the patient.",
                    created_by=patient_email
                )
                # Add an initial stage so the journey isn't completely empty
                initial_stage_id = create_disease_stage(
                    template_id=new_template_id,
                    name=custom_stage,
                    order_index=1,
                    description="The beginning of your custom journey."
                )
                assign_patient_journey(patient_email, new_template_id, str(initial_stage_id))
                flash('Custom journey created! You can now add stages from the timeline view.')
            except Exception as exc:
                flash(f'An error occurred: {str(exc)}')

        elif template_id:
            cloned_template_id = clone_disease_template(template_id, patient_email)
            if cloned_template_id:
                cloned_stages = get_stages_for_template(cloned_template_id)
                initial_stage = str(cloned_stages[0].get('id', getattr(cloned_stages[0], 'doc_id', None))) if cloned_stages else None
                assign_patient_journey(patient_email, cloned_template_id, initial_stage)
                flash('Timeline customized and created successfully!')
        
        # We don't have the exact inserted journey_id readily available across TinyDB/MongoDB without more refactoring, 
        # so we rely on the my_journey route's new behavior of defaulting to the most recent journey `journeys[-1]`.
        return redirect(url_for('my_journey'))

    @app.route('/journey/<journey_id>/add_stage', methods=['POST'])
    def add_journey_stage(journey_id):
        user = current_user()
        if not user:
            return redirect(url_for('login'))
            
        patient_id = user.get('email')
        stage_name = request.form.get('stage_name', '').strip()
        stage_desc = request.form.get('stage_description', '').strip()
        
        if not stage_name:
            flash('Stage name is required.')
            return redirect(url_for('my_journey'))
        
        # Verify ownership or admin
        journeys = get_patient_journeys(patient_id)
        current_journey = next((j for j in journeys if str(j.get('id', j.get('_id', getattr(j, 'doc_id', None)))) == journey_id), None)
        
        is_admin = user.get('role') == 'admin'
        
        # If not the owner and not admin, deny
        if not current_journey and not is_admin:
            flash('Journey not found or access denied.')
            return redirect(url_for('my_journey'))
            
        # If admin is accessing, they might be interacting from a different page, but let's assume they are on the patient's view
        if not current_journey and is_admin:
            # For simplicity in this demo, admin must pass the journey context. 
            # In a robust system, we would fetch global journeys. We'll stick to patient scope for now if current_journey is None.
            pass
            
        if current_journey:
            template_id = current_journey.get('template_id')
            stages = get_stages_for_template(template_id)
            
            # The order_index should be the next logical step
            next_order_index = len(stages) + 1
            
            create_disease_stage(
                template_id=template_id,
                name=stage_name,
                order_index=next_order_index,
                description=stage_desc
            )
            flash(f'New stage "{stage_name}" added successfully!')
            
        return redirect(url_for('my_journey'))

    @app.route('/journey/overview')
    def journey_overview():
        """Overview page showing all active journeys as horizontal tracking timelines."""
        user = current_user()
        if not user:
            return redirect(url_for('login'))
            
        patient_id = user.get('email')
        journeys = get_patient_journeys(patient_id)
        
        # Build a list of journey objects with their full stage lists and progress data
        journeys_with_stages = []
        for j in journeys:
            template_id = j.get('template_id')
            
            # Get template to display its name
            templates = get_disease_templates()
            template = next((t for t in templates if str(t.get('doc_id', t.get('_id', getattr(t, 'id', '')))) == str(template_id)), {})
            template_name = template.get('name', 'Recovery Journey')
            
            stages = get_stages_for_template(template_id)
            current_stage_id = str(j.get('current_stage_id', ''))
            
            # Find the index of the current stage for progress calculation
            current_idx = 0
            for i, s in enumerate(stages):
                sid = str(s.get('id', s.get('_id', getattr(s, 'doc_id', None))))
                if sid == current_stage_id:
                    current_idx = i
                    break
                    
            journeys_with_stages.append({
                'journey': j,
                'stages': stages,
                'current_stage_id': current_stage_id,
                'current_idx': current_idx
            })
            
        return render_template('journey_overview.html', journeys_data=journeys_with_stages)

    @app.route('/journey', defaults={'view_journey_id': None})
    @app.route('/journey/<view_journey_id>')
    def my_journey(view_journey_id):
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        
        patient_id = user.get('email')
        journeys = get_patient_journeys(patient_id)
        
        # Get baseline global templates so the patient can start one if they want
        available_templates = get_disease_templates(created_by="admin")

        show_new_journey = request.args.get('new') == '1'

        if not journeys or show_new_journey:
            return render_template(
                'journey.html', 
                journeys=journeys, 
                stages=[], 
                entries=[], 
                current_journey=None,
                available_templates=available_templates,
                show_new_journey=show_new_journey
            )
        
        # Select current journey
        current_journey = None
        if view_journey_id:
            current_journey = next((j for j in journeys if str(j.get('id', j.get('_id', getattr(j, 'doc_id', None)))) == str(view_journey_id)), None)
            
        if not current_journey:
            # Default to the most recently started journey (last in list)
            current_journey = journeys[-1]
            
        template_id = current_journey.get('template_id')
        
        # Get stages
        stages = get_stages_for_template(template_id)
        
        # Get entries
        raw_entries = list_entries_for_patient(patient_id)
        entries = _normalize_entries(raw_entries)
        
        # Group entries by stage (only for THIS journey)
        entries_by_stage = {}
        current_journey_id_str = str(current_journey.get('id', current_journey.get('_id', getattr(current_journey, 'doc_id', None))))
        
        for e in entries:
            # We already have stage_id mapped in _normalize_entries
            sid = str(e.stage_id) if e.stage_id else ''
            # Only include entries that belong to this journey specifically
            if getattr(e, 'journey_id', None) and str(e.journey_id) != current_journey_id_str:
                continue
                
            if sid not in entries_by_stage:
                entries_by_stage[sid] = []
            entries_by_stage[sid].append(e)

        current_template = get_disease_template(template_id)

        return render_template(
            'journey.html', 
            journeys=journeys, 
            current_journey=current_journey, 
            stages=stages, 
            entries_by_stage=entries_by_stage,
            available_templates=available_templates,
            current_template=current_template
        )

    @app.route('/journey/<journey_id>/delete', methods=['POST'])
    def delete_journey(journey_id):
        """Allows a patient or admin to delete a fully custom timeline."""
        user = current_user()
        if not user:
            return redirect(url_for('login'))
            
        patient_id = user.get('email')
        
        # In a real app, an admin might be able to delete any journey. 
        # For this implementation, we restrict deletion to the patient who owns it.
        if delete_patient_journey(journey_id, patient_id):
            flash('Journey timeline deleted successfully.')
        else:
            flash('Failed to delete timeline. You may not have permission.')
            
        return redirect(url_for('my_journey'))

    @app.route('/journey/<journey_id>/download')
    def download_journey(journey_id):
        """Generates a print-friendly HTML view of the completed journey."""
        user = current_user()
        if not user:
            return redirect(url_for('login'))
            
        patient_id = user.get('email')
        
        # Verify ownership
        journeys = get_patient_journeys(patient_id)
        current_journey = next((j for j in journeys if str(j.get('id', j.get('_id', getattr(j, 'doc_id', None)))) == journey_id), None)
        
        if not current_journey:
            flash('Journey not found.')
            return redirect(url_for('my_journey'))
            
        template_id = current_journey.get('template_id')
        stages = get_stages_for_template(template_id)
        
        # Get entries
        raw_entries = list_entries_for_patient(patient_id)
        entries = _normalize_entries(raw_entries)
        
        entries_by_stage = {}
        for e in entries:
            sid = str(e.stage_id) if e.stage_id else ''
            if sid not in entries_by_stage:
                entries_by_stage[sid] = []
            entries_by_stage[sid].append(e)
            
        return render_template(
            'journey_download.html',
            journey=current_journey,
            stages=stages,
            entries_by_stage=entries_by_stage
        )

    @app.route('/journey/<journey_id>/advance', methods=['POST'])
    def advance_journey_stage(journey_id):
        user = current_user()
        if not user or user.get('role') != 'patient':
            return redirect(url_for('login'))
            
        patient_id = user.get('email')
        
        # Verify ownership
        journeys = get_patient_journeys(patient_id)
        current_journey = next((j for j in journeys if str(j.get('id', j.get('_id', getattr(j, 'doc_id', None)))) == journey_id), None)
        
        if not current_journey:
            flash('Journey not found.')
            return redirect(url_for('my_journey'))
            
        template_id = current_journey.get('template_id')
        stages = get_stages_for_template(template_id)
        current_stage_id = str(current_journey.get('current_stage_id'))
        
        # Find index of current stage to determine the next one
        current_idx = -1
        for i, s in enumerate(stages):
            if str(s.get('id', s.get('_id', getattr(s, 'doc_id', None)))) == current_stage_id:
                current_idx = i
                break
                
        # If we found it and it's not the last stage
        if current_idx != -1 and current_idx < len(stages) - 1:
            next_stage = stages[current_idx + 1]
            next_stage_id = str(next_stage.get('id', next_stage.get('_id', getattr(next_stage, 'doc_id', None))))
            update_patient_journey_stage(journey_id, next_stage_id)
            flash('Stage marked as complete! You have moved to the next phase of your journey.')
        elif current_idx == len(stages) - 1:
            complete_patient_journey(journey_id)
            flash('Congratulations, you have completed the final stage of this journey!')
            
        return redirect(url_for('my_journey'))



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
