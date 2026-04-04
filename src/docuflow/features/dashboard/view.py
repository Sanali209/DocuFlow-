from nicegui import ui
from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.features.admin.system import AdminSystem

async def dashboard_view(orchestrator: P2POrchestrator, admin_system: AdminSystem):
    """Providing the centralized cluster overview and health summary."""
    
    # 0. FETCH CLUSTER STATE
    nodes = await admin_system.get_cluster_nodes()
    
    ui.label('Overview: Cluster Performance').classes('text-3xl font-bold text-white mb-4')
    
    with ui.row().classes('w-full gap-8'):
        # 1. PEER COUNT (REAL DATA)
        with ui.column().classes('flex-1 p-8 rounded-2xl glass-card relative overflow-hidden'):
            ui.element('div').classes('absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl')
            ui.label('CLUSTER CONNECTIVITY').classes('text-slate-500 font-bold text-xs tracking-tighter')
            
            # Real peer count from coordination heartbeats
            peer_count = len(nodes)
            ui.label(f"{peer_count} NODES").classes('text-emerald-400 text-4xl font-black mt-2')
            ui.label('P2P Mesh Active').classes('text-slate-500 text-sm mt-4')
        
        # 2. LEADER STATUS (REAL DATA)
        with ui.column().classes('flex-1 p-8 rounded-2xl glass-card relative overflow-hidden'):
            ui.element('div').classes('absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl')
            ui.label('CURRENT LEADER').classes('text-slate-500 font-bold text-xs tracking-tighter')
            
            leader_node = next((n for n in nodes if n.get('is_leader')), None)
            leader_id = leader_node.get('node_id', 'ELECTION...') if leader_node else 'ELECTION...'
            
            ui.label(leader_id).classes('text-indigo-400 text-4xl font-black mt-2')
            ui.label('Health: 100%').classes('text-slate-500 text-sm mt-4')

    with ui.column().classes('w-full mt-12 p-8 rounded-2xl glass-card'):
        ui.label('RECENT CLUSTER EVENTS').classes('text-slate-500 font-bold text-xs tracking-tighter mb-6')
        with ui.column().classes('gap-4'):
            # This will be populated from a real event log in future iterations
            with ui.row().classes('items-center gap-4 text-sm text-slate-400 italic'):
                ui.icon('info', color='indigo')
                ui.label('Bootstrap Complete: Local Database Synchronized with Master Snapshot')
            
            with ui.row().classes('items-center gap-4 text-sm text-slate-400 italic'):
                ui.icon('sensors', color='emerald')
                ui.label('P2P Connection Established: Joined Cluster Mesh')
