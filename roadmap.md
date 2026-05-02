# Roadmap for agile-tracker-api

### Day 1: Add story dependencies and blockers
Implement many-to-many blocking relationships between stories. Add validation to prevent marking stories done if blockers remain. New endpoint: POST /stories/{id}/block/{blocker_id}

### Day 2: Add retrospective notes per sprint
Create Retrospective model linked to sprints. Capture went_well, needs_improvement, and action_items. New endpoint: POST /sprints/{id}/retrospective to record retro data after sprint close

### Day 3: Add team member assignments and capacity planning
Create TeamMember model with per-sprint capacity. Add assigned_to field on stories. New endpoint: GET /sprints/{id}/capacity showing per-person workload vs. capacity

### Day 4: Add epic grouping for stories
Create Epic model to group related stories. Add epic_id foreign key to Story. New endpoints for epic CRUD and GET /epics/{id}/progress showing completion percentage across sprints

### Day 5: Add automated sprint rollover
Implement POST /sprints/{id}/rollover to close current sprint, create next sprint, and move incomplete stories forward. Reset in_progress stories to todo. Return migration summary
