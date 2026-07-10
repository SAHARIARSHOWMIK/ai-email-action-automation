# Changelog

## 2.0.0 — Operations Console Upgrade

### Added

- React and TypeScript operations console
- overview analytics and charts
- split-pane smart inbox
- editable human approval queue
- internal task lifecycle
- execution history workspace
- filterable audit trail
- integrations and safety status page
- idempotent demo bootstrap API
- dashboard overview API
- task list, complete, and reopen APIs
- backend/frontend CI jobs
- Nginx frontend container
- expanded test coverage

### Changed

- replaced the Streamlit interface with a responsive React frontend
- separated frontend and backend deployment concerns
- upgraded Docker Compose to include PostgreSQL and a production frontend service
- improved local Windows setup and verification scripts
- refreshed screenshots and portfolio documentation

### Safety

- preserved mandatory human approval before execution
- preserved draft-only Gmail behavior
- demo bootstrap does not approve or execute actions
