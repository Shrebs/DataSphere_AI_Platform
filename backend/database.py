from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# For development, we use local SQLite. For production, we just swap this URL to MySQL!
DATABASE_URL = "sqlite:///./datasphere.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define your Datasets table schema
class DatasetMetadata(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    total_rows = Column(Integer)
    total_columns = Column(Integer)
    duplicate_rows = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

# Create the tables in the database
def init_db():
    Base.metadata.create_all(bind=engine)

# Helper function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()