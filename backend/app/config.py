from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App / auth
    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    database_url: str = "sqlite:///./billing_report.db"

    # Admin seed
    admin_username: str = "admin"
    admin_password: str = "change-me"

    # ION integration
    ion_mode: str = "mock"  # "mock" | "live"
    ion_token_url: str = "https://ion.tdsynnex.com/oauth/token"
    ion_base_url: str = "https://ion.tdsynnex.com"
    ion_account_id: str = ""
    ion_refresh_token: str = ""
    ion_token_cache_path: str = ".ion_token_cache.json"
    ion_customers_path: str = "/api/v3/accounts/{account_id}/customers"
    ion_subscriptions_path: str = "/api/v3/accounts/{account_id}/subscriptions"

    # CORS
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
