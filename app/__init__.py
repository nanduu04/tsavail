# app/__init__.py
from flask import Flask
from .routes import main, init_jinja_filters

def create_app():
    app = Flask(__name__)
    
    init_jinja_filters(app)

    app.register_blueprint(main)
    
    return app