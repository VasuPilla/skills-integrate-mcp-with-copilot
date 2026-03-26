from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from pathlib import Path
import json
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
CORS(app, supports_credentials=True)

BASE_DIR = Path(__file__).resolve().parent
ACTIVITIES_FILE = BASE_DIR / 'activities.json'
ADMIN_FILE = BASE_DIR / 'admin_users.json'

# Default data files
DEFAULT_ACTIVITIES = [
    {
        'id': 1,
        'name': 'Chess Club',
        'description': 'Weekly chess practice and tournament preparation.',
        'capacity': 30,
        'registrations': [],
    },
    {
        'id': 2,
        'name': 'Programming Class',
        'description': 'Python and web basics for all grades.',
        'capacity': 40,
        'registrations': [],
    },
    {
        'id': 3,
        'name': 'Gym Class',
        'description': 'Physical fitness and sports development.',
        'capacity': 20,
        'registrations': [],
    },
]

DEFAULT_ADMIN = {'teachers': [{'username': 'admin', 'password': 'teacher123'}]}

def read_json_file(path, default):
    if path.exists():
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    with path.open('w', encoding='utf-8') as f:
        json.dump(default, f, indent=2)
    return default


def write_json_file(path, data):
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/activities', methods=['GET'])
def get_activities():
    activities = read_json_file(ACTIVITIES_FILE, DEFAULT_ACTIVITIES)
    return jsonify({'activities': activities})


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    body = request.json or {}
    username = body.get('username')
    password = body.get('password')
    admin = read_json_file(ADMIN_FILE, DEFAULT_ADMIN)
    for teacher in admin.get('teachers', []):
        if teacher['username'] == username and teacher['password'] == password:
            session['is_admin'] = True
            session['admin_user'] = username
            return jsonify({'ok': True, 'message': 'Logged in as admin'})
    return jsonify({'ok': False, 'message': 'Invalid admin credentials'}), 401


@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_user', None)
    return jsonify({'ok': True})


def require_admin():
    if not session.get('is_admin'):
        return jsonify({'ok': False, 'message': 'Admin login required'}), 403
    return None


@app.route('/api/activities/<int:activity_id>/register', methods=['POST'])
def register_student(activity_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check

    payload = request.json or {}
    student = payload.get('student')
    if not student:
        return jsonify({'ok': False, 'message': 'Student name required'}), 400

    data = read_json_file(ACTIVITIES_FILE, DEFAULT_ACTIVITIES)
    for activity in data:
        if activity['id'] == activity_id:
            if student in activity['registrations']:
                return jsonify({'ok': False, 'message': 'Student already registered'}), 400
            if len(activity['registrations']) >= activity['capacity']:
                return jsonify({'ok': False, 'message': 'Activity is full'}), 400
            activity['registrations'].append(student)
            write_json_file(ACTIVITIES_FILE, data)
            return jsonify({'ok': True, 'activity': activity})

    return jsonify({'ok': False, 'message': 'Activity not found'}), 404


@app.route('/api/activities/<int:activity_id>/unregister', methods=['POST'])
def unregister_student(activity_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check

    payload = request.json or {}
    student = payload.get('student')
    if not student:
        return jsonify({'ok': False, 'message': 'Student name required'}), 400

    data = read_json_file(ACTIVITIES_FILE, DEFAULT_ACTIVITIES)
    for activity in data:
        if activity['id'] == activity_id:
            if student not in activity['registrations']:
                return jsonify({'ok': False, 'message': 'Student not registered'}), 400
            activity['registrations'].remove(student)
            write_json_file(ACTIVITIES_FILE, data)
            return jsonify({'ok': True, 'activity': activity})

    return jsonify({'ok': False, 'message': 'Activity not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
