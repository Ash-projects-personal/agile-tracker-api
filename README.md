# Agile Tracker API

[![CI](https://github.com/Ash-projects-personal/agile-tracker-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Ash-projects-personal/agile-tracker-api/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

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

## v0.4.0 — analytics: rolling velocity + capacity utilisation, deeper blocker tests

**New endpoints**

- `GET /sprints/{id}/capacity` — committed points, capacity, utilisation ratio, and an `over_capacity` flag. Capacity-0 sprints with any committed story report `utilization: null` (undefined ratio) and `over_capacity: true`.
- `GET /sprints/analytics/rolling-velocity?window=3` — mean completed velocity over the last N **closed** sprints (active sprints are excluded so an in-flight sprint can't inflate the number).

**New tests (25)**

- `tests/test_blocker_cycles.py` (9) — length-3/5/6 rings, diamond dependencies allowed, disjoint chains, direct-vs-transitive blocker semantics, removing the last link frees the transitive DONE.
- `tests/test_sprint_capacity.py` (8) — zero-capacity sprints, exactly-at-capacity boundary, over-capacity flag, negative capacity rejected by validation, completing a story does not change committed points.
- `tests/test_velocity_rolling_average.py` (8) — no-closed-sprints returns 0, single/three-sprint mean, window-most-recent selection, active sprints excluded, `window=0` rejected, default window of 3.
