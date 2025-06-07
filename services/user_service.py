# services/user_service.py
from models.user import User
from models.car import Car
from repositories.repositories import UserRepository

class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def register(self, user_id: str, password: str, car_id: str, car_capacity: float) -> User:
        if self._user_repo.find_by_id(user_id):
            raise ValueError("User ID already exists.")
        
        car = Car(car_id=car_id, user_id=user_id, capacity_kwh=car_capacity)
        # In a real app, hash the password
        password_hash = f"hashed_{password}"
        new_user = User(user_id=user_id, password_hash=password_hash, car=car)
        
        self._user_repo.save(user_id, new_user)
        print(f"[UserService] User '{user_id}' registered successfully.")
        return new_user