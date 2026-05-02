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
