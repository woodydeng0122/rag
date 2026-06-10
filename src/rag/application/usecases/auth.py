from rag.domain.entities.user import User
from rag.domain.ports.user_repository import UserRepositoryPort
from rag.infra.auth.jwt_handler import create_access_token, verify_token
from rag.infra.auth.password import verify_password


class AuthUseCase:
    """认证用例 — 登录验证与 token 生成"""

    def __init__(self, user_repo: UserRepositoryPort, jwt_secret_key: str, jwt_expire_hours: int = 24):
        self._user_repo = user_repo
        self._jwt_secret_key = jwt_secret_key
        self._jwt_expire_hours = jwt_expire_hours

    async def login(self, username: str, password: str) -> str:
        """验证用户名密码，返回 JWT access_token"""
        user = await self._user_repo.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("用户名或密码错误")
        token = create_access_token(
            data={"user_id": user.id, "username": user.username},
            secret_key=self._jwt_secret_key,
            expire_hours=self._jwt_expire_hours,
        )
        return token

    async def get_current_user(self, token: str) -> User:
        """验证 token 并返回用户实体"""
        try:
            payload = verify_token(token, self._jwt_secret_key)
        except Exception:
            raise ValueError("无效的认证凭据")
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("无效的认证凭据")
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("用户不存在")
        return user
