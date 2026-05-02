from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Story, StoryCreate, StoryUpdate, StoryStatus
from src import crud

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
    story = crud.update_story(db, story_id, updates)
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
