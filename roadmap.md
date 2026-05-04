# Roadmap for agile-tracker-api

### Day 1: Add story dependencies and blockers ✅ (shipped in v0.2.0)
Implement many-to-many blocking relationships between stories. Add validation to prevent marking stories done if blockers remain. New endpoint: POST /stories/{id}/block/{blocker_id}

Shipped:
- `story_blockers` association table with cascade delete
- `add_blocker` / `remove_blocker` CRUD with self-block + cycle detection
- `update_story` returns 409 when status=DONE while blockers are unresolved
- New endpoints: `GET /stories/{id}/blockers`, `POST /stories/{id}/block/{blocker_id}`, `DELETE /stories/{id}/block/{blocker_id}`

### Day 2: Add retrospective notes per sprint ✅ (shipped in v0.3.0)
Create Retrospective model linked to sprints. Capture went_well, needs_improvement, and action_items. New endpoint: POST /sprints/{id}/retrospective to record retro data after sprint close

Shipped:
- `RetrospectiveDB` table with one-to-one `sprint` ↔ `retrospective` link (unique sprint_id, cascade delete from sprint)
- `action_items` stored as a JSON list of strings; `went_well` / `needs_improvement` are required non-empty text
- `POST /sprints/{id}/retrospective` returns 201; rejects with 409 when sprint isn't `closed` or a retro already exists; 404 when sprint missing
- Companion `GET /sprints/{id}/retrospective` for retrieval

### Day 3: Add team member assignments and capacity planning
Create TeamMember model with per-sprint capacity. Add assigned_to field on stories. New endpoint: GET /sprints/{id}/capacity showing per-person workload vs. capacity

### Day 4: Add epic grouping for stories
Create Epic model to group related stories. Add epic_id foreign key to Story. New endpoints for epic CRUD and GET /epics/{id}/progress showing completion percentage across sprints

### Day 5: Add automated sprint rollover
Implement POST /sprints/{id}/rollover to close current sprint, create next sprint, and move incomplete stories forward. Reset in_progress stories to todo. Return migration summary
