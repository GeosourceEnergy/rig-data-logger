import os
import logging
import psutil
from flask import Flask
from main_routes import main_bp
from config import SECRET_KEY, TEMPLATE_FILE_PATH, ALLOWED_EXTENSIONS
from flask_session import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.FileHandler("application.log"), logging.StreamHandler()])
mb = psutil.Process(os.getpid()).memory_info().rss // (1024*1024)
logging.info(f"[ColdStart] memory right after imports: {mb} MB")

app = Flask(__name__)
app.secret_key = SECRET_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.FileHandler("application.log"), logging.StreamHandler()])

app.config['TEMPLATE_FILE'] = TEMPLATE_FILE_PATH
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.register_blueprint(main_bp)

if __name__ == "__main__":
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        Timer(1.0, open_browser).start()

    app.run(debug=True)
