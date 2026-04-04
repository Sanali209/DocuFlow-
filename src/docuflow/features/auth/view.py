from nicegui import ui, app as nicegui_app
from docuflow.features.auth.system import AuthSystem
from docuflow.domain.entities.identity import User
from sqlmodel import Session, select

def login_view(auth_system: AuthSystem):
    """Providing the centralized, glassmorphic login screen for the DocuFlow node."""
    
    async def try_login():
        user = await auth_system.authenticate_user(username.value, password.value)
        if user:
            # Storing session info
            nicegui_app.storage.user.update({
                'user': {
                    'username': user.username,
                    'role': user.role.name if user.role else 'Worker',
                    'permissions': user.role.permissions_list if user.role else [],
                    'workplace_modules': [] # This will be populated from Workplace during logic
                }
            })
            ui.navigate.to('/')
        else:
            ui.notify('Invalid Credentials', color='red', icon='priority_high')

    with ui.column().classes('w-full min-h-screen items-center justify-center bg-[#020617]'):
        # Background Orbs
        ui.element('div').classes('absolute top-[-20%] left-[-10%] w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-[120px]')
        ui.element('div').classes('absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-[120px]')

        with ui.column().classes('w-[450px] p-12 rounded-3xl glass-card items-center gap-10 shadow-2xl relative z-10'):
            with ui.column().classes('items-center gap-4'):
                ui.icon('waves', size='64px', color='indigo-400').classes('animate-pulse')
                ui.label('DocuFlow').classes('text-4xl font-extrabold tracking-tight text-white')
                ui.label('P2P ORCHESTRATION ENGINE').classes('text-[10px] tracking-[0.4em] text-slate-500 font-bold')

            with ui.column().classes('w-full gap-5'):
                username = ui.input('Username').classes('w-full').props('dark rounded standout color=indigo')
                password = ui.input('Password', password=True).classes('w-full').props('dark rounded standout color=indigo')
                
                ui.button('AUTHORIZE NODE', on_click=try_login).classes('w-full h-14 vibrant-btn text-white font-bold rounded-2xl shadow-lg mt-4')
                
            ui.label('DECENTRALIZED WORKPLACE IDENTITY').classes('text-[10px] text-slate-600 font-medium')
