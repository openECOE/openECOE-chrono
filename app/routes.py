from . import socketio, app
from .classes import Chrono

from flask import render_template, request


@app.route('/<int:station_id>/<int:round_id>')
def index(station_id, round_id):
    return render_template('index.html', station_id=station_id, round_id=round_id)


@app.route('/admin')
def admin():
    return render_template('admin.html', rounds=app.chronos)


def manage_chronos(active, round_id):

    if round_id is None:
        for chrono in app.chronos:
            if active:
                chrono.activate()
            else:
                chrono.pause()
    else:
        chronos = [c for c in app.chronos if c.id == round_id]

        if active:
            chronos[0].activate()
        else:
            chronos[0].pause()


@app.route('/pause')
@app.route('/pause/<int:round_id>')
def pause_chronos(round_id=None):

    manage_chronos(active=False, round_id=round_id)

    return '', 200


@app.route('/play')
@app.route('/play/<int:round_id>')
def play_chronos(round_id=None):

    manage_chronos(active=True, round_id=round_id)

    return '', 200


def has_threads_alive():

    return len(app.chr_threads) > 0 or True in [t.is_alive() for t in app.chr_threads]


@app.route('/load', methods=['POST'])
def load_configuration():

    if not has_threads_alive():

        data = request.get_json()

        del app.chronos[:]

        for r in data['rounds']:
            app.chronos.append(Chrono(r['id'], data['seconds'], r['events']))

        return 'OK', 200
    else:
        return 'Not loaded: chronos already started', 200


@app.route('/start')
def start_chronos():

    if not has_threads_alive():

        for chrono in app.chronos:
            app.chr_threads.append(socketio.start_background_task(target=chrono.play))

        return 'OK', 200
    else:
        return 'Already started', 200


###############################

@socketio.on('connect')
def test_connect():
    print('Client connected')


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

################################
