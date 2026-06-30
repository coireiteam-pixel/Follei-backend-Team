from fastapi import Depends

from app.models.tenancy import User
from app.routers.auth import get_current_user as get_follei_current_user


def require_api_token(current_user: User = Depends(get_follei_current_user)) -> User:
    return current_user
