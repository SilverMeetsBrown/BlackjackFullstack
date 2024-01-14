from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_socketio import SocketIO, emit, send, join_room, leave_room
import json
import random
import os
import traceback
import threading
import time
import math
import warnings
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
warnings.filterwarnings('ignore')
app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'wow'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
socketio = SocketIO(app)

USER_STARTING_MONEY = 1000
DECKS_IN_SHOE = 6 
MAX_PLAYERS_IN_ROOM = 6
COUNTDOWN_TIMER = 8 		# Time period for players to join game.
START_WAIT = 1				# Delay between end of COUNTDOWN_TIMER and start of game.
TURN_COUNTDOWN = 15 		# Maximum allowed time for a turn.
RESET = False				# Reset database on loadup.

FORCE_DEALER_ACE = False
FORCE_DEALER_BLACKJACK = False
FORCE_FIRST_PLAYER_BLACKJACK = False
FORCE_FIRST_PLAYER_SPLIT = True

