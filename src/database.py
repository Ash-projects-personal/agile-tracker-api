from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Date, Enum, ForeignKey, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from src.models import StoryStatus, SprintStatus

DATABASE_URL = "sqlite:///./agile_tracker.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Self-referential many-to-many table for story blocking relationships.
# A row (blocked_id=A, blocker_id=B) means "story A is blocked by story B" —
# i.e. B must reach DONE before A can be marked DONE.
story_blockers = Table(
    "story_blockers",
    Base.metadata,
    Column("blocked_id", Integer, ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True),
    Column("blocker_id", Integer, ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True),
)

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

    # Stories that must be DONE before this one can move to DONE.
    blockers = relationship(
        "StoryDB",
        secondary=story_blockers,
        primaryjoin=id == story_blockers.c.blocked_id,
        secondaryjoin=id == story_blockers.c.blocker_id,
        backref="blocking",
    )

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
    retrospective = relationship(
        "RetrospectiveDB",
        back_populates="sprint",
        uselist=False,
        cascade="all, delete-orphan",
    )

class RetrospectiveDB(Base):
    """One retrospective per sprint, recorded after the sprint closes."""
    __tablename__ = "retrospectives"

    id = Column(Integer, primary_key=True, index=True)
    sprint_id = Column(
        Integer,
        ForeignKey("sprints.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    went_well = Column(String, nullable=False)
    needs_improvement = Column(String, nullable=False)
    # JSON list of strings; SQLite stores as TEXT, SQLAlchemy handles serialization.
    action_items = Column(JSON, nullable=False, default=list)
    created_at = Column(Date, default=date.today)

    sprint = relationship("SprintDB", back_populates="retrospective")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
