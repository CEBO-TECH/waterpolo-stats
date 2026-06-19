"""S3 / MinIO-backed storage (production). boto3 is imported lazily."""

from src.config import settings
from src.domain.ports.external import StoragePort


class S3StorageAdapter(StoragePort):
    def __init__(self):
        import boto3  # lazy: only required when STORAGE_BACKEND=s3

        self.bucket = settings.S3_BUCKET
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT or None,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        # Ensure bucket exists (idempotent).
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except Exception:
            try:
                self._client.create_bucket(Bucket=self.bucket)
            except Exception:
                pass

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def get_bytes(self, key: str) -> bytes | None:
        try:
            obj = self._client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read()
        except Exception:
            return None

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self.bucket, Key=key)
        except Exception:
            pass
