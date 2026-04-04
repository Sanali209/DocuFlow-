import json
from typing import Set
from docuflow.domain.entities.identity import User, Workplace

def check_access(user: User, workplace: Workplace) -> bool:
    """Determine if a specific user is authorized to operate a given workplace.
    
    Authorization is granted if the workplace ID is in the user's allowed list
    OR if the user holds an 'Admin' role name.
    
    Args:
        user: The authenticated User entity.
        workplace: The physical Workplace entity of the current node.
        
    Returns:
        True if access is granted, False otherwise.
    """
    # 1. Admin bypass
    # Note: In a production system, role name comparison should be case-insensitive 
    # or use a stable identifier.
    if hasattr(user, "role") and user.role.name == "Admin":
        return True
        
    # 2. Strict workplace matching
    try:
        allowed_ids = json.loads(user.allowed_workplaces)
        return workplace.id in allowed_ids
    except (json.JSONDecodeError, TypeError):
        return False

def get_active_ui_modules(user: User, workplace: Workplace) -> Set[str]:
    """Calculate the intersection of user permissions and workplace capabilities.
    
    The resulting set defines which UI modules should be rendered for the user.
    Admins are granted access to all modules available at the workplace.
    
    Args:
        user: The authenticated User entity.
        workplace: The physical Workplace entity.
        
    Returns:
        A set of module identifier strings (e.g., {"tracking", "inventory"}).
    """
    try:
        wp_mods = set(json.loads(workplace.allowed_modules))
    except (json.JSONDecodeError, TypeError):
        return set()

    # Admin sees everything the hardware supports
    if hasattr(user, "role") and user.role.name == "Admin":
        return wp_mods
        
    # Standard user: Intersection of Role permissions and Workplace modules
    try:
        user_perms = set(json.loads(user.role.permissions))
        return user_perms.intersection(wp_mods)
    except (json.JSONDecodeError, TypeError, AttributeError):
        return set()
