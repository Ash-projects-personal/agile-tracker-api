"""Tests for the story-blocker (dependencies) feature added in v0.2.0."""


def _create_story(client, title, points=3):
    resp = client.post("/stories", json={"title": title, "story_points": points})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_add_and_list_blocker(client):
    a = _create_story(client, "A — depends on B")
    b = _create_story(client, "B — must be done first")

    resp = client.post(f"/stories/{a['id']}/block/{b['id']}")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["story_id"] == a["id"]
    assert [s["id"] for s in body["blockers"]] == [b["id"]]
    assert body["blocking"] == []

    # The reverse direction is reflected via `blocking`
    resp = client.get(f"/stories/{b['id']}/blockers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["blockers"] == []
    assert [s["id"] for s in body["blocking"]] == [a["id"]]


def test_add_blocker_is_idempotent(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")

    client.post(f"/stories/{a['id']}/block/{b['id']}")
    resp = client.post(f"/stories/{a['id']}/block/{b['id']}")
    assert resp.status_code == 201
    assert len(resp.json()["blockers"]) == 1


def test_self_block_rejected(client):
    a = _create_story(client, "A")
    resp = client.post(f"/stories/{a['id']}/block/{a['id']}")
    assert resp.status_code == 400
    assert "itself" in resp.json()["detail"].lower()


def test_cycle_rejected(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")
    c = _create_story(client, "C")

    # Build chain A -> B -> C (A blocked by B, B blocked by C)
    assert client.post(f"/stories/{a['id']}/block/{b['id']}").status_code == 201
    assert client.post(f"/stories/{b['id']}/block/{c['id']}").status_code == 201

    # Attempting C blocked by A would close the cycle
    resp = client.post(f"/stories/{c['id']}/block/{a['id']}")
    assert resp.status_code == 400
    assert "cycle" in resp.json()["detail"].lower()


def test_unknown_story_or_blocker_returns_404(client):
    a = _create_story(client, "A")
    assert client.post(f"/stories/{a['id']}/block/9999").status_code == 404
    assert client.post("/stories/9999/block/" + str(a["id"])).status_code == 404


def test_done_blocked_by_open_blocker(client):
    a = _create_story(client, "A — needs B done")
    b = _create_story(client, "B — still open")
    client.post(f"/stories/{a['id']}/block/{b['id']}")

    resp = client.patch(f"/stories/{a['id']}", json={"status": "done"})
    assert resp.status_code == 409
    assert f"#{b['id']}" in resp.json()["detail"]


def test_done_allowed_once_blocker_resolved(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")
    client.post(f"/stories/{a['id']}/block/{b['id']}")

    # Resolve the blocker first
    resp = client.patch(f"/stories/{b['id']}", json={"status": "done"})
    assert resp.status_code == 200

    # Now A can be marked DONE
    resp = client.patch(f"/stories/{a['id']}", json={"status": "done"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "done"


def test_remove_blocker(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")
    client.post(f"/stories/{a['id']}/block/{b['id']}")

    resp = client.delete(f"/stories/{a['id']}/block/{b['id']}")
    assert resp.status_code == 204

    body = client.get(f"/stories/{a['id']}/blockers").json()
    assert body["blockers"] == []

    # And A can now go DONE without resolving B
    resp = client.patch(f"/stories/{a['id']}", json={"status": "done"})
    assert resp.status_code == 200


def test_non_done_status_change_is_unaffected_by_blockers(client):
    a = _create_story(client, "A")
    b = _create_story(client, "B")
    client.post(f"/stories/{a['id']}/block/{b['id']}")

    # Moving to in_progress should not be blocked
    resp = client.patch(f"/stories/{a['id']}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
