from loguru import logger
from rich.logging import RichHandler


def setup_logging(level: str = "INFO"):
    """Configures loguru to use RichHandler for pretty console output."""
    logger.remove()  # Remove default handler
    logger.add(
        RichHandler(rich_tracebacks=True, markup=True),
        format="{message}",
        level=level,
    )

    # Add file rotation for logs (max 10MB per file, keep 5 files)
    logger.add(
        "logs/docuflow.log",
        rotation="10 MB",
        retention="5 days",
        compression="zip",
        level="DEBUG",
    )

    logger.info(f"Logging initialized with level: [bold blue]{level}[/]")
