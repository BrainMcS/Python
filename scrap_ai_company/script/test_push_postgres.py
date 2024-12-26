import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn_string = f"dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')} host={os.getenv('POSTGRES_HOST')} port={os.getenv('POSTGRES_PORT')}"
    print(f"Connection String: {conn_string}")
    conn = psycopg2.connect(conn_string)
    print("Connection successful!")
    conn.close()
except psycopg2.Error as e:
    print(f"Connection error: {e}")