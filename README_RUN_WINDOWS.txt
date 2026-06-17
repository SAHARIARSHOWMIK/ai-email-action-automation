WINDOWS RUN GUIDE
=================

This version includes three helper files so you do not need to type long commands.

IMPORTANT
---------
Use Python 3.12 exactly. Python 3.13 may fail with one pinned dependency.
Install Python 3.12 from python.org and tick "Add Python to PATH".

FIRST TIME ONLY
---------------
1. Extract this zip.
2. Open the extracted folder.
3. Double-click: setup_windows.bat
4. Let it finish. It creates .venv, installs packages, creates .env, and runs tests.

EVERY TIME YOU RUN THE PROJECT
------------------------------
1. Double-click: start_backend.bat
   Keep that window open.
   Check: http://localhost:8000/docs

2. Double-click: start_dashboard.bat
   Keep that window open.
   Check: http://localhost:8501

HOW TO TEST THE APP
-------------------
1. In the dashboard, go to Emails.
2. Click Sync Emails.
3. Select the kickoff meeting email.
4. Click Analyze this email.
5. Click Plan action(s) for this email.
6. Go to Approval Queue.
7. Approve, then Execute.
8. Check Execution History and Audit Log.

SAFE FOR YOUR LAPTOP?
---------------------
Yes. Dependencies install inside the project folder's .venv only.
The app uses DEMO_MODE=true and SQLite by default.
It does not connect to your real Gmail unless you manually edit .env and set DEMO_MODE=false.

IF SOMETHING FAILS
------------------
Send me a screenshot or copy the last 20 lines of the error.
