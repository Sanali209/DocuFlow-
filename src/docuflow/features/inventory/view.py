from typing import List
from nicegui import ui
from docuflow.features.inventory.system import InventorySystem
from docuflow.domain.entities.production import (
    MaterialType, 
    MaterialStock, 
    MaterialAudit,
    MaterialStockStatus,
    MaterialFormFactor
)
from sqlmodel import select

async def warehouse_view(inventory_system: InventorySystem):
    """Provides the decentralized material stock management grid.
    
    Vertical Slice: features/inventory/view.py
    """
    
    with ui.column().classes('w-full h-full p-4 gap-4'):
        ui.label('Склад и Материалы').classes('text-3xl font-bold text-white mb-2')
        
        with ui.tabs().classes('w-full text-indigo-400') as tabs:
            catalog_tab = ui.tab('КАТАЛОГ')
            stock_tab = ui.tab('ОСТАТКИ')
            audit_tab = ui.tab('ИСТОРИЯ')
            
        with ui.tab_panels(tabs, value=catalog_tab).classes('w-full bg-transparent'):
            
            # --- TAB: CATALOG (Material Types) ---
            with ui.tab_panel(catalog_tab):
                def refresh_catalog():
                    types = inventory_system.get_material_catalog()
                    catalog_grid.rows[:] = [t.model_dump() for t in types]
                    catalog_grid.update()

                catalog_cols = [
                    {'name': 'code', 'label': 'Код (Марка)', 'field': 'code', 'align': 'left', 'sortable': True},
                    {'name': 'thickness', 'label': 'Толщина (мм)', 'field': 'thickness', 'align': 'center'},
                    {'name': 'form_factor', 'label': 'Тип', 'field': 'form_factor', 'align': 'center'},
                    {'name': 'cut_speed', 'label': 'V-рез (мм/м)', 'field': 'cut_speed_mm_per_min'},
                    {'name': 'drift', 'label': 'Drift%', 'field': 'time_tolerance_pct', 'align': 'center'},
                    {'name': 'actions', 'label': '', 'field': 'id', 'align': 'right'}
                ]
                
                catalog_grid = ui.table(columns=catalog_cols, rows=[], row_key='id').classes('w-full glass-card text-white')
                catalog_grid.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn flat round dense color="indigo" icon="settings" @click="$parent.$emit('settings', props.row)" />
                        <q-btn flat round dense color="orange" icon="shopping_cart" @click="$parent.$emit('reorder', props.row)" />
                    </q-td>
                ''')
                
                # --- Catalog Settings Dialog ---
                with ui.dialog().classes('glass-card p-6') as settings_dialog:
                    with ui.column().classes('w-[500px] gap-4'):
                        ui.label('Настройки материала').classes('text-xl font-bold text-indigo-400')
                        with ui.row().classes('w-full gap-4'):
                            v_cut = ui.number('V резки (мм/мин)', value=3000).classes('flex-1').props('dark standout rounded')
                            t_pierce = ui.number('T прокола (сек)', value=3.0).classes('flex-1').props('dark standout rounded')
                        with ui.row().classes('w-full gap-4'):
                            v_idle = ui.number('V холост. (мм/мин)', value=10000).classes('flex-1').props('dark standout rounded')
                            drift_limit = ui.number('Drift Limit %', value=15.0).classes('flex-1').props('dark standout rounded')
                        
                        target_id = ui.number().classes('hidden') # Hidden state

                        async def save_settings():
                            # Time params are fields on the database model. We need to update directly since inventory_system has no specific update_time_params method yet.
                            material = inventory_system.db_session.get(MaterialType, target_id.value)
                            if material:
                                material.cut_speed_mm_per_min = v_cut.value
                                material.pierce_time_sec = t_pierce.value
                                material.idle_speed_mm_per_min = v_idle.value
                                material.time_tolerance_pct = drift_limit.value
                                inventory_system.db_session.add(material)
                                inventory_system.db_session.commit()
                                settings_dialog.close()
                                refresh_catalog()
                                ui.notify('Параметры обновлены', color='positive')

                        ui.button('Сохранить', on_click=save_settings).classes('w-full h-12 vibrant-btn text-white rounded-xl shadow-lg')

                catalog_grid.on('settings', lambda e: (
                    target_id.set_value(e.args['id']),
                    v_cut.set_value(e.args['cut_speed_mm_per_min']),
                    t_pierce.set_value(e.args['pierce_time_sec']),
                    v_idle.set_value(e.args['idle_speed_mm_per_min']),
                    drift_limit.set_value(e.args['time_tolerance_pct']),
                    settings_dialog.open()
                ))

                # --- Reorder Dialog ---
                with ui.dialog().classes('glass-card p-6') as reorder_dialog:
                    with ui.column().classes('w-[400px] gap-4'):
                        ui.label('Сформировать заказ').classes('text-xl font-bold text-orange-400')
                        reorder_qty = ui.number('Количество листов', value=10).classes('w-full').props('dark standout rounded')
                        reorder_note = ui.textarea('Примечание').classes('w-full').props('dark standout rounded')
                        reorder_mat_id = ui.number().classes('hidden')

                        async def submit_reorder():
                            inventory_system.request_material_reorder(reorder_mat_id.value, reorder_qty.value, str(reorder_note.value), author="system")
                            reorder_dialog.close()
                            ui.notify('Заказ отправлен в чат!', color='orange')

                        ui.button('ОТПРАВИТЬ', on_click=submit_reorder).classes('w-full h-12 bg-orange-600 text-white rounded-xl shadow-lg')

                catalog_grid.on('reorder', lambda e: (
                    reorder_mat_id.set_value(e.args['id']),
                    reorder_dialog.open()
                ))
                
                refresh_catalog()

                # --- Create Material Dialog ---
                with ui.dialog().classes('glass-card p-6') as create_mat_dialog:
                    with ui.column().classes('w-[500px] gap-4'):
                        ui.label('Регистрация Материала').classes('text-xl font-bold text-emerald-400')
                        mat_code = ui.input('Код/Название (напр. ALU 3.0)').classes('w-full').props('dark standout rounded')
                        mat_thk = ui.number('Толщина (мм)', value=1.0).classes('w-full').props('dark standout rounded')
                        mat_unit = ui.select(['pcs', 'kg', 'm2'], label='Ед. изм.', value='pcs').classes('w-full').props('dark standout rounded')
                        mat_type = ui.select(['SHEET', 'TUBE', 'BAR', 'OTHER'], label='Форм-фактор', value='SHEET').classes('w-full').props('dark standout rounded')

                        async def handle_create_mat():
                            if mat_code.value and mat_thk.value:
                                inventory_system.create_material_definition(
                                    code=mat_code.value,
                                    thickness=mat_thk.value,
                                    primary_unit=mat_unit.value,
                                    form_factor=mat_type.value,
                                    # Default time params
                                    cut_speed_mm_per_min=3000,
                                    pierce_time_sec=3.0,
                                    idle_speed_mm_per_min=10000,
                                    time_tolerance_pct=15.0
                                )
                                create_mat_dialog.close()
                                refresh_catalog()
                                ui.notify(f"Материал {mat_code.value} добавлен", color='positive')
                        
                        ui.button('ЗАРЕГИСТРИРОВАТЬ', on_click=handle_create_mat).classes('w-full h-12 vibrant-btn text-white rounded-xl shadow-lg')

                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('НОВЫЙ МАТЕРИАЛ', icon='add', on_click=create_mat_dialog.open).classes('vibrant-btn text-white rounded-xl h-12 px-6')

            # --- TAB: STOCK (Batches) ---
            with ui.tab_panel(stock_tab):
                def refresh_stock():
                    stmt = select(MaterialStock)
                    batches = inventory_system.db_session.exec(stmt).all()
                    stock_grid.rows[:] = [{**b.model_dump(), 'mat_code': b.material_type.code if b.material_type else 'UNK'} for b in batches]
                    stock_grid.update()

                stock_cols = [
                    {'name': 'mat_code', 'label': 'Материал', 'field': 'mat_code', 'align': 'left'},
                    {'name': 'batch_code', 'label': 'Партия', 'field': 'batch_code', 'align': 'center'},
                    {'name': 'quantity', 'label': 'Остаток', 'field': 'quantity', 'sortable': True},
                    {'name': 'location', 'label': 'Место', 'field': 'location', 'align': 'center'},
                    {'name': 'status', 'label': 'Статус', 'field': 'status', 'align': 'center'},
                    {'name': 'actions', 'label': '', 'field': 'id', 'align': 'right'}
                ]
                
                stock_grid = ui.table(columns=stock_cols, rows=[], row_key='id').classes('w-full glass-card text-white')
                stock_grid.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn flat round dense color="green" icon="exposure_plus_1" @click="$parent.$emit('correct', props.row)" />
                    </q-td>
                ''')

                # --- Income/Receive Dialog ---
                with ui.dialog().classes('glass-card p-6') as income_dialog:
                    with ui.column().classes('w-[400px] gap-4'):
                        ui.label('Приход материала').classes('text-xl font-bold text-green-400')
                        mat_selector = ui.select({m.id: m.code for m in inventory_system.get_material_catalog()}, label='Выбрать марку').classes('w-full').props('dark standout rounded')
                        qty_income = ui.number('Кол-во', value=1.0).classes('w-full').props('dark standout rounded')
                        batch_input = ui.input('Код партии').classes('w-full').props('dark standout rounded')
                        loc_input = ui.input('Место хранения', value='MAIN').classes('w-full').props('dark standout rounded')

                        async def handle_income():
                            inventory_system.receive_material_batch(mat_selector.value, qty_income.value, batch_input.value, loc_input.value)
                            income_dialog.close()
                            refresh_stock()
                            ui.notify('Склад обновлён', color='green')

                        ui.button('ПРИНЯТЬ', on_click=handle_income).classes('w-full h-12 bg-green-700 text-white rounded-xl shadow-lg')

                # --- Correction Dialog ---
                with ui.dialog().classes('glass-card p-6') as correct_dialog:
                    with ui.column().classes('w-[400px] gap-4'):
                        ui.label('Инвентаризация').classes('text-xl font-bold text-yellow-400')
                        actual_qty = ui.number('Фактический остаток').classes('w-full').props('dark standout rounded')
                        corr_reason = ui.input('Причина').classes('w-full').props('dark standout rounded')
                        corr_stock_id = ui.number().classes('hidden')

                        async def apply_correction():
                            inventory_system.record_inventory_correction(corr_stock_id.value, actual_qty.value, corr_reason.value, author="system")
                            correct_dialog.close()
                            refresh_stock()
                            ui.notify('Инвентаризация проведена', color='yellow')

                        ui.button('КОРРЕКТИРОВАТЬ', on_click=apply_correction).classes('w-full h-12 bg-yellow-600 text-white rounded-xl shadow-lg')

                stock_grid.on('correct', lambda e: (
                    corr_stock_id.set_value(e.args['id']),
                    actual_qty.set_value(e.args['quantity']),
                    correct_dialog.open()
                ))

                with ui.row().classes('w-full justify-end'):
                    ui.button('ПРИНЯТЬ ЛИСТЫ', icon='add', on_click=income_dialog.open).classes('vibrant-btn text-white rounded-xl h-12 px-6')

                refresh_stock()

            # --- TAB: AUDIT (History) ---
            with ui.tab_panel(audit_tab):
                def refresh_audit():
                    stmt = select(MaterialAudit).order_by(MaterialAudit.created_at.desc()).limit(100)
                    logs = inventory_system.session.exec(stmt).all()
                    audit_grid.rows[:] = [l.model_dump() for l in logs]
                    audit_grid.update()

                audit_cols = [
                    {'name': 'created_at', 'label': 'Дата/Время', 'field': 'created_at', 'align': 'left'},
                    {'name': 'operation', 'label': 'Оп.', 'field': 'operation', 'align': 'center'},
                    {'name': 'qty_delta', 'label': 'Дельта', 'field': 'qty_delta', 'align': 'center'},
                    {'name': 'reason', 'label': 'Причина/Детали', 'field': 'reason', 'align': 'left'},
                    {'name': 'author', 'label': 'Автор', 'field': 'author'},
                    {'name': 'node_id', 'label': 'Узел', 'field': 'node_id'}
                ]
                audit_grid = ui.table(columns=audit_cols, rows=[], row_key='id').classes('w-full glass-card text-white')
                
                refresh_audit()
