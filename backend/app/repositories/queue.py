"""Repository for technician queue queries."""
from app.database import get_connection, get_technician_queue, utc_now


class QueueRepository:
    """Handles technician queue data access."""

    @staticmethod
    def get_queue() -> dict[str, list[dict]]:
        return get_technician_queue()

    @staticmethod
    def get_assignment(ticket_id: int) -> str | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT assigned_technician FROM repair_tickets WHERE id = ?",
                (ticket_id,),
            ).fetchone()
        if row is None:
            return None
        return row["assigned_technician"]

    @staticmethod
    def assign_ticket(ticket_id: int, assigned_technician: str | None) -> dict | None:
        timestamp = utc_now()
        with get_connection() as connection:
            existing = connection.execute(
                "SELECT id FROM repair_tickets WHERE id = ?",
                (ticket_id,),
            ).fetchone()
            if existing is None:
                return None

            connection.execute(
                """
                UPDATE repair_tickets
                SET assigned_technician = ?, updated_at = ?
                WHERE id = ?
                """,
                (assigned_technician, timestamp, ticket_id),
            )
            connection.commit()

        return {
            "ticket_id": ticket_id,
            "assigned_technician": assigned_technician,
            "updated": True,
        }
