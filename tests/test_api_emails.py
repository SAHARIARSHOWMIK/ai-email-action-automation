"""
API tests: health check, email sync, and duplicate prevention.
"""


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["demo_mode"] is True
    assert data["database_connected"] is True


def test_sync_loads_demo_emails(client):
    response = client.post("/emails/sync")
    assert response.status_code == 200
    data = response.json()

    assert data["source"] == "demo"
    assert data["fetched"] == 8
    assert data["new"] == 8
    assert data["duplicates"] == 0

    emails = client.get("/emails").json()
    assert len(emails) == 8


def test_syncing_twice_does_not_create_duplicates(client):
    first = client.post("/emails/sync").json()
    second = client.post("/emails/sync").json()

    assert first["new"] == 8
    assert second["new"] == 0
    assert second["duplicates"] == 8

    emails = client.get("/emails").json()
    assert len(emails) == 8  # still only 8, not 16


def test_get_email_detail_includes_no_analysis_before_analyzing(synced_client):
    emails = synced_client.get("/emails").json()
    email_id = emails[0]["id"]

    detail = synced_client.get(f"/emails/{email_id}").json()
    assert detail["analysis"] is None


def test_get_nonexistent_email_returns_404(client):
    response = client.get("/emails/999")
    assert response.status_code == 404
