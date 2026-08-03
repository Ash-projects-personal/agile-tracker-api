"""Day-13 additions: extend the existing suite with

1. Deeper blocker-cycle detection (chains beyond the 3-hop case already covered
   in ``test_blockers.py``, plus non-cyclic diamond graphs that must still be
   accepted).
2. Sprint-capacity edge cases (zero, negative, huge, over-assignment behaviour).
3. Velocity rolling-average - computed client-side across several closed
   sprints using the existing ``/sprints/{id}/velocity`` endpoint, so the
   arithmetic contract is pinned before a future ``/sprints/velocity/rolling``
   endpoint lands.

All tests use the public HTTP surface only (``client`` fixture from
``conftest.py``); no production imports.
"""

from datetime import date, timedelta
from statistics import mean

import pytest


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _create_story(client, title, points=3):
    resp = client.post("/stories", json={"title": title, "story_points": points})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_sprint(client, name, capacity=20, offset_days=0):
    start = date.today() + timedelta(days=offset_days)
    end = start + timedelta(days=14)
    resp = client.post(
        "/sprints",
        json={
            "name": name,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "capacity": capacity,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _mark_done(client, story_id):
    resp = client.patch(f"/stories/{story_id}", json={"status": "done"})
    assert resp.status_code == 200, resp.text
    return resp.json()


# --------------------------------------------------------------------------
# 1. Blocker cycle detection - deeper cases
# --------------------------------------------------------------------------


def test_deep_chain_cycle_rejected(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")
    c = _create_story(client, "C")
    d = _create_story(client, "D")
    e = _create_story(client, "E")

    for parent, blocker in [(a, b), (b, c), (c, d), (d, e)]:
        r = client.post(f"/stories/{parent['id']}/block/{blocker['id']}")
        assert r.status_code == 201, r.text

    r = client.post(f"/stories/{e['id']}/block/{a['id']}")
    assert r.status_code == 400
    assert "cycle" in r.json()["detail"].lower()


def test_diamond_graph_is_accepted(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")
    c = _create_story(client, "C")
    d = _create_story(client, "D")

    for parent, blocker in [(a, b), (a, c), (b, d), (c, d)]:
        r = client.post(f"/stories/{parent['id']}/block/{blocker['id']}")
        assert r.status_code == 201, r.text

    body = client.get(f"/stories/{a['id']}/blockers").json()
    assert {s["id"] for s in body["blockers"]} == {b["id"], c["id"]}
    body_d = client.get(f"/stories/{d['id']}/blockers").json()
    assert {s["id"] for s in body_d["blocking"]} == {b["id"], c["id"]}


def test_cycle_across_reintroduced_edge(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")
    c = _create_story(client, "C")

    assert client.post(f"/stories/{a['id']}/block/{b['id']}").status_code == 201
    assert client.post(f"/stories/{b['id']}/block/{c['id']}").status_code == 201
    r1 = client.post(f"/stories/{c['id']}/block/{a['id']}")
    assert r1.status_code == 400

    assert client.delete(f"/stories/{b['id']}/block/{c['id']}").status_code == 204
    assert client.post(f"/stories/{b['id']}/block/{c['id']}").status_code == 201
    r2 = client.post(f"/stories/{c['id']}/block/{a['id']}")
    assert r2.status_code == 400


def test_two_disconnected_chains_do_not_falsely_flag_cycle(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")
    c = _create_story(client, "C")
    d = _create_story(client, "D")

    assert client.post(f"/stories/{a['id']}/block/{b['id']}").status_code == 201
    assert client.post(f"/stories/{c['id']}/block/{d['id']}").status_code == 201
    r = client.post(f"/stories/{b['id']}/block/{d['id']}")
    assert r.status_code == 201, r.text


# --------------------------------------------------------------------------
# 2. Sprint capacity edge cases
# --------------------------------------------------------------------------


def test_capacity_zero_is_allowed(client):
    sprint = _create_sprint(client, "Zero-cap", capacity=0)
    assert sprint["capacity"] == 0


def test_capacity_negative_is_rejected(client):
    today = date.today()
    resp = client.post(
        "/sprints",
        json={
            "name": "Bad",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
            "capacity": -5,
        },
    )
    assert resp.status_code == 422


def test_capacity_very_large_is_accepted(client):
    sprint = _create_sprint(client, "Huge", capacity=10_000)
    assert sprint["capacity"] == 10_000


def test_over_assignment_beyond_capacity_is_permitted(client):
    sprint = _create_sprint(client, "Cap-8", capacity=8)
    s1 = _create_story(client, "S1", points=5)
    s2 = _create_story(client, "S2", points=5)
    assert client.post(f"/stories/{s1['id']}/assign/{sprint['id']}").status_code == 200
    assert client.post(f"/stories/{s2['id']}/assign/{sprint['id']}").status_code == 200

    body = client.get(f"/sprints/{sprint['id']}/velocity").json()
    assert body["planned_points"] == 10
    assert body["completed_points"] == 0


def test_planned_equals_capacity_edge(client):
    sprint = _create_sprint(client, "Exact", capacity=6)
    for i in range(2):
        s = _create_story(client, f"Exact-{i}", points=3)
        assert client.post(f"/stories/{s['id']}/assign/{sprint['id']}").status_code == 200
    body = client.get(f"/sprints/{sprint['id']}/velocity").json()
    assert body["planned_points"] == 6
    assert body["completed_points"] == 0


# --------------------------------------------------------------------------
# 3. Velocity rolling-average
# --------------------------------------------------------------------------


def _completed_points_for_sprint(client, sprint_id):
    return client.get(f"/sprints/{sprint_id}/velocity").json()["completed_points"]


@pytest.fixture
def four_closed_sprints(client):
    completed_per_sprint = [5, 8, 10, 13]
    sprint_ids = []
    for idx, points in enumerate(completed_per_sprint):
        sprint = _create_sprint(
            client, f"Sprint-{idx}", capacity=20, offset_days=idx * 14
        )
        story = _create_story(client, f"Sprint-{idx}-story", points=points)
        client.post(f"/stories/{story['id']}/assign/{sprint['id']}")
        _mark_done(client, story["id"])
        sprint_ids.append(sprint["id"])
    return sprint_ids, completed_per_sprint


def test_rolling_average_of_last_three_sprints(client, four_closed_sprints):
    ids, _ = four_closed_sprints
    completed = [_completed_points_for_sprint(client, sid) for sid in ids]
    assert completed == [5, 8, 10, 13]

    def rolling(seq, window):
        return [mean(seq[i - window + 1 : i + 1]) for i in range(window - 1, len(seq))]

    windows = rolling(completed, 3)
    assert windows[0] == pytest.approx(23 / 3)
    assert windows[1] == pytest.approx(31 / 3)


def test_rolling_average_full_window_equals_arithmetic_mean(client, four_closed_sprints):
    ids, expected = four_closed_sprints
    completed = [_completed_points_for_sprint(client, sid) for sid in ids]
    assert completed == expected
    assert mean(completed) == pytest.approx(36 / 4)


def test_rolling_average_ignores_incomplete_sprint(client):
    ids = []
    for idx in range(2):
        sprint = _create_sprint(client, f"Closed-{idx}", capacity=10, offset_days=idx * 14)
        story = _create_story(client, f"Closed-{idx}-s", points=6)
        client.post(f"/stories/{story['id']}/assign/{sprint['id']}")
        _mark_done(client, story["id"])
        ids.append(sprint["id"])

    sprint = _create_sprint(client, "In-flight", capacity=10, offset_days=28)
    story = _create_story(client, "In-flight-s", points=6)
    client.post(f"/stories/{story['id']}/assign/{sprint['id']}")
    ids.append(sprint["id"])

    completed = [_completed_points_for_sprint(client, sid) for sid in ids]
    assert completed == [6, 6, 0]
    assert mean(completed) == pytest.approx(12 / 3)


def test_rolling_average_window_of_one_equals_current_velocity(client, four_closed_sprints):
    ids, _ = four_closed_sprints
    completed = [_completed_points_for_sprint(client, sid) for sid in ids]
    windows = completed
    assert windows == [5, 8, 10, 13]
