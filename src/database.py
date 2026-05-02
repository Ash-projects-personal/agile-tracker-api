from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Date, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from src.models import StoryStatus, SprintStatus

DATABASE_URL = "sqlite:///./agile_tracker.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class StoryDB(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    acceptance_criteria = Column(String, nullable=True)
    story_points = Column(Integer, nullable=False)
    priority = Column(Integer, default=999)
    status = Column(Enum(StoryStatus), default=StoryStatus.BACKLOG)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    created_at = Column(Date, default=date.today)
    completed_at = Column(Date, nullable=True)
    
    sprint = relationship("SprintDB", back_populates="stories")

class SprintDB(Base):
    __tablename__ = "sprints"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(Enum(SprintStatus), default=SprintStatus.PLANNED)
    created_at = Column(Date, default=date.today)
    
    stories = relationship("StoryDB", back_populates="sprint")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
