from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

app.ecoes = []

socketio = SocketIO(app, async_mode='eventlet')

from app import routes

"""
Reload configuration if exists on start
"""

from .classes import Manager

Manager.reload_status()
