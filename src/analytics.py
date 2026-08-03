from datetime import date, timedelta
from src.database import SprintDB
from src.models import StoryStatus, VelocityData, BurndownData, BurndownPoint

def calculate_velocity(sprint: SprintDB) -> VelocityData:
    planned_points = sum(s.story_points for s in sprint.stories)
    completed_points = sum(
        s.story_points for s in sprint.stories 
        if s.status == StoryStatus.DONE
    )
    
    return VelocityData(
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        planned_points=planned_points,
        completed_points=completed_points,
        velocity=completed_points
    )

def calculate_burndown(sprint: SprintDB) -> BurndownData:
    total_points = sum(s.story_points for s in sprint.stories)
    
    burndown_points = []
    current_date = sprint.start_date
    
    while current_date <= min(sprint.end_date, date.today()):
        remaining = sum(
            s.story_points for s in sprint.stories
            if s.status != StoryStatus.DONE or 
               (s.completed_at and s.completed_at > current_date)
        )
        
        burndown_points.append(BurndownPoint(
            date=current_date,
            remaining_points=remaining
        ))
        
        current_date += timedelta(days=1)
    
    return BurndownData(
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        burndown=burndown_points
    )


# --- Rolling velocity (Day 3 / v0.4.0) ------------------------------------

from statistics import mean
from typing import Iterable

from src.models import CapacityUtilization


def calculate_rolling_velocity(sprints: Iterable[SprintDB], window: int = 3) -> float:
    """Return the mean completed velocity of the last `window` CLOSED sprints.

    - Only CLOSED sprints count (in-flight sprints inflate/depress the mean).
    - If fewer than `window` closed sprints exist, the mean is over what is
      available. Zero closed sprints -> 0.0.
    - Sprints are ordered by `end_date` descending, then the top `window` are
      taken and averaged.
    """
    from src.models import SprintStatus  # local import to avoid a cycle

    if window < 1:
        raise ValueError("window must be >= 1")

    closed = [s for s in sprints if s.status == SprintStatus.CLOSED]
    if not closed:
        return 0.0

    closed.sort(key=lambda s: s.end_date, reverse=True)
    considered = closed[:window]
    completed = [calculate_velocity(s).completed_points for s in considered]
    return round(mean(completed), 2)


def calculate_capacity_utilization(sprint: SprintDB) -> CapacityUtilization:
    """Return committed / capacity for a sprint plus an over_capacity flag.

    Committed points = sum of story_points of every story assigned to the
    sprint (regardless of status). ``over_capacity`` is True whenever the
    committed points exceed the sprint's declared capacity.

    A sprint with capacity=0 is a valid "cool-down" sprint; any committed
    points make it over-capacity, and utilization is reported as ``inf`` to
    signal "undefined ratio" without raising.
    """
    committed = sum(s.story_points for s in sprint.stories)
    capacity = sprint.capacity
    if capacity == 0:
        util = None if committed > 0 else 0.0
    else:
        util = round(committed / capacity, 4)
    return CapacityUtilization(
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        capacity=capacity,
        committed_points=committed,
        utilization=util,
        over_capacity=committed > capacity,
    )
