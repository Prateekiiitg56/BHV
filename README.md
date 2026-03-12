# BHV: Behavioral Health Vault

The Behavioral Health Vault (BHV) is a minimalist, secure, and professional platform designed to record the recovery journeys of individuals with serious mental illnesses. It complements traditional Electronic Health Records (EHRs) by storing patient-provided images (photographs, drawings) alongside their associated textual narratives.

## Key Features

- **Immutable Storage**: Every file upload creates a version-controlled Git commit, ensuring an audit trail of changes.
- **Narrative Tracking**: Associated text narratives for every image or entry.
- **Visual Analysis**: Built-in color analysis algorithm to track emotional trends over time.
- **Recovery Journeys**: Structured clinical pathways to guide and track patient progress.
- **Research Dashboard**: Admin-level insights into population-wide mood trends and clinical data.
- **Secure Authentication**: Traditional email/password login and quick Google OAuth integration.
- **Zero-Setup Deployment**: Uses an embedded TinyDB by default but can scale to MongoDB for production.

---

## Quick Start

### 1. Prerequisites
- Python 3.8+
- Git

### 2. Setup
```bash
# Clone the repository
git clone <repo-url>
cd BHV

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy the template to create your environment file:
```bash
cp .env.example .env
```
*(Optionally edit `.env` for MongoDB or Google OAuth settings. The app works out-of-the-box without them using TinyDB fallback.)*

### 4. Running the App
**Development Mode:**
```bash
python run.py
```
**Production Mode:**
```bash
gunicorn app:app --config gunicorn.conf.py
```

### 5. Access
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Guidelines for contributing to BHV.
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**: Standards for behavior in this project.
- **[FEATURES_IMPLEMENTED.md](FEATURES_IMPLEMENTED.md)**: Detailed log of current capabilities.

---

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: TinyDB (embedded) or MongoDB
- **Versioning**: Git (via GitPython)
- **Frontend**: Vanilla HTML/JS with a clean, professional "Alaska" theme (Sage Green palette).
- **Deployment**: Gunicorn / Procfile-ready for platforms like Render.

---

## License
Licensed under the [MIT License](LICENSE).
