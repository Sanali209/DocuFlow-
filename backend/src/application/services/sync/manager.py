import threading
import time
import logging
from .scanner import DirectoryScanner
from .processor import SyncProcessor

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, scanner: DirectoryScanner, settings_service):
        self.scanner = scanner
        self.settings_service = settings_service
        self.running = False
        self._stop_event = threading.Event()
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Modular SyncManager started")

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self.thread: self.thread.join()
        logger.info("Modular SyncManager stopped")

    def _run_loop(self):
        while self.running:
            try:
                self._sync_cycle()
            except Exception as e:
                logger.error(f"Error in sync cycle: {e}")
            
            # Fetch interval in minutes, convert to seconds
            interval_min = self.settings_service.get_rescan_interval()
            interval_sec = interval_min * 60
            
            if self._stop_event.wait(timeout=interval_sec): break

    def trigger_sync(self):
        """Triggers an immediate sync cycle in a background thread."""
        threading.Thread(target=self._sync_cycle, daemon=True).start()

    def _sync_cycle(self):
        # Logic to get paths from settings and call scanner.scan
        # For now, mock paths or integrate with settings_service
        mihtav_path = self.settings_service.get_mihtav_path()
        sidra_path = self.settings_service.get_sidra_path()
        
        if mihtav_path:
            self.scanner.scan(mihtav_path, "mihtav")
        if sidra_path:
            self.scanner.scan(sidra_path, "sidra")
