# models/car.py
from dataclasses import dataclass, field
from datetime import datetime
from utils.enums import ChargeMode, CarState

@dataclass
class ChargingRequest:
    """Represents a user's request to charge their vehicle."""
    car_id: str
    request_mode: ChargeMode
    request_amount_kwh: float # Requested energy in kWh
    request_time: datetime = field(default_factory=datetime.now)
    state: CarState = CarState.WAITING_IN_MAIN_QUEUE
    queue_number: str = "" # e.g., F1, T1

@dataclass
class Car:
    """Represents a user's electric vehicle."""
    car_id: str
    user_id: str
    capacity_kwh: float