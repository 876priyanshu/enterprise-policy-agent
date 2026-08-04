from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    database_url: str
    secret_key: str
    groq_api_key: str 
    TAVILY_API_KEY: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # class Config:
    #     env_file = ".env"

settings = Settings()