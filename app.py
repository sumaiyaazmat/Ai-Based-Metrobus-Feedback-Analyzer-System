import os, sys, hashlib
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import csv_handler, ai_analysis, report_generator

app = Flask(__name__)
app.secret_key = 'metro_bus_2025_ultra_secret'

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploaded_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ── Admin credentials (plain dict — easy to change) ───────────────────
ADMIN_USERS = {
    'admin':    'admin123',
    'manager':  'manager456',
}

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
ADMIN_HASHES = {u: hash_pw(p) for u, p in ADMIN_USERS.items()}

def logged_in(): return session.get('admin_logged_in') is True

csv_handler.init_csv()

# ════════════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════════════
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        data = request.get_json(force=True)
        username = data.get('username','').strip()
        password = data.get('password','')
        if username in ADMIN_HASHES and ADMIN_HASHES[username] == hash_pw(password):
            session['admin_logged_in'] = True
            session['admin_user'] = username
            return jsonify({'success': True, 'username': username})
        return jsonify({'success': False, 'message': 'Wrong username or password'}), 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ════════════════════════════════════════════════════════════════════════
# CUSTOMER PORTAL  (no login needed)
# ════════════════════════════════════════════════════════════════════════
@app.route('/')
def customer_portal():
    return render_template('customer_portal.html')

@app.route('/submit', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json(force=True)
        analysis = ai_analysis.analyze(data.get('feedback',''))
        data.update(analysis)
        tid = csv_handler.save_feedback(data)
        return jsonify({'success': True, 'tracking_id': tid, 'analysis': analysis})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        msg = request.get_json(force=True).get('message','')
        return jsonify({'reply': ai_analysis.chatbot_reply(msg)})
    except Exception as e:
        return jsonify({'reply': 'Error: ' + str(e)}), 500

# ════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD  (login required)
# ════════════════════════════════════════════════════════════════════════
@app.route('/admin')
def admin_dashboard():
    if not logged_in(): return redirect(url_for('login'))
    return render_template('admin_dashboard.html',
                           admin_user=session.get('admin_user','Admin'))

@app.route('/api/complaints')
def get_complaints():
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try: return jsonify(csv_handler.get_all())
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/complaint/<complaint_id>')
def get_complaint(complaint_id):
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try:
        c = csv_handler.get_by_id(complaint_id)
        if not c: return jsonify({'error':'Not found'}), 404
        notes = csv_handler.get_notes(complaint_id)
        return jsonify({'complaint': c, 'notes': notes})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try: return jsonify(csv_handler.get_stats())
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/route-scores')
def route_scores():
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try: return jsonify(csv_handler.get_route_scores())
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/update-status', methods=['POST'])
def update_status():
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try:
        data = request.get_json(force=True)
        ok = csv_handler.update_status(data.get('id'), data.get('status'))
        return jsonify({'success': ok})
    except Exception as e: return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add-note', methods=['POST'])
def add_note():
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try:
        data = request.get_json(force=True)
        ok = csv_handler.save_note(data.get('complaint_id'), data.get('note'),
                                   session.get('admin_user','Admin'))
        return jsonify({'success': ok})
    except Exception as e: return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try:
        text = request.get_json(force=True).get('text','')
        return jsonify(ai_analysis.analyze(text))
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/suggestions')
def get_suggestions():
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try: return jsonify(ai_analysis.generate_suggestions(csv_handler.get_all()))
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    if not logged_in(): return jsonify({'error':'Unauthorized'}), 401
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
        file = request.files['file']
        if not file or not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'Please upload a .csv file'})
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        count = csv_handler.merge_csv(filepath)
        return jsonify({'success': True, 'count': count})
    except Exception as e: return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/report')
def report_page():
    if not logged_in(): return redirect(url_for('login'))
    try:
        stats = csv_handler.get_stats()
        records = csv_handler.get_all()
        suggestions = ai_analysis.generate_suggestions(records)
        return report_generator.generate_html_report(stats, suggestions, records)
    except Exception as e: return '<h2>Report Error: ' + str(e) + '</h2>', 500

# ════════════════════════════════════════════════════════════════════════
# PUBLIC — Passenger Notification Lookup (no login needed)
# ════════════════════════════════════════════════════════════════════════
@app.route('/api/notifications/<tracking_id>')
def get_notifications(tracking_id):
    """Passengers look up admin replies using their tracking ID."""
    try:
        tid = tracking_id.strip().upper()
        complaint = csv_handler.get_by_id(tid)
        if not complaint:
            return jsonify({
                'found': False,
                'message': 'Tracking ID not found. Please check the ID on your submission screen.'
            })
        notes = csv_handler.get_notes(tid)
        public_notes = [
            {'note': n.get('note',''), 'timestamp': n.get('timestamp',''),
             'by': 'Metro Bus Admin Team'}
            for n in notes
        ]
        return jsonify({
            'found':       True,
            'tracking_id': tid,
            'status':      complaint.get('status', 'Pending'),
            'route':       complaint.get('route', ''),
            'date':        complaint.get('date', ''),
            'emotion':     complaint.get('emotion', ''),
            'notes':       public_notes,
            'has_reply':   len(notes) > 0,
            'reply_count': len(notes)
        })
    except Exception as e:
        return jsonify({'found': False, 'message': 'Lookup error: ' + str(e)}), 500

@app.route('/api/check-api-status')
def check_api_status():
    """Return whether the Anthropic API key is configured."""
    import os
    key = os.environ.get('ANTHROPIC_API_KEY', '')
    return jsonify({'api_configured': bool(key), 'model': 'claude-sonnet-4-20250514'})

@app.route('/ping')
def ping():
    return jsonify({'status':'ok'})

if __name__ == '__main__':
    print('\n' + '='*52)
    print('  Metro Bus Feedback Analyzer')
    print('='*52)
    print('  Login Page      : http://127.0.0.1:5000/login')
    print('  Customer Portal : http://127.0.0.1:5000/')
    print('  Admin Dashboard : http://127.0.0.1:5000/admin')
    print('  Default login   : admin / admin123')
    print('='*52 + '\n')
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
