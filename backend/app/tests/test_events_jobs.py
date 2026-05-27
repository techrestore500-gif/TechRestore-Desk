import pytest

import app.database as database
from app.events.dispatcher import EventDispatcher
from app.events.types import TicketClosedEvent
from app.jobs.queue import InProcessJobQueue, JobPriority, list_dead_letters


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_desk_jobs_test.sqlite"
    test_backups_dir = tmp_path / "backups"
    test_backups_dir.mkdir()
    test_activity_log_path = tmp_path / "system_activity_log.json"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "BACKUPS_DIR", test_backups_dir)
    monkeypatch.setattr(database, "SYSTEM_ACTIVITY_LOG_PATH", test_activity_log_path)

    database.initialize_database()


def test_event_dispatch_calls_subscriber():
    dispatcher = EventDispatcher()
    called = []

    def on_ticket_closed(event: TicketClosedEvent):
        called.append(event.ticket_id)

    dispatcher.subscribe(TicketClosedEvent, on_ticket_closed)
    dispatcher.publish(TicketClosedEvent(ticket_id=44, final_price=90.0))

    assert called == [44]


def test_event_dispatch_survives_subscriber_failure():
    dispatcher = EventDispatcher()
    called = []

    def failing(_event: TicketClosedEvent):
        raise RuntimeError("boom")

    def second(event: TicketClosedEvent):
        called.append(event.ticket_id)

    dispatcher.subscribe(TicketClosedEvent, failing)
    dispatcher.subscribe(TicketClosedEvent, second)
    dispatcher.publish(TicketClosedEvent(ticket_id=77, final_price=40.0))

    assert called == [77]


def test_job_retry_then_success(isolated_db):
    queue = InProcessJobQueue()
    attempts = {"count": 0}

    def flaky(_payload):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("transient")

    queue.register("flaky", flaky)
    result = queue.run_now(job_name="flaky", payload={}, queue=JobPriority.DEFAULT, max_retries=3, idempotency_key="retry-key")

    assert result["ok"] is True
    assert attempts["count"] == 3


def test_job_dead_letter_after_retries_exhausted(isolated_db):
    queue = InProcessJobQueue()

    def always_fail(_payload):
        raise ValueError("hard failure")

    queue.register("always_fail", always_fail)
    result = queue.run_now(job_name="always_fail", payload={"a": 1}, queue=JobPriority.CRITICAL, max_retries=2)

    assert result["ok"] is False
    dead_letters = list_dead_letters(limit=10)
    assert len(dead_letters) >= 1
    assert dead_letters[0]["job_name"] == "always_fail"
    assert dead_letters[0]["attempts"] == 2


def test_job_idempotency_prevents_duplicate_execution(isolated_db):
    queue = InProcessJobQueue()
    counter = {"count": 0}

    def only_once(_payload):
        counter["count"] += 1

    queue.register("once", only_once)

    first = queue.run_now(job_name="once", payload={}, idempotency_key="once-key")
    second = queue.run_now(job_name="once", payload={}, idempotency_key="once-key")

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["status"] == "already_completed"
    assert counter["count"] == 1
