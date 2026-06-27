"""Bootstrap seed for the first global admin.

Runs automatically on container startup (see ``entrypoint.sh``) and via ``make seed``.
Idempotent at the database level: the insert uses ``ON CONFLICT DO NOTHING`` on the
unique ``email``, so running it on every boot is safe and race-free. This is the only
way to provision the first account, since ``POST /auth/register`` is restricted to
admins (RN-001).
"""

import asyncio

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import Settings, get_settings
from app.core.logger import get_logger, stop_logger
from app.core.security import PasswordSecurity
from app.db.engine import async_session
from app.db.models import GlobalRole, User

logger = get_logger("app.seed")

_DEFAULT_ADMIN_PASSWORD = Settings.model_fields["SEED_ADMIN_PASSWORD"].default


async def seed_admin() -> None:
    settings = get_settings()
    security = PasswordSecurity()

    if settings.SEED_ADMIN_PASSWORD == _DEFAULT_ADMIN_PASSWORD:
        logger.warning("Seeding admin with the default password; override SEED_ADMIN_PASSWORD")

    stmt = (
        pg_insert(User)
        .values(
            name=settings.SEED_ADMIN_NAME,
            email=settings.SEED_ADMIN_EMAIL,
            password_hash=security.generate_password_hash(settings.SEED_ADMIN_PASSWORD),
            global_role=GlobalRole.ADMIN,
        )
        .on_conflict_do_nothing(index_elements=["email"])
        .returning(User.id)
    )

    async with async_session() as db:
        inserted_id = await db.scalar(stmt)
        await db.commit()

    if inserted_id is not None:
        logger.info(
            "Admin user seeded",
            extra={"user_id": str(inserted_id), "email": settings.SEED_ADMIN_EMAIL},
        )
    else:
        logger.info(
            "Admin already present; seed skipped",
            extra={"email": settings.SEED_ADMIN_EMAIL},
        )


async def main() -> None:
    try:
        await seed_admin()
    finally:
        stop_logger()


if __name__ == "__main__":
    asyncio.run(main())
