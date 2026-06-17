"""
AI Email-to-Action Automation System - Approval Dashboard.

Run with:
    streamlit run dashboard/app.py

Configure the backend URL with the API_BASE_URL environment variable
(defaults to http://localhost:8000).

Page structure:
  Home              - system status, metrics, demo seeding
  Emails            - synced emails, AI analysis, action planning
  Approval Queue    - review/edit/approve/reject/execute proposed actions
  Execution History - completed/escalated/failed/rejected/ignored actions
  Audit Log         - full event trail
"""

import json
from datetime import datetime

import streamlit as st

from api_client import API_BASE_URL, get, post, patch

st.set_page_config(page_title="AI Email-to-Action Automation", layout="wide")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ACTIVE_STATUSES = ["pending", "edited", "approved", "failed"]
HISTORY_STATUSES = ["executed", "escalated", "failed", "rejected", "ignored"]

ACTION_TYPE_LABELS = {
    "CREATE_GMAIL_DRAFT": "✉️ Gmail Draft",
    "CREATE_CALENDAR_EVENT": "📅 Calendar Event",
    "CREATE_TASK": "🗒️ Internal Task",
    "ESCALATE": "🚩 Escalate",
    "IGNORE": "🚫 Ignore",
}

STATUS_BADGES = {
    "pending": "🟡 pending",
    "edited": "✏️ edited",
    "approved": "🟢 approved",
    "rejected": "🔴 rejected",
    "executed": "✅ executed",
    "failed": "❌ failed",
    "escalated": "🚩 escalated",
}


def fmt_dt(value: str | None) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def show_error(error: str | None) -> bool:
    if error:
        st.error(error)
        return True
    return False


@st.cache_data(ttl=15)
def load_emails_index():
    """Return {email_id: (subject, sender)} for quick lookups, cached briefly."""
    data, error = get("/emails", params={"limit": 200})
    if error or not data:
        return {}
    return {e["id"]: (e["subject"], e["sender"]) for e in data}


def email_label(email_id: int) -> str:
    index = load_emails_index()
    subject, sender = index.get(email_id, ("(unknown email)", ""))
    return f"#{email_id} - {subject} (from {sender})" if sender else f"#{email_id} - {subject}"


# ---------------------------------------------------------------------------
# Page: Home
# ---------------------------------------------------------------------------

def page_home():
    st.title("📬 AI Email-to-Action Automation System")
    st.caption(
        "AI recommends. Human approves. System executes. "
        "This dashboard lets you run and review the full workflow."
    )

    health, error = get("/health")
    if show_error(error):
        st.info(f"Make sure the backend is running and reachable at **{API_BASE_URL}**.")
        return

    cols = st.columns(4)
    cols[0].metric("Status", health["status"].upper())
    cols[1].metric("Environment", health["env"])
    cols[2].metric("Demo mode", "ON" if health["demo_mode"] else "OFF")
    cols[3].metric("Database", "connected" if health["database_connected"] else "unreachable")

    if health["demo_mode"]:
        st.success(
            "Demo mode is ON - sample emails and mock AI/execution are used, "
            "so you can test the full workflow without any Gmail or AI credentials."
        )

    st.divider()
    st.subheader("Workflow snapshot")

    metrics, error = get("/dashboard/metrics")
    if show_error(error):
        return

    cols = st.columns(6)
    cols[0].metric("Emails synced", metrics["total_emails"])
    cols[1].metric("Analyzed", metrics["emails_analyzed"])
    cols[2].metric("Pending review", metrics["pending_actions"])
    cols[3].metric("Approved", metrics["approved_actions"])
    cols[4].metric("Executed", metrics["executed_actions"])
    cols[5].metric("Escalated", metrics["escalated_emails"])

    st.divider()
    st.subheader("Get started")
    st.markdown(
        "1. Go to **Emails** and click **Sync Emails** to pull in new messages "
        "(sample data in demo mode, real Gmail otherwise).\n"
        "2. Click **Analyze** on an email to run AI classification.\n"
        "3. Click **Plan Action** to generate a proposed workflow action.\n"
        "4. Go to **Approval Queue** to review, edit, approve, reject, and execute actions.\n"
        "5. Check **Execution History** and **Audit Log** to see the full trace."
    )


# ---------------------------------------------------------------------------
# Page: Emails
# ---------------------------------------------------------------------------

def page_emails():
    st.title("📥 Emails")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Sync Emails", type="primary", use_container_width=True):
            result, error = post("/emails/sync")
            if not show_error(error):
                st.success(
                    f"Synced from **{result['source']}**: "
                    f"{result['fetched']} fetched, {result['new']} new, {result['duplicates']} duplicates."
                )
                st.cache_data.clear()

    emails, error = get("/emails", params={"limit": 200})
    if show_error(error):
        return

    if not emails:
        st.info("No emails synced yet. Click **Sync Emails** to load sample data.")
        return

    st.write(f"**{len(emails)} email(s) synced.**")

    options = {f"#{e['id']} - {e['subject']} (from {e['sender']})": e["id"] for e in emails}
    selected_label = st.selectbox("Select an email to inspect", list(options.keys()))
    email_id = options[selected_label]

    detail, error = get(f"/emails/{email_id}")
    if show_error(error):
        return

    st.markdown(f"### {detail['subject']}")
    st.caption(f"From: {detail['sender']}  |  Synced: {fmt_dt(detail['synced_at'])}")
    with st.expander("Email body", expanded=True):
        st.text(detail["body"])

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("AI Analysis")
        if st.button("🤖 Analyze this email"):
            result, error = post(f"/emails/{email_id}/analyze")
            if not show_error(error):
                st.success("Analysis complete.")
                st.rerun()

        analysis = detail.get("analysis")
        if analysis:
            st.markdown(f"**Intent:** `{analysis['intent']}`")
            st.markdown(f"**Priority:** `{analysis['priority']}`")
            st.markdown(f"**Confidence:** {analysis['confidence_score']:.2f}")
            st.markdown(f"**Requested action:** `{analysis['requested_action']}`")
            st.markdown(f"**Summary:** {analysis['summary']}")
            if analysis.get("suggested_reply"):
                st.markdown("**Suggested reply:**")
                st.text(analysis["suggested_reply"])
            for field in ("deadline", "meeting_date", "meeting_time"):
                if analysis.get(field):
                    st.markdown(f"**{field.replace('_', ' ').title()}:** {analysis[field]}")
            with st.expander("Raw AI response"):
                st.json(analysis.get("raw_ai_response") or {})
        else:
            st.info("This email has not been analyzed yet.")

    with col2:
        st.subheader("Workflow Action")
        if analysis:
            if st.button("🧭 Plan action(s) for this email"):
                result, error = post(f"/emails/{email_id}/plan")
                if not show_error(error):
                    st.success(f"{len(result)} action(s) proposed - see Approval Queue.")
                    st.rerun()

            actions, error = get("/actions", params={"limit": 200})
            if not error and actions:
                related = [a for a in actions if a["email_id"] == email_id]
                if related:
                    st.markdown("**Proposed action(s) for this email:**")
                    for a in related:
                        st.markdown(
                            f"- {ACTION_TYPE_LABELS.get(a['action_type'], a['action_type'])} "
                            f"&mdash; {STATUS_BADGES.get(a['status'], a['status'])}"
                        )
                else:
                    st.caption("No actions proposed yet for this email.")
        else:
            st.caption("Analyze this email first to enable action planning.")


# ---------------------------------------------------------------------------
# Page: Approval Queue
# ---------------------------------------------------------------------------

def render_action_card(action: dict):
    action_id = action["id"]
    action_type_label = ACTION_TYPE_LABELS.get(action["action_type"], action["action_type"])
    status_label = STATUS_BADGES.get(action["status"], action["status"])

    with st.container(border=True):
        st.markdown(f"#### {action_type_label}  &nbsp; {status_label}  &nbsp; (Action #{action_id})")
        st.caption(f"Email: {email_label(action['email_id'])}")

        if action.get("reason"):
            st.markdown(f"**Reason:** {action['reason']}")

        payload_key = f"payload_{action_id}"
        payload_str = json.dumps(action.get("payload") or {}, indent=2)
        edited_str = st.text_area("Payload (editable JSON)", value=payload_str, key=payload_key, height=160)

        if action["status"] == "failed" and action.get("execution_result"):
            st.error(f"Last error: {action['execution_result'].get('error')}")

        cols = st.columns(4)

        # Save edits
        if action["status"] in ("pending", "edited"):
            if cols[0].button("💾 Save edit", key=f"save_{action_id}"):
                try:
                    new_payload = json.loads(edited_str)
                except json.JSONDecodeError as exc:
                    st.error(f"Invalid JSON: {exc}")
                else:
                    _, error = patch(f"/actions/{action_id}", json_body={"payload": new_payload})
                    if not show_error(error):
                        st.success("Payload updated.")
                        st.rerun()

        # Approve
        if action["status"] in ("pending", "edited"):
            if cols[1].button("✅ Approve", key=f"approve_{action_id}"):
                _, error = post(f"/actions/{action_id}/approve")
                if not show_error(error):
                    st.success("Approved.")
                    st.rerun()

        # Reject
        if action["status"] in ("pending", "edited"):
            if cols[2].button("⛔ Reject", key=f"reject_{action_id}"):
                _, error = post(f"/actions/{action_id}/reject")
                if not show_error(error):
                    st.warning("Rejected.")
                    st.rerun()

        # Execute / retry
        if action["status"] in ("approved", "failed"):
            label = "🔁 Retry execution" if action["status"] == "failed" else "🚀 Execute"
            if cols[3].button(label, key=f"execute_{action_id}"):
                result, error = post(f"/actions/{action_id}/execute")
                if not show_error(error):
                    if result["action"]["status"] == "failed":
                        st.error(result["message"])
                    else:
                        st.success(result["message"])
                    st.rerun()


def page_approval_queue():
    st.title("🗂️ Approval Queue")
    st.caption("Nothing here is sent or created externally until you click Approve, then Execute.")

    status_filter = st.multiselect(
        "Show statuses",
        options=ACTIVE_STATUSES,
        default=ACTIVE_STATUSES,
    )

    all_actions = []
    for status in status_filter:
        data, error = get("/actions", params={"status": status, "limit": 100})
        if show_error(error):
            return
        all_actions.extend(data)

    all_actions.sort(key=lambda a: a["created_at"], reverse=True)

    if not all_actions:
        st.info("No actions in the selected statuses. Go to **Emails** to analyze and plan actions.")
        return

    st.write(f"**{len(all_actions)} action(s).**")
    for action in all_actions:
        render_action_card(action)


# ---------------------------------------------------------------------------
# Page: Execution History
# ---------------------------------------------------------------------------

def page_execution_history():
    st.title("📜 Execution History")

    status_filter = st.multiselect(
        "Show statuses",
        options=HISTORY_STATUSES,
        default=["executed", "escalated", "failed", "rejected"],
    )

    all_actions = []
    for status in status_filter:
        data, error = get("/actions", params={"status": status, "limit": 100})
        if show_error(error):
            return
        all_actions.extend(data)

    all_actions.sort(key=lambda a: (a.get("executed_at") or a["created_at"]), reverse=True)

    if not all_actions:
        st.info("No completed actions yet.")
        return

    for action in all_actions:
        status_label = STATUS_BADGES.get(action["status"], action["status"])
        action_type_label = ACTION_TYPE_LABELS.get(action["action_type"], action["action_type"])

        with st.container(border=True):
            st.markdown(f"#### {action_type_label}  &nbsp; {status_label}  &nbsp; (Action #{action['id']})")
            st.caption(
                f"Email: {email_label(action['email_id'])}  |  "
                f"Created: {fmt_dt(action['created_at'])}  |  "
                f"Executed: {fmt_dt(action.get('executed_at'))}"
            )
            if action.get("reason"):
                st.markdown(f"**Reason:** {action['reason']}")
            if action.get("execution_result"):
                st.markdown("**Result:**")
                st.json(action["execution_result"])


# ---------------------------------------------------------------------------
# Page: Audit Log
# ---------------------------------------------------------------------------

def page_audit_log():
    st.title("🧾 Audit Log")
    st.caption("Full trace of every system event - syncs, analyses, proposals, approvals, executions, and failures.")

    logs, error = get("/audit-logs", params={"limit": 300})
    if show_error(error):
        return

    if not logs:
        st.info("No audit events yet.")
        return

    event_types = sorted({log["event_type"] for log in logs})
    selected_types = st.multiselect("Filter by event type", options=event_types, default=event_types)

    rows = []
    for log in logs:
        if log["event_type"] not in selected_types:
            continue
        rows.append(
            {
                "Time": fmt_dt(log["created_at"]),
                "Event": log["event_type"],
                "Email": f"#{log['related_email_id']}" if log.get("related_email_id") else "",
                "Action": f"#{log['related_action_id']}" if log.get("related_action_id") else "",
                "Message": log["message"],
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

PAGES = {
    "Home": page_home,
    "Emails": page_emails,
    "Approval Queue": page_approval_queue,
    "Execution History": page_execution_history,
    "Audit Log": page_audit_log,
}

st.sidebar.title("AI Email Automation")
selected_page = st.sidebar.radio("Navigate", list(PAGES.keys()))
st.sidebar.divider()
st.sidebar.caption(f"Backend API:\n`{API_BASE_URL}`")

PAGES[selected_page]()
