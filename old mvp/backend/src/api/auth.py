
from fastapi import Depends, Header, HTTPException

# Simple header-based auth
# Client sends 'X-User-Role': 'admin' or 'operator'


def get_current_role(x_user_role: str | None = Header("operator", alias="X-User-Role")):
    return x_user_role.lower()


def verify_admin(role: str = Depends(get_current_role)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Operation requires Admin privileges")
    return role
