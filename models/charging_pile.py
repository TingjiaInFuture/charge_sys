# models/charging_pile.py
from dataclasses import dataclass, field
from typing import List, Optional
from collections import deque
from utils.enums import WorkState, ChargeMode
from models.car import ChargingRequest

@dataclass
class ChargingPile:
    """Base class for a charging pile."""
    pile_id: str
    pile_type: ChargeMode
    state: WorkState = WorkState.IDLE
    power_kw: float = 0.0 # Power in kW
    local_queue: deque = field(default_factory=lambda: deque(maxlen=2))
    current_charging_session: Optional['ChargingSession'] = None

    def add_to_local_queue(self, request: ChargingRequest):
        if len(self.local_queue) < self.local_queue.maxlen:
            request.state = CarState.WAITING_AT_PILE_QUEUE
            self.local_queue.append(request)
            return True
        return False
        
    def get_next_car_from_queue(self) -> Optional[ChargingRequest]:
        if self.local_queue:
            return self.local_queue.popleft()
        return None

@dataclass
class FastChargingPile(ChargingPile):
    """Represents a fast charging pile."""
    pile_type: ChargeMode = ChargeMode.FAST
    power_kw: float = 60.0 # Example power for fast charger

@dataclass
class TrickleChargingPile(ChargingPile):
    """Represents a trickle (slow) charging pile."""
    pile_type: ChargeMode = ChargeMode.TRICKLE
    power_kw: float = 7.0 # Example power for slow charger