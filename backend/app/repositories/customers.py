"""Repository for customer data access."""
from app.database import create_customer, get_customer, list_customer_tickets, list_customers, update_customer


class CustomerRepository:
    """Handles customer database operations."""

    @staticmethod
    def list_customers(search: str | None = None) -> list[dict]:
        return list_customers(search)

    @staticmethod
    def create_customer(payload: dict) -> dict:
        return create_customer(payload)

    @staticmethod
    def get_customer(customer_id: int) -> dict | None:
        return get_customer(customer_id)

    @staticmethod
    def update_customer(customer_id: int, payload: dict) -> dict | None:
        return update_customer(customer_id, payload)

    @staticmethod
    def list_customer_tickets(customer_id: int) -> list[dict]:
        return list_customer_tickets(customer_id)
