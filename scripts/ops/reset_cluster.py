import subprocess
from pathlib import Path


def kill_on_port(port):
    """Find and kill process running on a specific port (Windows)."""
    try:
        output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        pids = set()
        for line in output.strip().split("\n"):
            parts = line.split()
            if len(parts) > 4:
                pids.add(parts[-1])

        for pid in pids:
            print(f"Stopping process {pid} on port {port}...")
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=False)
    except subprocess.CalledProcessError:
        print(f"Port {port} is already clear.")


def reset_heartbeats():
    """Clear the shared heartbeat and message registries."""
    for folder in ["HEARTBEATS", "BUS", "SNAPSHOTS"]:
        hb_path = Path("shared_network") / folder
        if hb_path.exists():
            for f in hb_path.glob("*.*"):
                try:
                    f.unlink()
                except OSError:
                    pass
            print(f"{folder} registry cleared.")


def reset_databases():
    """Clear all node-specific SQLite database files in the current folder."""
    for f in Path(".").glob("node_*.db"):
        try:
            f.unlink()
        except OSError:
            pass
    # Also clear any old default local.db
    if Path("local.db").exists():
        Path("local.db").unlink()
    print("Database files cleared.")


if __name__ == "__main__":
    print("--- DocuFlow Cluster Reset ---")
    for p in [8082, 8083, 8084]:
        kill_on_port(p)
    reset_heartbeats()
    reset_databases()
    print("Done. Ready for fresh launch.")
