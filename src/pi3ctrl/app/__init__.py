# Mandatory imports
import hashlib
import os
import shutil
import socket
import sqlite3
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for 
)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Relative imports
from .. import utils
from ..database import db, Trigger
from ..wifi import update_hostapd_config
version_not_found = "[VERSION-NOT-FOUND]"
try:
    from ..version import version
except (ModuleNotFoundError, AssertionError):
    version = version_not_found


# Create the Flask app
def create_app(test_config=None) -> Flask:
    """Create and configure the Flask app
    """
    app = Flask(__name__, instance_relative_config=True)

    app.json.compact = False
    app.json.sort_keys = False

    app.config.from_object('pi3ctrl.config.DefaultConfig')

    if test_config is None:
        # load the instance config when not testing
        if os.environ.get('PI3CTRL_CONFIG') is not None:
            app.config.from_envvar('PI3CTRL_CONFIG')
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # store if platform is RPi
    is_RPi = utils.is_RPi

    # set cross-origin resource sharing
    CORS(app, resources=r'/*')

    # hash secret
    app.config['SECRET_SHA256'] = hashlib.sha256(
        bytes(app.config['CTRL_SECRET'], 'utf-8')
    ).hexdigest()

    # set hostname and referers
    hostname = socket.gethostname()
    referers = (
        "http://127.0.0.1",
        f"http://{hostname.lower()}",
        f"http://{utils.get_ipv4_address()}"
    )

    # quick check for an internal request
    def is_internal_referer():
        if 'Referer' not in request.headers:
            return False
        return any(r in request.headers['Referer'] for r in referers)

    # update the hostapd config
    hostapd = update_hostapd_config(app.config)

    # prepare template globals
    context_globals = dict(
        hostname=hostname.replace('.local', ''),
        version=version,
        services=utils.core_services + app.config['SYSTEMD_STATUS'],
        hostapd=hostapd,
    )

    # Initialize the database with the app
    db.init_app(app)

    # Create the database tables
    with app.app_context():
        db.create_all()

    # inject template globals
    @app.context_processor
    def inject_stage_and_region():
        return context_globals

    # create the routes
    @app.route("/", methods=['GET'])
    def index():
        return render_template('base.html.jinja')

    @app.route("/_tab/<tab>", methods=['GET'])
    def load_tab(tab="home"):
        if not is_internal_referer():
            return "Invalid request", 400
        try:
            html = render_template(f"tabs/{tab}.html.jinja")
        except FileNotFoundError:
            return f"Tab {tab} not found", 404
        except Exception as e:
            return f"Server Error: {e}", 500
        resp = {
            "succes": True,
            "tab": tab,
            "html": html,
        }
        return jsonify(resp), 200

    @app.route("/_version", methods=['GET'])
    def multi_ear_version():
        return jsonify({"version": version}), 200

    @app.route("/_systemd_status", methods=['GET'])
    def systemd_status():
        if not is_RPi:
            return "I'm not Raspberry Pi", 418
        service = request.args.get('service') or '*'
        if service == '*':
            resp = utils.systemd_status_all()
        else:
            resp = utils.systemd_status(service)
        return jsonify(resp), 200

    @app.route("/_append_wpa_supplicant", methods=['POST'])
    def append_wpa_supplicant():
        if not is_internal_referer():
            return "Invalid request", 403
        if not is_RPi:
            return "I'm not Raspberry Pi", 418
        secret = request.args.get('secret')
        if secret != app.config['SECRET_SHA256']:
            return "Secret invalid", 403
        ssid = request.args.get('ssid')
        passphrase = request.args.get('passphrase')
        if not (ssid and passphrase):
            return "Invalid ssid and/or passphrase arguments", 400
        resp = utils.wifi_ssid_passphrase(ssid, passphrase)
        return jsonify(resp), 200

    @app.route("/_autohotspot", methods=['POST'])
    def autohotspot():
        if not is_internal_referer():
            return "Invalid request", 403
        if not is_RPi:
            return "I'm not Raspberry Pi", 418
        secret = request.args.get('secret')
        if secret != app.config['SECRET_SHA256']:
            return "Secret invalid", 403
        resp = utils.wifi_autohotspot()
        return jsonify(resp), 200

    @app.route("/_ssid", methods=['GET'])
    def ssid_api():
        if not is_internal_referer():
            return "Invalid request", 403
        if not is_RPi:
            return "I'm not Raspberry Pi", 418
        ssid = os.popen("sudo iwgetid -r").read().rstrip("\n")
        return jsonify({"ssid": ssid}), 200

    @app.route("/_storage", methods=['GET'])
    def storage_api():
        if not is_internal_referer():
            return "Invalid request", 403
        if not is_RPi:
            return "I'm not Raspberry Pi", 418
        usage = shutil.disk_usage("/")
        return jsonify({
            "total": usage.total,
            "used": usage.used,
            "free": usage.free}), 200

    def allowed_file(filename, file):
        exts = app.config[f"{file}_ALLOWED_EXTENSIONS"]
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in exts

    @app.route('/_soundfile', methods=['POST'])
    def upload_soundfile():
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename, 'SOUNDFILE'):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['SOUNDFILE_FOLDER'], filename))
            return redirect(url_for('_soundfile', name=filename))

    @app.route('/_soundfile/<name>')
    def download_soundfile(name):
        return send_from_directory(app.config["SOUNDFILE_FOLDER"], name)

    @app.route('/_trigger/<int:pin>')
    def add_trigger(pin: int):
        # Add a new trigger
        new_trigger = Trigger(pin=pin)
        db.session.add(new_trigger)
        db.session.commit()
        return jsonify({'success': True}), 200

    @app.route('/_triggers')
    def get_triggers():
        # Query the triggers table
        triggers = Trigger.query.all()
        trigger_info = [
            f"Trigger ID: {trigger.id}, Created: {trigger.created}, Pin: {trigger.pin}"
            for trigger in triggers
        ]
        return "<br>".join(trigger_info)

    return app
