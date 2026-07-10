# Update the Existing GitHub Repository

This upgraded package is intended for the existing repository:

```text
https://github.com/SAHARIARSHOWMIK/ai-email-action-automation
```

Do **not** create a second GitHub repository.

## Recommended method: fresh clone, replace, commit, push

This method preserves all existing GitHub history while avoiding mistakes in an older local folder.

### 1. Extract the upgraded ZIP

Extract it to:

```text
C:\Users\showmik\Downloads\ai-email-action-automation-upgraded-final
```

### 2. Clone the existing repository into a temporary update folder

```powershell
cd "C:\Users\showmik\Downloads"
git clone https://github.com/SAHARIARSHOWMIK/ai-email-action-automation.git ai-email-action-automation-update
```

### 3. Mirror the upgraded project into the clone

```powershell
$source = "C:\Users\showmik\Downloads\ai-email-action-automation-upgraded-final"
$target = "C:\Users\showmik\Downloads\ai-email-action-automation-update"

robocopy $source $target /MIR /XD ".git" ".venv" "node_modules" "dist" "__pycache__" ".pytest_cache" /XF ".env" "app.db" "token.json"
```

`robocopy` return codes from 0 through 7 indicate successful copying or normal file differences.

### 4. Review and push one combined upgrade commit

```powershell
cd "C:\Users\showmik\Downloads\ai-email-action-automation-update"

git status
git add -A
git commit -m "Upgrade email automation platform and React operations console"
git push origin main
```

This sends all added, modified, renamed, and removed files in one commit to the same repository.

## Verify after pushing

Open:

```text
https://github.com/SAHARIARSHOWMIK/ai-email-action-automation
https://github.com/SAHARIARSHOWMIK/ai-email-action-automation/actions
```

Confirm that:

- the new README and screenshots render;
- `frontend/` is present;
- the old `dashboard/` directory is removed;
- the newest GitHub Actions run passes; and
- `.env`, `app.db`, `.venv`, `node_modules`, and tokens are absent.

## Suggested repository description

```text
Human-in-the-loop AI email automation platform with a React operations console, FastAPI workflow engine, Gmail and Calendar integrations, approval gates, task tracking, analytics, and audit logs.
```

## Suggested topics

```text
ai-automation
email-automation
fastapi
react
typescript
human-in-the-loop
workflow-automation
gmail-api
google-calendar-api
python
```
