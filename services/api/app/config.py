from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    project_name: str = "cyclone-risk-network"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.7-flash"
    google_genai_use_vertexai: bool = False
    google_cloud_project: str = ""
    google_cloud_location: str = "asia-south1"
    bigquery_dataset: str = "cyclone_risk_network"
    gcs_bucket: str = ""
    firebase_project_id: str = ""
    maps_api_key: str = ""
    earth_engine_project: str = ""
    cors_origins: str = "http://localhost:3050,http://localhost:3051"

    # Cloud Translation + Text-to-Speech REST (API key restricted to those two APIs)
    google_cloud_api_key: str = ""
    # Sandbox dispatch. SMS: Twilio test credentials "ACCOUNT_SID:AUTH_TOKEN"; messaging: Telegram bot token.
    sms_sandbox_key: str = ""
    sms_sandbox_from: str = ""
    sms_sandbox_to: str = ""
    messaging_sandbox_token: str = ""
    messaging_sandbox_chat_id: str = ""

    # Local store (SQLite) used when Firestore is not configured
    store_path: str = str(REPO_ROOT / "services" / "api" / ".data" / "tatraksha.sqlite3")
    # Force every integration into demo mode (tests, offline demos)
    force_demo_mode: bool = False


settings = Settings()
