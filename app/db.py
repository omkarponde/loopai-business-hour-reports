from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Specify the path to your .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

POSTGRES_DATABASE_URI = os.getenv("DATABASE_URI")
engine = create_engine(POSTGRES_DATABASE_URI, echo=True)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
