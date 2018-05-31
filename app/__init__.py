from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

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