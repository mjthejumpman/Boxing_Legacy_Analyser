from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
print("Connecting to host:", os.getenv("host"))

# Flask app init
app = Flask(__name__)

# Construct DB URL
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

@app.route('/')
def home():
    return "<h1>The Boxing Legacy Analyser</h1>"

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/test-db')
def test_db():
    try:
        result = db.session.execute(text("SELECT 1")).scalar()
        return f"Database connection successful: {result}"
    except Exception as e:
        return f"Database connection failed: {e}"
