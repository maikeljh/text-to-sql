import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.models import Base

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_APP_USER')}:{os.getenv('DB_APP_PASSWORD')}"
    f"@{os.getenv('DB_APP_HOST')}:{os.getenv('DB_APP_PORT')}/{os.getenv('DB_APP_DATABASE')}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
