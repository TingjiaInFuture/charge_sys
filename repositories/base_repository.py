# repositories/base_repository.py
from typing import Dict, Any, Optional

class BaseRepository:
    """A simple in-memory repository for demonstration."""
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def save(self, entity_id: str, entity: Any):
        print(f"[Repo] Saving {type(entity).__name__} with ID: {entity_id}")
        self._data[entity_id] = entity

    def find_by_id(self, entity_id: str) -> Optional[Any]:
        return self._data.get(entity_id)

    def get_all(self):
        return list(self._data.values())

    def delete(self, entity_id: str):
        if entity_id in self._data:
            del self._data[entity_id]

# repositories/repositories.py
from collections import deque
from models.user import User
from models.charging_pile import ChargingPile
from models.car import ChargingRequest
from models.bill import ChargingSession, Bill
from utils.enums import ChargeMode

# You can have separate files, but for simplicity, we combine them here.
class UserRepository(BaseRepository): pass
class PileRepository(BaseRepository): pass
class SessionRepository(BaseRepository): pass
class BillRepository(BaseRepository): pass
class RequestRepository(BaseRepository): pass

class QueueRepository:
    """Manages the main waiting queues for fast and trickle charging."""
    def __init__(self):
        self.queues: Dict[ChargeMode, deque] = {
            ChargeMode.FAST: deque(),
            ChargeMode.TRICKLE: deque()
        }

    def add_to_queue(self, request: ChargingRequest):
        self.queues[request.request_mode].append(request)
        request.queue_number = f"{request.request_mode.name[0]}{len(self.queues[request.request_mode])}"
        print(f"[QueueRepo] Car {request.car_id} added to {request.request_mode.value} queue. Number: {request.queue_number}")

    def get_next_from_queue(self, mode: ChargeMode) -> Optional[ChargingRequest]:
        if self.queues[mode]:
            return self.queues[mode].popleft()
        return None
        
    def get_queue_status(self, mode: ChargeMode) -> list:
        return list(self.queues[mode])