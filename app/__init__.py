from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

app.ecoe_threads = []
app.ecoe_rounds = []

socketio = SocketIO(app, async_mode='eventlet')

from app import routes