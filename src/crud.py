from datetime import date
from sqlalchemy.orm import Session
from src.database import StoryDB, SprintDB
from src.models import StoryCreate, StoryUpdate, StoryStatus, SprintCreate, SprintStatus

def create_story(db: Session, story: StoryCreate) -> StoryDB:
    db_story = StoryDB(**story.model_dump())
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story

def get_story(db: Session, story_id: int) -> StoryDB:
    return db.query(StoryDB).filter(StoryDB.id == story_id).first()

def get_stories(db: Session, status: StoryStatus = None, sprint_id: int = None) -> list[StoryDB]:
    query = db.query(StoryDB)
    if status:
        query = query.filter(StoryDB.status == status)
    if sprint_id is not None:
        query = query.filter(StoryDB.sprint_id == sprint_id)
    return query.order_by(StoryDB.priority).all()

def update_story(db: Session, story_id: int, updates: StoryUpdate) -> StoryDB:
    db_story = get_story(db, story_id)
    if not db_story:
        return None
    
    update_data = updates.model_dump(exclude_unset=True)
    
    if "status" in update_data and update_data["status"] == StoryStatus.DONE:
        update_data["completed_at"] = date.today()
    
    for key, value in update_data.items():
        setattr(db_story, key, value)
    
    db.commit()
    db.refresh(db_story)
    return db_story

def assign_story_to_sprint(db: Session, story_id: int, sprint_id: int) -> StoryDB:
    db_story = get_story(db, story_id)
    if not db_story:
        return None
    db_story.sprint_id = sprint_id
    if db_story.status == StoryStatus.BACKLOG:
        db_story.status = StoryStatus.TODO
    db.commit()
    db.refresh(db_story)
    return db_story

def delete_story(db: Session, story_id: int) -> bool:
    db_story = get_story(db, story_id)
    if not db_story:
        return False
    db.delete(db_story)
    db.commit()
    return True

def create_sprint(db: Session, sprint: SprintCreate) -> SprintDB:
    db_sprint = SprintDB(**sprint.model_dump())
    db.add(db_sprint)
    db.commit()
    db.refresh(db_sprint)
    return db_sprint

def get_sprint(db: Session, sprint_id: int) -> SprintDB:
    return db.query(SprintDB).filter(SprintDB.id == sprint_id).first()

def get_sprints(db: Session) -> list[SprintDB]:
    return db.query(SprintDB).order_by(SprintDB.start_date.desc()).all()

def close_sprint(db: Session, sprint_id: int) -> SprintDB:
    db_sprint = get_sprint(db, sprint_id)
    if not db_sprint:
        return None
    db_sprint.status = SprintStatus.CLOSED
    db.commit()
    db.refresh(db_sprint)
    return db_sprint
