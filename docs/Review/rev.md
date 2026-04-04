1. tasck board page empty
2. folder scaner page empty
3. worckshop chat page empty
4. 2026-04-04 15:35:53.914 | DEBUG    | docuflow.application.bus.orchestrator:_polling_worker:143 - Orchestrator [node_01]: Polling bus (interval: 5.0s)
name 'Session' is not defined
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 459, in wait_for_result
    await result
  File "D:\github\DocuFlow-\src\docuflow\main.py", line 127, in switch_view
    session = await request_container.get(Session)
                                          ^^^^^^^
NameError: name 'Session' is not defined
name 'Session' is not defined
Traceback (most recent call last):
5. SDK.orchestrator is uninitialized. Ensure on_startup() is called in the app lifespan.
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 459, in wait_for_result
    await result
  File "D:\github\DocuFlow-\src\docuflow\main.py", line 138, in switch_view
    await folder_scanner_view(_sdk, _config, engine)
  File "D:\github\DocuFlow-\src\docuflow\features\folder_scanner\view.py", line 33, in folder_scanner_view
    is_master = sdk.orchestrator.is_leader
                ^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\src\docuflow\sdk.py", line 59, in orchestrator
    raise RuntimeError("SDK.orchestrator is uninitialized. Ensure on_startup() is called in the app lifespan.")    
RuntimeError: SDK.orchestrator is uninitialized. Ensure on_startup() is called in the app lifespan.
2026-04-04 15:36:03.865 | DEBUG    | docuflow.application.bus.orchestrator:_maintenance_worker:194 - Orchestrator [node_01]: PEER LEADER - Running maintenance...
2026-04-04 15:36:03.891 | INFO     | docuflow.infrastructure.sync:create_master_snapshot:64 - DataSync: Created master snapshot SNAP_node_01_2026-04-04T15-36-03.868048.json
2026-04-04 15:36:03.906 | INFO     | docuflow.infrastructure.housekeeping:rotate_snapshots:101 - Housekeeping: Rotated 1 old snapshots
2026-04-04 15:36:03.927 | DEBUG    | docuflow.application.bus.orchestrator:_polling_worker:143 - Orchestrator [node_01]: Polling bus (interval: 5.0s)
2026-04-04 15:36:03.959 | DEBUG    | docuflow.infrastructure.coordination:_emit_node_heartbeat:93 - Coordination [node_01]: Writing heartbeat 1775306163.9592044 to shared_network\HEARTBEATS\node_node_01.tmp
2026-04-04 15:36:03.966 | DEBUG    | docuflow.infrastructure.coordination:_emit_node_heartbeat:96 - Coordination [node_01]: Heartbeat published (leader=True)
'InventorySystem' object has no attribute 'get_material_types'
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 459, in wait_for_result
    await result
  File "D:\github\DocuFlow-\src\docuflow\main.py", line 109, in switch_view
    await warehouse_view(inventory_system)
  File "D:\github\DocuFlow-\src\docuflow\features\inventory\view.py", line 172, in warehouse_view
    mat_selector = ui.select({m.id: m.code for m in inventory_system.get_material_types()}, label='Выбрать марку').classes('w-full').props('dark standout rounded')
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'InventorySystem' object has no attribute 'get_material_types'. Did you mean: 'get_material_catalog'?
2026-04-04 15:36:08.934 | DEBUG    | docuflow.application.bus.orchestrator:_polling_worker:143 - Orchestrator [node
6. 2026-04-04 15:49:05.107 | DEBUG    | docuflow.infrastructure.coordination:_emit_node_heartbeat:96 - Coordination [node_01]: Heartbeat published (leader=True)
This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (sqlite3.OperationalError) table incidentlog has no column named resolution_note
[SQL: INSERT INTO incidentlog (created_at, updated_at, task_item_id, work_item_id, node_id, incident_type, description, reported_by, resolved, resolved_by, resolved_at, resolution_note, downtime_minutes, attachments) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)]
[parameters: ('2026-04-04 15:49:01.256096', '2026-04-04 15:49:01.256096', None, None, 'node_01', 'BREAKDOWN', '321', 'workshop-op', 0, None, None, None, None, '[]')]
(Background on this error at: https://sqlalche.me/e/20/e3q8) (Background on this error at: https://sqlalche.me/e/20/7s2a)
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 459, in wait_for_result
    await result
  File "D:\github\DocuFlow-\src\docuflow\features\chat\incident_view.py", line 181, in submit
    self.incident_system.report_incident(type_select.value, desc.value, "workshop-op")
  File "D:\github\DocuFlow-\src\docuflow\features\chat\incidents.py", line 77, in report_incident
    db.flush()
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4331, in flush
    self._flush(objects)
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4423, in _flush
    flush_context.transaction = transaction = self._autobegin_t()._begin()
                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<string>", line 2, in _begin
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\state_changes.py", line 101, in _go
    self._raise_for_prerequisite_state(fn.__name__, current_state)
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 971, in _raise_for_prerequisite_state
    raise sa_exc.PendingRollbackError(
sqlalchemy.exc.PendingRollbackError: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (sqlite3.OperationalError) table incidentlog has no column named resolution_note
[SQL: INSERT INTO incidentlog (created_at, updated_at, task_item_id, work_item_id, node_id, incident_type, description, reported_by, resolved, resolved_by, resolved_at, resolution_note, downtime_minutes, attachments) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)]
[parameters: ('2026-04-04 15:49:01.256096', '2026-04-04 15:49:01.256096', None, None, 'node_01', 'BREAKDOWN', '321', 'workshop-op', 0, None, None, None, None, '[]')]
(Background on this error at: https://sqlalche.me/e/20/e3q8) (Background on this error at: https://sqlalche.me/e/20/7s2a)