# services/user_service.py
from models.user import User
from models.car import Car
from repositories.repositories import UserRepository
import hashlib
import os
import re
from typing import Tuple

class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo
        self._min_password_length = 8
        self._max_battery_capacity = 100.0  # 最大电池容量（kWh）

    def _validate_user_id(self, user_id: str) -> Tuple[bool, str]:
        """验证用户ID格式"""
        if not user_id:
            return False, "用户ID不能为空"
        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', user_id):
            return False, "用户ID必须是4-20位字母、数字或下划线"
        return True, ""

    def _validate_car_id(self, car_id: str) -> Tuple[bool, str]:
        """验证车辆ID格式"""
        if not car_id:
            return False, "车辆ID不能为空"
        if not re.match(r'^[A-Z0-9]{4,10}$', car_id):
            return False, "车辆ID必须是4-10位大写字母或数字"
        return True, ""

    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """验证密码强度"""
        if len(password) < self._min_password_length:
            return False, f"密码长度必须至少为{self._min_password_length}位"
        if not re.search(r'[A-Z]', password):
            return False, "密码必须包含大写字母"
        if not re.search(r'[a-z]', password):
            return False, "密码必须包含小写字母"
        if not re.search(r'[0-9]', password):
            return False, "密码必须包含数字"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "密码必须包含特殊字符"
        return True, ""

    def _hash_password(self, password: str) -> str:
        """使用PBKDF2算法对密码进行哈希"""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,  # 迭代次数
            dklen=32
        )
        return f"{salt.hex()}:{key.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """验证密码"""
        try:
            salt_hex, key_hex = stored_hash.split(':')
            salt = bytes.fromhex(salt_hex)
            stored_key = bytes.fromhex(key_hex)
            
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000,
                dklen=32
            )
            return key == stored_key
        except Exception:
            return False

    def register(self, user_id: str, password: str, car_id: str, battery_capacity: float) -> None:
        """注册新用户"""
        try:
            # 验证用户ID
            is_valid, message = self._validate_user_id(user_id)
            if not is_valid:
                raise ValueError(message)
                
            # 验证密码强度
            is_valid, message = self._validate_password(password)
            if not is_valid:
                raise ValueError(message)
                
            # 验证车辆ID
            is_valid, message = self._validate_car_id(car_id)
            if not is_valid:
                raise ValueError(message)
                
            # 验证电池容量
            try:
                battery_capacity = float(battery_capacity)
                if battery_capacity <= 0 or battery_capacity > self._max_battery_capacity:
                    raise ValueError(f"电池容量必须在0-{self._max_battery_capacity}kWh之间")
            except ValueError as e:
                raise ValueError("电池容量必须是有效的数字")
                
            # 检查用户ID是否已存在
            if self._user_repo.get(user_id):
                raise ValueError("用户ID已存在")
                
            # 创建车辆对象
            car = Car(
                car_id=car_id,
                user_id=user_id,
                capacity_kwh=battery_capacity
            )
            
            # 创建用户对象
            user = User(
                user_id=user_id,
                password_hash=self._hash_password(password),
                car=car
            )
            
            # 保存用户数据
            try:
                self._user_repo.save(user_id, user)
                print(f"用户 {user_id} 注册成功")
            except Exception as e:
                print(f"保存用户数据失败: {str(e)}")
                raise RuntimeError(f"保存用户数据失败: {str(e)}")
                
        except Exception as e:
            print(f"用户注册失败: {str(e)}")
            raise

    def login(self, user_id: str, password: str) -> User:
        """用户登录"""
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        if not self._verify_password(password, user.password_hash):
            raise ValueError("密码错误")
        
        print(f"[UserService] 用户 '{user_id}' 登录成功")
        return user

    def get_user_car(self, user_id: str) -> Car:
        """获取用户的车辆信息"""
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        return user.car