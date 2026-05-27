"""Application startup helpers."""
from app.core.monitoring import initialize_monitoring
from app.core.settings import get_settings
from app.database import initialize_database
from app.events.subscribers import register_event_subscribers
from app.jobs.registry import register_job_handlers


def initialize_app() -> None:
    """Initialize application state before serving requests."""
    settings = get_settings()
    initialize_monitoring(settings)
    initialize_database()
    register_job_handlers()
    register_event_subscribers()
