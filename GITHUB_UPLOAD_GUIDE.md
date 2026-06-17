# GitHub Upload Guide

Recommended repository name:

```text
ai-email-action-automation
```

## Before uploading

Make sure these files are present:

```text
README.md
LICENSE
requirements.txt
dashboard/requirements.txt
app/
dashboard/
tests/
docs/screenshots/
.github/workflows/tests.yml
setup_windows.bat
start_backend.bat
start_dashboard.bat
```

Do not upload `.venv`, `.env`, `app.db`, `token.json`, or any real credentials. They are already covered by `.gitignore`.

## Upload using Git commands

Open PowerShell inside the project folder and run:

```powershell
git init
git add .
git commit -m "Initial commit: AI email action automation system"
git branch -M main
```

Create an empty GitHub repository named:

```text
ai-email-action-automation
```

Do not add a README, license, or gitignore on GitHub because this project already has them.

Then connect and push:

```powershell
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/ai-email-action-automation.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

## Upload using GitHub CLI

If GitHub CLI is installed:

```powershell
gh auth login
gh repo create ai-email-action-automation --public --source=. --remote=origin --push
```

## After pushing

1. Open the repository on GitHub.
2. Check that screenshots show correctly in README.
3. Go to the **Actions** tab and confirm the test workflow runs.
4. Add these repository topics:

```text
ai-automation
fastapi
streamlit
email-automation
human-in-the-loop
workflow-automation
gmail-api
google-calendar-api
llm
python
```

## Suggested repository description

```text
Human-in-the-loop AI email automation system that analyzes emails, plans safe workflow actions, requires approval, executes actions, and stores audit logs.
```
