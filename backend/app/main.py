from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.error_handlers import install_error_handlers
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.core.startup import initialize_app
from app.middleware.access_log import AccessLogMiddleware
from app.middleware.auth_gate import AuthGateMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.routes.attachments import router as attachment_router
from app.routes.auth import router as auth_router
from app.routes.customers import router as customer_router
from app.routes.dashboard import router as dashboard_router
from app.routes.health import router as health_router
from app.routes.hours import router as hours_router
from app.routes.inventory import router as inventory_router
from app.routes.loaners import router as loaner_router
from app.routes.pricing import router as pricing_router
from app.routes.repair_categories import router as repair_category_router
from app.routes.queue import router as queue_router
from app.routes.reports import router as reports_router
from app.routes.system import router as system_router
from app.routes.twilio import router as twilio_router
from app.routes.twilio_public import router as twilio_public_router
from app.routes.status_workflow import router as status_workflow_router
from app.routes.supported_models import router as supported_model_router
from app.routes.tickets import router as ticket_router

settings = get_settings()
configure_logging(settings.log_level, settings.log_json)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_app()
    yield


app = FastAPI(title="Tech Restore Desk", lifespan=lifespan)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(AuthGateMiddleware)
app.add_middleware(AccessLogMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

install_error_handlers(app, include_trace=settings.app_env == "development")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(ticket_router)
app.include_router(supported_model_router)
app.include_router(loaner_router)
app.include_router(dashboard_router)
app.include_router(pricing_router)
app.include_router(repair_category_router)
app.include_router(queue_router, prefix="/api")
app.include_router(hours_router, prefix="/api")
app.include_router(inventory_router)
app.include_router(reports_router)
app.include_router(system_router)
app.include_router(twilio_public_router)
app.include_router(twilio_router)
app.include_router(status_workflow_router)
app.include_router(attachment_router)