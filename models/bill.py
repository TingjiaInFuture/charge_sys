# models/bill.py
from dataclasses import dataclass
from datetime import datetime
from utils.enums import ChargeMode

@dataclass
class ChargingSession:
    """Represents an active charging session."""
    session_id: str
    car_id: str
    pile_id: str
    start_time: datetime
    request_amount_kwh: float
    
@dataclass
class Bill:
    """Represents the final bill for a completed charging session."""
    bill_id: str
    car_id: str
    pile_id: str
    start_time: datetime
    end_time: datetime
    charged_kwh: float
    charge_mode: ChargeMode
    charge_fee: float
    service_fee: float
    total_fee: float