import os
from flask import Flask, request, jsonify, send_file
from io import BytesIO

from .storage.git_adapter import GitAdapter

app = Flask(__name__)

# configure storage root relative to repo
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STORAGE_ROOT = os.path.join(BASE_DIR, 'data', 'storage')
os.makedirs(STORAGE_ROOT, exist_ok=True)

storage = GitAdapter(STORAGE_ROOT)


@app.route('/upload', methods=['POST'])
def upload():
    # Expect form fields: patient_id, user_id, action, file
    patient_id = request.form.get('patient_id')
    user_id = request.form.get('user_id', 'anonymous')
    action = request.form.get('action', 'upload')
    f = request.files.get('file')
    if not patient_id or not f:
        return jsonify({'error': 'patient_id and file are required'}), 400

    filename = f.filename
    relative_path = os.path.join(patient_id, filename)
    data = f.read()
    commit = storage.save(relative_path, data, user_id=user_id, action=action)
    return jsonify({'status': 'ok', 'commit': commit})


@app.route('/history/<patient_id>/<path:filename>', methods=['GET'])
def history(patient_id, filename):
    relative_path = os.path.join(patient_id, filename)
    h = storage.history(relative_path)
    return jsonify(h)


@app.route('/file/<patient_id>/<path:filename>', methods=['GET'])
def get_file(patient_id, filename):
    version = request.args.get('version')
    relative_path = os.path.join(patient_id, filename)
    data = storage.get(relative_path, version=version)
    return send_file(BytesIO(data), download_name=filename)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
