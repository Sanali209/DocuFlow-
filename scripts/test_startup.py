import sys
from pathlib import Path

# Add src to sys.path to resolve docuflow package
sys.path.append(str(Path(__file__).parent.parent / "src"))

import asyncio

from dishka import make_async_container
from sqlalchemy import Engine
from sqlmodel import SQLModel

from docuflow.features.admin.system import AdminSystem
from docuflow.features.inventory.system import InventorySystem
from docuflow.features.reports.system import ReportSystem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.di import AppProvider


async def test_app_startup():
    print("🚀 Starting DocuFlow v3.1 Startup Test...")

    # 1. Load Config
    config = Config()
    print(f"✅ Config loaded. Node ID: {config.node_id}")

    # 2. Setup Container
    provider = AppProvider(config)
    container = make_async_container(provider)
    print("✅ DI Container created.")

    try:
        # 3. Resolve Database Engine
        engine = await container.get(Engine)
        print("✅ DB Engine resolved.")

        # 4. Initialize Database Schema
        SQLModel.metadata.create_all(engine)
        print("✅ DB Schema initialized.")

        # 5. Resolve Core Systems (Testing BUG-001 fix and DI integrity)
        async with container() as request_scope:
            admin_sys = await request_scope.get(AdminSystem)
            print("✅ AdminSystem resolved.")

            task_sys = await request_scope.get(TaskBoardSystem)
            print("✅ TaskBoardSystem resolved.")

            report_sys = await request_scope.get(ReportSystem)
            print("✅ ReportSystem resolved.")

            inv_sys = await request_scope.get(InventorySystem)
            print("✅ InventorySystem resolved.")

            # 6. Test basic operation (Workplace listing)
            workplaces = admin_sys.get_all_workplaces()
            print(f"✅ DB Connectivity: {len(workplaces)} workplaces found.")

        print("\n✨ STARTUP TEST PASSED: All systems are operational.")

    except Exception as e:
        print(f"\n❌ STARTUP TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(test_app_startup())
