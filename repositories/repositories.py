from collections import deque
from typing import Dict, Optional, List, TypeVar, Generic
from .base_repository import BaseRepository
from models.car import ChargingRequest
from utils.enums import ChargeMode
from datetime import datetime
import json
import os
import shutil
import threading
import time

from models.user import User
from models.car import Car, ChargingRequest
from models.charging_pile import ChargingPile
from models.bill import ChargingSession, Bill

T = TypeVar('T')

class Repository(Generic[T]):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: Dict[str, T] = {}
        self._lock = threading.Lock()  # 添加线程锁
        self._backup_dir = 'data/backups'
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        os.makedirs(self._backup_dir, exist_ok=True)
        
        self._load()
    
    def _create_backup(self):
        """创建数据备份"""
        if not os.path.exists(self._backup_dir):
            os.makedirs(self._backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(self._backup_dir, f"{os.path.basename(self.file_path)}_{timestamp}")
        
        try:
            shutil.copy2(self.file_path, backup_file)
            # 保留最近的5个备份
            backups = sorted([f for f in os.listdir(self._backup_dir) if f.startswith(os.path.basename(self.file_path))])
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    os.remove(os.path.join(self._backup_dir, old_backup))
        except Exception as e:
            print(f"创建备份失败: {str(e)}")
    
    def _load(self):
        """从文件加载数据"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"加载数据失败: {str(e)}")
                self.data = {}
    
    def _save(self):
        """保存数据到文件"""
        try:
            # 创建备份
            if os.path.exists(self.file_path):
                self._create_backup()
            
            # 使用临时文件进行写入
            temp_file = f"{self.file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            # 原子性地替换文件
            os.replace(temp_file, self.file_path)
        except Exception as e:
            print(f"保存数据失败: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def save(self, key: str, value: T):
        """保存数据"""
        with self._lock:
            self.data[key] = value
            self._save()
    
    def get(self, key: str) -> Optional[T]:
        """获取数据"""
        with self._lock:
            return self.data.get(key)
    
    def get_all(self) -> List[T]:
        """获取所有数据"""
        with self._lock:
            return list(self.data.values())
    
    def delete(self, key: str):
        """删除数据"""
        with self._lock:
            if key in self.data:
                del self.data[key]
                self._save()
    
    def clear(self):
        """清空所有数据"""
        with self._lock:
            self.data.clear()
            self._save()

class UserRepository(Repository[User]):
    def __init__(self):
        super().__init__('data/users.json')
    
    def register_user(self, key: str, value: User) -> bool:
        """原子化检查并保存用户（解决竞态条件）"""
        with self._lock:
            if self.data.get(key):
                return False  # 用户已存在
            self.data[key] = value.to_dict()
            self._save()
            return True

    def save(self, key: str, value: User):
        """保存用户数据（保留原有方法用于其他场景）"""
        with self._lock:
            self.data[key] = value.to_dict()
            self._save()
    
    def get(self, key: str) -> Optional[User]:
        """获取用户数据"""
        with self._lock:
            data = self.data.get(key)
            if data:
                return User.from_dict(data)
            return None
    
    def get_all(self) -> List[User]:
        """获取所有用户数据"""
        with self._lock:
            return [User.from_dict(data) for data in self.data.values()]

    def find_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID查找用户（兼容旧接口）"""
        return self.get(user_id)

class PileRepository(Repository[ChargingPile]):
    def __init__(self):
        super().__init__('data/piles.json')
    
    def save(self, key: str, value: ChargingPile):
        """保存充电桩数据"""
        self.data[key] = value.to_dict()
        self._save()
    
    def get(self, key: str) -> Optional[ChargingPile]:
        """获取充电桩数据"""
        data = self.data.get(key)
        if data:
            return ChargingPile.from_dict(data)
        return None
    
    def get_all(self) -> List[ChargingPile]:
        """获取所有充电桩数据"""
        return [ChargingPile.from_dict(data) for data in self.data.values()]

class SessionRepository(Repository[ChargingSession]):
    def __init__(self):
        super().__init__('data/sessions.json')
    
    def save(self, key: str, value: ChargingSession):
        """保存充电会话数据"""
        self.data[key] = value.to_dict()
        self._save()
    
    def get(self, key: str) -> Optional[ChargingSession]:
        """获取充电会话数据"""
        data = self.data.get(key)
        if data:
            return ChargingSession.from_dict(data)
        return None
    
    def get_all(self) -> List[ChargingSession]:
        """获取所有充电会话数据"""
        return [ChargingSession.from_dict(data) for data in self.data.values()]

class BillRepository(Repository[Bill]):
    def __init__(self):
        super().__init__('data/bills.json')
    
    def save(self, key: str, value: Bill):
        """保存账单数据"""
        self.data[key] = value.to_dict()
        self._save()
    
    def get(self, key: str) -> Optional[Bill]:
        """获取账单数据"""
        data = self.data.get(key)
        if data:
            return Bill.from_dict(data)
        return None
    
    def get_all(self) -> List[Bill]:
        """获取所有账单数据"""
        return [Bill.from_dict(data) for data in self.data.values()]

class RequestRepository(Repository[ChargingRequest]):
    def __init__(self):
        super().__init__('data/requests.json')
    
    def save(self, key: str, value: ChargingRequest):
        """保存充电请求数据"""
        self.data[key] = value.to_dict()
        self._save()
    
    def get(self, key: str) -> Optional[ChargingRequest]:
        """获取充电请求数据"""
        data = self.data.get(key)
        if data:
            return ChargingRequest.from_dict(data)
        return None
    
    def get_all(self) -> List[ChargingRequest]:
        """获取所有充电请求数据"""
        return [ChargingRequest.from_dict(data) for data in self.data.values()]

class QueueRepository(Repository[ChargingRequest]):
    def __init__(self):
        super().__init__('data/queue.json')
    
    def save(self, key: str, value: ChargingRequest):
        """保存队列数据"""
        self.data[key] = value.to_dict()
        self._save()
    
    def get(self, key: str) -> Optional[ChargingRequest]:
        """获取队列数据"""
        data = self.data.get(key)
        if data:
            return ChargingRequest.from_dict(data)
        return None
    
    def get_all(self) -> List[ChargingRequest]:
        """获取所有队列数据"""
        return [ChargingRequest.from_dict(data) for data in self.data.values()]

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