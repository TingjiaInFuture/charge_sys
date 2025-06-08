# services/scheduling_service.py
from repositories.repositories import PileRepository, QueueRepository, RequestRepository
from services.charging_service import ChargingService
from utils.enums import WorkState, CarState

class SchedulingService:
    """A simple scheduler that runs periodically to assign cars to idle piles."""
    def __init__(self, pile_repo: PileRepository, queue_repo: QueueRepository, charging_service: ChargingService, request_repo: RequestRepository):
        self._pile_repo = pile_repo
        self._queue_repo = queue_repo
        self._charging_service = charging_service
        self._request_repo = request_repo

    def run_schedule_cycle(self):
        """
        This method simulates a scheduling tick.
        It finds idle piles and assigns cars from the corresponding queue.
        This implements the "常规调度" (Routine Dispatch) from the sequence diagram.
        """
        print("\n--- [Scheduler] Running a scheduling cycle ---")
        idle_piles = [p for p in self._pile_repo.get_all() if p.state == WorkState.IDLE]
        
        if not idle_piles:
            print("[Scheduler] No idle piles available.")
            return

        for pile in idle_piles:
            # Check if there's a car in the corresponding main queue
            next_car_request = self._queue_repo.get_next_from_queue(pile.pile_type)
            
            if next_car_request:
                print(f"[Scheduler] Assigning Car {next_car_request.car_id} to Idle Pile {pile.pile_id}")
                
                # 更新请求状态为充电中
                next_car_request.state = CarState.CHARGING
                next_car_request.pile_id = pile.pile_id
                self._request_repo.save(next_car_request.car_id, next_car_request)
                
                # 开始充电
                self._charging_service.start_charging(pile, next_car_request)
            else:
                print(f"[Scheduler] No cars waiting in {pile.pile_type.value} queue for Pile {pile.pile_id}")