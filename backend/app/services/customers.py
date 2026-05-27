"""Service layer for customer workflows."""
from app.repositories.customers import CustomerRepository


class CustomerService:
    """Business logic for customer operations."""

    @staticmethod
    def list_customers(search: str | None = None) -> list[dict]:
        return CustomerRepository.list_customers(search)

    @staticmethod
    def create_customer(payload: dict) -> dict:
        return CustomerRepository.create_customer(payload)

    @staticmethod
    def get_customer(customer_id: int) -> dict | None:
        return CustomerRepository.get_customer(customer_id)

    @staticmethod
    def update_customer(customer_id: int, payload: dict) -> dict | None:
        return CustomerRepository.update_customer(customer_id, payload)

    @staticmethod
    def list_customer_tickets(customer_id: int) -> list[dict]:
        return CustomerRepository.list_customer_tickets(customer_id)
