# Agile Tracker API

A working implementation of core agile concepts: user stories, story points, sprints, velocity tracking, and burndown metrics.

Built to understand agile from the inside out — not just theory, but the data structures and calculations that power sprint planning tools.

## What This Demonstrates

- **User story lifecycle**: Create stories with titles, descriptions, acceptance criteria, and story points
- **Sprint management**: Fixed-duration sprints with capacity and status tracking
- **Velocity calculation**: Track completed story points per sprint to forecast future capacity
- **Burndown data**: Daily remaining work to visualize sprint progress
- **Backlog prioritization**: Stories have priority ranks for grooming sessions
- **Story dependencies**: Stories can be marked as blocked by other stories; the API refuses to mark a story DONE while any blocker is still open, and rejects dependency cycles

## Setup

```bash
pip install -r requirements.txt
```

## Run

Start the API server:

```bash
uvicorn src.main:app --reload
```

API docs available at http://localhost:8000/docs

Or use the CLI:

```bash
python cli.py create-story "Add user login" --points 5
python cli.py create-sprint "Sprint 1" --duration 14
python cli.py assign-story 1 --sprint 1
python cli.py sprint-status 1
```

## Learning Exercise Notes

This is v0.2. It's intentionally missing:
- User authentication (all data is shared)
- Team member assignment
- Epic/theme grouping
- Retrospective tracking
- Historical velocity charts

These will be added incrementally (see `roadmap.md`) to practice iterative development.

## API Endpoints

### Stories
- `POST /stories` - Create a story
- `GET /stories` - List all stories (filterable by status, sprint)
- `GET /stories/{id}` - Get story details
- `PATCH /stories/{id}` - Update story (status, points, priority); rejects DONE if blockers are unresolved (409)
- `DELETE /stories/{id}` - Delete story
- `GET /stories/{id}/blockers` - List stories that block this one and stories it blocks
- `POST /stories/{id}/block/{blocker_id}` - Add a blocker (rejects self-block and cycles)
- `DELETE /stories/{id}/block/{blocker_id}` - Remove a blocker

### Sprints
- `POST /sprints` - Create a sprint
- `GET /sprints` - List all sprints
- `GET /sprints/{id}` - Get sprint details with assigned stories
- `GET /sprints/{id}/velocity` - Calculate completed story points
- `GET /sprints/{id}/burndown` - Get daily burndown data
- `POST /sprints/{id}/close` - Mark sprint complete

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Each test runs against a fresh in-memory SQLite database, so they're order-independent.

## Next Steps

See `roadmap.md` for planned work.
