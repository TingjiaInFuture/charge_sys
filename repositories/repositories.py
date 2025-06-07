from collections import deque
from typing import Dict, Optional
from .base_repository import BaseRepository
from models.car import ChargingRequest
from utils.enums import ChargeMode

# These are specific implementations of the BaseRepository
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
        # Add to the end of the line
        self.queues[request.request_mode].append(request)
        request.queue_number = f"{request.request_mode.name[0]}{len(self.queues[request.request_mode])}"
        print(f"[QueueRepo] Car {request.car_id} added to {request.request_mode.value} queue. Number: {request.queue_number}")

    def add_to_front_of_queue(self, request: ChargingRequest):
        # For re-queuing failed jobs with priority
        self.queues[request.request_mode].appendleft(request)
        # Re-assign queue numbers is complex, skipping for this simulation
        print(f"[QueueRepo] Car {request.car_id} added to FRONT of {request.request_mode.value} queue.")

    def get_next_from_queue(self, mode: ChargeMode) -> Optional[ChargingRequest]:
        if self.queues[mode]:
            return self.queues[mode].popleft()
        return None
        
    def get_queue_status(self, mode: ChargeMode) -> list:
        return list(self.queues[mode])