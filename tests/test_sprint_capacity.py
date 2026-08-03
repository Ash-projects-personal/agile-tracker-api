"""Sprint-capacity edge cases: zero-capacity, at-capacity, over-capacity."""
from datetime import date, timedelta


def _sprint(client, name, capacity):
    today = date.today()
    r = client.post(
        "/sprints",
        json={
            "name": name,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
            "capacity": capacity,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _story(client, points):
    r = client.post("/stories", json={"title": f"S({points})", "story_points": points})
    assert r.status_code == 201
    return r.json()


def _assign(client, story, sprint):
    r = client.post(f"/stories/{story['id']}/assign/{sprint['id']}")
    assert r.status_code == 200


def test_zero_capacity_sprint_is_creatable(client):
    sprint = _sprint(client, "Cool-down", 0)
    assert sprint["capacity"] == 0


def test_zero_capacity_with_no_stories_utilization_is_zero(client):
    sprint = _sprint(client, "Cool-down", 0)
    body = client.get(f"/sprints/{sprint['id']}/capacity").json()
    assert body["capacity"] == 0
    assert body["committed_points"] == 0
    assert body["utilization"] == 0.0
    assert body["over_capacity"] is False


def test_zero_capacity_with_any_story_is_over_capacity(client):
    sprint = _sprint(client, "Cool-down", 0)
    s = _story(client, 1)
    _assign(client, s, sprint)
    body = client.get(f"/sprints/{sprint['id']}/capacity").json()
    assert body["committed_points"] == 1
    assert body["over_capacity"] is True
    # utilization is undefined (0-capacity denominator); reported as null
    assert body["utilization"] is None


def test_exactly_at_capacity_is_not_over(client):
    sprint = _sprint(client, "Sprint 1", 10)
    _assign(client, _story(client, 4), sprint)
    _assign(client, _story(client, 6), sprint)
    body = client.get(f"/sprints/{sprint['id']}/capacity").json()
    assert body["committed_points"] == 10
    assert body["utilization"] == 1.0
    assert body["over_capacity"] is False


def test_over_capacity_flag_set_when_committed_exceeds(client):
    sprint = _sprint(client, "Sprint 2", 10)
    _assign(client, _story(client, 8), sprint)
    _assign(client, _story(client, 5), sprint)  # total 13 > 10
    body = client.get(f"/sprints/{sprint['id']}/capacity").json()
    assert body["committed_points"] == 13
    assert body["utilization"] == 1.3
    assert body["over_capacity"] is True


def test_negative_capacity_rejected(client):
    today = date.today()
    r = client.post(
        "/sprints",
        json={
            "name": "Bad",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=7)).isoformat(),
            "capacity": -1,
        },
    )
    assert r.status_code == 422  # pydantic validation (ge=0)


def test_capacity_endpoint_missing_sprint_404(client):
    r = client.get("/sprints/9999/capacity")
    assert r.status_code == 404


def test_completing_stories_does_not_change_committed(client):
    # Committed reflects planned points, not completed. Closing stories
    # inside the sprint must not reduce the committed number.
    sprint = _sprint(client, "Sprint 3", 5)
    s = _story(client, 3)
    _assign(client, s, sprint)
    client.patch(f"/stories/{s['id']}", json={"status": "done"})
    body = client.get(f"/sprints/{sprint['id']}/capacity").json()
    assert body["committed_points"] == 3
