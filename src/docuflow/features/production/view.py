from nicegui import ui
from sqlmodel import select
from docuflow.features.production.system import ProductionSystem
from docuflow.domain.entities.production import ProductionUnit

async def production_view(system: ProductionSystem, current_user: str = "operator") -> None:
    """Provides the UI for managing production pallets (ProductionUnit)."""
    
    with ui.column().classes('w-full h-full p-4 gap-4'):
        ui.label('Управление Паллетами (Склад готовой продукции)').classes('text-3xl font-bold text-white mb-2')
        
        search_term = ui.input('Поиск по номеру (label_id)').props('dark standout rounded').classes('w-64')

        grid_cols = [
            {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
            {'name': 'label_id', 'label': 'Номер (Label)', 'field': 'label_id', 'align': 'left', 'sortable': True},
            {'name': 'qty_produced', 'label': 'Кол-во', 'field': 'qty_produced', 'align': 'center'},
            {'name': 'parent_label_id', 'label': 'Родитель', 'field': 'parent_label_id', 'align': 'center'},
            {'name': 'created_by', 'label': 'Создал', 'field': 'created_by', 'align': 'center'},
            {'name': 'actions', 'label': '', 'field': 'id', 'align': 'right'}
        ]
        
        grid = ui.table(columns=grid_cols, rows=[], row_key='id', selection='multiple').classes('w-full glass-card text-white')
        grid.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn flat round dense color="orange" icon="call_split" @click="$parent.$emit('split', props.row)" />
            </q-td>
        ''')

        def refresh_grid():
            if len(search_term.value) >= 2:
                stmt = select(ProductionUnit).where(ProductionUnit.label_id.contains(search_term.value)).order_by(ProductionUnit.id.desc())
                units = system.db_session.exec(stmt).all()
            else:
                units = system.get_recent_production_units(50)
            
            grid.rows[:] = [{
                'id': u.id,
                'label_id': u.label_id,
                'qty_produced': u.qty_produced,
                'parent_label_id': u.parent_label_id or '-',
                'created_by': u.created_by
            } for u in units]
            grid.update()

        search_term.on_value_change(refresh_grid)

        # Split Dialog
        with ui.dialog().classes('glass-card p-6') as split_dlg:
            with ui.column().classes('w-[400px] gap-4'):
                ui.label('Разделение паллеты').classes('text-xl font-bold text-orange-400')
                src_pallet_id = ui.number().classes('hidden')
                src_label = ui.label().classes('text-gray-300 font-mono')
                max_qty = ui.number().classes('hidden')
                split_qty = ui.number('Отделить количество', min=1).classes('w-full').props('dark standout rounded')
                
                async def execute_split():
                    if not split_qty.value or split_qty.value >= max_qty.value:
                        ui.notify('Некорректное количество (должно быть меньше остатка)', type='negative')
                        return
                    system.split_production_unit(src_pallet_id.value, int(split_qty.value), current_user)
                    split_dlg.close()
                    refresh_grid()
                    ui.notify('Паллета успешно разделена', type='positive')
                
                ui.button('ОТДЕЛИТЬ В НОВУЮ ПАЛЛЕТУ', on_click=execute_split).classes('w-full h-12 bg-orange-600 text-white rounded-xl shadow-lg')

        grid.on('split', lambda e: (
            src_pallet_id.set_value(e.args['id']),
            src_label.set_text(f"Паллета: {e.args['label_id']} (Доступно: {e.args['qty_produced']})"),
            max_qty.set_value(e.args['qty_produced']),
            split_qty.set_value(1),
            split_qty.props(f"max={e.args['qty_produced'] - 1}"),
            split_dlg.open()
        ))

        # Merge Actions
        with ui.row().classes('w-full justify-between items-center mt-4'):
            ui.label('Слияние (Merge) доступно при выборе нескольких паллет.').classes('text-gray-400 text-sm')
            
            async def execute_merge():
                selected = grid.selected
                if len(selected) < 2:
                    ui.notify('Выберите минимум 2 паллеты (галочками) для слияния', type='warning')
                    return
                # Pick the first selected as the target, merge the rest into it
                target_id = selected[0]['id']
                source_ids = [s['id'] for s in selected[1:]]
                system.merge_production_units(source_ids, target_id, current_user)
                grid.selected.clear()
                refresh_grid()
                ui.notify(f"Паллеты слиты в {selected[0]['label_id']}", type='positive')

            ui.button('СЛИТЬ В ПЕРВУЮ ВЫБРАННУЮ', icon='call_merge', on_click=execute_merge).classes('vibrant-btn text-white rounded-xl h-12 px-6')

        # Load data on open
        ui.timer(0.1, refresh_grid, once=True)
