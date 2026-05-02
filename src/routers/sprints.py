from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Sprint, SprintCreate, SprintWithStories, VelocityData, BurndownData
from src import crud
from src.analytics import calculate_velocity, calculate_burndown

router = APIRouter()

@router.post("", response_model=Sprint, status_code=201)
def create_sprint(sprint: SprintCreate, db: Session = Depends(get_db)):
    if sprint.end_date <= sprint.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    return crud.create_sprint(db, sprint)

@router.get("", response_model=list[Sprint])
def list_sprints(db: Session = Depends(get_db)):
    return crud.get_sprints(db)

@router.get("/{sprint_id}", response_model=SprintWithStories)
def get_sprint(sprint_id: int, db: Session = Depends(get_db)):
    sprint = crud.get_sprint(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint

@router.get("/{sprint_id}/velocity", response_model=VelocityData)
def get_velocity(sprint_id: int, db: Session = Depends(get_db)):
    sprint = crud.get_sprint(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return calculate_velocity(sprint)

@router.get("/{sprint_id}/burndown", response_model=BurndownData)
def get_burndown(sprint_id: int, db: Session = Depends(get_db)):
    sprint = crud.get_sprint(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return calculate_burndown(sprint)

@router.post("/{sprint_id}/close", response_model=Sprint)
def close_sprint(sprint_id: int, db: Session = Depends(get_db)):
    sprint = crud.close_sprint(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint
