
- **Symmetric Truth**: Every node treats its **local database** as the source of truth. The "Master" node acts as a central synchronizer, managing snapshots on the shared filesystem and coordinating broad state consistency.
- **TDD-First**: Every development phase begins with the creation of failure-inducing tests that define the success criteria for the component.
- **Atomic Progress**: Tasks are broken down into the smallest verifiable units to ensure continuous stability. and contain all info needed for it to be completed.
- **Polling Stability**: We will use a `PollingObserver` for the File Bus to ensure reliable change detection across network (Samba/CIFS) shares.
- **Code as documentation**: Every phase will be documented in the code itself, with examples and explanations. Code folow principe self explain code. no magic numbers, no magic strings, no magic values. shortest posible functions, shortest posible classes, shortest posible methods. descreptive names for variables, functions, classes, methods. coments in code only for complex logic. but good docstrings for all functions, classes, methods.
-  **follow domain design principles.** each system is folow domain logic
-  **try folow hexogonal architecture principles.** - domain logic is in the center, and all other layers are around it.
- **for each phase** use all types of tests *- unit, integration, e2e
- **if improwe plan be user review** not onli reflect diference in new plan plan need be solid end describe all from start to finish, if plan so long yore do it step by step, starting from raw and detalize after
