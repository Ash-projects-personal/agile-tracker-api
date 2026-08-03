from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class StoryStatus(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class SprintStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    CLOSED = "closed"

class StoryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    story_points: int = Field(..., ge=0, le=100)
    priority: int = Field(default=999, ge=1)

class StoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    story_points: Optional[int] = Field(None, ge=0, le=100)
    priority: Optional[int] = Field(None, ge=1)
    status: Optional[StoryStatus] = None

class Story(BaseModel):
    id: int
    title: str
    description: Optional[str]
    acceptance_criteria: Optional[str]
    story_points: int
    priority: int
    status: StoryStatus
    sprint_id: Optional[int]
    created_at: date
    completed_at: Optional[date]

    class Config:
        from_attributes = True

class SprintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date
    capacity: int = Field(..., ge=0, description="Total story points the team can handle")

class Sprint(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    capacity: int
    status: SprintStatus
    created_at: date

    class Config:
        from_attributes = True

class SprintWithStories(Sprint):
    stories: list[Story] = []

class VelocityData(BaseModel):
    sprint_id: int
    sprint_name: str
    planned_points: int
    completed_points: int
    velocity: int

class BurndownPoint(BaseModel):
    date: date
    remaining_points: int

class BurndownData(BaseModel):
    sprint_id: int
    sprint_name: str
    burndown: list[BurndownPoint]

class StorySummary(BaseModel):
    """Lightweight Story view used in nested responses (e.g. blockers list)."""
    id: int
    title: str
    status: StoryStatus
    story_points: int

    class Config:
        from_attributes = True

class BlockersResponse(BaseModel):
    story_id: int
    blockers: list[StorySummary]
    blocking: list[StorySummary]


# --- Retrospectives (Day 2 / v0.3.0) ---

class RetrospectiveCreate(BaseModel):
    """Payload for recording a sprint retrospective.

    `action_items` is a list of short follow-up actions agreed upon by the team.
    Empty lists are allowed (some retros end with no concrete actions).
    """
    went_well: str = Field(..., min_length=1, max_length=4000)
    needs_improvement: str = Field(..., min_length=1, max_length=4000)
    action_items: list[str] = Field(default_factory=list)


class Retrospective(BaseModel):
    id: int
    sprint_id: int
    went_well: str
    needs_improvement: str
    action_items: list[str]
    created_at: date

    class Config:
        from_attributes = True


# --- Analytics (v0.4.0) ---

class CapacityUtilization(BaseModel):
    sprint_id: int
    sprint_name: str
    capacity: int
    committed_points: int
    # For capacity=0 sprints with committed>0 this is null; the client should
    # treat it as "over-committed by definition" rather than a real ratio.
    utilization: float | None = None
    over_capacity: bool


class RollingVelocity(BaseModel):
    window: int
    sprints_considered: int
    velocity: float
