from flask import Flask
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    # environment variables
    load_dotenv()
    print("Connecting to host:", os.getenv("host"))

    # flask app init
    app = Flask(__name__)

    from config import DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # set the secret key for the session
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

    # database initialisation
    db.init_app(app)

    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app