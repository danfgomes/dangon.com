from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    SECRET_KEY: SecretStr
    DATABASE_URL: str
    algorithm: str = "HS256"
    access_token_ex: int = 30

    max_upload_size_bytes: int = 5 * 1024 * 1024

    posts_per_page: int = 5

    reset_token_expiration_minutes: int = 60

    mail_server: str = "sandbox.smtp.mailtrap.io"
    mail_port: int = 587
    mail_username: str = "069213036475f9"
    mail_password: SecretStr = SecretStr("5d46923e9d89f3")

    mail_use_tls: bool = True
    mail_from: str = "d.ferreiragomezz@gmail.com"
    mail_from_name: str = "Daniele Ferreira Gomes"
    frontend_url: str = "http://localhost:8000"


settings = Settings()
