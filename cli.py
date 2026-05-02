#!/usr/bin/env python3
import sys
from datetime import date, timedelta
from src.database import SessionLocal, init_db
from src.models import StoryCreate, SprintCreate, StoryStatus
from src import crud
from src.analytics import calculate_velocity

def main():
    init_db()
    db = SessionLocal()
    
    if len(sys.argv) < 2:
        print("Usage: python cli.py <command> [args]")
        print("Commands: create-story, create-sprint, assign-story, sprint-status, list-stories")
        return
    
    command = sys.argv[1]
    
    if command == "create-story":
        if len(sys.argv) < 3:
            print("Usage: create-story <title> --points <points>")
            return
        title = sys.argv[2]
        points = 3
        if "--points" in sys.argv:
            points = int(sys.argv[sys.argv.index("--points") + 1])
        
        story = crud.create_story(db, StoryCreate(
            title=title,
            story_points=points
        ))
        print(f"Created story #{story.id}: {story.title} ({story.story_points} points)")
    
    elif command == "create-sprint":
        if len(sys.argv) < 3:
            print("Usage: create-sprint <name> --duration <days>")
            return
        name = sys.argv[2]
        duration = 14
        if "--duration" in sys.argv:
            duration = int(sys.argv[sys.argv.index("--duration") + 1])
        
        start = date.today()
        end = start + timedelta(days=duration)
        
        sprint = crud.create_sprint(db, SprintCreate(
            name=name,
            start_date=start,
            end_date=end,
            capacity=40
        ))
        print(f"Created sprint #{sprint.id}: {sprint.name} ({sprint.start_date} to {sprint.end_date})")
    
    elif command == "assign-story":
        if len(sys.argv) < 4:
            print("Usage: assign-story <story_id> --sprint <sprint_id>")
            return
        story_id = int(sys.argv[2])
        sprint_id = int(sys.argv[sys.argv.index("--sprint") + 1])
        
        story = crud.assign_story_to_sprint(db, story_id, sprint_id)
        print(f"Assigned story #{story.id} to sprint #{sprint_id}")
    
    elif command == "sprint-status":
        if len(sys.argv) < 3:
            print("Usage: sprint-status <sprint_id>")
            return
        sprint_id = int(sys.argv[2])
        sprint = crud.get_sprint(db, sprint_id)
        
        if not sprint:
            print(f"Sprint #{sprint_id} not found")
            return
        
        velocity = calculate_velocity(sprint)
        print(f"\nSprint: {sprint.name}")
        print(f"Status: {sprint.status.value}")
        print(f"Dates: {sprint.start_date} to {sprint.end_date}")
        print(f"Stories: {len(sprint.stories)}")
        print(f"Planned: {velocity.planned_points} points")
        print(f"Completed: {velocity.completed_points} points")
        print(f"Velocity: {velocity.velocity}")
    
    elif command == "list-stories":
        stories = crud.get_stories(db)
        print(f"\nAll stories ({len(stories)}):")
        for s in stories:
            sprint_info = f"Sprint #{s.sprint_id}" if s.sprint_id else "Backlog"
            print(f"  #{s.id}: {s.title} ({s.story_points}pt) [{s.status.value}] - {sprint_info}")
    
    else:
        print(f"Unknown command: {command}")
    
    db.close()

if __name__ == "__main__":
    main()
