import pytest
from unittest.mock import MagicMock
from nicegui import ui
from nicegui.testing import User, user_simulation
from docuflow.features.admin.view import admin_view
from docuflow.domain.entities.identity import User as DbUser, Role

@pytest.mark.asyncio
async def test_admin_view_tabs():
    """Verify that the Admin Panel has the correct tabs and titles."""
    # 1. Setup Mock AdminSystem
    admin_system = MagicMock()
    admin_system.get_all_users.return_value = [
        DbUser(username="admin", role=Role(name="Admin"))
    ]
    admin_system.get_all_roles.return_value = [
        Role(id=1, name="Admin"),
        Role(id=2, name="Operator")
    ]
    admin_system.get_all_workplaces.return_value = []
    
    # 2. Use user_simulation to test the component in isolation
    async with user_simulation(lambda: admin_view(admin_system)) as user:
        await user.open('/')
        
        # Check for tab labels
        await user.should_see('HEALTH')
        await user.should_see('USERS')
        await user.should_see('ROLES')
        await user.should_see('CONFIGURATION')
        
        # Check for Identity Registry title
        await user.should_see('Identity Registry')

@pytest.mark.asyncio
async def test_admin_user_registration_dialog():
    """Verify the 'Register User' dialog opens and has role options."""
    admin_system = MagicMock()
    admin_system.get_all_roles.return_value = [Role(id=1, name="Admin")]
    admin_system.get_all_users.return_value = []
    
    async with user_simulation(lambda: admin_view(admin_system)) as user:
        await user.open('/')
        
        # Click 'Register User' button
        # find() can use text or component type
        user.find('Register User').click()
        
        # Check for dialog content
        await user.should_see('Register New Identity')
        await user.should_see('Assign Role')
