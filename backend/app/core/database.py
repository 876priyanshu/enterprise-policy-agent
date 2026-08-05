import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import chromadb
from loguru import logger

# Load environment variables from a .env file
load_dotenv()


# 1. Database URL Construction
# Format: mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
# We use environment variables to keep credentials secure
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "policy_agent_db")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 2. Create the Database Engine
# This is the core interface to the database (similar to mongoose.connect)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Create a SessionLocal class
# Each instance of this class will be a database session.
# We set autocommit=False and autoflush=False for safer transaction management.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a Base class
# All of our database models (tables) will inherit from this Base class.
# It is similar to defining a new mongoose.Schema.
Base = declarative_base()

# 5. Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()