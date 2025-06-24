from dotenv import load_dotenv
import os

# .env variables
load_dotenv()

# SQLAlchemy database URL
DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('user')}:{os.getenv('password')}"
    f"@{os.getenv('host')}:{os.getenv('port')}/{os.getenv('dbname')}"
)