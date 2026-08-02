"""환경 설정 — .env 파일과 환경변수에서 로드."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # DB
    database_url: str = "postgresql+psycopg2://brain_core_kor:brain_core_kor@localhost:5432/brain_core_kor"

    # JWT — 기본값 없음(필수). 아래 주석 참고
    jwt_secret: str
    jwt_user_minutes: int = 20
    jwt_admin_minutes: int = 240

    # 이름/학번 암호화·HMAC 키 (hex 문자열) — 기본값 없음(필수)
    #
    # 이 세 값에는 의도적으로 기본값을 두지 않는다.
    # 기본값이 있으면 .env 주입에 실패했을 때 조용히 그 값으로 폴백해서
    # 암호화가 무력화된 줄 모른 채 서비스가 계속 돌아간다.
    # 기본값이 없으면 기동 시점에 ValidationError 로 즉시 멈춘다(= 알아챌 수 있다).
    name_aes_key: str
    name_hmac_key: str

    # 파일 저장
    storage_backend: str = "local"
    storage_dir: str = "./var/uploads"
    public_base_url: str = "/files"

    # S3 (storage_backend=s3 일 때 사용)
    s3_bucket: str = ""
    s3_region: str = "ap-northeast-2"
    s3_prefix: str = "uploads/"
    s3_presign_expires: int = 3600
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # 이미지 정책
    max_image_bytes: int = 10 * 1024 * 1024
    image_max_long_edge: int = 1280
    max_images_per_post: int = 5

    # CORS
    cors_origins: str = "http://localhost:5173"

    # 기능 플래그 — 댓글(학부모 댓글/관리자 답글/미답변 인박스) 임시 비활성화
    comments_enabled: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
