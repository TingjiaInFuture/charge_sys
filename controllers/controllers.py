# controllers/controllers.py
from services.user_service import UserService
from services.charging_service import ChargingService
from services.scheduling_service import SchedulingService
from repositories.repositories import PileRepository, QueueRepository

class UserController:
    def __init__(self, user_service: UserService):
        self._service = user_service
        
    def register(self, user_id, password, car_id, car_capacity):
        return self._service.register(user_id, password, car_id, car_capacity)

class DriverController:
    def __init__(self, charging_service: ChargingService, queue_repo: QueueRepository):
        self._service = charging_service
        self._queue_repo = queue_repo
        
    def request_charge(self, car_id, mode, amount):
        print(f"\n[Driver] Car {car_id} is requesting a {mode.value} for {amount} kWh.")
        return self._service.create_charging_request(car_id, mode, amount)
        
    def check_queue_status(self):
        fast_q = self._queue_repo.get_queue_status(ChargeMode.FAST)
        trickle_q = self._queue_repo.get_queue_status(ChargeMode.TRICKLE)
        print("\n--- Queue Status ---")
        print(f"Fast Queue: {[req.car_id for req in fast_q]}")
        print(f"Trickle Queue: {[req.car_id for req in trickle_q]}")
        print("--------------------")

class AdminController:
    def __init__(self, charging_service: ChargingService, pile_repo: PileRepository):
        self._service = charging_service
        self._pile_repo = pile_repo

    def report_failure(self, pile_id):
        self._service.report_pile_failure(pile_id)
        
    def recover_pile(self, pile_id):
        self._service.recover_pile(pile_id)
        
    def check_system_status(self):
        print("\n--- System Status (Admin View) ---")
        piles = self._pile_repo.get_all()
        for pile in piles:
            status = f"Pile {pile.pile_id} ({pile.pile_type.value}) - State: {pile.state.value}"
            if pile.current_charging_session:
                status += f" - Charging Car: {pile.current_charging_session.car_id}"
            print(status)
        print("---------------------------------")