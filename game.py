#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏逻辑类
"""
import random
import time
from typing import List, Dict, Optional
import tkinter as tk
from tkinter import messagebox
from player import Player
from roles import Role, Crewmate, Impostor
from tasks import TaskGenerator
from map import GameMap
from game_config import CREWMATE_TASK_GOAL
from game_rules import evaluate_game_outcome


class Game:
    """游戏逻辑类"""
    
    def __init__(self, player_names: List[str], num_impostors: int = 1):
        self.player_names = player_names
        self.num_impostors = num_impostors
        self.players: List[Player] = []
        self.map = GameMap()
        self.task_generator = TaskGenerator()
        self.current_round = 1
        self.game_over = False
        self.winner = None

    def initialize_players(self):
        """初始化玩家（修复：确保所有必要属性初始化）"""
        self.players = [Player(name) for name in self.player_names]
        # 初始化玩家的任务完成数和位置（避免属性不存在错误）
        for player in self.players:
            if not hasattr(player, 'completed_tasks'):
                player.completed_tasks = 0
            if not hasattr(player, 'current_location'):
                player.current_location = "飞船大厅"
            if not hasattr(player, 'is_alive'):
                player.is_alive = True
            if not hasattr(player, 'tasks'):
                player.tasks = []
    
    def assign_roles(self):
        """分配角色（修复：任务分配逻辑+属性初始化）"""
        # 打乱玩家顺序
        shuffled_players = random.sample(self.players, len(self.players))
        
        # 分配内鬼角色
        for i in range(self.num_impostors):
            impostor = Impostor()
            impostor.set_kill_cooldown(2)  # 设置击杀冷却时间为2回合
            shuffled_players[i].assign_role(impostor)
            # 内鬼无任务，初始化空列表
            shuffled_players[i].tasks = []
            shuffled_players[i].completed_tasks = 0
        
        # 分配船员角色
        for i in range(self.num_impostors, len(shuffled_players)):
            num_tasks = CREWMATE_TASK_GOAL
            crewmate = Crewmate(num_tasks=num_tasks)
            shuffled_players[i].assign_role(crewmate)
            # 为船员分配具体任务（确保任务实例独立）
            shuffled_players[i].tasks = self.task_generator.generate_tasks(num_tasks)
            # 初始化任务完成数
            shuffled_players[i].completed_tasks = 0
    
    def location_has_dead_body(self, location: str) -> bool:
        """检查指定位置是否有尸体（鲁棒性优化）"""
        try:
            return any(p for p in self.players if not p.is_alive and p.current_location == location)
        except AttributeError:
            return False
    
    def check_game_over(self) -> bool:
        """检查游戏是否结束（核心修复：任务完成判断逻辑）"""
        # 判断游戏结束条件（增加边界判断）
        self.game_over = False
        self.winner = None

        winner, _reason = evaluate_game_outcome(self)
        if winner:
            self.game_over = True
            self.winner = winner
        
        return self.game_over
    
    def get_alive_players(self) -> List[Player]:
        """获取所有存活的玩家（鲁棒性优化）"""
        return [p for p in self.players if hasattr(p, 'is_alive') and p.is_alive]
    
    def get_impostors(self) -> List[Player]:
        """获取所有内鬼（鲁棒性优化）"""
        return [p for p in self.players if isinstance(p.role, Impostor)]
    
    def get_crewmates(self) -> List[Player]:
        """获取所有船员（鲁棒性优化）"""
        return [p for p in self.players if isinstance(p.role, Crewmate)]
    
    # 新增：辅助方法 - 更新玩家任务完成数（适配图形化任务）
    def update_player_task_count(self, player: Player):
        """根据任务列表状态更新完成数"""
        if not hasattr(player, 'tasks') or not player.tasks:
            return
        
        completed_num = sum(1 for task in player.tasks if task.is_completed)
        player.completed_tasks = completed_num