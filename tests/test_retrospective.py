"""Tests for the sprint retrospective feature added in v0.3.0."""
from datetime import date, timedelta


def _create_sprint(client, name="Sprint 1", capacity=20):
    today = date.today()
    resp = client.post(
        "/sprints",
        json={
            "name": name,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
            "capacity": capacity,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _close_sprint(client, sprint_id):
    resp = client.post(f"/sprints/{sprint_id}/close")
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_retrospective_for_closed_sprint(client):
    sprint = _create_sprint(client)
    _close_sprint(client, sprint["id"])

    payload = {
        "went_well": "Tight standups, fast PR reviews.",
        "needs_improvement": "Story estimates were too optimistic.",
        "action_items": [
            "Re-estimate carryover stories on Monday",
            "Block 30 min for refinement on Wednesday",
        ],
    }
    resp = client.post(f"/sprints/{sprint['id']}/retrospective", json=payload)
    assert resp.status_code == 201, resp.text

    body = resp.json()
    assert body["sprint_id"] == sprint["id"]
    assert body["went_well"] == payload["went_well"]
    assert body["needs_improvement"] == payload["needs_improvement"]
    assert body["action_items"] == payload["action_items"]
    assert body["created_at"] == date.today().isoformat()
    assert isinstance(body["id"], int)


def test_retrospective_rejected_when_sprint_not_closed(client):
    sprint = _create_sprint(client)
    # Sprint is still PLANNED — retrospective should be rejected.
    resp = client.post(
        f"/sprints/{sprint['id']}/retrospective",
        json={
            "went_well": "n/a",
            "needs_improvement": "n/a",
            "action_items": [],
        },
    )
    assert resp.status_code == 409
    assert "closed" in resp.json()["detail"].lower()


def test_duplicate_retrospective_rejected(client):
    sprint = _create_sprint(client)
    _close_sprint(client, sprint["id"])

    payload = {
        "went_well": "Good demo.",
        "needs_improvement": "More testing.",
        "action_items": ["Add e2e tests"],
    }
    first = client.post(f"/sprints/{sprint['id']}/retrospective", json=payload)
    assert first.status_code == 201

    second = client.post(f"/sprints/{sprint['id']}/retrospective", json=payload)
    assert second.status_code == 409
    assert "already" in second.json()["detail"].lower()


def test_retrospective_for_unknown_sprint_returns_404(client):
    resp = client.post(
        "/sprints/9999/retrospective",
        json={
            "went_well": "n/a",
            "needs_improvement": "n/a",
            "action_items": [],
        },
    )
    assert resp.status_code == 404


def test_retrospective_validation_empty_strings_rejected(client):
    sprint = _create_sprint(client)
    _close_sprint(client, sprint["id"])

    resp = client.post(
        f"/sprints/{sprint['id']}/retrospective",
        json={
            "went_well": "",
            "needs_improvement": "Lots.",
            "action_items": [],
        },
    )
    assert resp.status_code == 422, resp.text


def test_retrospective_action_items_default_to_empty_list(client):
    sprint = _create_sprint(client)
    _close_sprint(client, sprint["id"])

    resp = client.post(
        f"/sprints/{sprint['id']}/retrospective",
        json={
            "went_well": "Smooth sprint.",
            "needs_improvement": "Nothing major.",
            # action_items omitted intentionally
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["action_items"] == []


def test_get_retrospective_returns_recorded_data(client):
    sprint = _create_sprint(client)
    _close_sprint(client, sprint["id"])
    payload = {
        "went_well": "Pairing helped.",
        "needs_improvement": "CI flakiness.",
        "action_items": ["Quarantine the flaky test"],
    }
    client.post(f"/sprints/{sprint['id']}/retrospective", json=payload)

    resp = client.get(f"/sprints/{sprint['id']}/retrospective")
    assert resp.status_code == 200
    body = resp.json()
    assert body["went_well"] == payload["went_well"]
    assert body["action_items"] == payload["action_items"]


def test_get_retrospective_404_when_none_recorded(client):
    sprint = _create_sprint(client)
    _close_sprint(client, sprint["id"])
    resp = client.get(f"/sprints/{sprint['id']}/retrospective")
    assert resp.status_code == 404


def test_get_retrospective_404_when_sprint_missing(client):
    resp = client.get("/sprints/9999/retrospective")
    assert resp.status_code == 404
