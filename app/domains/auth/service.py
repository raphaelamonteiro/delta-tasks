from app.core.logger import get_logger
from app.core.security import PasswordSecurity
from app.db.models import User
from app.domains.auth.repository import AuthRepository
from app.domains.auth.schemas import CreateUserDTO, RegisterUserDTO

logger = get_logger("app.auth.service")


class AuthService:
    def __init__(self, repo: AuthRepository, sec: PasswordSecurity):
        self.repo = repo
        self.sec = sec

    async def register_user(self, dto: RegisterUserDTO) -> User:
        password_hash = self.sec.generate_password_hash(dto.password)
        user = await self.repo.create(
            CreateUserDTO(name=dto.name, email=dto.email, password_hash=password_hash)
        )
        logger.info("User registered", extra={"user_id": str(user.id)})
        return user
