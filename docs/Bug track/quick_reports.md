1. 026-04-05 04:29:40.496 | DEBUG    | docuflow.application.bus.orchestrator:_polling_worker:150 - Orchestrator [node_01]: Polling bus (interval: 5.0s)
'WorkItemSystem' object has no attribute 'list'
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 459, in wait_for_result
    await result
  File "D:\github\DocuFlow-\src\docuflow\main.py", line 202, in switch_view
    view.render()
  File "D:\github\DocuFlow-\src\docuflow\features\projects\view.py", line 46, in render
    self._refresh_work_items()
  File "D:\github\DocuFlow-\src\docuflow\features\projects\view.py", line 91, in _refresh_work_items
    items = self.wi_system.list(filters)
            ^^^^^^^^^^^^^^^^^^^
AttributeError: 'WorkItemSystem' object has no attribute 'list'
2. 026-04-05 04:29:50.537 | DEBUG    | docuflow.infrastructure.coordination:_emit_node_heartbeat:99 - Coordination [node_01]: Heartbeat published (leader=True)
Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 453, in handle_event
    result = cast(Callable[[], Any], handler)()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\src\docuflow\features\projects\view.py", line 67, in <lambda>
    icon="login", on_click=lambda p=p: self._select_project(p.id)
                                                            ^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 569, in __get__
    return self.impl.get(state, dict_)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1096, in get
    value = self._fire_loader_callables(state, key, passive)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1126, in _fire_loader_callables
    return state._load_expired(state, passive)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\state.py", line 828, in _load_expired
    self.manager.expired_attribute_loader(self, toload, passive)
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\loading.py", line 1607, in load_scalar_attributes
    raise orm_exc.DetachedInstanceError(
sqlalchemy.orm.exc.DetachedInstanceError: Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
2026-04-05 04:29:55.514 | DEBUG    | docuflow.application.bus.orchestrator:_polling_worker:150 - Orchestrator [node_01]: Polling bus (interval: 5.0s)
Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 453, in handle_event
    result = cast(Callable[[], Any], handler)()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\src\docuflow\features\projects\view.py", line 67, in <lambda>
    icon="login", on_click=lambda p=p: self._select_project(p.id)
                                                            ^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 569, in __get__
    return self.impl.get(state, dict_)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1096, in get
    value = self._fire_loader_callables(state, key, passive)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1126, in _fire_loader_callables
    return state._load_expired(state, passive)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\state.py", line 828, in _load_expired
    self.manager.expired_attribute_loader(self, toload, passive)
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\loading.py", line 1607, in load_scalar_attributes
    raise orm_exc.DetachedInstanceError(
sqlalchemy.orm.exc.DetachedInstanceError: Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 453, in handle_event
    result = cast(Callable[[], Any], handler)()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\src\docuflow\features\projects\view.py", line 67, in <lambda>
    icon="login", on_click=lambda p=p: self._select_project(p.id)
                                                            ^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 569, in __get__
    return self.impl.get(state, dict_)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1096, in get
    value = self._fire_loader_callables(state, key, passive)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1126, in _fire_loader_callables
    return state._load_expired(state, passive)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\state.py", line 828, in _load_expired
    self.manager.expired_attribute_loader(self, toload, passive)
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\loading.py", line 1607, in load_scalar_attributes
    raise orm_exc.DetachedInstanceError(
sqlalchemy.orm.exc.DetachedInstanceError: Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 453, in handle_event
    result = cast(Callable[[], Any], handler)()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\src\docuflow\features\projects\view.py", line 67, in <lambda>
    icon="login", on_click=lambda p=p: self._select_project(p.id)
                                                            ^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 569, in __get__
    return self.impl.get(state, dict_)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1096, in get
    value = self._fire_loader_callables(state, key, passive)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1126, in _fire_loader_callables
    return state._load_expired(state, passive)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\state.py", line 828, in _load_expired
    self.manager.expired_attribute_loader(self, toload, passive)
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\loading.py", line 1607, in load_scalar_attributes
    raise orm_exc.DetachedInstanceError(
sqlalchemy.orm.exc.DetachedInstanceError: Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
Traceback (most recent call last):
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\nicegui\events.py", line 453, in handle_event
    result = cast(Callable[[], Any], handler)()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\src\docuflow\features\projects\view.py", line 67, in <lambda>
    icon="login", on_click=lambda p=p: self._select_project(p.id)
                                                            ^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 569, in __get__
    return self.impl.get(state, dict_)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1096, in get
    value = self._fire_loader_callables(state, key, passive)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\attributes.py", line 1126, in _fire_loader_callables
    return state._load_expired(state, passive)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\state.py", line 828, in _load_expired
    self.manager.expired_attribute_loader(self, toload, passive)
  File "D:\github\DocuFlow-\.venv\Lib\site-packages\sqlalchemy\orm\loading.py", line 1607, in load_scalar_attributes
    raise orm_exc.DetachedInstanceError(
sqlalchemy.orm.exc.DetachedInstanceError: Instance <Project at 0x2895a5fe1c0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
2026-04-05 04:30:00.506 | DEBUG    | docuflow.application.bus.orchestrator:_polling_worker:150 - Orchest
3. 