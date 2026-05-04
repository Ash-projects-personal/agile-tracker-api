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

class BlockerError(ValueError):
    """Raised when a blocker operation is invalid (cycle, self, unresolved blockers)."""

def update_story(db: Session, story_id: int, updates: StoryUpdate) -> StoryDB:
    db_story = get_story(db, story_id)
    if not db_story:
        return None

    update_data = updates.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] == StoryStatus.DONE:
        unresolved = [b for b in db_story.blockers if b.status != StoryStatus.DONE]
        if unresolved:
            blocker_ids = ", ".join(f"#{b.id}" for b in unresolved)
            raise BlockerError(
                f"Cannot mark story #{story_id} as DONE; "
                f"unresolved blockers: {blocker_ids}"
            )
        update_data["completed_at"] = date.today()

    for key, value in update_data.items():
        setattr(db_story, key, value)

    db.commit()
    db.refresh(db_story)
    return db_story

def add_blocker(db: Session, story_id: int, blocker_id: int) -> StoryDB:
    """Mark `blocker_id` as a story that must be DONE before `story_id` can be DONE.

    Raises BlockerError on self-block or cycle. Returns None if either story is missing.
    """
    if story_id == blocker_id:
        raise BlockerError("A story cannot block itself")

    db_story = get_story(db, story_id)
    db_blocker = get_story(db, blocker_id)
    if not db_story or not db_blocker:
        return None

    if db_blocker in db_story.blockers:
        # idempotent — already linked
        return db_story

    if _would_create_cycle(db, story_id, blocker_id):
        raise BlockerError(
            f"Adding #{blocker_id} as a blocker of #{story_id} would create a dependency cycle"
        )

    db_story.blockers.append(db_blocker)
    db.commit()
    db.refresh(db_story)
    return db_story

def remove_blocker(db: Session, story_id: int, blocker_id: int) -> StoryDB:
    db_story = get_story(db, story_id)
    db_blocker = get_story(db, blocker_id)
    if not db_story or not db_blocker:
        return None
    if db_blocker in db_story.blockers:
        db_story.blockers.remove(db_blocker)
        db.commit()
        db.refresh(db_story)
    return db_story

def _would_create_cycle(db: Session, story_id: int, new_blocker_id: int) -> bool:
    """Return True if adding new_blocker_id as a blocker of story_id forms a cycle.

    A cycle exists if story_id is already (transitively) a blocker of new_blocker_id —
    i.e. new_blocker_id depends, directly or indirectly, on story_id.
    """
    visited = set()
    stack = [new_blocker_id]
    while stack:
        current_id = stack.pop()
        if current_id == story_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        current = get_story(db, current_id)
        if current is None:
            continue
        stack.extend(b.id for b in current.blockers)
    return False

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
