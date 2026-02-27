"""MinIO (S3-compatible) storage service for encrypted evidence."""
import io
from minio import Minio
from minio.error import S3Error
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        # Ensure bucket exists
        if not _client.bucket_exists(settings.MINIO_BUCKET):
            _client.make_bucket(settings.MINIO_BUCKET)
            logger.info("minio.bucket_created", bucket=settings.MINIO_BUCKET)
    return _client


def upload_bytes(object_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """
    Upload encrypted bytes to MinIO.
    object_key is the opaque storage pointer (UUID-based, not tied to original filename).
    Returns the object key.
    """
    client = get_minio_client()
    stream = io.BytesIO(data)
    client.put_object(
        settings.MINIO_BUCKET,
        object_key,
        stream,
        length=len(data),
        content_type=content_type,
    )
    logger.info("minio.uploaded", key=object_key, size=len(data))
    return object_key


def download_bytes(object_key: str) -> bytes:
    """Download bytes from MinIO by object key."""
    client = get_minio_client()
    response = client.get_object(settings.MINIO_BUCKET, object_key)
    try:
        data = response.read()
    finally:
        response.close()
        response.release_conn()
    return data


def delete_object(object_key: str) -> None:
    """Delete an object from MinIO."""
    client = get_minio_client()
    client.remove_object(settings.MINIO_BUCKET, object_key)
    logger.info("minio.deleted", key=object_key)
