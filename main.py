# main.py
import time
from models.charging_pile import FastChargingPile, TrickleChargingPile
from repositories.repositories import *
from services.user_service import UserService
from services.billing_service import BillingService
from services.charging_service import ChargingService
from services.scheduling_service import SchedulingService
from controllers.controllers import UserController, DriverController, AdminController
from utils.enums import ChargeMode

def run_simulation():
    print("--- Initializing EV Charging System ---")

    # 1. Setup Repositories (Data Layer)
    user_repo = UserRepository()
    pile_repo = PileRepository()
    session_repo = SessionRepository()
    bill_repo = BillRepository()
    request_repo = RequestRepository()
    queue_repo = QueueRepository()

    # 2. Setup Services (Business Logic Layer)
    user_service = UserService(user_repo)
    billing_service = BillingService()
    charging_service = ChargingService(pile_repo, session_repo, bill_repo, request_repo, queue_repo, billing_service)
    scheduler = SchedulingService(pile_repo, queue_repo, charging_service)
    
    # 3. Setup Controllers (API/Presentation Layer)
    user_controller = UserController(user_service)
    driver_controller = DriverController(charging_service, queue_repo)
    admin_controller = AdminController(charging_service, pile_repo)

    # 4. Initialize System State
    pile_repo.save("F01", FastChargingPile(pile_id="F01"))
    pile_repo.save("F02", FastChargingPile(pile_id="F02"))
    pile_repo.save("T01", TrickleChargingPile(pile_id="T01"))
    admin_controller.check_system_status()
    
    print("\n--- Simulation Started ---\n")

    # Scenario 1: Users register and request charging
    user1 = user_controller.register("Alice", "pass123", "CAR-A", 50.0)
    user2 = user_controller.register("Bob", "pass456", "CAR-B", 60.0)
    user3 = user_controller.register("Charlie", "pass789", "CAR-C", 40.0)

    driver_controller.request_charge(user1.car.car_id, ChargeMode.FAST, 30)
    driver_controller.request_charge(user2.car.car_id, ChargeMode.TRICKLE, 20)
    driver_controller.request_charge(user3.car.car_id, ChargeMode.FAST, 25)
    
    driver_controller.check_queue_status()

    # Scenario 2: Scheduler runs and assigns cars to piles
    scheduler.run_schedule_cycle()
    admin_controller.check_system_status()
    driver_controller.check_queue_status() # See that first cars are gone from queue

    # Scenario 3: A pile fails during charging
    print("\n--- Simulating Pile Failure ---")
    admin_controller.report_failure("F01")
    admin_controller.check_system_status()
    driver_controller.check_queue_status() # See that CAR-A is back in the queue
    
    # Scenario 4: Scheduler runs again, re-assigning the interrupted car
    scheduler.run_schedule_cycle()
    admin_controller.check_system_status()
    
    # Scenario 5: A car finishes charging
    print("\n--- Simulating End of Charge ---")
    # Let's say Bob (in T01) finishes
    bill = charging_service.end_charging("T01")
    if bill:
        print(f"\nFinal Bill for Bob (Car CAR-B):\n{bill}\n")
    admin_controller.check_system_status()
    
    # Scenario 6: Admin recovers the failed pile
    print("\n--- Simulating Pile Recovery ---")
    admin_controller.recover_pile("F01")
    admin_controller.check_system_status()
    
    # Scenario 7: Scheduler runs again, assigning a car to the recovered pile
    scheduler.run_schedule_cycle()
    admin_controller.check_system_status()
    driver_controller.check_queue_status()


if __name__ == "__main__":
    run_simulation()