from __future__ import annotations

from app.jobs.queue import job_queue
from app.jobs.tasks import (
    generate_daily_report,
    scan_overdue_loaners,
    send_loaner_overdue_notification,
    send_low_inventory_alert,
    send_ready_for_pickup_notification,
)

_registered = False


def register_job_handlers() -> None:
    global _registered
    if _registered:
        return

    job_queue.register("send_ready_for_pickup_notification", send_ready_for_pickup_notification)
    job_queue.register("send_low_inventory_alert", send_low_inventory_alert)
    job_queue.register("send_loaner_overdue_notification", send_loaner_overdue_notification)
    job_queue.register("generate_daily_report", generate_daily_report)
    job_queue.register("scan_overdue_loaners", scan_overdue_loaners)
    _registered = True
