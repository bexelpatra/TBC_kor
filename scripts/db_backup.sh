#!/bin/bash
set -euo pipefail

BUCKET="tbc-kor-backup-bucket"
CONTAINER="tbc_kor_db_1"
DB_NAME="brain_core_kor"
DB_USER="admin"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
YEAR=$(date +%Y)
MONTH=$(date +%m)
S3_PATH="s3://${BUCKET}/db_backup/${YEAR}/${MONTH}/${DB_NAME}_${TIMESTAMP}.sql.gz"

TMPFILE=$(mktemp /tmp/db_backup_XXXXXX.sql.gz)
trap 'rm -f "$TMPFILE"' EXIT

echo "[$(date)] 백업 시작: ${DB_NAME}"

docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$TMPFILE"

SIZE=$(du -h "$TMPFILE" | cut -f1)
echo "[$(date)] 덤프 완료: ${SIZE}"

aws s3 cp "$TMPFILE" "$S3_PATH" --quiet

echo "[$(date)] 업로드 완료: ${S3_PATH}"

# 90일 이전 백업 삭제
CUTOFF=$(date -d '90 days ago' +%Y%m%d 2>/dev/null || date -v-90d +%Y%m%d)
echo "[$(date)] ${CUTOFF} 이전 백업 정리 중..."

aws s3 ls "s3://${BUCKET}/db_backup/" --recursive \
  | awk '{print $4}' \
  | while read -r key; do
      file_date=$(echo "$key" | grep -oP '\d{8}(?=_\d{6}\.sql\.gz$)' || true)
      if [[ -n "$file_date" && "$file_date" < "$CUTOFF" ]]; then
        aws s3 rm "s3://${BUCKET}/${key}" --quiet
        echo "  삭제: ${key}"
      fi
    done

echo "[$(date)] 백업 완료"
