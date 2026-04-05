#!/usr/bin/env python3
"""Diagnostic script to check FolderScannerSystem state.
Run this to diagnose why the scanner is not working.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pathlib import Path

from sqlmodel import Session, create_engine, select

from docuflow.domain.entities.identity import NodeSetting
from docuflow.features.folder_scanner.settings import FolderScannerSettings


def check_database_settings(db_path: str = "node_01.db"):
    """Check what settings are stored in the database."""
    print(f"\n=== Checking Database: {db_path} ===")

    engine = create_engine(f"sqlite:///{db_path}")

    with Session(engine) as session:
        settings = session.exec(
            select(NodeSetting).where(NodeSetting.module == "folder_scanner")
        ).all()

        if not settings:
            print("[WARNING] No folder_scanner settings found in database!")
            print("  This means default values will be used:")
            print("  - sidra_scan_path: '' (EMPTY)")
            print("  - enabled: True")
            return

        print(f"Found {len(settings)} settings:")
        for s in settings:
            print(f"  - {s.key}: {s.value}")

    # Check what FolderScannerSettings would return
    with Session(engine) as session:
        results = session.exec(
            select(NodeSetting).where(
                NodeSetting.node_id == "node_01", NodeSetting.module == "folder_scanner"
            )
        ).all()
        data = {s.key: s.value for s in results}

    settings = FolderScannerSettings(**data)
    print("\nFolderScannerSettings resolved:")
    print(f"  - sidra_scan_path: '{settings.sidra_scan_path}'")
    print(f"  - enabled: {settings.enabled}")
    print(f"  - mihtav_scan_path: '{settings.mihtav_scan_path}'")
    print(f"  - other_scan_path: '{settings.other_scan_path}'")
    print(f"  - poll_interval_seconds: {settings.poll_interval_seconds}")

    # Check if path exists
    if settings.sidra_scan_path:
        path = Path(settings.sidra_scan_path)
        if path.exists():
            print(f"\n[OK] SIDRA path exists: {path}")
            folders = [f for f in path.iterdir() if f.is_dir()]
            print(f"  Found {len(folders)} folders:")
            for f in folders[:5]:  # Show first 5
                print(f"    - {f.name}")
            if len(folders) > 5:
                print(f"    ... and {len(folders) - 5} more")
        else:
            print(f"\n[ERROR] SIDRA path does not exist: {path}")
    else:
        print("\n[WARNING] SIDRA path is empty!")
        print("  This is likely the cause of 'Last scan: Never'")
        print("  The scanner skips empty paths in _scan_all()")


def check_coordination_lock(shared_path: str = "shared"):
    """Check if coordination lock exists and who owns it."""
    print("\n=== Checking Coordination Lock ===")

    lock_path = Path(shared_path) / "coordinator.lock"

    if lock_path.exists():
        import json

        try:
            data = json.loads(lock_path.read_text())
            print(f"Lock file exists: {lock_path}")
            print(f"  - node_id: {data.get('node_id')}")
            print(f"  - timestamp: {data.get('timestamp')}")
            print(f"  - last_active: {data.get('last_active')}")

            import time

            age = time.time() - data.get("timestamp", 0)
            print(f"  - age: {age:.1f} seconds")

            if age > 60:  # More than 60 seconds old
                print("[WARNING] Lock is stale (>60s old)")
            else:
                print("[OK] Lock is fresh")
        except Exception as e:
            print(f"[ERROR] Failed to read lock file: {e}")
    else:
        print(f"Lock file does not exist: {lock_path}")
        print("  This means no node is currently the leader")


def check_heartbeats(shared_path: str = "shared"):
    """Check node heartbeats."""
    print("\n=== Checking Heartbeats ===")

    heartbeats_dir = Path(shared_path) / "heartbeats"

    if not heartbeats_dir.exists():
        print(f"Heartbeats directory does not exist: {heartbeats_dir}")
        return

    hb_files = list(heartbeats_dir.glob("node_*.json"))

    if not hb_files:
        print("No heartbeat files found")
        return

    import json
    import time

    print(f"Found {len(hb_files)} heartbeat files:")
    for hb_file in hb_files:
        try:
            data = json.loads(hb_file.read_text())
            age = time.time() - data.get("timestamp", 0)
            status = "STALE" if age > 60 else "OK"
            print(
                f"  - {hb_file.name}: node_id={data.get('node_id')}, "
                f"is_leader={data.get('is_leader')}, age={age:.1f}s [{status}]"
            )
        except Exception as e:
            print(f"  - {hb_file.name}: ERROR reading file: {e}")


def main():
    print("=" * 60)
    print("FolderScanner Diagnostic Tool")
    print("=" * 60)

    # Check database
    check_database_settings()

    # Check coordination
    check_coordination_lock()

    # Check heartbeats
    check_heartbeats()

    print("\n" + "=" * 60)
    print("Diagnosis Summary")
    print("=" * 60)
    print("""
Possible causes of 'Last scan: Never':

1. SIDRA path is empty in database settings
   -> Check: scripts/check_settings.py
   -> Fix: Add setting via admin UI or update_node_setting()

2. Node is not the cluster leader (is_master = False)
   -> Check: Look for 'Scan requested on slave node' in logs
   -> Fix: Ensure only one node is running, or wait for leader election

3. Scanner is disabled (enabled = False)
   -> Check: Look for 'Scanner is disabled' in logs
   -> Fix: Update enabled setting in database

4. SIDRA path does not exist on disk
   -> Check: Look for 'Scan root does not exist' in logs
   -> Fix: Ensure the path exists and is accessible

5. SDK orchestrator not initialized
   -> Check: Look for 'SDK.orchestrator is uninitialized' in logs
   -> Fix: Ensure SDK.on_startup() is called before scan_now()

To check logs, run the application and look for messages from:
  - docuflow.folder_scanner.system
  - docuflow.folder_scanner.view
""")


if __name__ == "__main__":
    main()
