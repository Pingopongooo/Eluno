import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables (useful for local development)
load_dotenv()

def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database.
    Requires DATABASE_URL environment variable.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is missing.")
    
    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    return conn