"""
Centralized application configuration.

All environment-driven settings live here so the rest of the codebase
never reads os.environ directly. This makes it trivial to switch between
demo mode (no credentials needed) and a real Gmail/AI setup.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- App ---
    app_name: str = "AI Email-to-Action Automation System"
    env: str = "development"
    demo_mode: bool = True

    # --- Database ---
    database_url: str = "sqlite:///./app.db"

    # --- Gmail API ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    gmail_token_file: str = "token.json"

    # --- AI Analysis ---
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # --- Workflow rules ---
    confidence_threshold: float = 0.75


settings = Settings()
