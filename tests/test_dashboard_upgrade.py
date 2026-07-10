"""Tests for the upgraded operations dashboard and demo workflow."""


def test_dashboard_overview_is_empty_initially(client):
    response = client.get("/dashboard/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["total_emails"] == 0
    assert body["analysis_rate"] == 0
    assert body["recent_activity"] == []


def test_demo_bootstrap_creates_complete_review_workspace(client):
    response = client.post("/demo/bootstrap")
    assert response.status_code == 200
    body = response.json()
    assert body["emails_total"] == 8
    assert body["emails_analyzed"] == 8
    assert body["actions_created"] >= 8

    overview = client.get("/dashboard/overview").json()
    assert overview["metrics"]["total_emails"] == 8
    assert overview["metrics"]["emails_analyzed"] == 8
    assert overview["analysis_rate"] == 100.0
    assert overview["average_confidence"] > 0
    assert overview["intent_distribution"]["meeting_request"] == 1
    assert len(overview["recent_activity"]) > 0


def test_demo_bootstrap_is_idempotent(client):
    first = client.post("/demo/bootstrap")
    second = client.post("/demo/bootstrap")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["emails_added"] == 0
    assert second.json()["emails_analyzed"] == 0
    assert second.json()["actions_created"] == 0


def test_task_lifecycle_after_task_action_execution(client):
    client.post("/demo/bootstrap")
    actions = client.get("/actions?limit=200").json()
    task_action = next(item for item in actions if item["action_type"] == "CREATE_TASK")

    approved = client.post(f"/actions/{task_action['id']}/approve")
    assert approved.status_code == 200
    executed = client.post(f"/actions/{task_action['id']}/execute")
    assert executed.status_code == 200

    tasks = client.get("/tasks").json()
    assert len(tasks) == 1
    task_id = tasks[0]["id"]
    assert tasks[0]["status"] == "open"

    completed = client.post(f"/tasks/{task_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["task"]["status"] == "done"

    reopened = client.post(f"/tasks/{task_id}/reopen")
    assert reopened.status_code == 200
    assert reopened.json()["task"]["status"] == "open"


def test_task_not_found_returns_404(client):
    response = client.post("/tasks/999/complete")
    assert response.status_code == 404


def test_audit_log_can_filter_event_type(client):
    client.post("/demo/bootstrap")
    response = client.get("/audit-logs?event_type=demo_workspace_ready")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["event_type"] == "demo_workspace_ready"
