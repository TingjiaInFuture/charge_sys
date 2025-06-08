# repositories/base_repository.py
from typing import Dict, Any, Optional, List, TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """A base repository interface with type safety and error handling."""
    def __init__(self):
        self._data: Dict[str, T] = {}

    def save(self, entity_id: str, entity: T) -> bool:
        """
        Save an entity to the repository.
        
        Args:
            entity_id: The unique identifier for the entity
            entity: The entity to save
            
        Returns:
            bool: True if save was successful, False if entity_id already exists
        """
        if entity_id in self._data:
            return False
        print(f"[Repo] Saving {type(entity).__name__} with ID: {entity_id}")
        self._data[entity_id] = entity
        return True

    def find_by_id(self, entity_id: str) -> Optional[T]:
        """
        Find an entity by its ID.
        
        Args:
            entity_id: The unique identifier to search for
            
        Returns:
            Optional[T]: The entity if found, None otherwise
        """
        return self._data.get(entity_id)

    def get_all(self) -> List[T]:
        """
        Get all entities in the repository.
        
        Returns:
            List[T]: A list of all entities
        """
        return list(self._data.values())

    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The unique identifier to delete
            
        Returns:
            bool: True if deletion was successful, False if entity not found
        """
        if entity_id in self._data:
            del self._data[entity_id]
            return True
        return False

    @abstractmethod
    def persist(self) -> bool:
        """
        Persist the current state of the repository.
        This method should be implemented by concrete repositories.
        
        Returns:
            bool: True if persistence was successful
        """
        pass

    @abstractmethod
    def load(self) -> bool:
        """
        Load the repository state from persistent storage.
        This method should be implemented by concrete repositories.
        
        Returns:
            bool: True if loading was successful
        """
        pass

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