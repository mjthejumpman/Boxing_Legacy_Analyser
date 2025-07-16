from flask import Flask, render_template
from models import db
from sqlalchemy import text
from dotenv import load_dotenv
import os

# environment variables
load_dotenv()
print("Connecting to host:", os.getenv("host"))

# flask app init
app = Flask(__name__)

# DB URL variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# database initialisation
db.init_app(app)


# test for the Supabase connection
@app.route('/test-db')
def test_db():
    try:
        result = db.session.execute(text("SELECT 1")).scalar()
        return f"Database connection successful: {result}"
    except Exception as e:
        return f"Database connection failed: {e}"

@app.route('/')
def home():
    return "<h1>The Boxing Legacy Analyser</h1>"

if __name__ == '__main__':
    app.run(debug=True)