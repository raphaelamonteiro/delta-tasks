#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}/${POSTGRES_DB}..."
ATTEMPTS=0
MAX_ATTEMPTS="${DB_WAIT_MAX_ATTEMPTS:-30}"
until python - <<'PY'
import asyncio
import os
import sys

import asyncpg


async def check_db() -> None:
  conn = await asyncpg.connect(
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ.get("POSTGRES_PORT", "5432")),
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    database=os.environ["POSTGRES_DB"],
  )
  await conn.close()


try:
  asyncio.run(check_db())
except Exception as exc:  # noqa: BLE001
  print(f"  db check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
  sys.exit(1)
PY
do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
    echo "❌ PostgreSQL não respondeu após ${MAX_ATTEMPTS} tentativas. Abortando." >&2
    exit 1
  fi
  echo "  postgres not ready yet (tentativa ${ATTEMPTS}/${MAX_ATTEMPTS}), retrying in 2s..."
  sleep 2
done

echo "✅ PostgreSQL is ready."

echo "🔄 Running Alembic migrations..."
alembic upgrade head

echo "🚀 Starting FastAPI..."
if [ "${UVICORN_RELOAD:-false}" = "true" ]; then
  exec uvicorn app.main:create_app \
  --factory \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir /app
fi

exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
