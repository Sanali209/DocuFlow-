import os
import logging
from typing import List, Set
from .processor import SyncProcessor

logger = logging.getLogger(__name__)

class DirectoryScanner:
    def __init__(self, processor: SyncProcessor):
        self.processor = processor
        self.suffixes = ['_801', 'to801', '_to801']

    def scan(self, root_path: str, source_type: str):
        if not os.path.exists(root_path):
            logger.warning(f"Scan path does not exist: {root_path}")
            return

        try:
            with os.scandir(root_path) as it:
                entries = sorted(list(it), key=lambda e: e.name)
        except OSError as e:
            logger.error(f"Failed to scan directory {root_path}: {e}")
            return

        # Deduplication logic implementation
        base_files = self._get_base_files(entries)

        for entry in entries:
            try:
                if entry.is_dir():
                    self._scan_directory(entry, source_type)
                elif entry.is_file() and entry.name.lower().endswith('.gnc'):
                    if self._should_skip_file(entry.name, base_files):
                        continue
                    self.processor.process_file(entry.path, source_type)
            except Exception as e:
                logger.error(f"Error processing entry {entry.name}: {e}")

    def _get_base_files(self, entries) -> Set[str]:
        base_files = set()
        for e in entries:
            if e.is_file() and e.name.lower().endswith('.gnc'):
                fname = e.name[:-4].lower()
                if not any(fname.endswith(s) for s in self.suffixes):
                    base_files.add(fname)
        return base_files

    def _should_skip_file(self, filename: str, base_files: Set[str]) -> bool:
        fname = filename[:-4].lower()
        for s in self.suffixes:
            if fname.endswith(s):
                potential_base = fname[:-len(s)]
                if potential_base in base_files:
                    return True
        return False

    def _scan_directory(self, entry: os.DirEntry, source_type: str):
        # Implementation for directory-as-document logic
        # For now, simplistic: scan all GNCs inside
        try:
            with os.scandir(entry.path) as it:
                sub_entries = list(it)
                base_files = self._get_base_files(sub_entries)
                for se in sub_entries:
                    if se.is_file() and se.name.lower().endswith('.gnc'):
                        if not self._should_skip_file(se.name, base_files):
                            self.processor.process_file(se.path, source_type, doc_name=entry.name)
        except OSError:
            pass
