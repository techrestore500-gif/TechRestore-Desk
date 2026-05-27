from __future__ import annotations

from app.jobs.tasks import (
    generate_daily_report,
    scan_overdue_loaners,
    send_loaner_overdue_notification,
    send_low_inventory_alert,
    send_ready_for_pickup_notification,
)

# Arq worker settings for production Redis-backed execution.
# Start with: arq app.jobs.arq_worker.WorkerSettings


class WorkerSettings:
    functions = [
        send_ready_for_pickup_notification,
        send_low_inventory_alert,
        send_loaner_overdue_notification,
        generate_daily_report,
        scan_overdue_loaners,
    ]
    max_jobs = 10
    job_timeout = 120
    keep_result = 3600
    queue_name = "default"
