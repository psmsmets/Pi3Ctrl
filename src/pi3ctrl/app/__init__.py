# Mandatory imports
import hashlib
import os
import pandas as pd
import shutil
import socket
from flask import (
    Flask,
    flash,
    jsonify,
    render_template,
    request,
    send_from_directory
)
from flask_cors import CORS
# from werkzeug.utils import secure_filename

# Relative imports
from .. import utils
from ..database import db, Trigger
from ..wifi import update_hostapd_config
version_not_found = "[VERSION-NOT-FOUND]"
try:
    from ..version import version
except (ModuleNotFoundError, AssertionError):
    version = version_not_found


def soundFile(button: int, pin: int) -> str:
    """Construct the soundFile name.
    """
    return f"soundFile.{button}.GPIO{pin}"


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
        if os.path.isfile('/etc/pi3ctrl/pi3ctrl.conf'):
            app.config.from_pyfile('/etc/pi3ctrl/pi3ctrl.conf')
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
        bytes(app.config['PI3CTRL_SECRET'], 'utf-8')
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

    def has_soundFile(button, pin):
        file = os.path.join(app.config["SOUNDFILE_FOLDER"], soundFile(button, pin))
        return os.path.isfile(file)

    # prepare template globals
    context_globals = dict(
        has_soundFile=has_soundFile,
        hostapd=hostapd,
        hostname=hostname.replace('.local', ''),
        services=utils.core_services + app.config['SYSTEMD_STATUS'],
        version=version,
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
        if 'button' not in request.form:
            return 'No button parameter provided', 423
        button = int(request.form.get('button'))
        pin = app.config['BUTTON_PINS'][button]
        if 'file' not in request.files:
            return 'No file part', 422
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 422
        if file and allowed_file(file.filename, 'SOUNDFILE'):
            file.save(os.path.join(app.config['SOUNDFILE_FOLDER'], soundFile(button, pin)))
            flash('New soundFile uploaded')
            return 'File uploaded!', 200

    @app.route('/_soundfile', methods=['GET'])
    def download_soundfile():
        if 'button' not in request.args:
            return 'No button parameter provided', 422
        button = int(request.args.get('button'))
        if 'pin' not in request.args:
            return 'No pin parameter provided', 422
        pin = int(request.args.get('pin'))
        file = os.path.join(app.config["SOUNDFILE_FOLDER"], soundFile(button, pin))
        if os.path.isfile(file):
            return send_from_directory(app.config["SOUNDFILE_FOLDER"], soundFile(button, pin))
        else:
            return "File not found", 403

    def get_triggers():
        return [trigger.serialize for trigger in Trigger.query.all()]

    @app.route('/_trigger/<int:button>/<int:pin>', methods=['GET'])
    def trigger(button, pin):
        new_trigger = Trigger(button=button, pin=pin)
        db.session.add(new_trigger)
        db.session.commit()
        return 'OK'

    @app.route('/_triggers', methods=['GET'])
    def triggers_api():
        # Query the triggers table
        return jsonify(get_triggers()), 200

    def get_metrics():
        # Triggers dataframe
        df = pd.DataFrame.from_records([trigger.serialize for trigger in Trigger.query.all()])

        if len(df) == 0:
            return {}

        # Convert the 'created' column to datetime
        df['created'] = pd.to_datetime(df['created'])

        # Create the 'bp' column
        df['bp'] = df.apply(lambda row: f"button {row['button']} | GPIO{row['pin']}", axis=1)

        # Extract the hour from the 'created' column
        df['hour'] = df['created'].dt.hour

        # Extract the weekday from the 'created' column (0=Monday, 6=Sunday)
        df['weekday'] = df['created'].dt.weekday

        # Extract the date from the 'created' column
        df['date'] = df['created'].dt.strftime('%Y-%m-%d')

        # Construct metrics
        metrics = {}
        metrics['last'] = {df.tail(1).bp.values[0]: df.tail(1).created.dt.strftime('%d-%m-%Y %H:%M:%S').values[0]}
        metrics['total'] = dict()
        for bp, grouped in df.groupby('bp'):
            metrics['total'][bp] = len(grouped)
            for metric in ('date', 'weekday', 'hour'):
                if metric not in metrics:
                    metrics[metric] = dict()
                metrics[metric][bp] = grouped.groupby([metric]).size().to_dict()

        return metrics

    @app.route('/_metrics', methods=['GET'])
    def metrics_api():
        return jsonify(get_metrics()), 200

    return app
