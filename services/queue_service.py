from typing import Optional, List, Dict
from datetime import datetime
from models.car import ChargingRequest
from utils.enums import ChargeMode

class QueueService:
    def __init__(self, queue_repo):
        self.queue_repo = queue_repo
        # 初始化排队号码计数器
        self._queue_counters = {
            ChargeMode.FAST: 0,
            ChargeMode.TRICKLE: 0
        }
        # 初始化日期记录
        self._last_date = datetime.now().date()
    
    def _reset_counters_if_new_day(self):
        """如果是新的一天，重置计数器"""
        current_date = datetime.now().date()
        if current_date != self._last_date:
            self._queue_counters = {
                ChargeMode.FAST: 0,
                ChargeMode.TRICKLE: 0
            }
            self._last_date = current_date
    
    def _generate_queue_number(self, mode: ChargeMode) -> str:
        """生成排队号码
        
        Args:
            mode: 充电模式
            
        Returns:
            str: 排队号码，格式为 "F001" 或 "T001"
        """
        self._reset_counters_if_new_day()
        
        # 增加计数器
        self._queue_counters[mode] += 1
        
        # 生成排队号码
        prefix = "F" if mode == ChargeMode.FAST else "T"
        number = str(self._queue_counters[mode]).zfill(3)
        return f"{prefix}{number}"
    
    def add_to_queue(self, request: ChargingRequest) -> str:
        """将请求添加到队列并生成排队号码
        
        Args:
            request: 充电请求
            
        Returns:
            str: 生成的排队号码
        """
        # 生成排队号码
        queue_number = self._generate_queue_number(request.request_mode)
        request.queue_number = queue_number
        
        # 添加到队列
        self.queue_repo.add_to_queue(request)
        
        return queue_number
    
    def get_queue_position(self, queue_number: str) -> Optional[int]:
        """获取请求在队列中的位置
        
        Args:
            queue_number: 排队号码
            
        Returns:
            Optional[int]: 队列位置（从1开始），如果未找到返回None
        """
        # 确定充电模式
        mode = ChargeMode.FAST if queue_number.startswith("F") else ChargeMode.TRICKLE
        
        # 获取队列
        queue = self.queue_repo.get_queue_status(mode)
        
        # 查找位置
        for i, request in enumerate(queue, 1):
            if request.queue_number == queue_number:
                return i
        
        return None
    
    def get_queue_status(self, mode: ChargeMode) -> List[Dict]:
        """获取队列状态
        
        Args:
            mode: 充电模式
            
        Returns:
            List[Dict]: 队列状态信息列表
        """
        queue = self.queue_repo.get_queue_status(mode)
        return [
            {
                "queue_number": request.queue_number,
                "car_id": request.car_id,
                "amount": request.amount,
                "status": request.status,
                "create_time": request.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            for request in queue
        ]
    
    def remove_from_queue(self, queue_number: str) -> bool:
        """从队列中移除请求
        
        Args:
            queue_number: 排队号码
            
        Returns:
            bool: 是否成功移除
        """
        # 确定充电模式
        mode = ChargeMode.FAST if queue_number.startswith("F") else ChargeMode.TRICKLE
        
        # 获取队列
        queue = self.queue_repo.get_queue_status(mode)
        
        # 查找并移除请求
        for request in queue:
            if request.queue_number == queue_number:
                self.queue_repo.remove_from_queue(request)
                return True
        
        return False
    
    def get_queue_length(self, mode: ChargeMode) -> int:
        """获取队列长度
        
        Args:
            mode: 充电模式
            
        Returns:
            int: 队列长度
        """
        return len(self.queue_repo.get_queue_status(mode))
    
    def get_estimated_waiting_time(self, queue_number: str) -> Optional[float]:
        """获取预计等待时间
        
        Args:
            queue_number: 排队号码
            
        Returns:
            Optional[float]: 预计等待时间（小时），如果未找到返回None
        """
        # 确定充电模式
        mode = ChargeMode.FAST if queue_number.startswith("F") else ChargeMode.TRICKLE
        
        # 获取队列
        queue = self.queue_repo.get_queue_status(mode)
        
        # 查找请求位置
        position = self.get_queue_position(queue_number)
        if position is None:
            return None
        
        # 计算前面所有请求的充电时间
        waiting_time = 0.0
        for request in queue[:position-1]:
            # 假设每个请求平均充电时间为30分钟
            waiting_time += 0.5
        
        return waiting_time 