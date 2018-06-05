from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import json

app = Flask(__name__)

CORS(app)

# TODO: replace list with dict where each item refers to info ecoe, indexed by id_ecoe
"""
    ecoe_rounds = {
        24: [...],
        27: [...]
    }
"""
app.ecoe_threads = []
app.ecoe_rounds = []

socketio = SocketIO(app, async_mode='eventlet')

from app import routes

"""
Reload configuration if exists on start
"""

ecoe_config = None

try:
    with open('ecoe_config.json', 'r') as json_file:
        ecoe_config = json.load(json_file)
except:
    pass

if ecoe_config:
    # 1. Create configuration in app memory
    from .classes import Manager
    Manager.create_config(ecoe_config)

    # 2. Load objects
    for e_round in app.ecoe_rounds:
        try:
            round_status = Manager.load_status_from_file(e_round.status_filename)

            if len(round_status) > 0:

                chrono_status = Manager.load_status_from_file(e_round.chrono.status_filename)

                if len(chrono_status) > 0:
                    e_round.chrono.minutes = chrono_status['minutes']
                    e_round.chrono.seconds = chrono_status['seconds']
                    e_round.chrono.state = chrono_status['state']

                app.ecoe_threads.append(socketio.start_background_task(target=e_round.start,
                                                                       state=round_status['state'],
                                                                       current_rerun=round_status['current_rerun'],
                                                                       idx_schedule=round_status['current_idx_schedule']))
        except:
            pass
