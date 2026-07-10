MAILPILOT AI — WINDOWS RUN GUIDE
================================

REQUIREMENTS
------------
- Python 3.12 or newer
- Node.js 20 or newer
- Internet access during first-time installation

FIRST TIME ONLY
---------------
1. Extract the project ZIP.
2. Open the extracted folder.
3. Double-click setup_windows.bat.
4. Wait for backend tests and the frontend build to finish.

EVERY TIME YOU RUN THE PROJECT
------------------------------
1. Double-click start_backend.bat and keep the window open.
2. Double-click start_frontend.bat and keep the window open.
3. Open http://localhost:5173.

USEFUL ADDRESSES
----------------
Operations console: http://localhost:5173
API documentation:  http://localhost:8000/docs
Health endpoint:     http://localhost:8000/health

LOAD THE WORKFLOW
-----------------
1. Open Overview.
2. Click "Load complete demo workflow".
3. Review Smart Inbox.
4. Open Approval Queue.
5. Edit/approve/reject proposed actions.
6. Execute an approved action.
7. Review Tasks, Execution History, and Audit Trail.

RUN ALL CHECKS
--------------
Double-click run_tests.bat.

SAFE LOCAL DEFAULTS
-------------------
- DEMO_MODE=true
- SQLite database stored locally and excluded from Git
- no external credentials required
- Gmail actions create drafts; they do not automatically send email
- dependencies remain inside this project (.venv and frontend/node_modules)

LIVE PROVIDERS
--------------
Live Gmail, Calendar, and Anthropic adapters require your own credentials.
Edit .env only after reading .env.example. Never commit .env or token.json.
