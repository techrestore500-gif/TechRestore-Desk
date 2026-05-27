"""Domain models and enums for ticket domain."""
from enum import Enum


class TicketStatus(str, Enum):
    """Valid ticket status values."""
    NEW_INTAKE = "New Intake"
    NEEDS_DIAGNOSIS = "Needs Diagnosis"
    WAITING_FOR_PARTS = "Waiting for Parts"
    CUSTOMER_APPROVAL_NEEDED = "Customer Approval Needed"
    IN_PROGRESS = "In Progress"
    NEEDS_REVIEW = "Needs Review"
    LOANER_OUTSTANDING = "Loaner Outstanding"
    PICKED_UP_CLOSED = "Picked Up / Closed"


class TicketPriority(str, Enum):
    """Valid ticket priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class DeviceCondition(str, Enum):
    """Known/Unknown status for device damage assessment."""
    UNKNOWN = "unknown"
    NO = "no"
    YES = "yes"
    UNDETERMINED = "undetermined"


class NoteType(str, Enum):
    """Types of notes that can be added to a ticket."""
    FRONT_DESK = "front_desk"
    TECHNICIAN = "technician"
    CUSTOMER_CALL = "customer_call"
    PRICING = "pricing"
    PARTS = "parts"
    WARRANTY = "warranty"
    INTERNAL = "internal"


class RepairActionStatus(str, Enum):
    """Status of a repair action."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
