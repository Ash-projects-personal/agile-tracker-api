"""Rolling-average velocity across closed sprints."""
from datetime import date, timedelta


def _sprint(client, name, start_offset, capacity=20):
    start = date.today() + timedelta(days=start_offset)
    r = client.post(
        "/sprints",
        json={
            "name": name,
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=14)).isoformat(),
            "capacity": capacity,
        },
    )
    return r.json()


def _story(client, points, status="todo", sprint_id=None):
    s = client.post("/stories", json={"title": "S", "story_points": points}).json()
    if sprint_id is not None:
        client.post(f"/stories/{s['id']}/assign/{sprint_id}")
    if status == "done":
        client.patch(f"/stories/{s['id']}", json={"status": "done"})
    return s


def _close(client, sprint):
    r = client.post(f"/sprints/{sprint['id']}/close")
    assert r.status_code == 200


def test_no_closed_sprints_returns_zero(client):
    body = client.get("/sprints/analytics/rolling-velocity?window=3").json()
    assert body["sprints_considered"] == 0
    assert body["velocity"] == 0.0


def test_single_closed_sprint_reports_its_own_velocity(client):
    sp = _sprint(client, "S1", start_offset=-60)
    _story(client, 5, status="done", sprint_id=sp["id"])
    _story(client, 3, status="done", sprint_id=sp["id"])
    _close(client, sp)

    body = client.get("/sprints/analytics/rolling-velocity?window=3").json()
    assert body["sprints_considered"] == 1
    assert body["velocity"] == 8.0


def test_rolling_average_over_three_closed_sprints(client):
    for i, points in enumerate([6, 9, 12]):
        sp = _sprint(client, f"S{i}", start_offset=-60 + i * 20)
        _story(client, points, status="done", sprint_id=sp["id"])
        _close(client, sp)

    body = client.get("/sprints/analytics/rolling-velocity?window=3").json()
    assert body["sprints_considered"] == 3
    assert body["velocity"] == 9.0  # (6+9+12)/3


def test_rolling_window_takes_most_recent_only(client):
    # Five closed sprints; window=3 must ignore the two oldest.
    points_by_end_date_desc = [10, 20, 30, 40, 50]  # oldest first
    for i, p in enumerate(points_by_end_date_desc):
        sp = _sprint(client, f"S{i}", start_offset=-90 + i * 15)
        _story(client, p, status="done", sprint_id=sp["id"])
        _close(client, sp)

    body = client.get("/sprints/analytics/rolling-velocity?window=3").json()
    # Most-recent 3 sprints correspond to points 30, 40, 50 -> mean 40
    assert body["sprints_considered"] == 3
    assert body["velocity"] == 40.0


def test_active_sprints_are_excluded(client):
    # Two closed sprints (velocity 5 each) + one currently-active with 100
    # completed points must NOT inflate the rolling average.
    for i in range(2):
        sp = _sprint(client, f"S{i}", start_offset=-60 + i * 15)
        _story(client, 5, status="done", sprint_id=sp["id"])
        _close(client, sp)

    active = _sprint(client, "Active", start_offset=0)
    _story(client, 100, status="done", sprint_id=active["id"])
    # (not closed)

    body = client.get("/sprints/analytics/rolling-velocity?window=3").json()
    assert body["sprints_considered"] == 2
    assert body["velocity"] == 5.0


def test_window_zero_returns_400(client):
    r = client.get("/sprints/analytics/rolling-velocity?window=0")
    assert r.status_code == 400


def test_completed_but_not_done_stories_are_excluded_from_velocity(client):
    sp = _sprint(client, "S", start_offset=-30)
    _story(client, 5, status="done", sprint_id=sp["id"])   # counts
    _story(client, 8, status="todo", sprint_id=sp["id"])   # does not count
    _close(client, sp)

    body = client.get("/sprints/analytics/rolling-velocity?window=3").json()
    assert body["velocity"] == 5.0


def test_rolling_velocity_default_window_is_three(client):
    for i, p in enumerate([2, 4, 6, 8]):
        sp = _sprint(client, f"S{i}", start_offset=-90 + i * 20)
        _story(client, p, status="done", sprint_id=sp["id"])
        _close(client, sp)
    # Default window=3 -> last three sprints (velocities 4, 6, 8) -> 6.0
    body = client.get("/sprints/analytics/rolling-velocity").json()
    assert body["window"] == 3
    assert body["velocity"] == 6.0
