from pydantic_settings import BaseSettings, SettingsConfigDict

from docuflow.infrastructure import constants


class Config(BaseSettings):
    """Centralized 'cold' configuration for the DocuFlow SDK.

    This Pydantic model validates all necessary environment variables
    required to boot the decentralized node infrastructure.

    Examples:
        >>> # Default initialization
        >>> config = Config()
        >>> print(config.node_id)
        node_01

        >>> # Overriding via constructor
        >>> config = Config(node_id="OFFICE_1")
        >>> config.node_id
        'OFFICE_1'
    """

    # --- Identification ---
    app_name: str = "DocuFlow"
    node_id: str = "node_01"  # Unique station identifier (e.g., LASER_01)
    debug: bool = False

    # --- Infrastructure Paths ---
    database_url: str = "sqlite:///./local.db"
    shared_path: str = "./shared_network"  # Root path for network storage

    # --- Distributed Coordination & P2P ---
    heartbeat_interval: float = constants.COORDINATOR_HEARTBEAT_INTERVAL
    coordinator_timeout: float = (
        constants.COORDINATOR_TIMEOUT_SECONDS
    )  # Seconds before a leader is considered dead

    # --- Polling & Maintenance Intervals (Seconds) ---
    bus_poll_interval: float = constants.BUS_POLLING_INTERVAL
    sync_check_interval: float = constants.SYNC_CHECK_INTERVAL
    gc_interval: float = constants.GC_INTERVAL
    # Age threshold (seconds) after which TEMP bus files are considered stale and
    # eligible for cleanup at startup. Default comes from infrastructure constants.
    bus_temp_cleanup_age_seconds: int = constants.GC_STALE_BUS_AGE_SECONDS

    # --- Security & Logging ---
    storage_secret: str = "docuflow_secret_change_me"  # noqa: S105
    log_level: str = "INFO"

    # --- Derived Paths (ReadOnly) ---
    @property
    def bus_path(self) -> str:
        """Absolute path to the File Bus folder on the shared drive.

        Example:
            >>> config = Config(shared_path='/mnt/shared')
            >>> config.bus_path
            '/mnt/shared/BUS'
        """
        return f"{self.shared_path}/{constants.BUS_DIR_NAME}"

    @property
    def snapshots_path(self) -> str:
        """Absolute path to the database snapshots folder.

        Example:
            >>> config = Config(shared_path='/mnt/shared')
            >>> config.snapshots_path
            '/mnt/shared/SNAPSHOTS'
        """
        return f"{self.shared_path}/{constants.SYNC_SNAPSHOTS_DIR}"

    model_config = SettingsConfigDict(
        env_prefix="DOCUFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
