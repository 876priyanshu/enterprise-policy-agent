from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    database_url: str
    secret_key: str
    groq_api_key: str  # Renamed from grok to groq
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()