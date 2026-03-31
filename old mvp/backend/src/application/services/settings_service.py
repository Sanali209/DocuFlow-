from typing import List, Dict
from sqlalchemy.orm import Session
from src.infrastructure.database.models import SettingDB, AssigneeDB, FilterPresetDB
from src.infrastructure.database.repositories import SQLFilterPresetRepository

class SettingsService:
    def list_filter_presets(self) -> List[Dict]:
        db = self.db_factory()
        try:
            repo = SQLFilterPresetRepository(db)
            presets = repo.list()
            return [{"id": p.id, "name": p.name, "config": p.config} for p in presets]
        finally:
            db.close()

    def create_filter_preset(self, name: str, config: str) -> bool:
        db = self.db_factory()
        try:
            repo = SQLFilterPresetRepository(db)
            repo.add(name, config)
            return True
        except Exception:
            return False
        finally:
            db.close()

    def delete_filter_preset(self, preset_id: int) -> bool:
        db = self.db_factory()
        try:
            repo = SQLFilterPresetRepository(db)
            return repo.delete(preset_id)
        finally:
            db.close()

    def get_rescan_interval(self) -> int:
        """Returns interval in minutes. Default 60."""
        val = self.get_setting("sync_rescan_interval")
        try:
            return int(val) if val else 60
        except ValueError:
            return 60

    def set_rescan_interval(self, minutes: int) -> bool:
        return self.set_setting("sync_rescan_interval", str(minutes))
    def __init__(self, db_factory):
        self.db_factory = db_factory

    def get_mihtav_path(self) -> str:
        return self.get_setting("sync_mihtav_path")

    def get_sidra_path(self) -> str:
        return self.get_setting("sync_sidra_path")

    def get_setting(self, key: str) -> str:
        db = self.db_factory()
        try:
            setting = db.query(SettingDB).filter(SettingDB.key == key).first()
            return setting.value if setting else ""
        finally:
            db.close()

    def set_setting(self, key: str, value: str) -> bool:
        db = self.db_factory()
        try:
            setting = db.query(SettingDB).filter(SettingDB.key == key).first()
            if setting:
                setting.value = value
            else:
                setting = SettingDB(key=key, value=value)
                db.add(setting)
            db.commit()
            return True
        except Exception as e:
            print(f"Error setting {key}: {e}")
            return False
        finally:
            db.close()

    def list_assignees(self) -> List[Dict]:
        db = self.db_factory()
        try:
            assignees = db.query(AssigneeDB).all()
            return [{"id": a.id, "name": a.name} for a in assignees]
        finally:
            db.close()

    def create_assignee(self, name: str) -> bool:
        db = self.db_factory()
        try:
            assignee = AssigneeDB(name=name)
            db.add(assignee)
            db.commit()
            return True
        except Exception:
            return False
        finally:
            db.close()

    def update_assignee(self, assignee_id: int, name: str) -> bool:
        db = self.db_factory()
        try:
            assignee = db.query(AssigneeDB).filter(AssigneeDB.id == assignee_id).first()
            if assignee:
                assignee.name = name
                db.commit()
                return True
            return False
        finally:
            db.close()

    def delete_assignee(self, assignee_id: int) -> bool:
        db = self.db_factory()
        try:
            assignee = db.query(AssigneeDB).filter(AssigneeDB.id == assignee_id).first()
            if assignee:
                db.delete(assignee)
                db.commit()
                return True
            return False
        finally:
            db.close()
