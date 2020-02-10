from . import socketio, app
from .classes import Manager
import json

from flask import render_template, request
from functools import wraps

def requires_tfc(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        tfc_header = request.headers.get('tfc')

        # Only start if "tfc" is the same in the file and the param send
        if not check_tfc(tfc_header):
            return 'Not authorized', 401
        return f(*args, **kwargs)
    return decorated


@app.route('/<int:station_id>/<int:round_id>')
def index(station_id, round_id):
    return render_template('index.html', station_id=station_id, round_id=round_id)


@app.route('/admin')
def admin():
    return render_template('admin.html', rounds=app.ecoe_rounds)

@app.route('/abort', methods=['POST'])
@requires_tfc
def abort_all():
    for e_round in app.ecoe_rounds:
        e_round.abort()
        e_round.chrono.stop()
    return '', 200

def manage_chronos(active, round_id):

    if round_id is None:
        for e_round in app.ecoe_rounds:
            if active:
                e_round.chrono.activate()
            else:
                e_round.chrono.pause()
    else:
        e_rounds = [c for c in app.ecoe_rounds if c.id == round_id]

        if active:
            e_rounds[0].chrono.activate()
        else:
            e_rounds[0].chrono.pause()


@app.route('/pause', methods=['POST'])
@app.route('/pause/<int:round_id>', methods=['POST'])
@requires_tfc
def pause_chronos(round_id=None):
    manage_chronos(active=False, round_id=round_id)
    return '', 200

@app.route('/play', methods=['POST'])
@app.route('/play/<int:round_id>', methods=['POST'])
@requires_tfc
def play_chronos(round_id=None):
    manage_chronos(active=True, round_id=round_id)
    return '', 200

def has_threads_alive():

    return True in [t.is_alive() for t in app.ecoe_threads]


@app.route('/load', methods=['POST'])
def load_configuration():

    if not has_threads_alive():

        Manager.create_config(request.get_json())

        return 'OK', 200
    else:
        return 'No cargado porque los cronos ya están iniciados', 409

@app.route('/', methods=['DELETE'])
@requires_tfc
def delete_configuration():
    if not has_threads_alive():

        Manager.delete_config()

        return 'OK', 200
    else:
        return 'No eliminado porque los cronos ya están iniciados', 409



@app.route('/start', methods=['POST'])
@requires_tfc
def start_chronos():
    if not has_threads_alive():

        for e_round in app.ecoe_rounds:
            app.ecoe_threads.append(socketio.start_background_task(target=e_round.start))

        return 'OK', 200
    else:
        return 'Cronos ya iniciados', 409


def check_tfc(tfc, filename = Manager.filename):
    try:
        ecoe_config = Manager.load_status_from_file(filename)
        file_tfc = ecoe_config['tfc']
    except:
        return False

    return file_tfc == tfc


@app.route('/configurations')
def get_configurations():
    path = '/tmp/'
    files = Manager.get_list_files(path)
    config = []

    for file in files:
        if file.endswith('.json'):
            conf = Manager.load_status_from_file(path + file)
            #If tfc exists, remove from configurations info
            if 'tfc' in conf:
                del conf['tfc']

            config.append(conf)

    return json.dumps(config), 200


###############################

@socketio.on('connect')
def test_connect():
    print('Client connected')


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

################################
