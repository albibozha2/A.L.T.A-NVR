from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import asyncio
from pathlib import Path

Base = declarative_base()

class Camera(Base):
    __tablename__ = 'cameras'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    enabled = Column(Boolean, default=True)
    settings = Column(Text)  # JSON string for camera-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    recordings = relationship("Recording", back_populates="camera")
    events = relationship("Event", back_populates="camera")

class Recording(Base):
    __tablename__ = 'recordings'
    
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    duration = Column(Float)  # in seconds
    event_based = Column(Boolean, default=False)
    motion_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    camera = relationship("Camera", back_populates="recordings")
    events = relationship("Event", back_populates="recording")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'), nullable=False)
    recording_id = Column(Integer, ForeignKey('recordings.id'), nullable=True)
    event_type = Column(String(50), nullable=False)  # motion, object, etc.
    label = Column(String(100))  # detected object label
    confidence = Column(Float)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    thumbnail_path = Column(String(500))
    data = Column(Text)  # JSON string for additional event data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    camera = relationship("Camera", back_populates="events")
    recording = relationship("Recording", back_populates="events")

class SystemSettings(Base):
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database setup
engine = None
SessionLocal = None

def init_database(db_url: str):
    """Initialize database connection"""
    global engine, SessionLocal
    
    # Create data directory if it doesn't exist
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

async def init_db():
    """Async database initialization"""
    from src.core.config import Config
    config = Config()
    init_database(config.database_url)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
