"""파일 저장 추상화 (로컬 FS / S3) + 이미지 리사이즈."""
import io
import uuid
from pathlib import Path

from PIL import Image

from app.config import settings
from app.errors import bad_request

ALLOWED_EXT = {"jpg", "jpeg", "png"}
_PIL_FORMAT = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG"}


class LocalStorage:
    """로컬 파일시스템 구현."""

    def __init__(self, base_dir: str, public_base: str):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.public_base = public_base.rstrip("/")

    def save(self, data: bytes, ext: str, prefix: str = "") -> str:
        name = f"{uuid.uuid4().hex}.{ext}"
        key = f"{prefix.strip('/')}/{name}" if prefix else name
        dest = self.base / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return key  # DB에는 key만 저장

    def delete(self, key: str) -> None:
        p = self.base / key
        if p.exists():
            p.unlink()

    def url(self, key: str) -> str:
        return f"{self.public_base}/{key}"


class S3Storage:
    """AWS S3 구현 (presigned URL)."""

    def __init__(self, bucket: str, region: str, prefix: str, presign_expires: int, access_key: str, secret_key: str):
        import boto3
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self._presign_expires = presign_expires
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=f"https://s3.{region}.amazonaws.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def save(self, data: bytes, ext: str, prefix: str = "") -> str:
        parts = [self.prefix, prefix.strip("/"), f"{uuid.uuid4().hex}.{ext}"]
        key = "/".join(p for p in parts if p)
        content_type = "image/png" if ext == "png" else "image/jpeg"
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def url(self, key: str) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self._presign_expires,
        )


def _build_storage():
    if settings.storage_backend == "s3":
        return S3Storage(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            prefix=settings.s3_prefix,
            presign_expires=settings.s3_presign_expires,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
        )
    return LocalStorage(settings.storage_dir, settings.public_base_url)


storage = _build_storage()


def process_image(raw: bytes, filename: str) -> tuple[bytes, str]:
    """확장자 검증 → 긴 변 1280px 초과 시 축소 → 10MB 초과 시 품질 낮춰 재저장."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT:
        raise bad_request("INVALID_IMAGE_TYPE", "jpg/jpeg/png 만 허용됩니다")

    img = Image.open(io.BytesIO(raw))
    img.load()
    fmt = _PIL_FORMAT[ext]

    # 1) 긴 변 축소 (720p 급)
    long_edge = max(img.size)
    if long_edge > settings.image_max_long_edge:
        ratio = settings.image_max_long_edge / long_edge
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))

    # 2) 인코딩 (PNG는 RGBA 가능, JPEG는 RGB 변환)
    def encode(quality: int) -> bytes:
        buf = io.BytesIO()
        if fmt == "JPEG":
            img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
        else:
            img.save(buf, "PNG", optimize=True)
        return buf.getvalue()

    out = encode(85)

    # 3) 여전히 10MB 초과면 품질을 낮춰 재인코딩 (JPEG 한정)
    if len(out) > settings.max_image_bytes and fmt == "JPEG":
        for q in (70, 55, 40):
            out = encode(q)
            if len(out) <= settings.max_image_bytes:
                break

    return out, ext
