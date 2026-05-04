"""Sanity tests for the pre-existing endpoints, to make sure the v0.2.0
refactor (status-DONE guard, BlockerError plumbing) didn't break anything.
"""
from datetime import date, timedelta


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["docs"] == "/docs"


def test_create_and_list_story(client):
    resp = client.post("/stories", json={"title": "Story 1", "story_points": 5})
    assert resp.status_code == 201
    assert resp.json()["status"] == "backlog"

    resp = client.get("/stories")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_status_transition_to_done_without_blockers(client):
    s = client.post("/stories", json={"title": "S", "story_points": 1}).json()
    resp = client.patch(f"/stories/{s['id']}", json={"status": "done"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "done"
    assert body["completed_at"] is not None


def test_sprint_lifecycle(client):
    today = date.today()
    sprint = client.post(
        "/sprints",
        json={
            "name": "Sprint 1",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
            "capacity": 30,
        },
    ).json()

    story = client.post("/stories", json={"title": "S", "story_points": 5}).json()
    resp = client.post(f"/stories/{story['id']}/assign/{sprint['id']}")
    assert resp.status_code == 200
    assert resp.json()["sprint_id"] == sprint["id"]

    resp = client.get(f"/sprints/{sprint['id']}/velocity")
    assert resp.status_code == 200
    body = resp.json()
    assert body["planned_points"] == 5
    assert body["completed_points"] == 0


def test_invalid_sprint_dates_rejected(client):
    today = date.today()
    resp = client.post(
        "/sprints",
        json={
            "name": "Bad",
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "capacity": 10,
        },
    )
    assert resp.status_code == 400
