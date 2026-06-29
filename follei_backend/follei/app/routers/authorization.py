from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.tenancy import User
from app.routers.auth import get_current_user


router = APIRouter(prefix="/authorization", tags=["Identity & Auth"])


ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "admin": frozenset({"*"}),
    "manager": frozenset(
        {
            "agents.read",
            "agents.write",
            "billing.read",
            "campaigns.read",
            "campaigns.write",
            "conversations.read",
            "conversations.write",
            "customers.read",
            "customers.write",
            "knowledge.read",
            "knowledge.write",
            "leads.read",
            "leads.write",
            "tools.execute",
            "users.read",
        }
    ),
    "member": frozenset(
        {
            "agents.read",
            "campaigns.read",
            "conversations.read",
            "conversations.write",
            "customers.read",
            "knowledge.read",
            "leads.read",
            "tools.execute",
        }
    ),
}


def permissions_for_role(role: str) -> frozenset[str]:
    return ROLE_PERMISSIONS.get(role.lower(), frozenset())


def user_has_permission(user: User, permission: str) -> bool:
    permissions = permissions_for_role(user.role)
    return "*" in permissions or permission in permissions


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    normalized_roles = {role.lower() for role in allowed_roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.lower() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role",
            )
        return current_user

    return dependency


def require_permissions(*required_permissions: str) -> Callable[..., User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        missing_permissions = [
            permission
            for permission in required_permissions
            if not user_has_permission(current_user, permission)
        ]
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "You do not have the required permission",
                    "missing_permissions": missing_permissions,
                },
            )
        return current_user

    return dependency


CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/me")
def read_current_authorization(current_user: CurrentUser) -> dict[str, object]:
    permissions = permissions_for_role(current_user.role)
    return {
        "user_id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "role": current_user.role,
        "permissions": sorted(permissions),
    }


@router.get("/check")
def check_permission(
    current_user: CurrentUser,
    permission: str = Query(examples=["leads.read"]),
) -> dict[str, object]:
    return {
        "permission": permission,
        "allowed": user_has_permission(current_user, permission),
        "role": current_user.role,
    }
