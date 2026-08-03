"""Deep-cycle and diamond-dependency tests for the blocker graph.

Complements ``test_blockers.py`` (which covers direct A -> B -> C -> A cycles)
with longer chains, self-blocks, sibling relationships, and diamond
dependencies where the cycle detector must NOT confuse a converging shape for
a cycle.
"""


def _story(client, title, points=1):
    r = client.post("/stories", json={"title": title, "story_points": points})
    assert r.status_code == 201, r.text
    return r.json()


def _block(client, blocked, blocker, expect=201):
    r = client.post(f"/stories/{blocked['id']}/block/{blocker['id']}")
    assert r.status_code == expect, r.text
    return r


def test_long_chain_five_nodes_rejects_closing_cycle(client):
    # A <- B <- C <- D <- E, then adding E blocked by A closes the ring.
    a = _story(client, "A"); b = _story(client, "B"); c = _story(client, "C")
    d = _story(client, "D"); e = _story(client, "E")
    _block(client, a, b); _block(client, b, c); _block(client, c, d); _block(client, d, e)

    r = _block(client, e, a, expect=400)
    assert "cycle" in r.json()["detail"].lower()


def test_diamond_dependency_is_allowed(client):
    # A depends on B and C; both B and C depend on D. Not a cycle; the graph
    # is a diamond. All four adds must succeed.
    a = _story(client, "A"); b = _story(client, "B")
    c = _story(client, "C"); d = _story(client, "D")
    _block(client, a, b)
    _block(client, a, c)
    _block(client, b, d)
    _block(client, c, d)

    # The blockers list on A shows both immediate predecessors.
    body = client.get(f"/stories/{a['id']}/blockers").json()
    assert sorted(s["id"] for s in body["blockers"]) == sorted([b["id"], c["id"]])


def test_two_disjoint_chains_do_not_interfere(client):
    # Chain 1: A <- B <- C. Chain 2: X <- Y. Adding Y blocked by C must
    # succeed; adding A blocked by Y would still be fine (no cycle).
    a = _story(client, "A"); b = _story(client, "B"); c = _story(client, "C")
    x = _story(client, "X"); y = _story(client, "Y")
    _block(client, a, b); _block(client, b, c)
    _block(client, x, y)
    _block(client, y, c)
    _block(client, a, y)  # no cycle


def test_reverse_direction_cycle_is_caught(client):
    # A -> B (A blocked by B). Try to add B blocked by A -> cycle of length 2.
    a = _story(client, "A"); b = _story(client, "B")
    _block(client, a, b)
    r = _block(client, b, a, expect=400)
    assert "cycle" in r.json()["detail"].lower()


def test_removing_last_link_frees_transitive_done(client):
    # A <- B <- C. Removing A's dependency on B lets A go DONE even while
    # C is still open (C only blocks B, not A directly).
    a = _story(client, "A"); b = _story(client, "B"); c = _story(client, "C")
    _block(client, a, b); _block(client, b, c)

    # A cannot go DONE while B is open
    assert client.patch(f"/stories/{a['id']}", json={"status": "done"}).status_code == 409

    # Remove A -> B link
    assert client.delete(f"/stories/{a['id']}/block/{b['id']}").status_code == 204

    # Now A can go DONE
    r = client.patch(f"/stories/{a['id']}", json={"status": "done"})
    assert r.status_code == 200, r.text


def test_status_done_needs_ALL_direct_blockers_resolved(client):
    # A has two blockers B, C. Resolving only B is not enough.
    a = _story(client, "A"); b = _story(client, "B"); c = _story(client, "C")
    _block(client, a, b); _block(client, a, c)

    assert client.patch(f"/stories/{b['id']}", json={"status": "done"}).status_code == 200
    r = client.patch(f"/stories/{a['id']}", json={"status": "done"})
    assert r.status_code == 409
    assert f"#{c['id']}" in r.json()["detail"]

    assert client.patch(f"/stories/{c['id']}", json={"status": "done"}).status_code == 200
    assert client.patch(f"/stories/{a['id']}", json={"status": "done"}).status_code == 200


def test_blocker_of_blocker_is_not_a_direct_blocker(client):
    # A <- B <- C. Only B is a DIRECT blocker of A. C is transitive.
    a = _story(client, "A"); b = _story(client, "B"); c = _story(client, "C")
    _block(client, a, b); _block(client, b, c)
    body = client.get(f"/stories/{a['id']}/blockers").json()
    assert [s["id"] for s in body["blockers"]] == [b["id"]]


def test_cycle_of_length_three(client):
    a = _story(client, "A"); b = _story(client, "B"); c = _story(client, "C")
    _block(client, a, b); _block(client, b, c)
    r = _block(client, c, a, expect=400)
    assert "cycle" in r.json()["detail"].lower()


def test_cycle_of_length_six(client):
    nodes = [_story(client, f"S{i}") for i in range(6)]
    # S0 <- S1 <- S2 <- S3 <- S4 <- S5
    for i in range(5):
        _block(client, nodes[i], nodes[i + 1])
    # Closing S5 <- S0 would be a length-6 cycle
    r = _block(client, nodes[5], nodes[0], expect=400)
    assert "cycle" in r.json()["detail"].lower()
