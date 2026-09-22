from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

#Loads .env variables using the dockerfile
load_dotenv()

#Variables for DatabseURL
DB_USER = os.getenv("POSTGRES_USER", "temp_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "weather_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

#Engine for creating a session with the databse
engine = create_engine(DATABASE_URL) 