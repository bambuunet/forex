#!/root/.pyenv/versions/3.6.2/bin/python3
import sys,os
sys.path.append('/root/.pyenv/versions/3.6.2/lib/python3.6/site-packages')

import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('flaskr.config')


formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
)
debug_log = os.path.join(app.root_path, 'logs/debug.log')
debug_file_handler = RotatingFileHandler(
    debug_log, maxBytes=100000, backupCount=10
)
debug_file_handler.setLevel(logging.INFO)
debug_file_handler.setFormatter(formatter)
app.logger.addHandler(debug_file_handler)
    
error_log = os.path.join(app.root_path, 'logs/error.log')
error_file_handler = RotatingFileHandler(
    error_log, maxBytes=100000, backupCount=10
)    
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(formatter)
app.logger.addHandler(error_file_handler)



db = SQLAlchemy(app)

import flaskr.views