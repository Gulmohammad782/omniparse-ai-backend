import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Update with your local MySQL credentials: username:password@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL")

# Added connect_args to handle Aiven MySQL SSL requirement cleanly
engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl": {}}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()