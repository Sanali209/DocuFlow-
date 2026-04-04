from pydantic import Field
from docuflow.domain.settings import BaseModuleSettings, registry

class FolderScannerSettings(BaseModuleSettings):
    """
    Configuration for the Folder Scanner system.
    Used for declarative P2P configuration.
    """
    # LOCAL: Node-specific paths (e.g. drive mappings Z:, X:)
    sidra_scan_path: str = Field(
        default="", 
        description="Network path to SIDRA folder",
        json_schema_extra={"scope": "local"}
    )
    mihtav_scan_path: str = Field(
        default="", 
        description="Network path to MIHTAV folder",
        json_schema_extra={"scope": "local"}
    )
    other_scan_path: str = Field(
        default="", 
        description="Network path to REWORK/Other folder",
        json_schema_extra={"scope": "local"}
    )
    poll_interval_seconds: int = Field(
        default=60, 
        description="Scan interval in seconds",
        json_schema_extra={"scope": "local"}
    )
    
    # NS Mirror specific (Local for now, as it's node-specific activity)
    local_ns_path: str = Field(
        default="", 
        description="Local path for NS Mirror (GNC copies)",
        json_schema_extra={"scope": "local"}
    )
    ns_mirror_interval_seconds: int = Field(
        default=300, 
        json_schema_extra={"scope": "local"}
    )
    ns_mirror_copy_timeout_s: int = Field(
        default=30, 
        json_schema_extra={"scope": "local"}
    )

    # GLOBAL: Unified cluster behavior
    enabled: bool = Field(
        default=True, 
        description="Global master switch for scanner",
        json_schema_extra={"scope": "global"}
    )
    default_project_name: str = Field(
        default="GENERAL", 
        description="Project to use if meta extraction fails",
        json_schema_extra={"scope": "global"}
    )

# Self-registration
registry.register("folder_scanner", FolderScannerSettings)
