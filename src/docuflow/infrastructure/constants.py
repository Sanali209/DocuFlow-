"""Centralized registry for all DocuFlow infrastructure constants.

This module houses all 'magic' strings, numbers, and protocol literals
to ensure a self-documenting and maintainable codebase.

Examples:
    >>> BUS_INBOX_DIR
    INBOX
"""

# --- File Bus Protocol ---
BUS_DIR_NAME = "BUS"
BUS_INBOX_DIR = "INBOX"
BUS_OUTBOX_DIR = "OUTBOX"
BUS_TEMP_PREFIX = "TEMP_"
BUS_EXTENSION = ".json"
BUS_PREFIX_REQ = "REQ_"
BUS_PREFIX_RES = "RES_"
BUS_PREFIX_BROADCAST = "BROADCAST_"
BUS_DELIMITER = "_"

# --- Distributed Coordination ---
COORDINATOR_LOCK_FILE = ".coordinator.lock"
COORDINATOR_TEMP_LOCK_PREFIX = ".tmp."
COORDINATOR_TEMP_LOCK_SUFFIX = ".lock"
COORDINATOR_HEARTBEATS_DIR = "HEARTBEATS"
COORDINATOR_TIMEOUT_SECONDS = 45.0  # Seconds before leader considered dead
COORDINATOR_STALE_NODE_SECONDS = 60

# --- Data Synchronization ---
SYNC_SNAPSHOTS_DIR = "SNAPSHOTS"
SYNC_PREFIX_SNAP = "SNAP_"
SYNC_EXTENSION = ".json"

# --- Housekeeping & GC Defaults ---
# Default age for stale bus messages (24 hours)
GC_STALE_BUS_AGE_SECONDS = 86400

# Default number of database snapshots to retain
GC_MAX_SNAPSHOTS_TO_KEEP = 10

# --- Orchestration & Polling ---
BUS_POLLING_INTERVAL = 5.0
SYNC_CHECK_INTERVAL = 60.0
GC_INTERVAL = 3600.0
COORDINATOR_HEARTBEAT_INTERVAL = 15.0

# Default interval for the polling observer (seconds)
OBSERVER_POLLING_INTERVAL = 2.0
