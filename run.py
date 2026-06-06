"""
run.py  —  Simple startup script for Metro Bus Feedback Analyzer
Just double-click this file OR run:  python run.py
"""
import os, sys, subprocess, webbrowser, time, socket

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

def port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

def install_deps():
    print("Checking and installing dependencies...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',
        'flask', 'pandas', 'textblob', 'scikit-learn', 'nltk', 'werkzeug',
        '--quiet', '--break-system-packages'], stderr=subprocess.DEVNULL)
    print("Dependencies OK")

def download_nltk():
    import nltk
    for pkg in ['punkt', 'averaged_perceptron_tagger', 'brown', 'wordnet']:
        nltk.download(pkg, quiet=True)

if __name__ == '__main__':
    install_deps()
    download_nltk()

    if not port_free(5000):
        print("Port 5000 is busy. Close whatever is using it and try again.")
        sys.exit(1)

    print()
    print("=" * 50)
    print("  Metro Bus Feedback Analyzer")
    print("=" * 50)
    print("  Customer Portal : http://127.0.0.1:5000/")
    print("  Admin Dashboard : http://127.0.0.1:5000/admin")
    print("  Report          : http://127.0.0.1:5000/report")
    print("  Press CTRL+C to stop")
    print("=" * 50)
    print()

    # Open browser after 2 seconds
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://127.0.0.1:5000/')
    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Flask
    from app import app
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
