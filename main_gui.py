import os
import sys
import random
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import List, Dict, Optional
import math

# 添加平台特定支持
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
# 字体检测函数
def get_available_font():
    """获取系统可用的字体"""
    try:
        # 确保Tkinter根窗口已创建
        if not tk._default_root:
            # 创建临时根窗口来获取字体
            temp_root = tk.Tk()
            temp_root.withdraw()  # 隐藏窗口
        
        # 直接返回Arial，避免字体检测问题
        return 'Arial'
    except Exception as e:
        # 如果出现任何错误，直接返回Arial
        return 'Arial'

# 导入游戏组件
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from game import Game
from player import Player
from roles import Role, Crewmate, Impostor
from tasks import Task
from map import GameMap
from tasks import (
    WireFixTask, FilterCleanTask, BodyScanTask, DownloadDataTask,
    CalibrateDownEngineTask, CalibrateUpEngineTask, RepairReactorTask,
    RefuelTask, StartSatelliteTask, MorseCodeTask, OxygenRepairTask
)

# ========== 太空狼人杀图形界面类 ==========
class AmongUsGUI:
    """太空狼人杀图形界面类"""
    
    def __init__(self, root, game):
        self.root = root
        self.root.title("太空狼人杀 - Among Us 简化版")
        self.root.geometry("1920x1080+0+0")
        self.root.configure(bg="#1a1a2e")
        self.game = game
        self.current_player = None
        self.action_steps = 0
        self.max_steps = 4
        # 统一使用Arial字体，避免跨平台字体问题
        self.font_family = 'Arial'
        self.current_player_index = 0
        
        # 全局回合变量
        self.global_round = 1
        self.players_acted_this_round = 0
        self.alive_players_count = 0
        
        # 氧气系统破坏核心变量（2回合超时直接结算）
        self.oxygen_sabotaged = False
        self.oxygen_sabotage_round = 0
        self.oxygen_repaired = False
        self.oxygen_timeout_rounds = 2
        self.oxygen_remaining_rounds = 0
        
        # 内鬼穿梭功能核心变量
        self.impostor_teleport_cooldown = {}
        self.all_rooms = [
            "飞船大厅", "电力室", "上升引擎室", "下降引擎室", "反应堆",
            "氧气室", "医疗室", "通讯室", "监控室", "燃料室", "主控室"
        ]
        
        # 紧急会议核心变量
        self.emergency_meeting_count = {}  # 记录每个玩家剩余紧急会议次数 {player_name: remaining_count}
        self.max_emergency_meetings = 2    # 每人最大紧急会议次数
        self.meeting_room = "飞船大厅"     # 仅飞船大厅可发起紧急会议
        
        # ========== 旁观模式核心变量 ==========
        self.spectator_players = []  # 处于旁观模式的玩家列表
        self.all_players_list = []   # 保存所有玩家的完整列表（包含死亡/存活）
        self.spectator_view_room = ""  # 旁观视角所在房间（与玩家物理位置分离）
        self.dead_player_locations = {}  # 记录死亡玩家的尸体位置（清理后标记为已移除）
        
        self.reported_bodies = {}  # 已报告的尸体字典 {player_name: "reported" | "voted_out"}
        
        # 创建主界面
        self.create_main_frame()

    def add_action_step(self):
        """增加行动步数，校验是否达到上限"""
        if self.action_steps >= self.max_steps:
            messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n无法继续执行该操作")
            return False
        self.action_steps += 1
        return True

    def clear_all_bodies(self):
        """
        清除所有尸体（核心新函数）
        - 保留旁观模式玩家列表
        - 标记尸体位置为已清理
        - 游戏日志记录清理操作
        """
        if not self.dead_player_locations:
            # 初始化死亡玩家位置记录
            for player in self.spectator_players:
                self.dead_player_locations[player.name] = {
                    "location": player.current_location,
                    "cleared": False
                }
        
        # 清除所有尸体记录（投票出去的玩家记录保留）
        # 只清除标记为"reported"的尸体，保留"voted_out"的记录
        bodies_to_remove = []
        for player_name, status in self.reported_bodies.items():
            if status == "reported":
                bodies_to_remove.append(player_name)
        
        for player_name in bodies_to_remove:
            del self.reported_bodies[player_name]
        
        # 清理所有尸体
        cleared_count = 0
        for player_name in self.dead_player_locations:
            if not self.dead_player_locations[player_name]["cleared"]:
                self.dead_player_locations[player_name]["cleared"] = True
                cleared_count += 1

       
        # 提示玩家
        messagebox.showinfo("尸体清理", f"🧹 投票结束，所有尸体已被清理！\n旁观玩家仍保持旁观模式，仅尸体消失")


    def switch_to_next_player(self):
        """切换至下一个玩家（包含死亡玩家），死亡玩家自动进入旁观模式"""
        # 使用完整玩家列表（包含死亡/存活）进行轮换，永不跳过任何玩家
        if not self.all_players_list:
            self.all_players_list = self.game.players.copy()
        
        # 获取当前玩家索引
        if self.current_player in self.all_players_list:
            current_idx = self.all_players_list.index(self.current_player)
        else:
            current_idx = 0
        
        # 切换到下一个玩家（循环轮换）
        next_idx = (current_idx + 1) % len(self.all_players_list)
        self.current_player = self.all_players_list[next_idx]
        self.current_player_index = self.game.players.index(self.current_player)
        
        # 重置行动步数（无论是否存活）
        self.action_steps = 0
        
        # 死亡玩家自动加入旁观模式
        if not self.current_player.is_alive and self.current_player not in self.spectator_players:
            self.spectator_players.append(self.current_player)
            # 记录尸体位置
            self.dead_player_locations[self.current_player.name] = {
                "location": self.current_player.current_location,
                "cleared": False
            }
            # 初始化旁观视角为玩家死亡位置
            self.spectator_view_room = self.current_player.current_location
            self.add_log(f"👻 {self.current_player.name}已死亡，进入旁观模式！尸体位置：{self.current_player.current_location}")
        
        # 旁观玩家初始化视角位置
        if self.current_player in self.spectator_players and not self.spectator_view_room:
            self.spectator_view_room = self.current_player.current_location
        
        # 全局回合计数逻辑（仅存活玩家参与回合计数）
        alive_players = [p for p in self.game.players if p.is_alive]
        self.alive_players_count = len(alive_players)
        
        # 仅存活玩家行动后才计数回合
        if self.current_player.is_alive:
            self.players_acted_this_round += 1
            
            if self.players_acted_this_round >= self.alive_players_count:
                # 回合结束，更新氧气剩余回合数
                if self.oxygen_sabotaged and not self.oxygen_repaired:
                    self.oxygen_remaining_rounds -= 1
                    self.add_log(f"⚠️ 氧气系统破坏剩余修复回合：{self.oxygen_remaining_rounds}")
                    
                    # 核心逻辑：剩余回合为0则直接结束游戏跳结算
                    if self.oxygen_remaining_rounds <= 0:
                        self.game.winner = "impostor"
                        self.game.game_over = True
                        self.show_game_over()
                        return
                
                # 更新内鬼穿梭冷却时间
                for player_name in list(self.impostor_teleport_cooldown.keys()):
                    if self.impostor_teleport_cooldown[player_name] > 0:
                        self.impostor_teleport_cooldown[player_name] -= 1
                        if self.impostor_teleport_cooldown[player_name] == 0:
                            del self.impostor_teleport_cooldown[player_name]
                            
                # 更新内鬼击杀冷却时间
                for player in self.game.players:
                    if hasattr(player.role, 'update_cooldown'):
                        player.role.update_cooldown()
                            
                
                # 更新全局回合数
                self.global_round += 1
                self.players_acted_this_round = 0
                
                # 仅游戏未结束时显示回合提示
                if not self.game.game_over:
                    messagebox.showinfo("回合结束", f"第{self.global_round-1}回合结束！\n进入第{self.global_round}回合")
        
        # 显示玩家切换提示（区分存活/旁观）
        if not self.game.game_over:
            if self.current_player in self.spectator_players:
                # 检查尸体是否已清理
                body_status = "（尸体已清理）" if self.dead_player_locations.get(self.current_player.name, {}).get("cleared", False) else f"（尸体位置：{self.current_player.current_location}）"
                messagebox.showinfo("玩家切换", f"当前旁观视角：{self.current_player.name}\n{body_status}\n当前查看房间：{self.spectator_view_room}")
            else:
                messagebox.showinfo("玩家切换", f"当前操作玩家：{self.current_player.name}\n全局回合：{self.global_round}")
        
        # 刷新UI
        self.create_game_frame()

    def add_log(self, message):
        """添加日志信息"""
        if hasattr(self, 'log_text'):
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")

    def create_main_frame(self):
        """创建主界面"""
        # 清除所有现有组件
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 重置全局变量
        self.global_round = 1
        self.players_acted_this_round = 0
        self.alive_players_count = 0
        
        # 重置氧气系统状态
        self.oxygen_sabotaged = False
        self.oxygen_sabotage_round = 0
        self.oxygen_repaired = False
        self.oxygen_remaining_rounds = 0
        
        # 重置内鬼穿梭冷却
        self.impostor_teleport_cooldown = {}
        
        # 重置紧急会议次数
        self.emergency_meeting_count = {}
        
        # 重置旁观模式变量
        self.spectator_players = []
        self.all_players_list = []
        self.spectator_view_room = ""
        self.dead_player_locations = {}  # 重置尸体位置记录
        self.reported_bodies = {}  # 重置已报告的尸体列表
        
        # 创建标题
        title_label = tk.Label(
            self.root, 
            text="太空狼人杀", 
            font=(self.font_family, 48, "bold"),
            fg="#e94560",
            bg="#1a1a2e"
        )
        title_label.pack(pady=50)
        
        # 创建副标题
        subtitle_label = tk.Label(
            self.root, 
            text="Among Us 简化版", 
            font=(self.font_family, 18),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        subtitle_label.pack(pady=10)
        
        # 创建玩家数量选择框架
        player_frame = tk.Frame(self.root, bg="#16213e", padx=30, pady=20)
        player_frame.pack(pady=30)
        
        player_label = tk.Label(
            player_frame, 
            text="请选择玩家数量 (4-10):", 
            font=(self.font_family, 14),
            fg="#ffffff",
            bg="#16213e"
        )
        player_label.pack(pady=10)
        
        # 创建玩家数量滑块
        self.num_players_var = tk.IntVar(value=10)
        player_scale = tk.Scale(
            player_frame, 
            from_=4, 
            to=10, 
            orient="horizontal",
            variable=self.num_players_var,
            length=300,
            bg="#16213e",
            fg="#ffffff",
            troughcolor="#0f3460",
            highlightbackground="#16213e"
        )
        player_scale.pack(pady=10)
        
        # 显示当前选择的玩家数量
        self.num_players_display = tk.Label(
            player_frame, 
            text=f"当前选择: {self.num_players_var.get()} 人", 
            font=(self.font_family, 12),
            fg="#00ff00",
            bg="#16213e"
        )
        self.num_players_display.pack(pady=5)
        player_scale.bind("<Motion>", lambda event: self.update_player_count())
        
        # 创建开始按钮
        # 为所有平台创建兼容的按钮
        if sys.platform == 'darwin':
            # Mac上使用ttk按钮
            start_button = ttk.Button(
                player_frame, 
                text="开始游戏", 
                style="Start.TButton",
                command=self.start_game_setup
            )
            style = ttk.Style()
            style.theme_use('alt')
            style.configure("Start.TButton", 
                          font=(self.font_family, 16, "bold"),
                          padding=(30, 10),
                          background="#4CAF50",
                          foreground="#FFFFFF")
            style.map("Start.TButton",
                      background=[("active", "#388E3C"),("!active", "#4CAF50")],
                      foreground=[("active", "#E8F5E9"),("!active", "#FFFFFF")])

        else:
            # Windows上使用普通按钮
            start_button = tk.Button(
                player_frame, 
                text="开始游戏", 
                font=(self.font_family, 16, "bold"),
                bg="#4caf50",
                fg="#ffffff",
                padx=30,
                pady=10,
                bd=2,
                relief="flat",
                command=self.start_game_setup
            )
        start_button.pack(pady=20)
    
    def update_player_count(self):
        """更新玩家数量显示"""
        self.num_players_display.config(text=f"当前选择: {self.num_players_var.get()} 人")
    
    def start_game_setup(self):
        """开始游戏设置（船员任务数固定为3，临时任务单独处理）"""
        num_players = self.num_players_var.get()
        player_names = []
        
        # 获取玩家名称
        for i in range(1, num_players + 1):
            name = f"玩家{i}"
            player_names.append(name)
        
        # 根据玩家数量确定内鬼数量
        if num_players <= 6:
            num_impostors = 1
        else:
            num_impostors = 2
        
        # 初始化游戏
        self.game = Game(player_names, num_impostors)
        self.game.initialize_players()
        self.game.assign_roles()
        
        # 初始化所有玩家的紧急会议次数（每人2次）
        self.emergency_meeting_count = {p.name: self.max_emergency_meetings for p in self.game.players}
        
        # 保存完整玩家列表
        self.all_players_list = self.game.players.copy()
        
        # 核心修改1：船员固定3个基础任务，移除默认OxygenRepairTask
        for player in self.game.players:
            if isinstance(player.role, Crewmate):
                player.role.num_tasks = 3
                player.completed_tasks = 0
                
                # 清空任务列表，只添加3个基础任务
                player.tasks = []
                # 确保任务池不含氧气修复任务（作为临时任务单独添加）
                try:
                    task_pool = [
                        WireFixTask(), FilterCleanTask(), BodyScanTask(),
                        DownloadDataTask(), CalibrateDownEngineTask(),
                        CalibrateUpEngineTask(), RepairReactorTask(),
                        RefuelTask(), StartSatelliteTask(), MorseCodeTask()
                    ]
                    player.tasks = random.sample(task_pool, 3)
                except ImportError:
                    # 备用任务，确保3个
                    class DummyTask(Task):
                        def __init__(self, name, location):
                            self.name = name
                            self.location = location
                            self.difficulty = 1
                            self.is_completed = False
                        def run_task_gui(self, main_root=None):
                            self.is_completed = True
                            return True
                        def complete(self):
                            self.is_completed = True
                            return True
                    player.tasks = [
                        DummyTask("校准引擎", "上升引擎室"),
                        DummyTask("下载数据", "通讯室"),
                        DummyTask("清理过滤器", "氧气室")
                    ]
        
        # 初始化回合变量
        self.global_round = 1
        self.players_acted_this_round = 0
        self.alive_players_count = len([p for p in self.game.players if p.is_alive])
        
        # 初始化内鬼穿梭冷却
        self.impostor_teleport_cooldown = {}
        
        # 显示角色信息（仅自己可见）
        self.show_role_info()
    
    def show_role_info(self):
        """显示角色信息（新增紧急会议位置限制提示）"""
        if self.current_player_index < len(self.game.players):
            player = self.game.players[self.current_player_index]
            
            # 清除界面
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # 创建角色信息界面
            role_frame = tk.Frame(self.root, bg="#16213e", padx=40, pady=30)
            role_frame.pack(fill="both", expand=True, pady=50, padx=50)
            
            # 玩家信息
            player_label = tk.Label(
                role_frame, 
                text=f"玩家: {player.name}", 
                font=(self.font_family, 24, "bold"),
                fg="#ffffff",
                bg="#16213e"
            )
            player_label.pack(pady=20)
            
            # 角色信息
            role_name = player.role.__class__.__name__
            role_color = "#e94560" if role_name == "Impostor" else "#00ff00"
            
            role_label = tk.Label(
                role_frame, 
                text=f"角色: {role_name}", 
                font=(self.font_family, 32, "bold"),
                fg=role_color,
                bg="#16213e"
            )
            role_label.pack(pady=30)
            
            # 角色说明
            info_text = player.role.get_role_info()
            info_label = tk.Label(
                role_frame, 
                text=info_text, 
                font=(self.font_family, 14),
                fg="#ffffff",
                bg="#16213e",
                wraplength=600,
                justify="center"
            )
            info_label.pack(pady=20)
            
            # 紧急会议规则提示（新增位置限制）
            meeting_rule_label = tk.Label(
                role_frame,
                text=f"📢 紧急会议规则：每人可发起{self.max_emergency_meetings}次紧急会议，仅在【飞船大厅】可发起！",
                font=(self.font_family, 12),
                fg="#00ffff",
                bg="#16213e"
            )
            meeting_rule_label.pack(pady=5)
            
            # 任务信息（仅船员可见，明确提示3个常规任务+临时氧气任务规则）
            if isinstance(player.role, Crewmate):
                task_label = tk.Label(
                    role_frame, 
                    text=f"你需要完成 3 个常规任务", 
                    font=(self.font_family, 16),
                    fg="#4caf50",
                    bg="#16213e"
                )
                task_label.pack(pady=10)
                oxygen_rule_label = tk.Label(
                    role_frame,
                    text="⚠️ 内鬼破坏氧气后会新增临时修复任务，修复后自动移除！\n临时任务不占用3个常规任务数量，2回合内未修复则内鬼胜利！",
                    font=(self.font_family, 12),
                    fg="#ff0000",
                    bg="#16213e"
                )
                oxygen_rule_label.pack(pady=5)
            
            # 其他内鬼信息（仅内鬼可见）
            if isinstance(player.role, Impostor):
                other_impostors = [p.name for p in self.game.players 
                                 if p != player and isinstance(p.role, Impostor)]
                if other_impostors:
                    impostor_label = tk.Label(
                        role_frame, 
                        text=f"其他内鬼: {', '.join(other_impostors)}", font=(self.font_family, 14),
                        fg="#e94560",
                        bg="#16213e"
                    )
                    impostor_label.pack(pady=10)
                # 提示内鬼氧气破坏规则
                oxygen_tip_label = tk.Label(
                    role_frame,
                    text="⚠️ 破坏氧气后船员会新增临时修复任务，2回合内未修复你将直接胜利！",
                    font=(self.font_family, 12),
                    fg="#ffcc00",
                    bg="#16213e"
                )
                oxygen_tip_label.pack(pady=5)
                # 提示内鬼穿梭规则
                teleport_rule_label = tk.Label(
                    role_frame,
                    text="🔮 穿梭规则：第一回合禁用，使用后冷却3回合，可跳至任意房间！",
                    font=(self.font_family, 12),
                    fg="#00ffff",
                    bg="#16213e"
                )
                teleport_rule_label.pack(pady=5)
            
            # 提示文本
            tip_label = tk.Label(
                role_frame, 
                text="请记住你的角色信息，然后点击继续按钮", 
                font=(self.font_family, 12),
                fg="#ffcc00",
                bg="#16213e"
            )
            tip_label.pack(pady=30)
            
            # 继续按钮
            # 为所有平台创建兼容的按钮
            if sys.platform == 'darwin':
                # Mac上使用ttk按钮
                continue_button = ttk.Button(
                    role_frame, 
                    text="继续", 
                    style="Continue.TButton",
                    command=self.next_role_info
                )
                style = ttk.Style()
                style.configure("Continue.TButton", 
                              font=(self.font_family, 16),
                              padding=(30, 10),
                              background="#2196F3",
                              foreground="#FFFFFF")
                style.map("Continue.TButton",
                      background=[("active", "#1976D2"),("!active", "#2196F3")],
                      foreground=[("active", "#E3F2FD"),("!active", "#FFFFFF")])
            else:
                # Windows上使用普通按钮
                continue_button = tk.Button(
                    role_frame, 
                    text="继续", 
                    font=(self.font_family, 16),
                    bg="#2196f3",
                    fg="#ffffff",
                    padx=30,
                    pady=10,
                    bd=2,
                    relief="flat",
                    command=self.next_role_info
                )
            continue_button.pack()
        else:
            # 所有玩家都已查看角色，开始游戏
            self.start_game_loop()
    
    def next_role_info(self):
        """显示下一个玩家的角色信息"""
        self.current_player_index += 1
        self.show_role_info()
    
    def start_game_loop(self):
        """开始游戏主循环"""
        self.game.game_over = False
        # 重置全局回合变量
        self.global_round = 1
        self.players_acted_this_round = 0
        self.alive_players_count = len([p for p in self.game.players if p.is_alive])
        
        # 设置第一个玩家
        if self.all_players_list:
            self.current_player = self.all_players_list[0]
        else:
            self.current_player = self.game.players[0]
        
        # 开始游戏
        self.create_game_frame()

    def handle_emergency_meeting(self, player):
        """处理发起紧急会议的核心逻辑（新增位置校验）"""
        # 旁观玩家无法发起紧急会议
        if player in self.spectator_players:
            messagebox.showwarning("旁观限制", "❌ 旁观模式下无法发起紧急会议！")
            return
        
        # 1. 检查剩余次数
        remaining = self.emergency_meeting_count.get(player.name, 0)
        if remaining <= 0:
            messagebox.showwarning("次数用尽", "❌ 您发起紧急会议的次数已使用完毕！")
            return
        
        # 2. 新增：检查当前位置是否为飞船大厅
        if player.current_location != self.meeting_room:
            messagebox.showwarning("位置限制", f"❌ 仅在【{self.meeting_room}】可发起紧急会议！\n当前位置：{player.current_location}")
            return
        
        # 3. 确认发起紧急会议
        confirm = messagebox.askyesno(
            "发起紧急会议",
            f"📢 你确定要发起紧急会议吗？\n当前剩余次数：{remaining-1}/{self.max_emergency_meetings}",
            parent=self.root
        )
        if not confirm:
            return
        
        # 4. 消耗紧急会议次数
        self.emergency_meeting_count[player.name] -= 1
        remaining_after = self.emergency_meeting_count[player.name]
        
        # 5. 记录日志
        self.add_log(f"📢 {player.name}在{self.meeting_room}发起了紧急会议！剩余次数：{remaining_after}/{self.max_emergency_meetings}")
        
        # 6. 进入讨论阶段（复用原有讨论逻辑）
        self.discussion_phase(player, None)

    def discussion_phase(self, reporter, victim):
        """讨论阶段（投票结束后自动清理尸体）"""
        # 创建讨论窗口
        discussion_window = tk.Toplevel(self.root)
        discussion_window.title("紧急会议 - 讨论阶段")
        discussion_window.geometry("800x600+560+200")
        discussion_window.configure(bg="#1a1a2e")
        discussion_window.transient(self.root)
        discussion_window.grab_set()
        
        # 标题
        if victim:
            title = f"紧急会议 - 讨论{victim.name}的死亡"
        else:
            title = "紧急会议 - 自由讨论"
        
        title_label = tk.Label(
            discussion_window,
            text=title,
            font=(self.font_family, 20, "bold"),
            fg="#e94560",
            bg="#1a1a2e"
        )
        title_label.pack(pady=20)
        
        # 存活玩家列表
        alive_players = [p for p in self.game.players if p.is_alive]
        suspect_var = tk.StringVar()
        
        # 嫌疑人列表
        suspect_frame = tk.Frame(discussion_window, bg="#16213e")
        suspect_frame.pack(fill="x", padx=20, pady=10)
        
        suspect_label = tk.Label(
            suspect_frame,
            text="选择你怀疑的玩家：",
            font=(self.font_family, 14),
            fg="#ffffff",
            bg="#16213e"
        )
        suspect_label.pack(pady=5)
        
        suspect_listbox = tk.Listbox(
            suspect_frame,
            listvariable=suspect_var,
            font=(self.font_family, 12),
            bg="#0f3460",
            fg="#ffffff",
            selectbackground="#e94560",
            selectforeground="#ffffff",
            height=len(alive_players)
        )
        suspect_listbox.pack(fill="x", padx=10, pady=5)
        
        for player in alive_players:
            suspect_listbox.insert(tk.END, player.name)
        
        # 投票按钮
        # 为所有平台创建兼容的按钮
        if sys.platform == 'darwin':
            # Mac上使用ttk按钮
            vote_button = ttk.Button(
                discussion_window,
                text="投票", 
                style="Vote.TButton",
                command=lambda: self.vote(discussion_window, suspect_listbox, reporter, victim)
            )
            style = ttk.Style()
            style.configure("Vote.TButton", 
                          font=(self.font_family, 14),
                          padding=(20, 10),
                          background="#E94560",
                          foreground="#FFFFFF")
            style.map("Vote.TButton",
                              background=[("active", "#C62828"),("!active", "#E94560")],
                              foreground=[("active", "#FFEBEE"),("!active", "#FFFFFF")])
        else:
            # Windows上使用普通按钮
            vote_button = tk.Button(
                discussion_window,
                text="投票",
                font=(self.font_family, 14),
                bg="#e94560",
                fg="#ffffff",
                padx=20,
                pady=10,
                bd=2,
                relief="flat",
                command=lambda: self.vote(discussion_window, suspect_listbox, reporter, victim)
            )
        vote_button.pack(pady=20)

    def vote(self, window, listbox, reporter, victim):
        """投票逻辑（核心修改：投票结束后调用尸体清理函数）"""
        if not listbox.curselection():
            messagebox.showwarning("警告", "请选择一个玩家进行投票！", parent=window)
            return
        
        selected_idx = listbox.curselection()[0]
        accused_name = listbox.get(selected_idx)
        accused = next(p for p in self.game.players if p.name == accused_name)
        
        # 记录投票
        self.add_log(f"{self.current_player.name}投票给了{accused_name}")
        
        # 确认投票
        confirm = messagebox.askyesno(
            "确认投票",
            f"你确定要投票给{accused_name}吗？",
            parent=window
        )
        if not confirm:
            return
        
        # 关闭讨论窗口
        window.destroy()
        
        # 投票结果
        if isinstance(accused.role, Impostor):
            # 投中内鬼
            self.add_log(f"🎉 {accused_name}是内鬼！投票成功！")
            accused.is_alive = False
            # 内鬼死亡后加入旁观模式
            if accused not in self.spectator_players:
                self.spectator_players.append(accused)
                self.dead_player_locations[accused.name] = {
                    "location": accused.current_location,
                    "cleared": False
                }
            # 标记为被投票出去的玩家（不能再次报告）
            self.reported_bodies[accused.name] = "voted_out"
            messagebox.showinfo("投票结果", f"🎉 {accused_name}是内鬼！\n你成功找出了内鬼！")
        else:
            # 投错了
            self.add_log(f"❌ {accused_name}不是内鬼！投票失败！")
            # 标记为被投票出去的玩家（不能再次报告）
            self.reported_bodies[accused.name] = "voted_out"
            messagebox.showinfo("投票结果", f"❌ {accused_name}不是内鬼！\n投票失败！")
        
        # ========== 核心修改：投票结束后自动清理所有尸体 ==========
        
        
        # 检查游戏是否结束
        self.check_game_over()
        
        # 刷新游戏界面
        self.create_game_frame()

    def get_room_mates_text(self):
        """获取当前视角房间的玩家文本（旁观模式显示视角房间的玩家）"""
        # 旁观模式：显示视角房间的玩家信息
        if self.current_player in self.spectator_players:
            view_room = self.spectator_view_room or self.current_player.current_location
            room_mates = [
                p for p in self.game.players 
                if p.current_location == view_room
            ]
            text_lines = [f"当前查看房间({view_room})玩家及身份："]
            if not room_mates:
                text_lines.append("无其他玩家")
            else:
                player_info = []
                for p in room_mates:
                    role_name = p.role.__class__.__name__
                    status = "🔴死亡" if not p.is_alive else "🟢存活"
                    # 标记自己的尸体（如果未清理）
                    if p == self.current_player and not p.is_alive:
                        if self.dead_player_locations.get(p.name, {}).get("cleared", False):
                            status += "（你的尸体已清理）"
                        else:
                            status += "（你的尸体）"
                    player_info.append(f"{p.name}: {role_name} ({status})")
                line1 = " | ".join(player_info)
                text_lines.append(line1)
            return "\n".join(text_lines[:2])
        # 正常模式：仅显示当前房间的存活玩家名
        else:
            current_player = self.current_player
            room_mates = [
                p.name for p in self.game.players 
                if p.is_alive and p != current_player and p.current_location == current_player.current_location
            ]
            text_lines = [f"当前房间({current_player.current_location})玩家："]
            if not room_mates:
                text_lines.append("无其他玩家")
            else:
                line1 = " | ".join(room_mates[:])
                text_lines.append(line1)
            return "\n".join(text_lines[:2])
    
    def teleport_to_room(self, player):
        """内鬼穿梭功能：跳转到任意房间"""
        # 旁观玩家无法使用穿梭
        if player in self.spectator_players:
            messagebox.showwarning("旁观限制", "❌ 旁观模式下无法使用穿梭功能！")
            return
        
        # 步数检查
        if self.action_steps > self.max_steps:
            messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n无法使用穿梭")
            return
        
        # 创建穿梭房间选择窗口
        teleport_window = tk.Toplevel(self.root)
        teleport_window.title("内鬼穿梭 - 选择目标房间")
        teleport_window.geometry("1000x750+460+165")
        teleport_window.configure(bg="#1a1a2e")
        teleport_window.transient(self.root)
        teleport_window.grab_set()
        teleport_window.wm_attributes("-topmost", True)
        
        # 标题
        title_label = tk.Label(
            teleport_window,
            text="🔮 选择要穿梭到的房间",
            font=(self.font_family, 16, "bold"),
            fg="#00ffff",
            bg="#1a1a2e"
        )
        title_label.pack(pady=15)
        
        # 房间列表
        room_var = tk.StringVar()
        room_listbox = tk.Listbox(
            teleport_window,
            listvariable=room_var,
            font=(self.font_family, 12),
            bg="#0f3460",
            fg="#ffffff",
            selectbackground="#00ffff",
            selectforeground="#000000",
            width=25,
            height=12
        )
        room_listbox.pack(pady=10, padx=20)
        
        # 添加所有房间选项
        for room in self.all_rooms:
            room_listbox.insert(tk.END, room)
        
        # 确认穿梭
        def confirm_teleport():
            if room_listbox.curselection():
                selected_idx = room_listbox.curselection()[0]
                target_room = room_listbox.get(selected_idx)
                
                # 消耗行动步数
                self.action_steps += 1
                
                # 执行穿梭
                old_room = player.current_location
                player.current_location = target_room
                
                # 设置3回合冷却
                self.impostor_teleport_cooldown[player.name] = 1
                
                # 关闭窗口
                teleport_window.destroy()
                
                # 提示
                messagebox.showinfo("穿梭成功", f"✅ 已成功穿梭到【{target_room}】！\n穿梭将进入3回合冷却")
                
                # 刷新UI
                self.create_game_frame()
                
                # 检查步数是否超限
                if self.action_steps > self.max_steps:
                    messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n自动切换至下一位玩家")
                    self.switch_to_next_player()
            else:
                messagebox.showwarning("警告", "请选择一个目标房间！")
        
        # 按钮框架
        btn_frame = tk.Frame(teleport_window, bg="#1a1a2e")
        btn_frame.pack(pady=15)
        
        # 确认按钮
        # 为所有平台创建兼容的按钮
        if sys.platform == 'darwin':
            # Mac上使用ttk按钮
            confirm_btn = ttk.Button(
                btn_frame,
                text="确认穿梭", 
                style="Confirm.TButton",
                command=confirm_teleport
            )
            cancel_btn = ttk.Button(
                btn_frame,
                text="取消", 
                style="Cancel.TButton",
                command=teleport_window.destroy
            )
            style = ttk.Style()
            style.configure("Confirm.TButton", 
                          font=(self.font_family, 12),
                          padding=(20, 5),
                          background="#00FFFF",
                          foreground="#000000")
            style.map("Confirm.TButton",
                      background=[("active", "#00CCCC"),("!active", "#00FFFF")],
                      foreground=[("active", "#000000"),("!active", "#000000")])
            style.configure("Cancel.TButton", 
                          font=(self.font_family, 12),
                          padding=(20, 5),
                          background="#F44336",
                          foreground="#FFFFFF")
            style.map("Cancel.TButton",
                      background=[("active", "#D32F2F"),("!active", "#F44336")],
                      foreground=[("active", "#FFEBEE"),("!active", "#FFFFFF")])
            confirm_btn.pack(side="left", padx=10)
        else:
            # Windows上使用普通按钮
            # Windows上使用普通按钮
            confirm_btn = tk.Button(
                btn_frame,
                text="确认穿梭",
                font=(self.font_family, 12),
                bg="#00ffff",
                fg="#000000",
                padx=20,
                pady=5,
                bd=2,
                relief="flat",
                command=confirm_teleport
            )
            cancel_btn = tk.Button(
                btn_frame,
                text="取消",
                font=(self.font_family, 12),
                bg="#f44336",
                fg="#ffffff",
                padx=20,
                pady=5,
                bd=2,
                relief="flat",
                command=teleport_window.destroy
            )
        cancel_btn.pack(side="left", padx=10)
    
    def create_game_frame(self):
        """创建游戏主界面（死亡玩家保留并进入旁观模式，尸体固定位置）"""
        # 清除所有现有组件
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 创建游戏主框架
        self.game_frame = tk.Frame(self.root, bg="#16213e")
        self.game_frame.pack(fill="both", expand=True)
        
        self.create_task_list() 
        # 顶部信息栏
        top_frame = tk.Frame(self.game_frame, bg="#0f3460", height=60)
        top_frame.pack(fill="x")
        
        # 显示全局回合数 + 氧气系统状态 + 内鬼穿梭冷却
        # 新增：旁观模式标识
        spectator_tag = "【旁观模式】" if self.current_player in self.spectator_players else ""
        round_text = f"{spectator_tag}全局回合：{self.global_round} | 当前玩家行动步数：{self.action_steps}/{self.max_steps}"
        
        if self.oxygen_sabotaged and not self.oxygen_repaired:
            round_text += f" | ⚠️ 氧气已破坏！剩余修复回合：{self.oxygen_remaining_rounds} (共2回合)"
            if self.oxygen_remaining_rounds <= 1:
                round_text += " ⏰ 最后倒计时！"
        
        # 添加内鬼穿梭冷却提示（仅存活内鬼显示）
        if isinstance(self.current_player.role, Impostor) and self.current_player.is_alive:
            if self.current_player.name in self.impostor_teleport_cooldown:
                round_text += f" | 🔮 穿梭冷却剩余：{self.impostor_teleport_cooldown[self.current_player.name]}回合"
            elif self.global_round == 1:
                round_text += f" | 🔮 第一回合无法使用穿梭"
        
        round_label = tk.Label(
            top_frame, 
            text=round_text, 
            font=(self.font_family, 16),
            fg="#ffffff",
            bg="#0f3460"
        )
        round_label.pack(side="left", padx=20)
        
        # 显示当前玩家剩余紧急会议次数 + 位置限制提示（旁观玩家显示次数但无法使用）
        remaining_meetings = self.emergency_meeting_count.get(self.current_player.name, 0)
        meeting_label = tk.Label(
            top_frame,
            text=f"📢 紧急会议剩余次数：{remaining_meetings}/{self.max_emergency_meetings} | 仅{self.meeting_room}可发起",
            font=(self.font_family, 14),
            fg="#00ffff",
            bg="#0f3460"
        )
        meeting_label.pack(side="left", padx=20)
        
        # 玩家存活状态（显示所有玩家，死亡玩家标记👻）
        status_frame = tk.Frame(top_frame, bg="#0f3460")
        status_frame.pack(side="right", padx=20)
        
        status_label = tk.Label(
            status_frame, 
            text="所有玩家状态:", 
            font=(self.font_family, 12),
            fg="#ffffff",
            bg="#0f3460"
        )
        status_label.pack(side="left")
        
        for player in self.all_players_list:
            status = "🔵" if player.is_alive else "🔴"
            # 旁观玩家额外标记
            if player in self.spectator_players:
                status += "👻"
            player_status = tk.Label(
                status_frame, 
                text=f"{status}{player.name}", 
                font=(self.font_family, 10),
                fg="#ffffff",
                bg="#0f3460"
            )
            player_status.pack(side="left", padx=5)
        
        # 中间内容区域
        content_frame = tk.Frame(self.game_frame, bg="#16213e")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 左侧地图区域
        map_container = tk.Frame(content_frame, bg="#16213e")
        map_container.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # 核心：固定两行显示当前视角房间的玩家
        room_mates_label = tk.Label(
            map_container,
            text=self.get_room_mates_text(),
            font=(self.font_family, 12),
            fg="#00ffff",
            bg="#16213e",
            justify="left",
            wraplength=780,
            anchor="nw",
            height=2  # 强制固定2行高度
        )
        room_mates_label.pack(pady=(0, 5), fill="x")
        
        # 原有地图框架
        map_frame = tk.LabelFrame(map_container, text="飞船地图", bg="#1a1a2e", fg="#ffffff", font=(self.font_family, 12))
        map_frame.pack(fill="both", expand=True)
        
        # 绘制简单的地图
        self.draw_map(map_frame)
        
        # 右侧信息区域
        info_frame = tk.LabelFrame(content_frame, text="游戏信息", bg="#1a1a2e", fg="#ffffff", font=(self.font_family, 12))
        info_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # 当前玩家信息
        player_info_frame = tk.Frame(info_frame, bg="#1a1a2e")
        player_info_frame.pack(fill="x", padx=10, pady=10)
        
        player_info_label = tk.Label(
            player_info_frame, 
            text=f"当前玩家: {self.current_player.name}", 
            font=(self.font_family, 14, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        player_info_label.pack(pady=5)
        
        # 显示存活状态
        if self.current_player in self.spectator_players:
            # 检查尸体是否已清理
            body_cleared = self.dead_player_locations.get(self.current_player.name, {}).get("cleared", False)
            if body_cleared:
                alive_status = f"🔴 死亡（旁观）| 你的尸体已被清理"
            else:
                alive_status = f"🔴 死亡（旁观）| 尸体位置：{self.current_player.current_location}"
            
            status_label = tk.Label(
                player_info_frame,
                text=alive_status,
                font=(self.font_family, 12),
                fg="#ff0000",
                bg="#1a1a2e"
            )
            status_label.pack(pady=5)
            
            # 显示当前旁观视角位置
            view_status = f"当前查看房间：{self.spectator_view_room or self.current_player.current_location}"
            view_label = tk.Label(
                player_info_frame,
                text=view_status,
                font=(self.font_family, 12),
                fg="#00ffff",
                bg="#1a1a2e"
            )
            view_label.pack(pady=5)
        else:
            alive_status = "🟢 存活" if self.current_player.is_alive else "🔴 死亡"
            status_label = tk.Label(
                player_info_frame,
                text=f"状态: {alive_status}",
                font=(self.font_family, 12),
                fg="#00ff00" if self.current_player.is_alive else "#ff0000",
                bg="#1a1a2e"
            )
            status_label.pack(pady=5)
            
            location_label = tk.Label(
                player_info_frame, 
                text=f"当前位置: {self.current_player.current_location}", 
                font=(self.font_family, 12),
                fg="#4caf50",
                bg="#1a1a2e"
            )
            location_label.pack(pady=5)
        
        # 显示当前玩家剩余步数（死亡玩家也显示，但无法使用）
        steps_label = tk.Label(
            player_info_frame, 
            text=f"剩余行动步数: {self.max_steps - self.action_steps + 1}", 
            font=(self.font_family, 12),
            fg="#ffcc00",
            bg="#1a1a2e"
        )
        steps_label.pack(pady=5)
        
        # 显示船员常规任务进度（死亡船员也显示）
        if isinstance(self.current_player.role, Crewmate):
            progress = f"{self.current_player.completed_tasks}/3"
            progress_label = tk.Label(
                player_info_frame,
                text=f"常规任务进度: {progress}",
                font=(self.font_family, 12),
                fg="#00ff00",
                bg="#1a1a2e"
            )
            progress_label.pack(pady=5)
        
        # 行动按钮区域
        action_frame = tk.Frame(info_frame, bg="#1a1a2e")
        action_frame.pack(fill="x", padx=10, pady=10)
        
        # ========== 旁观模式：禁用所有操作按钮，仅视角移动 ==========
        if self.current_player in self.spectator_players:
            # 旁观模式提示
            spectator_label = tk.Label(
                action_frame,
                text="👻 你已死亡，进入旁观模式",
                font=(self.font_family, 14, "bold"),
                fg="#ffcc00",
                bg="#1a1a2e"
            )
            spectator_label.pack(fill="x", pady=10)
            
            # 提示尸体状态
            body_cleared = self.dead_player_locations.get(self.current_player.name, {}).get("cleared", False)
            if body_cleared:
                body_label = tk.Label(
                    action_frame,
                    text=f"⚠️ 你的尸体已被清理！",
                    font=(self.font_family, 12),
                    fg="#ff6666",
                    bg="#1a1a2e"
                )
            else:
                body_label = tk.Label(
                    action_frame,
                    text=f"⚠️ 你的尸体将永久停留在：{self.current_player.current_location}",
                    font=(self.font_family, 12),
                    fg="#ff6666",
                    bg="#1a1a2e"
                )
            body_label.pack(fill="x", pady=5)
            
            # 旁观专用：视角移动（仅改变查看房间，不移动尸体）
            move_label = tk.Label(
                action_frame,
                text="旁观视角移动：可查看任意房间，尸体位置不变（清理后消失）",
                font=(self.font_family, 12),
                fg="#00ffff",
                bg="#1a1a2e"
            )
            move_label.pack(fill="x", pady=5)
            
            # 房间选择下拉框
            room_var = tk.StringVar(value=self.spectator_view_room or self.current_player.current_location)
            room_combobox = ttk.Combobox(
                action_frame,
                textvariable=room_var,
                values=self.all_rooms,
                state="readonly",
                font=(self.font_family, 10),
                width=20
            )
            room_combobox.pack(fill="x", pady=5)
            
            # 视角移动按钮（仅改变视角，不移动玩家本体）
            def spectator_move_view():
                target_room = room_var.get()
                self.spectator_view_room = target_room
                body_status = "（尸体已清理）" if body_cleared else f"（尸体仍在{self.current_player.current_location}）"
                self.add_log(f"👻 {self.current_player.name}(旁观)切换视角到{target_room} {body_status}")
                self.create_game_frame()
            
            # 为所有平台创建兼容的按钮
            if sys.platform == 'darwin':
                # Mac上使用ttk按钮
                move_btn = ttk.Button(
                    action_frame,
                    text="切换到选中房间视角", 
                    style="Move.TButton",
                    command=spectator_move_view
                )
                style = ttk.Style()
                style.configure("Move.TButton", 
                              font=(self.font_family, 10),
                              padding=(5, 3),
                              background="#0F3460",
                              foreground="#FFFFFF")
                style.map("Move.TButton",
                      background=[("active", "#0A2647"),("!active", "#0F3460")],
                      foreground=[("active", "#E3F2FD"),("!active", "#FFFFFF")])
            else:
                # Windows上使用普通按钮
                move_btn = tk.Button(
                    action_frame,
                    text="切换到选中房间视角",
                    font=(self.font_family, 10),
                    bg="#0f3460",
                    fg="#ffffff",
                    bd=2,
                    relief="flat",
                    command=spectator_move_view
                )
            move_btn.pack(fill="x", pady=5)
            
            # 禁用所有操作按钮的提示
            disabled_label = tk.Label(
                action_frame,
                text="⚠️ 旁观模式下无法执行任何游戏操作，仅可查看",
                font=(self.font_family, 12),
                fg="#ff0000",
                bg="#1a1a2e"
            )
            disabled_label.pack(fill="x", pady=10)
        else:
            # ========== 存活玩家：正常显示操作按钮 ==========
            # 紧急会议按钮（仅飞船大厅+剩余次数>0可用）
            remaining_meetings = self.emergency_meeting_count.get(self.current_player.name, 0)
            is_in_meeting_room = self.current_player.current_location == self.meeting_room
            
            if remaining_meetings > 0 and is_in_meeting_room:
                meeting_btn_state = "normal"
                meeting_btn_bg = "#ff9800"
                meeting_btn_text = f"发起紧急会议（剩余{remaining_meetings}次）"
            else:
                meeting_btn_state = "disabled"
                meeting_btn_bg = "#666666"
                if remaining_meetings <= 0:
                    meeting_btn_text = "发起紧急会议（次数已用尽）"
                else:
                    meeting_btn_text = f"发起紧急会议（仅{self.meeting_room}可发起）"
            
            # 为所有平台创建兼容的按钮
            if sys.platform == 'darwin':
                # Mac上使用ttk按钮
                emergency_meeting_btn = ttk.Button(
                    action_frame,
                    text=meeting_btn_text, 
                    style="Emergency.TButton",
                    state=meeting_btn_state,
                    command=lambda: self.handle_emergency_meeting(self.current_player)
                )
                style = ttk.Style()
                if meeting_btn_state == "normal":
                    style.configure("Emergency.TButton", 
                                  font=(self.font_family, 12),
                                  padding=(10, 5),
                                  background="#FF9800",
                                  foreground="#FFFFFF")
                    style.map("Emergency.TButton",
                      background=[("active", "#F57C00"),("!active", "#FF9800")],
                      foreground=[("active", "#FFF3E0"),("!active", "#FFFFFF")])
                else:
                    style.configure("Emergency.TButton", 
                                  font=(self.font_family, 12),
                                  padding=(10, 5),
                                  background="#CCCCCC",
                                  foreground="#999999")
                    style.map("Emergency.TButton",
                      background=[("active", "#BBBBBB"),("!active", "#CCCCCC")],
                      foreground=[("active", "#666666"),("!active", "#999999")])
            else:
                # Windows上使用普通按钮
                emergency_meeting_btn = tk.Button(
                    action_frame,
                    text=meeting_btn_text,
                    font=(self.font_family, 12),
                    bg=meeting_btn_bg,
                    fg="#ffffff",
                    padx=10,
                    pady=5,
                    width=15,
                    bd=2,
                    relief="flat",
                    state=meeting_btn_state,
                    command=lambda: self.handle_emergency_meeting(self.current_player)
                )
            emergency_meeting_btn.pack(fill="x", pady=5)
            
            # 根据角色显示不同按钮
            if isinstance(self.current_player.role, Crewmate):
                # 步数超限检查
                if self.action_steps > self.max_steps:
                    task_label = tk.Label(
                        action_frame, 
                        text="⚠️ 行动步数已达上限", 
                        font=(self.font_family, 12),
                        fg="#ff0000",
                        bg="#1a1a2e"
                    )
                    task_label.pack(fill="x", pady=5)
                else:
                    # 为所有平台创建兼容的按钮
                    if sys.platform == 'darwin':
                        # Mac上使用ttk按钮
                        task_button = ttk.Button(
                            action_frame, 
                            text="完成任务", 
                            style="Task.TButton",
                            command=lambda: self.handle_complete_task(self.current_player)
                        )
                        style = ttk.Style()
                        style.configure("Task.TButton", 
                                      font=(self.font_family, 12),
                                      padding=(10, 5),
                                      background="#4CAF50",
                                      foreground="#FFFFFF")
                        style.map("Task.TButton",
                                      background=[("active", "#388E3C"),("!active", "#4CAF50")],
                                      foreground=[("active", "#E8F5E9"),("!active", "#FFFFFF")])
                    else:
                        # Windows上使用普通按钮
                        task_button = tk.Button(
                            action_frame, 
                            text="完成任务", 
                            font=(self.font_family, 12),
                            bg="#4caf50",
                            fg="#ffffff",
                            padx=10,
                            pady=5,
                            width=15,
                            bd=2,
                            relief="flat",
                            command=lambda: self.handle_complete_task(self.current_player)
                        )
                    task_button.pack(fill="x", pady=5)
            elif isinstance(self.current_player.role, Impostor):
                # 内鬼穿梭按钮
                teleport_state = "normal"
                teleport_bg = "#00ffff"
                teleport_fg = "#000000"
                teleport_text = "穿梭"
                
                # 第一回合禁用
                if self.global_round == 1:
                    teleport_state = "disabled"
                    teleport_bg = "#666666"
                    teleport_fg = "#ffffff"
                    teleport_text = "穿梭（第一回合禁用）"
                # 冷却中禁用
                elif self.current_player.name in self.impostor_teleport_cooldown:
                    teleport_state = "disabled"
                    teleport_bg = "#666666"
                    teleport_fg = "#ffffff"
                    teleport_text = f"穿梭（冷却{self.impostor_teleport_cooldown[self.current_player.name]}回合）"
                # 步数超限禁用
                elif self.action_steps > self.max_steps:
                    teleport_state = "disabled"
                    teleport_bg = "#666666"
                    teleport_fg = "#ffffff"
                    teleport_text = "穿梭（步数已达上限）"
                
                # 为所有平台创建兼容的按钮
                if sys.platform == 'darwin':
                    # Mac上使用ttk按钮
                    teleport_button = ttk.Button(
                        action_frame, 
                        text=teleport_text, 
                        style="Teleport.TButton",
                        state=teleport_state,
                        command=lambda: self.teleport_to_room(self.current_player)
                    )
                    style = ttk.Style()
                    if teleport_state == "normal":
                        style.configure("Teleport.TButton", 
                                      font=(self.font_family, 12),
                                      padding=(10, 5),
                                      background="#00FFFF",
                                      foreground="#000000")
                        style.map("Teleport.TButton",
                                      background=[("active", "#00CCCC"), ("disabled", "#CCCCCC"), ("!disabled", "#00FFFF")],
                                      foreground=[("active", "#000000"), ("disabled", "#999999"), ("!disabled", "#000000")])
                    else:
                        style.configure("Teleport.TButton", 
                                      font=(self.font_family, 12),
                                      padding=(10, 5),
                                      background="#CCCCCC",
                                      foreground="#999999")
                        style.map("Teleport.TButton",
                                      background=[("active", "#BBBBBB"), ("disabled", "#CCCCCC"), ("!disabled", "#CCCCCC")],
                                      foreground=[("active", "#666666"), ("disabled", "#999999"), ("!disabled", "#999999")])
                else:
                    # Windows上使用普通按钮
                    teleport_button = tk.Button(
                        action_frame, 
                        text=teleport_text, 
                        font=(self.font_family, 12),
                        bg=teleport_bg,
                        fg=teleport_fg,
                        padx=10,
                        pady=5,
                        width=15,
                        bd=2,
                        relief="flat",
                        state=teleport_state,
                        command=lambda: self.teleport_to_room(self.current_player)
                    )
                teleport_button.pack(fill="x", pady=5)
                
                # 内鬼击杀判定
                if self.current_player.role.current_cooldown == 0 and self.global_round > 1:
                    if self.action_steps > self.max_steps:
                        kill_label = tk.Label(
                            action_frame, 
                            text="⚠️ 行动步数已达上限", 
                            font=(self.font_family, 12),
                            fg="#ff0000",
                            bg="#1a1a2e"
                        )
                        kill_label.pack(fill="x", pady=5)
                    else:
                        # 为所有平台创建兼容的按钮
                        if sys.platform == 'darwin':
                            # Mac上使用ttk按钮
                            kill_button = ttk.Button(
                                action_frame, 
                                text="击杀船员", 
                                style="Kill.TButton",
                                command=lambda: self.handle_kill(self.current_player)
                            )
                            style = ttk.Style()
                            style.configure("Kill.TButton", 
                                          font=(self.font_family, 12),
                                          padding=(10, 5),
                                          background="#E94560",
                                          foreground="#FFFFFF")
                            style.map("Kill.TButton",
                                          background=[("active", "#C62828"),("!active", "#E94560")],
                                          foreground=[("active", "#FFEBEE"),("!active", "#FFFFFF")])
                        else:
                            # Windows上使用普通按钮
                            kill_button = tk.Button(
                                action_frame, 
                                text="击杀船员", 
                                font=(self.font_family, 12),
                                bg="#e94560",
                                fg="#ffffff",
                                padx=10,
                                pady=5,
                                width=15,
                                bd=2,
                                relief="flat",
                                command=lambda: self.handle_kill(self.current_player)
                            )
                        kill_button.pack(fill="x", pady=5)
                elif self.global_round == 1:
                    notice_label = tk.Label(
                        action_frame, 
                        text=f"第一回合内鬼禁止击杀！", 
                        font=(self.font_family, 12),
                        fg="#ff9800",
                        bg="#1a1a2e"
                    )
                    notice_label.pack(fill="x", pady=5)
                else:
                    cooldown_label = tk.Label(
                        action_frame, 
                        text=f"击杀冷却中: {self.current_player.role.current_cooldown}回合", 
                        font=(self.font_family, 12),
                        fg="#ff9800",
                        bg="#1a1a2e"
                    )
                    cooldown_label.pack(fill="x", pady=5)
                
                # 破坏系统按钮步数检查
                if self.action_steps > self.max_steps:
                    sabotage_label = tk.Label(
                        action_frame, 
                        text="⚠️ 行动步数已达上限", 
                        font=(self.font_family, 12),
                        fg="#ff0000",
                        bg="#1a1a2e"
                    )
                    sabotage_label.pack(fill="x", pady=5)
                else:
                    # 为所有平台创建兼容的按钮
                    if sys.platform == 'darwin':
                        # Mac上使用ttk按钮
                        sabotage_button = ttk.Button(
                            action_frame, 
                            text="破坏系统", 
                            style="Sabotage.TButton",
                            command=lambda: self.handle_sabotage(self.current_player)
                        )
                        style = ttk.Style()
                        style.configure("Sabotage.TButton", 
                                      font=(self.font_family, 12),
                                      padding=(10, 5),
                                      background="#9C27B0",
                                      foreground="#FFFFFF")
                        style.map("Sabotage.TButton",
                                      background=[("active", "#7B1FA2"),("!active", "#9C27B0")],
                                      foreground=[("active", "#F3E5F5"),("!active", "#FFFFFF")])
                    else:
                        # Windows上使用普通按钮
                        sabotage_button = tk.Button(
                            action_frame, 
                            text="破坏系统", 
                            font=(self.font_family, 12),
                            bg="#9c27b0",
                            fg="#ffffff",
                            padx=10,
                            pady=5,
                            width=15,
                            bd=2,
                            relief="flat",
                            command=lambda: self.handle_sabotage(self.current_player)
                        )
                    sabotage_button.pack(fill="x", pady=5)
            
                        # 报告尸体按钮（根据尸体清理状态更新）
            has_body = False
            # 检查当前房间是否有未清理的尸体
            for player in self.game.players:
                if not player.is_alive and player.current_location == self.current_player.current_location:
                    if not self.dead_player_locations.get(player.name, {}).get("cleared", False):
                        has_body = True
                        break
            
            # 设置默认值
            report_state = "disabled"
            report_bg = "#666666"
            
            # 如果条件满足，则启用按钮
            if not self.action_steps > self.max_steps and has_body:
                report_state = "normal"
                report_bg = "#ff9800"
            
            # 为所有平台创建兼容的按钮
            if sys.platform == 'darwin':
                # Mac上使用ttk按钮
                report_button = ttk.Button(
                    action_frame, 
                    text="报告尸体", 
                    style="Report.TButton",
                    state=report_state,
                    command=lambda: self.handle_report(self.current_player)
                )
                style = ttk.Style()
                if report_state == "normal":
                    style.configure("Report.TButton", 
                                  font=(self.font_family, 12),
                                  padding=(10, 5),
                                  background="#FF9800",
                                  foreground="#FFFFFF")
                    style.map("Report.TButton",
                                  background=[("active", "#F57C00"),("!active", "#FF9800")],
                                  foreground=[("active", "#FFF3E0"),("!active", "#FFFFFF")])
                else:
                    style.configure("Report.TButton", 
                                  font=(self.font_family, 12),
                                  padding=(10, 5),
                                  background="#CCCCCC",
                                  foreground="#999999")
                    style.map("Report.TButton",
                                  background=[("active", "#BBBBBB"),("!active", "#CCCCCC")],
                                  foreground=[("active", "#666666"),("!active", "#999999")])
                # 禁用状态的特殊处理
                if report_state == "disabled":
                    style.map("Report.TButton",
                                  background=[("disabled", "#CCCCCC")],
                                  foreground=[("disabled", "#999999")])
            else:
                # Windows上使用普通按钮
                report_button = tk.Button(
                    action_frame, 
                    text="报告尸体", 
                    font=(self.font_family, 12),
                    bg=report_bg,
                    fg="#ffffff",
                    padx=10,
                    pady=5,
                    width=15,
                    bd=2,
                    relief="flat",
                    state=report_state,
                    command=lambda: self.handle_report(self.current_player)
                )
            report_button.pack(fill="x", pady=5)
        
        # 结束回合/切换视角按钮（所有玩家都显示，死亡玩家切换旁观视角）
        next_button_text = "切换旁观视角" if self.current_player in self.spectator_players else "结束回合"
        # 为所有平台创建兼容的按钮
        if sys.platform == 'darwin':
            # Mac上使用ttk按钮
            next_button = ttk.Button(
                action_frame, 
                text=next_button_text, 
                style="Next.TButton",
                command=self.switch_to_next_player
            )
            style = ttk.Style()
            style.configure("Next.TButton", 
                          font=(self.font_family, 12),
                          padding=(10, 5),
                          background="#795548",
                          foreground="#FFFFFF")
            style.map("Next.TButton",
                          background=[("active", "#5D4037"),("!active", "#795548")],
                          foreground=[("active", "#EFEBE9"),("!active", "#FFFFFF")])
        else:
            # Windows上使用普通按钮
            next_button = tk.Button(
                action_frame, 
                text=next_button_text, 
                font=(self.font_family, 12),
                bg="#795548",
                fg="#ffffff",
                padx=10,
                pady=5,
                width=15,
                bd=2,
                relief="flat",
                command=self.switch_to_next_player
            )
        next_button.pack(fill="x", pady=5)
        
        # 底部日志区域
        log_frame = tk.LabelFrame(self.game_frame, text="游戏日志", bg="#1a1a2e", fg="#ffffff", font=(self.font_family, 12))
        log_frame.pack(fill="x", padx=20, pady=10)
        
        # 日志文本框
        self.log_text = tk.Text(
            log_frame, 
            height=5, 
            font=(self.font_family, 10),
            bg="#0f0f0f",
            fg="#ffffff",
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text.config(state="disabled")

    def draw_map(self, parent_frame):
        """绘制高分辨率地图，旁观玩家可切换视角但尸体固定（清理后不显示尸体标记）"""
        # 创建一个容器框架来放置地图
        map_frame = tk.Frame(parent_frame, bg="#0f0f0f")
        map_frame.pack(fill="both", expand=True)
        
        # 创建一个Canvas作为背景，只用于绘制连接线
        canvas = tk.Canvas(map_frame, width=800, height=600, bg="#0f0f0f", highlightthickness=0)
        canvas.place(x=0, y=0)
        
        # 定义位置坐标
        location_positions = {
            "飞船大厅": (400, 100),
            "电力室": (275, 400),
            "上升引擎室": (150, 100),
            "下降引擎室": (150, 400),
            "反应堆": (100, 250),
            "氧气室": (600, 100),
            "医疗室": (250, 250),
            "通讯室": (550, 400),
            "监控室": (700, 400),
            "燃料室": (400, 400),
            "主控室": (500, 300)
        }
        
        # 绘制连接线
        for location, connections in self.game.map.connections.items():
            x1, y1 = location_positions[location]
            for connected in connections:
                x2, y2 = location_positions[connected]
                if location < connected:
                    canvas.create_line(x1, y1, x2, y2, fill="#4a4a4a", width=3)
        
        # 获取当前位置（旁观玩家用视角位置，正常玩家用物理位置）
        if self.current_player in self.spectator_players:
            current_location = self.spectator_view_room or self.current_player.current_location
        else:
            current_location = self.current_player.current_location
        
        available_moves = self.game.map.get_available_moves(current_location)
        
        # 创建按钮字典用于存储所有按钮
        self.location_buttons = {}
        
        # 创建舱室按钮
        for location, (x, y) in location_positions.items():
            # 检查该位置是否有未清理的尸体
            has_uncleared_body = False
            for player in self.game.players:
                if not player.is_alive and player.current_location == location:
                    if not self.dead_player_locations.get(player.name, {}).get("cleared", False):
                        has_uncleared_body = True
                        break
            
            # 检查当前视角/位置是否在该位置
            is_current = location == current_location
            # 检查该位置是否可移动
            can_move = location in available_moves
            
            # 旁观玩家：当前位置应该是尸体位置
            if self.current_player in self.spectator_players:
                is_current = location == self.current_player.current_location
            
            # 根据状态设置按钮样式
            if is_current:
                bg_color = "#00ff00"
                fg_color = "#000000"
                state = "disabled"
            else:
                bg_color = "#0f3460"
                fg_color = "#ffffff"
                state = "normal" if can_move else "disabled"
            
            # 旁观玩家：所有房间按钮都可用（仅切换视角）
            if self.current_player in self.spectator_players:
                state = "normal"
            
            # 步数超限则禁用所有移动按钮（仅存活玩家）
            if not self.current_player in self.spectator_players and self.action_steps > self.max_steps and state == "normal":
                state = "disabled"
                bg_color = "#333333"
            
            # 为Mac平台调整颜色
            if sys.platform == 'darwin':
                if is_current:
                    bg_color = "#4CAF50"
                    fg_color = "#000000"
                elif state == "disabled":
                    bg_color = "#333333"
                    fg_color = "#888888"
                
                else:
                    bg_color = "#2196F3"
                    fg_color = "#FFFFFF"
                
                # 为每个按钮创建唯一样式名称
                style_name = f"Map.{location.replace(' ', '_')}.TButton"
                
                # 创建按钮框架 - 使用ttk.Frame
                button_frame = ttk.Frame(
                    map_frame,
                )
                button_frame.place(x=x-35, y=y-20, anchor="center")
                
                # 创建按钮 - Mac上使用ttk按钮
                button = ttk.Button(
                    button_frame, 
                    text=location,
                    style=style_name,
                    state=state,
                    command=lambda loc=location: self.on_location_click(loc)
                )
                # 为ttk按钮设置样式
                button_style = ttk.Style()
                button_style.configure(style_name, 
                              font=(self.font_family, 9, "bold"),
                              padding=(5, 2),
                              background=bg_color,
                              foreground=fg_color)
                if is_current:
                    button_style.map(style_name,
                              background=[("active", "#4CAF50"), ("disabled", "#4CAF50")],
                              foreground=[("active", "#FFFFFF"), ("disabled", "#FFFFFF")])
                elif state == "disabled":
                    button_style.map(style_name,
                              background=[("active", "#BBBBBB"), ("disabled", "#CCCCCC")],
                              foreground=[("active", "#666666"), ("disabled", "#999999")])
                else:
                    button_style.map(style_name,
                              background=[("active", "#1976D2"), ("!active", bg_color)],
                              foreground=[("active", fg_color), ("!active", fg_color)])
                button.pack(fill="both", expand=True)
            else:
                # Windows和其他平台保持原有样式
                button_frame = tk.Frame(
                    map_frame, 
                    bg=bg_color, 
                    width=50, 
                    height=50,
                    highlightbackground="#ffffff",
                    highlightthickness=2,
                    bd=0
                )
                button_frame.place(x=x-25, y=y-25, anchor="center")
                
                button = tk.Button(
                    button_frame, 
                    text=location, 
                    bg=bg_color,
                    fg=fg_color,
                    font=(self.font_family, 10, "bold"),
                    width=8,
                    height=2,
                    bd=0,
                    relief="flat",
                    state=state,
                    command=lambda loc=location: self.on_location_click(loc)
                )
                button.pack(fill="both", expand=True)
            
            # 存储按钮引用
            self.location_buttons[location] = button
            
            # 标记自己的尸体（如果未清理）
            if self.current_player in self.spectator_players and location == self.current_player.current_location:
                body_cleared = self.dead_player_locations.get(self.current_player.name, {}).get("cleared", False)
                if not body_cleared:
                    canvas.create_text(x, y+30, text="🪦", font=("Arial", 20), fill="#ff6666")

    def on_location_click(self, location):
        """处理舱室按钮点击事件（旁观玩家仅切换视角，尸体固定）"""
        current_player = self.current_player
        
        # 旁观玩家：仅切换视角，不移动尸体/玩家本体
        if current_player in self.spectator_players:
            self.spectator_view_room = location
            body_cleared = self.dead_player_locations.get(current_player.name, {}).get("cleared", False)
            body_status = "（尸体已清理）" if body_cleared else f"（尸体仍在{current_player.current_location}）"
            self.add_log(f"👻 {current_player.name}(旁观)切换视角到{location} {body_status}")
            self.create_game_frame()
            return
        
        # 存活玩家：消耗步数移动
        if self.action_steps > self.max_steps:
            messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n无法移动")
            return
        
        # 执行移动（消耗步数）
        if self.add_action_step():
            current_player.move(location)
            self.add_log(f"{current_player.name}移动到了{location}")
            # 重新绘制地图以更新状态
            self.create_game_frame()

    def create_task_list(self):
        """创建任务列表显示区域（旁观模式显示所有玩家信息）"""
        task_frame = tk.Frame(self.game_frame, bg="#1a1a2e")
        task_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 任务标题
        task_label = tk.Label(
            task_frame, 
            text="任务列表 / 旁观信息", 
            font=(self.font_family, 14, "bold"),
            fg="#e94560",
            bg="#1a1a2e"
        )
        task_label.pack(pady=5)
        
        # 任务列表框
        self.task_listbox = tk.Listbox(
            task_frame,
            font=(self.font_family, 12),
            bg="#0f3460",
            fg="#ffffff",
            selectbackground="#e94560",
            width=30,
            height=8
        )
        self.task_listbox.pack(fill="both", expand=True, pady=5)
        
        # 更新任务列表
        self.update_task_list()
    
    def update_task_list(self):
        """更新任务列表显示（旁观模式显示所有玩家信息）"""
        if not hasattr(self, 'task_listbox'):
            return
        
        self.task_listbox.delete(0, tk.END)
        current_player = self.current_player
        
        # 旁观模式：显示所有玩家的完整信息 + 尸体状态
        if current_player in self.spectator_players:
            self.task_listbox.insert(tk.END, "👻 旁观视角 - 所有玩家信息")
            self.task_listbox.insert(tk.END, "────────────────────")
            
            # 显示每个玩家的详细信息
            for p in self.all_players_list:
                role_name = p.role.__class__.__name__
                status = "🟢存活" if p.is_alive else "🔴死亡"
                if p in self.spectator_players:
                    body_cleared = self.dead_player_locations.get(p.name, {}).get("cleared", False)
                    if body_cleared:
                        status += f"👻旁观 | 尸体已清理"
                    else:
                        status += f"👻旁观 | 尸体位置：{p.current_location}"
                
                # 船员显示任务进度，内鬼显示身份
                if isinstance(p.role, Crewmate):
                    task_info = f"任务进度: {p.completed_tasks}/3"
                    self.task_listbox.insert(tk.END, f"{p.name}: {role_name} {status} | {task_info}")
                else:
                    self.task_listbox.insert(tk.END, f"{p.name}: {role_name} {status}")
            
            # 显示氧气系统状态
            self.task_listbox.insert(tk.END, "────────────────────")
            if self.oxygen_sabotaged and not self.oxygen_repaired:
                self.task_listbox.insert(tk.END, f"⚠️ 氧气系统已破坏！剩余修复回合：{self.oxygen_remaining_rounds}")
                self.task_listbox.itemconfig(self.task_listbox.size() - 1, fg="#ff0000")
            else:
                self.task_listbox.insert(tk.END, "✅ 氧气系统正常")
            return
        
        # 正常模式：显示当前玩家的任务
        # 核心修改2：氧气破坏时添加临时任务，修复后移除
        if self.oxygen_sabotaged and not self.oxygen_repaired and isinstance(current_player.role, Crewmate):
            self.task_listbox.insert(tk.END, "🚨 临时紧急任务：修复氧气系统 (氧气室)")
            self.task_listbox.insert(tk.END, f"⏰ 剩余修复回合：{self.oxygen_remaining_rounds} (共2回合)")
            self.task_listbox.insert(tk.END, "────────────────────")
            # 标记紧急任务行
            self.task_listbox.itemconfig(0, fg="#ff0000")
            self.task_listbox.itemconfig(1, fg="#ffcc00")
        
        # 仅显示常规任务（固定3个）
        if hasattr(current_player, 'tasks') and current_player.tasks:
            task_count = 0
            for task in current_player.tasks:
                if task_count >= 3:
                    break
                status = "✓" if task.is_completed else "✗"
                difficulty_stars = "★" * getattr(task, 'difficulty', 1)
                self.task_listbox.insert(tk.END, f"{status} 常规任务：{task.name} ({task.location}) {difficulty_stars}")
                task_count += 1
        else:
            self.task_listbox.insert(tk.END, "无常规任务")
    
    def handle_complete_task(self, player):
        """
        处理玩家完成任务的核心函数
        - 优先处理临时氧气修复任务（不占用常规任务数）
        - 常规任务仅需完成3个即可获胜
        - 集成新版氧气管道修复任务
        """
        # 旁观玩家无法完成任务
        if player in self.spectator_players:
            messagebox.showwarning("旁观限制", "❌ 旁观模式下无法完成任务！")
            return
        
        # 步数超限检查
        if self.action_steps > self.max_steps:
            messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n无法完成任务")
            return
        
        # 紧急氧气修复任务优先级处理
        current_loc = player.current_location.replace("室", "").replace("区", "").replace("房", "")
        if self.oxygen_sabotaged and not self.oxygen_repaired and isinstance(player.role, Crewmate) and current_loc == "氧气":
            confirm = messagebox.askyesno("紧急任务", "🚨 氧气系统已被破坏！是否立即修复氧气系统？\n(临时任务，不占用3个常规任务数量)", parent=self.root)
            if confirm:
                oxygen_task = OxygenRepairTask()
                task_completed = oxygen_task.run_task_gui(main_root=self.root)
                
                if task_completed:
                    self.oxygen_repaired = True
                    self.oxygen_sabotaged = False
                    self.add_log(f"🚨 {player.name}完成临时紧急任务：修复了被破坏的氧气系统！")
                    
                    self.action_steps += 1
                    self.update_task_list()
                    self.create_game_frame()
                    messagebox.showinfo("任务完成", "✅ 成功修复氧气系统！\n临时紧急任务已完成，不影响常规任务进度", parent=self.root)
                else:
                    messagebox.showinfo("任务取消", "❌ 已取消氧气系统修复任务！", parent=self.root)
            return
        
        # 原有常规任务逻辑
        has_available_task = False
        target_task = None
        task_executed = False
        task_completed = False
        task_name = "未知任务"
        
        current_loc = player.current_location.replace("室", "").replace("区", "").replace("房", "")
        
        if hasattr(player, 'tasks') and player.tasks:
            for task in player.tasks:
                if not task.is_completed:
                    task_loc = getattr(task, 'location', '').replace("室", "").replace("区", "").replace("房", "")
                    if task_loc == current_loc:
                        has_available_task = True
                        target_task = task
                        break
        
        if not has_available_task:
            messagebox.showinfo("无法完成任务", f"当前位置{player.current_location}没有可完成的常规任务", parent=self.root)
            return
        
        # 匹配具体常规任务
        wire_fix_task = None
        filter_clean_task = None
        body_scan_task = None
        download_data_task = None
        calibrate_down_engine_task = None
        calibrate_up_engine_task = None
        repair_reactor_task = None
        fuel_supply_task = None
        start_satellite_task = None
        morse_code_task = None
        normal_task = None
        
        for task in player.tasks:
            if not task.is_completed:
                task_loc = getattr(task, 'location', '').replace("室", "").replace("区", "").replace("房", "")
                if task_loc == current_loc:
                    if isinstance(task, WireFixTask) and current_loc == "电力":
                        wire_fix_task = task
                    elif hasattr(task, 'name') and task.name == "清理过滤器" and current_loc == "氧气":
                        filter_clean_task = task
                    elif hasattr(task, 'name') and task.name == "扫描身体" and current_loc == "医疗":
                        body_scan_task = task
                    elif hasattr(task, 'name') and task.name == "下载数据" and current_loc == "通讯":
                        download_data_task = task
                    elif hasattr(task, 'name') and "下降引擎" in task.name and current_loc == "下降引擎":
                        calibrate_down_engine_task = task
                    elif hasattr(task, 'name') and "上升引擎" in task.name and current_loc == "上升引擎":
                        calibrate_up_engine_task = task
                    elif hasattr(task, 'name') and "反应堆" in task.name and current_loc == "反应堆":
                        repair_reactor_task = task
                    elif hasattr(task, 'name') and "燃料" in task.name and current_loc == "燃料":
                        fuel_supply_task = task
                    elif hasattr(task, 'name') and "卫星" in task.name and current_loc == "监控":
                        start_satellite_task = task
                    elif hasattr(task, 'name') and "摩斯密码" in task.name and current_loc == "主控":
                        morse_code_task = task
                    elif normal_task is None:
                        normal_task = task
        
        # 执行具体常规任务
        if wire_fix_task:
            task_executed = True
            task_name = wire_fix_task.name
            task_completed = wire_fix_task.run_task_gui(main_root=self.root)
        
        elif filter_clean_task:
            task_executed = True
            task_name = filter_clean_task.name
            try:
                task_completed = filter_clean_task.run_task_gui(main_root=self.root)
            except Exception as e:
                print(f"清理过滤器任务异常：{str(e)}")
                messagebox.showerror("任务异常", f"清理过滤器任务执行出错：{str(e)}", parent=self.root)
        
        elif body_scan_task:
            task_executed = True
            task_name = body_scan_task.name
            try:
                task_completed = body_scan_task.run_task_gui(main_root=self.root)
            except Exception as e:
                print(f"扫描身体任务异常：{str(e)}")
                messagebox.showerror("任务异常", f"扫描身体任务执行出错：{str(e)}", parent=self.root)
        
        elif download_data_task:
            task_executed = True
            task_name = download_data_task.name
            try:
                task_completed = download_data_task.run_task_gui(main_root=self.root)
            except Exception as e:
                print(f"下载数据任务异常：{str(e)}")
                messagebox.showerror("任务异常", f"下载数据任务执行出错：{str(e)}", parent=self.root)
        
        elif calibrate_down_engine_task:
            task_executed = True
            task_name = calibrate_down_engine_task.name
            try:
                task_completed = calibrate_down_engine_task.run_task_gui(main_root=self.root)
            except Exception as e:
                print(f"校准下降引擎任务异常：{str(e)}")
                messagebox.showerror("任务异常", f"校准下降引擎任务执行出错：{str(e)}", parent=self.root)
        
        elif calibrate_up_engine_task:
            task_executed = True
            task_name = calibrate_up_engine_task.name
            max_retries = 2
            retry_count = 0
            while retry_count < max_retries and not task_completed:
                try:
                    task_completed = calibrate_up_engine_task.run_task_gui(main_root=self.root)
                    if not task_completed and retry_count < max_retries - 1:
                        messagebox.showinfo("提示", "上升引擎任务窗口未正常打开，正在重试...", parent=self.root)
                except Exception as e:
                    print(f"上升引擎任务失败（重试{retry_count+1}）：{str(e)}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        messagebox.showerror("任务失败", f"上升引擎任务执行失败：{str(e)}", parent=self.root)
        
        elif repair_reactor_task:
            task_executed = True
            task_name = repair_reactor_task.name
            max_retries = 2
            retry_count = 0
            while retry_count < max_retries and not task_completed:
                try:
                    task_completed = repair_reactor_task.run_task_gui(main_root=self.root)
                    if not task_completed and retry_count < max_retries - 1:
                        messagebox.showinfo("提示", "反应堆任务窗口未正常打开，正在重试...", parent=self.root)
                except Exception as e:
                    print(f"反应堆任务失败（重试{retry_count+1}）：{str(e)}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        messagebox.showerror("任务失败", f"反应堆任务执行失败：{str(e)}", parent=self.root)
        
        elif fuel_supply_task:
            task_executed = True
            task_name = fuel_supply_task.name
            try:
                task_completed = fuel_supply_task.run_task_gui(main_root=self.root)
            except Exception as e:
                print(f"燃料补给任务异常：{str(e)}")
                messagebox.showerror("任务异常", f"燃料补给任务执行出错：{str(e)}", parent=self.root)
        
        elif start_satellite_task:
            task_executed = True
            task_name = start_satellite_task.name
            try:
                task_completed = start_satellite_task.run_task_gui(main_root=self.root)
            except Exception as e:
                print(f"启动卫星任务异常：{str(e)}")
                messagebox.showerror("任务异常", f"启动卫星任务执行出错：{str(e)}", parent=self.root)
                
        elif morse_code_task:
            task_executed = True
            task_name = morse_code_task.name
            try:
                task_completed = morse_code_task.run_task_gui(main_root=self.root)
            except Exception as e:
                print(f"摩斯密码任务异常：{str(e)}")
                messagebox.showerror("任务异常", f"摩斯密码任务执行出错：{str(e)}", parent=self.root)
                
        elif normal_task:
            task_executed = True
            task_name = normal_task.name
            confirm = messagebox.askyesno("确认完成任务", f"是否确认完成常规任务【{task_name}】？", parent=self.root)
            if confirm:
                task_completed = normal_task.complete()
            else:
                task_completed = False
        
        else:
            if target_task and isinstance(target_task, (
                WireFixTask, FilterCleanTask, BodyScanTask,
                DownloadDataTask, CalibrateDownEngineTask, CalibrateUpEngineTask,
                RepairReactorTask, RefuelTask, StartSatelliteTask, MorseCodeTask
            )):
                task_executed = True
                task_name = target_task.name
                try:
                    task_completed = target_task.run_task_gui(main_root=self.root)
                except Exception as e:
                    print(f"兜底执行任务异常：{str(e)}")
                    messagebox.showerror("任务异常", f"任务执行出错：{str(e)}", parent=self.root)
            else:
                messagebox.showinfo("无法完成任务", "未找到可执行的图形化常规任务", parent=self.root)
                return
        
        # 常规任务完成后处理
        if task_executed and task_completed:
            self.action_steps += 1
            
            if wire_fix_task:
                wire_fix_task.is_completed = True
            elif filter_clean_task:
                filter_clean_task.is_completed = True
            elif body_scan_task:
                body_scan_task.is_completed = True
            elif download_data_task:
                download_data_task.is_completed = True
            elif calibrate_down_engine_task:
                calibrate_down_engine_task.is_completed = True
            elif calibrate_up_engine_task:
                calibrate_up_engine_task.is_completed = True
            elif repair_reactor_task:
                repair_reactor_task.is_completed = True
            elif fuel_supply_task:
                fuel_supply_task.is_completed = True
            elif start_satellite_task:
                start_satellite_task.is_completed = True
            elif morse_code_task:
                morse_code_task.is_completed = True
            elif normal_task:
                normal_task.is_completed = True
            
            if player.completed_tasks < 3:
                player.completed_tasks += 1
            
            self.add_log(f"✅ {player.name}完成了常规任务【{task_name}】！当前进度：{player.completed_tasks}/3")
            self.update_task_list()
            
            # 检查是否所有常规任务完成
            all_tasks_completed = all(
                p.completed_tasks >= 3 
                for p in self.game.players 
                if p.is_alive and isinstance(p.role, Crewmate)
            )
            
            if all_tasks_completed:
                self.game.winner = "crewmate"
                self.game.game_over = True
                self.show_game_over()
            else:
                progress = f"{player.completed_tasks}/3"
                messagebox.showinfo(
                    "任务完成", 
                    f"✅ 成功完成常规任务【{task_name}】！\n当前常规任务进度：{progress}", 
                    parent=self.root
                )
                
                if self.action_steps > self.max_steps and not self.game.game_over:
                    messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n自动切换至下一位玩家")
                    self.switch_to_next_player()
        elif task_executed and not task_completed:
            messagebox.showinfo("任务取消", f"❌ 已取消常规任务【{task_name}】！", parent=self.root)
    
    def handle_kill(self, impostor):
        """处理击杀操作"""
        if self.action_steps > self.max_steps:
            messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n无法执行击杀")
            return
        
        targets = [p for p in self.game.players 
                if p.is_alive and p != impostor and 
                p.current_location == impostor.current_location and 
                not isinstance(p.role, Impostor)]
        
        if not targets:
            messagebox.showinfo("无法击杀", "当前位置没有可击杀的船员")
            return
        
        # 创建击杀选择对话框
        kill_window = tk.Toplevel(self.root)
        kill_window.title("选择击杀目标")
        kill_window.geometry("1000x750+460+165")
        kill_window.configure(bg="#1a1a2e")
        kill_window.transient(self.root)
        kill_window.grab_set()
        
        label = tk.Label(
            kill_window, 
            text="请选择要击杀的目标:", 
            font=(self.font_family, 14),
            fg="#e94560",
            bg="#1a1a2e"
        )
        label.pack(pady=15)
        
        target_listbox = tk.Listbox(
            kill_window, 
            font=(self.font_family, 12),
            bg="#0f3460",
            fg="#ffffff",
            selectbackground="#e94560",
            width=25, height=10
        )
        target_listbox.pack(pady=10, padx=20)
        
        for target in targets:
            target_listbox.insert(tk.END, target.name)
        
        def confirm_kill():
            if target_listbox.curselection():
                selected_index = target_listbox.curselection()[0]
                target = targets[selected_index]
                
                if self.global_round == 1:
                    messagebox.showerror("操作拦截", "⚠️ 第1回合内鬼禁止杀人！\n请等待所有玩家轮完第一回合后再进行操作")
                    kill_window.destroy()
                    return
                
                self.action_steps += 1
                impostor.kill(target)
                self.add_log(f"⚠️ {impostor.name}击杀了{target.name}！")
                
                kill_window.destroy()
                
                if self.game.check_game_over():
                    self.show_game_over()
                else:
                    if self.action_steps > self.max_steps:
                        messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n自动切换至下一位玩家")
                        self.switch_to_next_player()
                    else:
                        self.create_game_frame()
            else:
                messagebox.showwarning("警告", "请选择一个目标")

        button_frame = tk.Frame(kill_window, bg="#1a1a2e")
        button_frame.pack(pady=15)

        if sys.platform == 'darwin':
            confirm_btn = ttk.Button(
                button_frame, 
                text="确认击杀", 
                style="ConfirmKill.TButton",
                command=confirm_kill
            )
            cancel_btn = ttk.Button(
                button_frame, 
                text="取消", 
                style="CancelKill.TButton",
                command=kill_window.destroy
            )
            style = ttk.Style()
            style.configure("ConfirmKill.TButton", 
                          font=(self.font_family, 12),
                          padding=(20, 5),
                          background="#E94560",
                          foreground="#FFFFFF")
            style.map("ConfirmKill.TButton",
                          background=[("active", "#C62828"),("!active", "#E94560")],
                          foreground=[("active", "#FFEBEE"),("!active", "#FFFFFF")])
            style.configure("CancelKill.TButton", 
                          font=(self.font_family, 12),
                          padding=(20, 5),
                          background="#F44336",
                          foreground="#FFFFFF")
            style.map("CancelKill.TButton",
                          background=[("active", "#D32F2F"),("!active", "#F44336")],
                          foreground=[("active", "#FFEBEE"),("!active", "#FFFFFF")])
        else:
            confirm_btn = tk.Button(
                button_frame, 
                text="确认击杀", 
                font=(self.font_family, 12),
                bg="#e94560",
                fg="#ffffff",
                padx=20,
                command=confirm_kill
            )
            cancel_btn = tk.Button(
                button_frame, 
                text="取消", 
                font=(self.font_family, 12),
                bg="#f44336",
                fg="#ffffff",
                padx=20,
                command=kill_window.destroy
            )
        confirm_btn.pack(side="left", padx=10)
        cancel_btn.pack(side="left", padx=10)

    def handle_sabotage(self, player):
        """处理破坏系统操作"""
        if self.action_steps > self.max_steps:
            messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n无法破坏系统")
            return
        
        self.oxygen_sabotaged = True
        self.oxygen_sabotage_round = self.global_round
        self.oxygen_repaired = False
        self.oxygen_remaining_rounds = self.oxygen_timeout_rounds
        
        self.action_steps += 1
        
        player.role.sabotage("氧气")
        self.add_log(f"🔧 {player.name}在第{self.global_round}回合破坏了氧气系统！船员仅有{self.oxygen_remaining_rounds}个回合修复时间！")
        
        messagebox.showinfo("破坏成功", f"⚠️ 氧气系统已被破坏！\n船员仅有{self.oxygen_remaining_rounds}个回合修复时间，超时则内鬼直接胜利！\n该任务不占用3个常规任务数量")
        
        if self.action_steps > self.max_steps:
            messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n自动切换至下一位玩家")
            self.switch_to_next_player()
        else:
            self.create_game_frame()

    def handle_report(self, player):
        """处理报告尸体操作"""
        if self.action_steps > self.max_steps:
            messagebox.showinfo("行动限制", "⚠️ 您的行动步数已达上限！\n无法报告尸体")
            return
        
        # 检查当前位置是否有尸体
        dead_players_at_location = [p for p in self.game.players 
                                  if not p.is_alive and p.current_location == player.current_location]
        
        if not dead_players_at_location:
            messagebox.showinfo("报告尸体", "⚠️ 当前位置没有尸体可报告")
            return
        
        # 过滤掉已经被报告过或被投票出去的尸体
        available_bodies = []
        for p in dead_players_at_location:
            status = self.reported_bodies.get(p.name)
            # 只有没有被记录过（None）的尸体才可以报告
            if status is None:
                available_bodies.append(p)
        
        if not available_bodies:
            messagebox.showinfo("报告尸体", "⚠️ 该位置的所有尸体都已经被报告过或被投票出去了")
            return
        
        # 如果只有一个尸体，直接报告；如果有多个，让玩家选择
        if len(available_bodies) == 1:
            victim = available_bodies[0]
            self._execute_report(player, victim)
        else:
            self._show_body_selection(player, available_bodies)
    
    def _show_body_selection(self, player, available_bodies):
        """显示尸体选择界面"""
        selection_window = tk.Toplevel(self.root)
        selection_window.title("选择要报告的尸体")
        selection_window.geometry("800x600+500+300")
        selection_window.configure(bg="#1a1a2e")
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        label = tk.Label(
            selection_window, 
            text=f"当前位置有多个尸体，请选择要报告哪一个：", 
            font=(self.font_family, 12),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        label.pack(pady=15)
        
        # 创建尸体选择列表
        body_listbox = tk.Listbox(
            selection_window, 
            font=(self.font_family, 12),
            bg="#0f3460",
            fg="#ffffff",
            selectbackground="#2196f3",
            width=30, height=8
        )
        body_listbox.pack(pady=10, padx=20)
        
        for body in available_bodies:
            if self.reported_bodies.get(body.name) is None:
                body_listbox.insert(tk.END, f"{body.name}")
        
        # 创建按钮框架
        button_frame = tk.Frame(selection_window, bg="#1a1a2e")
        button_frame.pack(pady=15)
        
        def confirm_selection():
            if body_listbox.curselection():
                selected_index = body_listbox.curselection()[0]
                victim = available_bodies[selected_index]
                selection_window.destroy()
                self._execute_report(player, victim)
            else:
                messagebox.showwarning("警告", "请选择一个尸体")
        
        if sys.platform == 'darwin':
            confirm_btn = ttk.Button(
                button_frame,
                text="确认报告", 
                style="ConfirmReport.TButton",
                command=confirm_selection
            )
            cancel_btn = ttk.Button(
                button_frame,
                text="取消", 
                style="CancelReport.TButton",
                command=selection_window.destroy
            )
            style = ttk.Style()
            style.configure("ConfirmReport.TButton", 
                          font=(self.font_family, 12),
                          padding=(20, 5),
                          background="#4CAF50",
                          foreground="#FFFFFF")
            style.map("ConfirmReport.TButton",
                          background=[("active", "#388E3C"),("!active", "#4CAF50")],
                          foreground=[("active", "#E8F5E9"),("!active", "#FFFFFF")])
            style.configure("CancelReport.TButton", 
                          font=(self.font_family, 12),
                          padding=(20, 5),
                          background="#F44336",
                          foreground="#FFFFFF")
            style.map("CancelReport.TButton",
                          background=[("active", "#D32F2F"),("!active", "#F44336")],
                          foreground=[("active", "#FFEBEE"),("!active", "#FFFFFF")])
        else:
            confirm_btn = tk.Button(
                button_frame,
                text="确认报告", 
                font=(self.font_family, 12),
                bg="#4caf50",
                fg="#ffffff",
                padx=20,
                command=confirm_selection
            )
            cancel_btn = tk.Button(
                button_frame,
                text="取消", 
                font=(self.font_family, 12),
                bg="#f44336",
                fg="#ffffff",
                padx=20,
                command=selection_window.destroy
            )
        confirm_btn.pack(side="left", padx=10)
        cancel_btn.pack(side="left", padx=10)
    
    def _execute_report(self, player, victim):
        """执行尸体报告操作"""
        self.action_steps += 1
        
        # 记录已报告的尸体（基于玩家名称，而不是位置）
        self.reported_bodies[victim.name] = "reported"
        
        # 执行报告逻辑
        result = player.report_dead_body()
        self.discussion_phase(player, victim)

    def next_player_turn(self):
        """兼容旧代码"""
        self.switch_to_next_player()

    def discussion_phase(self, reporter, victim):  
        """讨论阶段"""
        # 清除所有现有组件
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 创建讨论阶段界面
        discussion_frame = tk.Frame(self.root, bg="#16213e")
        discussion_frame.pack(fill="both", expand=True)
        
        # 标题
        title_label = tk.Label(
            discussion_frame, 
            text="讨论阶段", 
            font=(self.font_family, 24, "bold"),
            fg="#e94560",
            bg="#16213e"
        )
        title_label.pack(pady=30)
        
        # 讨论区域
        discussion_text = tk.Text(
            discussion_frame, 
            height=10, 
            font=(self.font_family, 12),
            bg="#0f3460",
            fg="#ffffff",
            wrap="word"
        )
        discussion_text.pack(fill="x", padx=50, pady=10)
        
        # 区分紧急会议和报告尸体的讨论标题
        if victim:
            discussion_text.insert(tk.END, f"{reporter.name}报告了{victim.name}的尸体！请玩家们讨论谁是内鬼。\n")
        else:
            discussion_text.insert(tk.END, f"{reporter.name}发起了紧急会议！请玩家们讨论谁是内鬼。\n")
        
        # 投票结果字典
        votes = {}
        
        # 为每个存活玩家显示投票选项（顺序投票版）
        def collect_votes():
            votes.clear()
            alive_players = [p for p in self.game.players if p.is_alive]
            current_voter_index = [0]
            
            def vote_next_player():
                if current_voter_index[0] >= len(alive_players):
                    show_vote_results()
                    return
                
                voter = alive_players[current_voter_index[0]]
                
                # 创建投票对话框
                vote_window = tk.Toplevel(self.root)
                vote_window.title(f"{voter.name}的投票")
                vote_window.geometry("1000x750+460+165")
                vote_window.configure(bg="#1a1a2e")
                vote_window.transient(self.root)
                vote_window.grab_set()
                
                label = tk.Label(
                    vote_window, 
                    text=f"{voter.name}，请选择要投票的玩家:", 
                    font=(self.font_family, 12),
                    fg="#ffffff",
                    bg="#1a1a2e"
                )
                label.pack(pady=15)
                
                # 创建投票选项列表
                vote_listbox = tk.Listbox(
                    vote_window, 
                    font=(self.font_family, 12),
                    bg="#0f3460",
                    fg="#ffffff",
                    selectbackground="#2196f3",
                    width=25, height=10
                )
                vote_listbox.pack(pady=10, padx=20)
                vote_listbox.insert(tk.END, "跳过投票")
                
                for suspect in alive_players:
                    vote_listbox.insert(tk.END, suspect.name)
                
                # 创建按钮框架
                button_frame = tk.Frame(vote_window, bg="#1a1a2e")
                button_frame.pack(pady=15)
                
                # 确认投票函数
                def confirm_vote():
                    if vote_listbox.winfo_exists() and vote_listbox.curselection():
                        selected_index = vote_listbox.curselection()[0]
                        if selected_index == 0:
                            voter.vote(None)
                            votes["跳过"] = votes.get("跳过", 0) + 1
                        else:
                            selected_name = vote_listbox.get(selected_index)
                            suspect = next(p for p in alive_players if p.name == selected_name)
                            voter.vote(suspect)
                            votes[selected_name] = votes.get(selected_name, 0) + 1
                        
                        vote_window.destroy()
                        current_voter_index[0] += 1
                        vote_next_player()
                    else:
                        messagebox.showwarning("警告", "请做出选择")
                
                # 创建确认按钮
                if sys.platform == 'darwin':
                    # Mac上使用ttk按钮
                    confirm_btn = ttk.Button(
                        button_frame,
                        text="确认投票", 
                        style="ConfirmVote.TButton",
                        command=confirm_vote
                    )
                    style = ttk.Style()
                    style.configure("ConfirmVote.TButton", 
                                  font=(self.font_family, 12),
                                  padding=(20, 5),
                                  background="#4CAF50",
                                  foreground="#FFFFFF")
                    style.map("ConfirmVote.TButton",
                                  background=[("active", "#388E3C"),("!active", "#4CAF50")],
                                  foreground=[("active", "#E8F5E9"),("!active", "#FFFFFF")])
                else:
                    # Windows上使用普通按钮
                    confirm_btn = tk.Button(
                        button_frame,
                        text="确认投票", 
                        font=(self.font_family, 12),
                        bg="#4caf50",
                        fg="#ffffff",
                        padx=20,
                        command=confirm_vote
                    )
                confirm_btn.pack()
            
            vote_next_player()

        # 显示投票结果
        def show_vote_results():
            # 清除投票区域
            for widget in discussion_frame.winfo_children():
                widget.destroy()
            
            if votes:
                result_text = "投票结果:\n"
                for name, count in votes.items():
                    result_text += f"{name}: {count} 票\n"
                
                result_label = tk.Label(
                    discussion_frame, 
                    text=result_text, 
                    font=(self.font_family, 12),
                    fg="#ffffff",
                    bg="#1a1a2e",
                    justify="left"
                )
                result_label.pack(pady=10, padx=20)
                
                # 找出得票最多的人（排除跳过选项）
                player_votes = {k: v for k, v in votes.items() if k != "跳过"}
                if player_votes:
                    max_votes = max(player_votes.values())
                    suspects = [name for name, count in player_votes.items() if count == max_votes]
                    
                    if len(suspects) == 1:
                        ejected_player = next(p for p in self.game.players if p.name == suspects[0])
                        result_text = f"⚠️ {ejected_player.name}被多数票选出，将被流放！\n"
                        result_text += f"{ejected_player.name}的真实身份是: {ejected_player.role.__class__.__name__}"
                        
                        self.reported_bodies[ejected_player.name] = "voted_out"
                        # 流放玩家
                        ejected_player.is_alive = False
                        
                    else:
                        result_text = "票数相同，没有人被流放"
                    
                    result_label = tk.Label(
                        discussion_frame, 
                        text=result_text, 
                        font=(self.font_family, 12, "bold"),
                        fg="#ffcc00",
                        bg="#1a1a2e",
                        justify="left"
                    )
                    result_label.pack(pady=10, padx=20)
            else:
                result_label = tk.Label(
                    discussion_frame, 
                    text="所有人都跳过了投票", 
                    font=(self.font_family, 12),
                    fg="#ffffff",
                    bg="#1a1a2e"
                )
                result_label.pack(pady=10, padx=20)
            
            # 检查游戏是否结束（直接跳结算）
            if self.game.check_game_over():
                start_vote_button.destroy()
                self.show_game_over()
            else:
                # 继续游戏按钮
                start_vote_button.destroy()
                if sys.platform == 'darwin':
                    continue_button = ttk.Button(
                        discussion_frame, 
                        text="继续游戏", 
                        style="ContinueGame.TButton",
                        command=self.create_game_frame
                    )
                    style = ttk.Style()
                    style.configure("ContinueGame.TButton", 
                                  font=(self.font_family, 14),
                                  padding=(30, 10),
                                  background="#2196F3",
                                  foreground="#FFFFFF")
                    style.map("ContinueGame.TButton",
                                  background=[("active", "#1976D2"),("!active", "#2196F3")],
                                  foreground=[("active", "#E3F2FD"),("!active", "#FFFFFF")])
                else:
                    continue_button = tk.Button(
                        discussion_frame, 
                        text="继续游戏", 
                        font=(self.font_family, 14),
                        bg="#2196f3",
                        fg="#ffffff",
                        padx=30,
                        pady=10,
                        command=self.create_game_frame
                    )
                continue_button.pack(pady=20)
                
        
        # 开始投票按钮
        if sys.platform == 'darwin':
            # Mac上使用ttk按钮
            start_vote_button = ttk.Button(
                discussion_frame, 
                text="开始投票", 
                style="StartVote.TButton",
                command=collect_votes
            )
            style = ttk.Style()
            style.configure("StartVote.TButton", 
                          font=(self.font_family, 14),
                          padding=(30, 10),
                          background="#FF9800",
                          foreground="#FFFFFF")
            style.map("StartVote.TButton",
                          background=[("active", "#FF9800"),("!active", "#FF9800")],
                          foreground=[("active", "#FFFFFF"),("!active", "#FFFFFF")])
        else:
            # Windows上使用普通按钮
            start_vote_button = tk.Button(
                discussion_frame, 
                text="开始投票", 
                font=(self.font_family, 14),
                bg="#ff9800",
                fg="#ffffff",
                padx=30,
                pady=10,
                command=collect_votes
            )
        start_vote_button.pack(pady=20)
                
    def show_game_over(self):
        """显示游戏结束结算界面（直接跳转，无多余弹窗）"""
        # 清除所有现有组件
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 创建游戏结束界面
        game_over_frame = tk.Frame(self.root, bg="#16213e")
        game_over_frame.pack(fill="both", expand=True)
        
        # 标题
        title_text = "游戏结束"
        title_label = tk.Label(
            game_over_frame, 
            text=title_text, 
            font=(self.font_family, 36, "bold"),
            fg="#e94560",
            bg="#16213e"
        )
        title_label.pack
        
        # 胜利方
        winner_text = f"胜利方: {'船员' if self.game.winner == 'crewmate' else '内鬼'}"
        winner_color = "#00ff00" if self.game.winner == 'crewmate' else "#e94560"
        
        winner_label = tk.Label(
            game_over_frame, 
            text=winner_text, 
            font=(self.font_family, 24, "bold"),
            fg=winner_color,
            bg="#16213e"
        )
        winner_label.pack(pady=30)
        
        # 显示结束原因（重点标注氧气超时）
        reason_text = ""
        if self.oxygen_sabotaged and not self.oxygen_repaired:
            reason_text = f"⚠️ 氧气系统在第{self.oxygen_sabotage_round}回合被破坏，船员未在2个回合内完成修复，内鬼胜利！"
        elif self.game.winner == "crewmate":
            reason_text = "🎉 所有船员完成3个常规任务，船员胜利！"
        else:
            reason_text = "⚠️ 内鬼击杀足够多船员，人数占优，内鬼胜利！"
        
        if reason_text:
            reason_label = tk.Label(
                game_over_frame,
                text=reason_text,
                font=(self.font_family, 16),
                fg="#ffcc00" if self.game.winner == "crewmate" else "#ff0000",
                bg="#16213e"
            )
            reason_label.pack(pady=10)
        
        # 身份揭示
        reveal_frame = tk.LabelFrame(game_over_frame, text="最终身份揭示", bg="#1a1a2e", fg="#ffffff", font=(self.font_family, 14))
        reveal_frame.pack(fill="x", padx=100, pady=20)
        
        for player in self.game.players:
            status = "存活" if player.is_alive else "死亡"
            role_name = player.role.__class__.__name__
            # 显示船员任务完成情况
            if isinstance(player.role, Crewmate):
                role_name += f" (完成{player.completed_tasks}/3任务)"
            
            player_label = tk.Label(
                reveal_frame, 
                text=f"{player.name}: {role_name} ({status})", 
                font=(self.font_family, 12),
                fg="#ffffff",
                bg="#1a1a2e"
            )
            player_label.pack(pady=5, padx=20)
        
        # 按钮区域
        button_frame = tk.Frame(game_over_frame, bg="#16213e")
        button_frame.pack(pady=40)
        
        # 重新开始按钮
        if sys.platform == 'darwin':
            restart_button = ttk.Button(
                button_frame, 
                text="重新开始", 
                style="Restart.TButton",
                command=self.create_main_frame
            )
            quit_button = ttk.Button(
                button_frame, 
                text="退出游戏", 
                style="Quit.TButton",
                command=self.root.quit
            )
            style = ttk.Style()
            style.configure("Restart.TButton", 
                          font=(self.font_family, 14),
                          padding=(30, 10),
                          background="#4CAF50",
                          foreground="#FFFFFF")
            style.map("Restart.TButton",
                          background=[("active", "#4CAF50"),("!active", "#4CAF50")],
                          foreground=[("active", "#FFFFFF"),("!active", "#FFFFFF")])
            style.configure("Quit.TButton", 
                          font=(self.font_family, 14),
                          padding=(30, 10),
                          background="#F44336",
                          foreground="#FFFFFF")
            style.map("Quit.TButton",
                          background=[("active", "#F44336"),("!active", "#F44336")],
                          foreground=[("active", "#FFFFFF"),("!active", "#FFFFFF")])
        else:
            restart_button = tk.Button(
                button_frame, 
                text="重新开始", 
                font=(self.font_family, 14),
                bg="#4caf50",
                fg="#ffffff",
                padx=30,
                pady=10,
                command=self.create_main_frame
            )
            quit_button = tk.Button(
                button_frame, 
                text="退出游戏", 
                font=(self.font_family, 14),
                bg="#f44336",
                fg="#ffffff",
                padx=30,
                pady=10,
                command=self.root.quit
            )
        restart_button.pack(side="left", padx=20)
        quit_button.pack(side="left", padx=20)

def main():
    """主函数"""
    root = tk.Tk()
    app = AmongUsGUI(root, game=None)
    root.mainloop()

if __name__ == "__main__":
    main()
    #task_frame