from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Story, StoryCreate, StoryUpdate, StoryStatus, BlockersResponse, StorySummary
from src import crud
from src.crud import BlockerError

router = APIRouter()

@router.post("", response_model=Story, status_code=201)
def create_story(story: StoryCreate, db: Session = Depends(get_db)):
    return crud.create_story(db, story)

@router.get("", response_model=list[Story])
def list_stories(
    status: StoryStatus = None,
    sprint_id: int = None,
    db: Session = Depends(get_db)
):
    return crud.get_stories(db, status=status, sprint_id=sprint_id)

@router.get("/{story_id}", response_model=Story)
def get_story(story_id: int, db: Session = Depends(get_db)):
    story = crud.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@router.patch("/{story_id}", response_model=Story)
def update_story(story_id: int, updates: StoryUpdate, db: Session = Depends(get_db)):
    try:
        story = crud.update_story(db, story_id, updates)
    except BlockerError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@router.post("/{story_id}/assign/{sprint_id}", response_model=Story)
def assign_story(story_id: int, sprint_id: int, db: Session = Depends(get_db)):
    story = crud.assign_story_to_sprint(db, story_id, sprint_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@router.delete("/{story_id}", status_code=204)
def delete_story(story_id: int, db: Session = Depends(get_db)):
    if not crud.delete_story(db, story_id):
        raise HTTPException(status_code=404, detail="Story not found")

@router.get("/{story_id}/blockers", response_model=BlockersResponse)
def list_blockers(story_id: int, db: Session = Depends(get_db)):
    """Return both directions of the blocking graph for a story."""
    story = crud.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return BlockersResponse(
        story_id=story.id,
        blockers=[StorySummary.model_validate(b) for b in story.blockers],
        blocking=[StorySummary.model_validate(b) for b in story.blocking],
    )

@router.post("/{story_id}/block/{blocker_id}", response_model=BlockersResponse, status_code=201)
def add_blocker(story_id: int, blocker_id: int, db: Session = Depends(get_db)):
    """Mark `blocker_id` as a blocker of `story_id` (story_id can't be DONE until blocker is DONE)."""
    try:
        story = crud.add_blocker(db, story_id, blocker_id)
    except BlockerError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not story:
        raise HTTPException(status_code=404, detail="Story or blocker not found")
    return BlockersResponse(
        story_id=story.id,
        blockers=[StorySummary.model_validate(b) for b in story.blockers],
        blocking=[StorySummary.model_validate(b) for b in story.blocking],
    )

@router.delete("/{story_id}/block/{blocker_id}", status_code=204)
def remove_blocker(story_id: int, blocker_id: int, db: Session = Depends(get_db)):
    story = crud.remove_blocker(db, story_id, blocker_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story or blocker not found")
