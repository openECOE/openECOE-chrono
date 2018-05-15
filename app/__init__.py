from flask import Flask
from flask_socketio import SocketIO


app = Flask(__name__)

app.ecoe_threads = []
app.ecoe_rounds = []

socketio = SocketIO(app, async_mode='eventlet')

from app import routes