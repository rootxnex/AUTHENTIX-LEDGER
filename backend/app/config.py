"""AUTHENTIX LEDGER — Application Configuration"""
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://authentix:changeme@localhost:5432/authentix"

    # JWT
    SECRET_KEY: str = secrets.token_hex(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # AES-256 encryption key (64-char hex = 32 bytes)
    AES_KEY: str = "0" * 64

    # MinIO / S3 Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "authentix-evidence"
    MINIO_SECURE: bool = False

    # Blockchain adapter: "mock" or "fabric"
    BLOCKCHAIN_MODE: str = "mock"
    FABRIC_GATEWAY_ENDPOINT: str = ""
    FABRIC_CHANNEL: str = "authentix-channel"
    FABRIC_CHAINCODE: str = "authentix-ledger"
    FABRIC_MSP_ID: str = "Org1MSP"
    FABRIC_CERT_PATH: str = ""
    FABRIC_KEY_PATH: str = ""
    FABRIC_TLS_CERT_PATH: str = ""

    # Seeded admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin@123!"
    ADMIN_EMAIL: str = "admin@authentix.gov.in"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def aes_key_bytes(self) -> bytes:
        return bytes.fromhex(self.AES_KEY)


settings = Settings()
