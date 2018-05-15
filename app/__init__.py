from flask import Flask
from flask_socketio import SocketIO


app = Flask(__name__)
app.chronos = []
app.chr_threads = []

socketio = SocketIO(app, async_mode='eventlet')

from app import routes