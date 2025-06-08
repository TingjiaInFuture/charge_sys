from typing import List, Optional, Tuple
from datetime import datetime
from models.charging_pile import ChargingPile, FastChargingPile, TrickleChargingPile
from models.car import ChargingRequest
from utils.enums import ChargeMode, CarState, PileState
from services.queue_service import QueueService

class DispatchService:
    """Service for handling charging pile dispatch strategies."""

    def __init__(self, pile_repo, queue_repo, waiting_area_capacity: int = 10):
        self.pile_repo = pile_repo
        self.queue_repo = queue_repo
        self.queue_service = QueueService(queue_repo)
        self.waiting_area_capacity = waiting_area_capacity

    def can_accept_request(self, request: ChargingRequest) -> Tuple[bool, str]:
        """检查是否可以接受新的充电请求
        
        Args:
            request: 充电请求
            
        Returns:
            Tuple[bool, str]: (是否可以接受, 原因说明)
        """
        # 检查等待区容量
        current_queue_size = self.queue_service.get_queue_length(request.request_mode)
        if current_queue_size >= self.waiting_area_capacity:
            return False, "等待区已满，请稍后再试"
        
        # 检查是否有可用的充电桩
        available_piles = self._get_available_piles(request.request_mode)
        if not available_piles:
            return False, "当前没有可用的充电桩"
        
        return True, "可以接受请求"
    
    def _get_available_piles(self, mode: ChargeMode) -> List[ChargingPile]:
        """获取指定模式下可用的充电桩
        
        Args:
            mode: 充电模式
            
        Returns:
            List[ChargingPile]: 可用的充电桩列表
        """
        return [
            pile for pile in self.pile_repo.get_all()
            if (pile.pile_type == mode and 
                pile.state != PileState.FAULT and 
                pile.state != PileState.REPAIRING)
        ]
    
    def find_best_pile(self, request: ChargingRequest) -> Optional[Tuple[ChargingPile, float]]:
        """为充电请求找到最佳充电桩
        
        Args:
            request: 充电请求
            
        Returns:
            Tuple[ChargingPile, float]: (最佳充电桩, 预计总时长)
            如果没有可用的充电桩，返回None
        """
        # 检查是否可以接受请求
        can_accept, reason = self.can_accept_request(request)
        if not can_accept:
            return None
        
        # 获取所有同类型的充电桩
        available_piles = self._get_available_piles(request.request_mode)
        
        if not available_piles:
            return None
        
        # 计算每个充电桩的总时长
        best_pile = None
        min_total_time = float('inf')
        
        for pile in available_piles:
            # 计算等待时间（当前队列中所有车辆的充电时间之和）
            waiting_time = self._calculate_waiting_time(pile)
            
            # 计算充电时间
            charging_time = request.request_amount_kwh / pile.power_kw
            
            # 计算总时长
            total_time = waiting_time + charging_time
            
            # 更新最佳充电桩
            if total_time < min_total_time:
                min_total_time = total_time
                best_pile = pile
        
        return (best_pile, min_total_time) if best_pile else None
    
    def _calculate_waiting_time(self, pile: ChargingPile) -> float:
        """计算充电桩队列的等待时间
        
        Args:
            pile: 充电桩
            
        Returns:
            float: 等待时间（小时）
        """
        waiting_time = 0.0
        
        # 获取充电桩的排队队列
        queue = self.queue_service.get_queue_status(pile.pile_type)
        
        # 计算队列中所有车辆的充电时间
        for request in queue:
            if request.pile_id == pile.pile_id:
                charging_time = request.request_amount_kwh / pile.power_kw
                waiting_time += charging_time
        
        return waiting_time
    
    def handle_pile_fault(self, fault_pile: ChargingPile) -> List[ChargingRequest]:
        """处理充电桩故障
        
        Args:
            fault_pile: 故障充电桩
            
        Returns:
            List[ChargingRequest]: 需要重新调度的请求列表
        """
        # 获取故障充电桩的排队队列
        queue = self.queue_service.get_queue_status(fault_pile.pile_type)
        affected_requests = []
        
        # 找出故障充电桩队列中的请求
        for request in queue:
            if request.pile_id == fault_pile.pile_id:
                affected_requests.append(request)
                # 从原队列中移除
                self.queue_service.remove_from_queue(request.queue_number)
        
        # 重新调度这些请求
        for request in affected_requests:
            # 检查等待区容量
            can_accept, _ = self.can_accept_request(request)
            if not can_accept:
                # 如果等待区已满，将请求标记为等待中
                request.status = "等待中"
                continue
                
            best_pile, _ = self.find_best_pile(request)
            if best_pile:
                request.pile_id = best_pile.pile_id
                self.queue_service.add_to_queue(request)
        
        return affected_requests
    
    def handle_pile_repair(self, repaired_pile: ChargingPile) -> List[ChargingRequest]:
        """处理充电桩修复
        
        Args:
            repaired_pile: 修复后的充电桩
            
        Returns:
            List[ChargingRequest]: 需要重新调度的请求列表
        """
        # 获取所有同类型充电桩的排队队列
        queue = self.queue_service.get_queue_status(repaired_pile.pile_type)
        all_requests = []
        
        # 收集所有未开始充电的请求
        for request in queue:
            if request.pile_id != repaired_pile.pile_id:
                all_requests.append(request)
                # 从原队列中移除
                self.queue_service.remove_from_queue(request.queue_number)
        
        # 按排队号码排序
        all_requests.sort(key=lambda x: x.queue_number)
        
        # 重新调度所有请求
        for request in all_requests:
            # 检查等待区容量
            can_accept, _ = self.can_accept_request(request)
            if not can_accept:
                # 如果等待区已满，将请求标记为等待中
                request.status = "等待中"
                continue
                
            best_pile, _ = self.find_best_pile(request)
            if best_pile:
                request.pile_id = best_pile.pile_id
                self.queue_service.add_to_queue(request)
        
        return all_requests
    
    def modify_request(self, request: ChargingRequest, new_mode: Optional[ChargeMode] = None, 
                      new_amount: Optional[float] = None) -> bool:
        """修改充电请求
        
        Args:
            request: 要修改的请求
            new_mode: 新的充电模式（可选）
            new_amount: 新的充电量（可选）
            
        Returns:
            bool: 修改是否成功
        """
        # 检查是否可以修改
        if not self._can_modify_request(request):
            return False
        
        # 从原队列中移除
        self.queue_service.remove_from_queue(request.queue_number)
        
        # 修改请求
        if new_mode is not None:
            request.request_mode = new_mode
            # 重新生成排队号码
            request.queue_number = None
        
        if new_amount is not None:
            request.request_amount_kwh = new_amount
        
        # 检查等待区容量
        can_accept, _ = self.can_accept_request(request)
        if not can_accept:
            # 如果等待区已满，将请求标记为等待中
            request.status = "等待中"
            return False
        
        # 重新加入队列
        self.queue_service.add_to_queue(request)
        return True
    
    def _can_modify_request(self, request: ChargingRequest) -> bool:
        """检查请求是否可以修改
        
        Args:
            request: 要检查的请求
            
        Returns:
            bool: 是否可以修改
        """
        # 检查充电桩状态
        pile = self.pile_repo.find_by_id(request.pile_id)
        if not pile:
            return True  # 如果没有分配充电桩，可以修改
        
        # 如果已经在充电，不能修改
        if pile.state == PileState.CHARGING:
            return False
        
        return True

    def batch_dispatch(self, requests: List[ChargingRequest]) -> None:
        """
        Perform batch dispatch for multiple vehicles.
        This is an extension feature that optimizes for total charging time
        across all vehicles in the batch.
        """
        # Combine all available piles
        all_piles = self.pile_repo.get_all()
        available_piles = [p for p in all_piles if p.state != PileState.FAULT and p.state != PileState.REPAIRING]

        # Calculate total charging time for each possible assignment
        best_assignment = None
        min_total_time = float('inf')

        # Simple implementation: assign each request to the pile that will
        # result in the shortest total charging time
        for request in requests:
            best_pile = None
            min_time = float('inf')

            for pile in available_piles:
                # Calculate total time for this pile
                queue_time = sum(r.request_amount_kwh / pile.power_kw for r in self.queue_service.get_queue_status(pile.pile_type))
                charging_time = request.request_amount_kwh / pile.power_kw
                total_time = queue_time + charging_time

                if total_time < min_time:
                    min_time = total_time
                    best_pile = pile

            if best_pile:
                request.pile_id = best_pile.pile_id
                self.queue_service.add_to_queue(request)

    def get_waiting_area_status(self) -> dict:
        """获取等待区状态
        
        Returns:
            dict: 等待区状态信息
        """
        fast_queue = self.queue_service.get_queue_status(ChargeMode.FAST)
        trickle_queue = self.queue_service.get_queue_status(ChargeMode.TRICKLE)
        
        return {
            "fast_queue": {
                "current_size": len(fast_queue),
                "capacity": self.waiting_area_capacity,
                "is_full": len(fast_queue) >= self.waiting_area_capacity
            },
            "trickle_queue": {
                "current_size": len(trickle_queue),
                "capacity": self.waiting_area_capacity,
                "is_full": len(trickle_queue) >= self.waiting_area_capacity
            }
        } 