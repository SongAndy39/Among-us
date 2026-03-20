#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色定义类
"""
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from player import Player


class Role(ABC):
    """角色抽象基类"""
    
    def __init__(self):
        # 使用字符串类型注解避免运行时导入错误
        self.player: Optional['Player'] = None
    
    def assign_to_player(self, player: 'Player'):
        """将角色分配给玩家"""
        self.player = player
    
    @abstractmethod
    def get_role_info(self) -> str:
        """获取角色信息"""
        pass


class Crewmate(Role):
    """船员角色"""
    
    def __init__(self, num_tasks: int = 5):
        super().__init__()
        self.num_tasks = num_tasks
        self.tasks_completed = 0
    
    def complete_task(self) -> bool:
        """船员完成任务"""
        if self.tasks_completed < self.num_tasks:
            self.tasks_completed += 1
            print(f"✅ {self.player.name}完成了一个任务！({self.tasks_completed}/{self.num_tasks})")
            return True
        return False
    
    def get_role_info(self) -> str:
        """获取船员角色信息"""
        return "你是船员！你的目标是完成所有任务或者找出内鬼。"


class Impostor(Role):
    """内鬼角色"""
    
    def __init__(self):
        super().__init__()
        self.kill_cooldown = 2
        self.current_cooldown = 0
    
    def set_kill_cooldown(self, cooldown: int):
        """设置击杀冷却时间"""
        self.kill_cooldown = 2
        self.current_cooldown = 0
    
    def update_cooldown(self):
        """更新冷却时间"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
    
    def kill(self) -> bool:
        """内鬼击杀技能"""
        if self.current_cooldown == 0:
            self.current_cooldown = self.kill_cooldown
            return True
        print(f"❌ 击杀冷却中，还剩{self.current_cooldown}回合")
        return False
    
    def sabotage(self, system: str) -> bool:
        """破坏系统"""
        print(f"🔧 {system}系统被破坏了！")
        return True
    
    def get_role_info(self) -> str:
        """获取内鬼角色信息"""
        return "你是内鬼！你的目标是偷偷杀害船员，直到内鬼数量与船员数量相等。"