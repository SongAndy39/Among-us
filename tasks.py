#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务系统定义
"""
import math
import time
import tkinter as tk
from tkinter import messagebox, Canvas
from typing import List, Tuple
import random

class Task:
    """基础任务类"""
    def __init__(self, name: str, location: str, difficulty: int = 1):
        self.name = name
        self.location = location
        self.difficulty = difficulty
        self.is_completed = False  # 任务是否完成
    
    def complete(self) -> bool:
        if not self.is_completed:
            self.is_completed = True
            return True
        return False
    
    def __str__(self) -> str:
        status = "已完成" if self.is_completed else "未完成"
        return f"任务: {self.name} (位置: {self.location}, 状态: {status})"
    
    def run_task_gui(self, main_root=None) -> bool:
        return False

#main_root


class WireFixTask(Task):
    """配电室修复电线任务（带图形化交互）"""
    
    def __init__(self):
        super().__init__("修复电线", "电力室", 1)
        self.task_completed = False  # 记录GUI任务是否完成
        self.task_window = None
    
    def run_task_gui(self, main_root=None) -> bool:
        """
        运行修复电线的图形化任务界面
        :param main_root: 主窗口对象（可选）
        :return: 任务是否完成
        """
        # 确保只创建一个任务窗口
        if self.task_window and tk.Toplevel.winfo_exists(self.task_window):
            self.task_window.lift()
            return False
        
        # 创建窗口（优先使用Toplevel依附主窗口）
        if main_root and isinstance(main_root, tk.Tk):
            self.task_window = tk.Toplevel(main_root)
        else:
            self.task_window = tk.Tk()  # 无主窗口时创建独立窗口
        
        root = self.task_window
        root.title("配电室 - 修复电线任务")
        root.geometry("800x600")
        root.configure(bg="#1a1a2e")
        root.resizable(False, False)
        root.wm_attributes("-topmost", True)  # 窗口置顶
        
        # 确保窗口关闭时正确清理
        root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
        
        # 电线颜色配置（三组对应颜色）
        colors = ["#ff0000", "#00ff00", "#0000ff"]  # 红、绿、蓝
        wire_states = [False, False, False]  # 记录每组电线是否连接成功
        dragging_wire = None  # 当前拖动的电线索引
        wire_ids = []  # 存储电线画布对象ID
        
        # 创建UI
        def create_ui():
            """创建任务界面"""
            # 标题
            title_label = tk.Label(
                root,
                text="配电室 - 修复电线",
                font=("SimHei", 20, "bold"),
                fg="#e94560",
                bg="#1a1a2e"
            )
            title_label.pack(pady=20)
            
            # 电线操作画布（核心区域）
            canvas = tk.Canvas(
                root,
                width=700,
                height=400,
                bg="#2c3e50",  # 灰色底座背景
                highlightthickness=2,
                highlightbackground="#e94560"
            )
            canvas.pack(pady=10)
            
            # 绘制灰色底座
            canvas.create_rectangle(
                50, 50, 650, 350,
                fill="#7f8c8d",  # 灰色底座
                outline="#bdc3c7",
                width=3
            )
            
            # 电线起始/结束位置配置（左边3根，右边3根）
            left_wires = [
                (150, 200),  # 红色线起点
                (150, 280),  # 绿色线起点
                (150, 120)   # 蓝色线起点
            ]
            right_wires = [
                (550, 120),  # 红色线终点
                (550, 200),  # 绿色线终点
                (550, 280)   # 蓝色线终点
            ]
            
            # 绘制电线端点（圆形）
            def draw_wire_endpoints():
                """绘制电线端点"""
                # 左边端点
                for i, (x, y) in enumerate(left_wires):
                    canvas.create_oval(
                        x-8, y-8, x+8, y+8,
                        fill=colors[i],
                        outline="#ffffff",
                        width=2
                    )
                
                # 右边端点
                for i, (x, y) in enumerate(right_wires):
                    canvas.create_oval(
                        x-8, y-8, x+8, y+8,
                        fill=colors[i],
                        outline="#ffffff" if not wire_states[i] else "#ffff00",
                        width=2,
                        tags=f"right_end_{i}"
                    )
            
            draw_wire_endpoints()
            
            # 绘制初始电线（短线条）
            nonlocal wire_ids
            wire_ids = []
            for i in range(3):
                x1, y1 = left_wires[i]
                wire_id = canvas.create_line(
                    x1, y1, x1 + 20, y1,
                    fill=colors[i],
                    width=5,
                    capstyle=tk.ROUND
                )
                wire_ids.append(wire_id)
            
            # 任务状态标签
            status_label = tk.Label(
                root,
                text="任务状态：未完成（需连接所有同色电线）",
                font=("SimHei", 12),
                fg="#ffffff",
                bg="#1a1a2e"
            )
            status_label.pack(pady=10)
            
            # 鼠标事件处理
            def on_wire_click(event):
                """点击电线开始拖动"""
                nonlocal dragging_wire
                # 检测是否点击了左边的电线
                for i in range(3):
                    if wire_states[i]:  # 已连接的电线不能再拖动
                        continue
                    x1, y1 = left_wires[i]
                    # 计算点击位置与电线起点的距离
                    distance = math.hypot(event.x - x1, event.y - y1)
                    if distance < 20:  # 点击范围
                        dragging_wire = i
                        # 提升当前电线层级
                        canvas.tag_raise(wire_ids[i])
                        break
            
            def on_wire_drag(event):
                """拖动电线"""
                if dragging_wire is not None and not wire_states[dragging_wire]:
                    i = dragging_wire
                    x1, y1 = left_wires[i]
                    # 更新电线终点为鼠标位置
                    canvas.coords(
                        wire_ids[i],
                        x1, y1,
                        event.x, event.y
                    )
            
            def on_wire_release(event):
                """释放电线，检测是否吸附到同色端点"""
                nonlocal dragging_wire
                if dragging_wire is None:
                    return
                
                i = dragging_wire
                x1, y1 = left_wires[i]
                
                # 检测是否靠近右边同色端点
                target_x, target_y = right_wires[i]
                distance = math.hypot(event.x - target_x, event.y - target_y)
                
                if distance < 30:  # 吸附范围
                    # 吸附到目标端点
                    canvas.coords(
                        wire_ids[i],
                        x1, y1,
                        target_x, target_y
                    )
                    wire_states[i] = True
                    # 更新右边端点样式（高亮）
                    canvas.itemconfig(
                        f"right_end_{i}",
                        outline="#ffff00",
                        width=3
                    )
                    status_label.config(
                        text=f"任务状态：已连接{sum(wire_states)}/3根电线"
                    )
                    
                    # 检查是否所有电线都连接完成
                    if all(wire_states):
                        complete_task()
                else:
                    # 未吸附，恢复电线初始状态
                    canvas.coords(
                        wire_ids[i],
                        x1, y1,
                        x1 + 20, y1
                    )
                
                dragging_wire = None
            
            def complete_task():
                """完成任务"""
                self.task_completed = True
                status_label.config(
                    text="任务状态：已完成！",
                    fg="#00ff00"
                )
                # 禁用所有交互
                canvas.unbind("<ButtonPress-1>")
                canvas.unbind("<B1-Motion>")
                canvas.unbind("<ButtonRelease-1>")
                # 弹出完成提示
                messagebox.showinfo("任务完成", "🎉 配电室电线修复完成！")
                # 延迟关闭窗口（让用户看到提示）
                root.after(1000, lambda: (root.quit(), root.destroy()))
            
            # 绑定鼠标事件
            canvas.bind("<ButtonPress-1>", on_wire_click)
            canvas.bind("<B1-Motion>", on_wire_drag)
            canvas.bind("<ButtonRelease-1>", on_wire_release)
        
        create_ui()
        
        # 启动主循环
        try:
            root.mainloop()
        except Exception as e:
            print(f"GUI运行错误: {e}")
        
        # GUI关闭后，返回任务是否完成
        if self.task_completed:
            self.complete()  # 标记任务为已完成
            return True
        return False
class FilterCleanTask(Task):
    """氧气室清理过滤器任务（带图形化交互）"""
    
    def __init__(self):
        super().__init__("清理过滤器", "氧气室", 1)
        self.task_completed = False  # 记录GUI任务是否完成
        self.task_window = None  # 新增：记录任务窗口对象
    
    def run_task_gui(self, main_root=None) -> bool:
        """
        运行清理过滤器的图形化任务界面
        :param main_root: 主窗口对象（可选）
        :return: 任务是否完成
        """
        # 确保只创建一个任务窗口
        if self.task_window and (
            (isinstance(self.task_window, tk.Toplevel) and tk.Toplevel.winfo_exists(self.task_window)) or
            (isinstance(self.task_window, tk.Tk) and tk.Tk.winfo_exists(self.task_window))
        ):
            self.task_window.lift()
            return False
        
        # 创建窗口（优先使用Toplevel依附主窗口）
        if main_root and isinstance(main_root, tk.Tk):
            self.task_window = tk.Toplevel(main_root)
        else:
            self.task_window = tk.Tk()  # 无主窗口时创建独立窗口
        
        root = self.task_window
        root.title("氧气室 - 清理过滤器")
        root.geometry("800x600")
        root.configure(bg="#1a1a2e")
        root.resizable(False, False)
        root.wm_attributes("-topmost", True)  # 窗口置顶
        
        # 窗口关闭协议：确保正确清理资源
        root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
        
        # 中文字体（增加兼容性）
        font_family = "SimHei"
        try:
            tk.font.Font(family=font_family, size=12)
        except:
            font_family = "Arial"  # 兜底字体
        
        # 核心参数
        ring_radius = 150  # 圆环半径
        ring_center = (400, 250)  # 圆环中心坐标
        min_ball_radius = 10  # 小球最小半径
        max_ball_radius = int(ring_radius / 4)  # 小球最大半径（圆环1/4）
        ball_count = random.randint(3, 5)  # 随机生成3-5个小球
        balls = {}  # 存储小球ID和属性 {ball_id: (x, y, radius)}
        dragging_ball = None  # 当前拖动的小球ID
        
        # 创建UI
        def create_ui():
            """创建任务界面"""
            # 标题
            title_label = tk.Label(
                root,
                text="氧气室 - 清理过滤器",
                font=(font_family, 20, "bold"),
                fg="#e94560",
                bg="#1a1a2e"
            )
            title_label.pack(pady=20)
            
            # 过滤器操作画布（核心区域）
            canvas = tk.Canvas(
                root,
                width=700,
                height=400,
                bg="#7f8c8d",  # 灰色底板
                highlightthickness=2,
                highlightbackground="#e94560"
            )
            canvas.pack(pady=10)
            
            # 绘制黑色圆环（中心红色）
            # 外层黑色圆环
            canvas.create_oval(
                ring_center[0] - ring_radius, ring_center[1] - ring_radius,
                ring_center[0] + ring_radius, ring_center[1] + ring_radius,
                outline="#000000", width=8, tags="ring"
            )
            # 中心红色区域
            canvas.create_oval(
                ring_center[0] - (ring_radius - 10), ring_center[1] - (ring_radius - 10),
                ring_center[0] + (ring_radius - 10), ring_center[1] + (ring_radius - 10),
                fill="#ff0000", outline="", tags="ring_center"
            )
            
            # 任务状态标签
            status_label = tk.Label(
                root,
                text=f"任务状态：未完成（需清理{ball_count}个杂质小球）",
                font=(font_family, 12),
                fg="#ffffff",
                bg="#1a1a2e"
            )
            status_label.pack(pady=10)
            
            # 生成随机棕色小球
            def generate_balls():
                """生成随机位置、大小的棕色小球"""
                nonlocal balls
                balls = {}  # 初始化小球字典
                for _ in range(ball_count):
                    # 随机半径（1/4圆环内）
                    radius = random.randint(min_ball_radius, max_ball_radius)
                    # 随机位置（圆环内，避免超出边界）
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(0, ring_radius - radius - 5)
                    x = ring_center[0] + distance * math.cos(angle)
                    y = ring_center[1] + distance * math.sin(angle)
                    # 绘制棕色小球
                    ball_id = canvas.create_oval(
                        x - radius, y - radius,
                        x + radius, y + radius,
                        fill="#8B4513", outline="#5D2906", width=1,
                        tags="ball"
                    )
                    balls[ball_id] = (x, y, radius)
            
            generate_balls()
            
            # 鼠标事件处理
            def on_ball_click(event):
                """点击小球开始拖动"""
                nonlocal dragging_ball
                # 获取点击位置的对象
                clicked_items = canvas.find_closest(event.x, event.y)
                if not clicked_items:
                    dragging_ball = None
                    return
                
                ball_id = clicked_items[0]
                # 只处理小球对象
                if ball_id in balls:
                    dragging_ball = ball_id
                    # 提升层级，拖动时显示在最上层
                    canvas.tag_raise(dragging_ball)
                else:
                    dragging_ball = None
            
            def on_ball_drag(event):
                """拖动小球"""
                if dragging_ball and dragging_ball in balls:
                    x, y, radius = balls[dragging_ball]
                    # 更新小球位置为鼠标位置
                    canvas.coords(
                        dragging_ball,
                        event.x - radius, event.y - radius,
                        event.x + radius, event.y + radius
                    )
                    # 更新小球坐标记录
                    balls[dragging_ball] = (event.x, event.y, radius)
            
            def on_ball_release(event):
                """释放小球，判断是否脱离圆环"""
                nonlocal dragging_ball
                if not dragging_ball or dragging_ball not in balls:
                    dragging_ball = None
                    return
                
                # 获取小球当前位置
                x, y, radius = balls[dragging_ball]
                # 计算小球中心到圆环中心的距离
                distance = math.hypot(x - ring_center[0], y - ring_center[1])
                
                # 脱离圆环（距离 > 圆环半径）
                if distance > ring_radius:
                    # 删除小球
                    canvas.delete(dragging_ball)
                    del balls[dragging_ball]
                    # 更新状态
                    remaining = len(balls)
                    status_label.config(
                        text=f"任务状态：未完成（剩余{remaining}个杂质小球）"
                    )
                    # 检查是否全部清理完成
                    if remaining == 0:
                        complete_task()
                else:
                    # 未脱离，恢复到圆环内随机位置
                    angle = random.uniform(0, 2 * math.pi)
                    new_distance = random.uniform(0, ring_radius - radius - 5)
                    new_x = ring_center[0] + new_distance * math.cos(angle)
                    new_y = ring_center[1] + new_distance * math.sin(angle)
                    canvas.coords(
                        dragging_ball,
                        new_x - radius, new_y - radius,
                        new_x + radius, new_y + radius
                    )
                    balls[dragging_ball] = (new_x, new_y, radius)
                
                dragging_ball = None
            
            def complete_task():
                """完成任务"""
                # 移除错误的nonlocal self声明
                self.task_completed = True
                status_label.config(
                    text="任务状态：已完成！",
                    fg="#00ff00"
                )
                # 禁用所有交互
                canvas.unbind("<ButtonPress-1>")
                canvas.unbind("<B1-Motion>")
                canvas.unbind("<ButtonRelease-1>")
                # 弹出完成提示
                messagebox.showinfo("任务完成", "🎉 过滤器杂质清理完成！")
                # 延迟关闭窗口（让用户看到提示）
                root.after(1000, lambda: (root.quit(), root.destroy()))
            
            # 绑定鼠标事件
            canvas.bind("<ButtonPress-1>", on_ball_click)
            canvas.bind("<B1-Motion>", on_ball_drag)
            canvas.bind("<ButtonRelease-1>", on_ball_release)
        
        create_ui()
        
        # 启动主循环（增加异常处理）
        try:
            root.mainloop()
        except Exception as e:
            print(f"过滤器清理任务GUI运行错误: {e}")
            self.task_completed = False
        
        # GUI关闭后，返回任务是否完成
        if self.task_completed:
            self.complete()  # 标记任务为已完成
            return True
        return False
class BodyScanTask(Task):
    """医疗室扫描身体任务（带图形化交互）"""
    
    def __init__(self):
        super().__init__("扫描身体", "医疗室", 1)
        self.task_completed = False  # 记录GUI任务是否完成
        self.task_window = None      # 任务窗口对象
        self.scan_running = False    # 扫描状态（移到实例变量，避免nonlocal问题）
        self.scan_line_id = None     # 扫描线ID
        self.scan_direction = 1      # 扫描方向：1=向下，-1=向上
        self.requests = None
    
    def run_task_gui(self, main_root=None) -> bool:
        """
        运行扫描身体的图形化任务界面
        :param main_root: 主窗口对象（可选）
        :return: 任务是否完成
        """
        # 确保只创建一个任务窗口
        if self.task_window and (
            (isinstance(self.task_window, tk.Toplevel) and tk.Toplevel.winfo_exists(self.task_window)) or
            (isinstance(self.task_window, tk.Tk) and tk.Tk.winfo_exists(self.task_window))
        ):
            self.task_window.lift()
            return False
        
        # 创建窗口（优先使用Toplevel依附主窗口）
        if main_root and isinstance(main_root, tk.Tk):
            self.task_window = tk.Toplevel(main_root)
        else:
            self.task_window = tk.Tk()  # 无主窗口时创建独立窗口
        
        root = self.task_window
        root.title("医疗室 - 扫描身体")
        root.geometry("800x600")
        root.configure(bg="#1a1a2e")
        root.resizable(False, False)
        root.wm_attributes("-topmost", True)  # 窗口置顶
        
        # 窗口关闭协议：确保正确清理资源
        root.protocol("WM_DELETE_WINDOW", lambda: self._cleanup_window(root))
        
        # 中文字体（增加兼容性）
        font_family = "SimHei"
        try:
            tk.font.Font(family=font_family, size=12)
        except:
            font_family = "Arial"  # 兜底字体
        
        # 创建UI
        def create_ui():
            """创建任务界面"""
            # 标题
            title_label = tk.Label(
                root,
                text="医疗室 - 扫描身体",
                font=(font_family, 20, "bold"),
                fg="#e94560",
                bg="#1a1a2e"
            )
            title_label.pack(pady=20)
            
            # 主画布（蓝色底板）
            main_canvas = tk.Canvas(
                root,
                width=700,
                height=400,
                bg="#0066cc",  # 蓝色底板
                highlightthickness=2,
                highlightbackground="#e94560"
            )
            main_canvas.pack(pady=10)
            
            # 左侧按钮区域（占1/2宽度）
            btn_x, btn_y = 175, 200
            scan_btn = tk.Button(
                root,
                text="开始扫描",
                font=(font_family, 14, "bold"),
                bg="#4caf50",
                fg="#ffffff",
                width=10,
                height=2,
                command=lambda: self.start_scan(main_canvas, status_label)
            )
            # 将按钮放置在画布左侧
            btn_window_id = main_canvas.create_window(
                btn_x, btn_y, window=scan_btn, tags="scan_btn"
            )
            # 保存按钮引用（防止被GC回收）
            main_canvas.scan_btn = scan_btn
            
            # 右侧灰色底板（占1/2宽度，蓝色底板的1/2）
            gray_x1, gray_y1 = 350, 50
            gray_x2, gray_y2 = 650, 350
            main_canvas.create_rectangle(
                gray_x1, gray_y1, gray_x2, gray_y2,
                fill="#7f8c8d", outline="#000000", width=2, tags="gray_board"
            )
            
            # 加载人体图片并自适应缩放
                        # 加载人体图片并自适应缩放
            try:
                import os
                # 构建图片的绝对路径
                script_dir = os.path.dirname(os.path.abspath(__file__))
                img_path = os.path.join(script_dir, "pictures", "human_body.png")
                
                # 直接使用PhotoImage加载图片
                tk_img = tk.PhotoImage(file=img_path)
                
                # 获取图片原始尺寸
                img_width = tk_img.width()
                img_height = tk_img.height()
                
                # 计算灰色底板可用区域（留边距）
                board_width = gray_x2 - gray_x1 - 20  # 左右各留10px边距
                board_height = gray_y2 - gray_y1 - 20 # 上下各留10px边距
                
                # 自适应缩放图片（保持比例）
                img_ratio = img_width / img_height
                board_ratio = board_width / board_height
                
                if img_ratio > board_ratio:
                    # 图片更宽，按宽度缩放
                    new_width = board_width
                    new_height = int(new_width / img_ratio)
                else:
                    # 图片更高，按高度缩放
                    new_height = board_height
                    new_width = int(new_height * img_ratio)
                
                # 使用subsample方法缩放图片
                scale_x = img_width / new_width
                scale_y = img_height / new_height
                scale_factor = max(scale_x, scale_y)
                
                # 缩放图片
                if scale_factor > 1:
                    tk_img = tk_img.subsample(int(scale_factor), int(scale_factor))
                
                # 计算图片居中位置
                img_x = gray_x1 + (board_width - new_width) / 2 + 10
                img_y = gray_y1 + (board_height - new_height) / 2 + 10
                
                # 在灰色底板上绘制图片
                main_canvas.create_image(
                    img_x, img_y,
                    image=tk_img,
                    anchor=tk.NW,
                    tags="human_image"
                )
                # 保存图片引用（防止被GC回收）
                main_canvas.human_img = tk_img
                
            except Exception as e:
                # 加载失败时绘制默认人体轮廓（兜底）
                print(f"图片加载失败：{e}")
                body_points = [
                    (500, 80), (480, 100), (520, 100), (500, 120),
                    (500, 180), (470, 250), (530, 250), (500, 180),
                    (480, 140), (460, 120), (480, 140), (520, 140),
                    (540, 120), (520, 140), (480, 250), (470, 320),
                    (480, 250), (520, 250), (530, 320)
                ]
                main_canvas.create_polygon(
                    body_points,
                    fill="", outline="#000000", width=3, tags="human_body"
                )
            # 任务状态标签
            status_label = tk.Label(
                root,
                text="任务状态：未完成（点击开始扫描按钮）",
                font=(font_family, 12),
                fg="#ffffff",
                bg="#1a1a2e"
            )
            status_label.pack(pady=10)
            
            return main_canvas, status_label
        
        # 创建UI并启动
        main_canvas, status_label = create_ui()
        
        # 启动主循环（增加异常处理）
        try:
            root.mainloop()
        except Exception as e:
            print(f"身体扫描任务GUI运行错误: {e}")
            self.task_completed = False
        
        # GUI关闭后，返回任务是否完成
        if self.task_completed:
            self.complete()  # 标记任务为已完成
            return True
        return False
    
    def _cleanup_window(self, root):
        """窗口清理函数"""
        self.scan_running = False  # 停止扫描动画
        if root:
            root.quit()
            root.destroy()
    
    def start_scan(self, canvas, status_label):
        """开始扫描动画（改为实例方法，避免nonlocal）"""
        if self.scan_running:
            return
        
        self.scan_running = True
        self.scan_direction = 1  # 重置扫描方向
        status_label.config(text="任务状态：扫描中...")
        
        # 扫描线初始位置（灰色底板顶部）
        scan_y = 50
        # 创建扫描线（蓝色）
        self.scan_line_id = canvas.create_line(
            350, scan_y, 650, scan_y,
            fill="#00ccff", width=3, tags="scan_line"
        )
        # 启动扫描动画
        self.animate_scan(canvas, scan_y, status_label)
    
    def animate_scan(self, canvas, y, status_label):
        """扫描动画逻辑：向下→向上（改为实例方法）"""
        if not self.scan_running:
            return
        
        # 更新扫描线位置
        if self.scan_line_id:
            canvas.coords(self.scan_line_id, 350, y, 650, y)
        
        # 扫描到底部（灰色底板底部），切换方向向上
        if y >= 350:
            self.scan_direction = -1
        # 扫描到顶部且已完成一次往返，结束扫描
        elif y <= 50 and self.scan_direction == -1:
            self.complete_scan(canvas, status_label)
            return
        
        # 继续动画（控制扫描速度）
        new_y = y + (3 * self.scan_direction)
        canvas.after(10, self.animate_scan, canvas, new_y, status_label)
    
    def complete_scan(self, canvas, status_label):
        """完成扫描（改为实例方法）"""
        self.scan_running = False
        
        # 隐藏扫描线
        if self.scan_line_id:
            canvas.delete(self.scan_line_id)
            self.scan_line_id = None
        
        self.task_completed = True
        status_label.config(text="任务状态：已完成！", fg="#00ff00")
        
        # 禁用扫描按钮
        try:
            btn = canvas.scan_btn
            if btn:
                btn.config(state=tk.DISABLED)
                btn.config(bg="#cccccc")  # 视觉上禁用
        except:
            pass
        
        # 弹出完成提示
        messagebox.showinfo("任务完成", "🎉 身体扫描完成！")
        
        # 延迟关闭窗口（让用户看到提示）
        canvas.after(1000, lambda: self._cleanup_window(self.task_window))
class DownloadDataTask(Task):
    """通讯室下载数据任务（带图形化交互）"""
    
    def __init__(self):
        super().__init__("下载数据", "通讯室", 1)
        self.task_completed = False  # 记录GUI任务是否完成
        self.task_window = None      # 任务窗口对象
        # 核心参数改为实例变量，避免nonlocal问题
        self.download_progress = 0   # 下载进度（0-100）
        self.usb_dragging = False    # U盘是否正在拖动
        self.usb_id = None           # U盘图形ID
        self.usb_plugged = False     # U盘是否插入接口
        self.progress_label = None   # 进度显示标签
        self.download_after_id = None # 进度更新定时器ID
    
    def run_task_gui(self, main_root=None) -> bool:
        """
        运行下载数据的图形化任务界面
        :param main_root: 主窗口对象（可选）
        :return: 任务是否完成
        """
        # 确保只创建一个任务窗口
        if self.task_window and (
            (isinstance(self.task_window, tk.Toplevel) and tk.Toplevel.winfo_exists(self.task_window)) or
            (isinstance(self.task_window, tk.Tk) and tk.Tk.winfo_exists(self.task_window))
        ):
            self.task_window.lift()
            return False
        
        # 创建窗口（优先使用Toplevel依附主窗口）
        if main_root and isinstance(main_root, tk.Tk):
            self.task_window = tk.Toplevel(main_root)
        else:
            self.task_window = tk.Tk()  # 无主窗口时创建独立窗口
        
        root = self.task_window
        root.title("通讯室 - 下载数据")
        root.geometry("800x600")
        root.configure(bg="#1a1a2e")
        root.resizable(False, False)
        root.wm_attributes("-topmost", True)  # 窗口置顶
        
        # 窗口关闭协议：确保正确清理资源
        root.protocol("WM_DELETE_WINDOW", lambda: self._cleanup_window(root))
        
        # 中文字体（增加兼容性）
        font_family = "SimHei"
        try:
            tk.font.Font(family=font_family, size=12)
        except:
            font_family = "Arial"  # 兜底字体
        
        # 创建UI
        def create_ui():
            """创建任务界面"""
            # 标题
            title_label = tk.Label(
                root,
                text="通讯室 - 下载数据",
                font=(font_family, 20, "bold"),
                fg="#e94560",
                bg="#1a1a2e"
            )
            title_label.pack(pady=20)
            
            # 主画布（蓝色底板）
            main_canvas = tk.Canvas(
                root,
                width=700,
                height=400,
                bg="#0066cc",  # 蓝色底板
                highlightthickness=2,
                highlightbackground="#e94560",
                cursor="hand2"  # 鼠标悬停显示手型
            )
            main_canvas.pack(pady=10)
            
            # ========== 左侧1/3区域：绘制横置U盘 ==========
            usb_x1, usb_y1 = 50, 180  # U盘初始位置（横置）
            usb_width = 100  # 横置后宽度更长
            usb_height = 60  # 横置后高度更短
            
            # 绘制U盘主体（灰色，横置）
            usb_body = main_canvas.create_rectangle(
                usb_x1, usb_y1,
                usb_x1 + usb_width, usb_y1 + usb_height,
                fill="#7f8c8d", outline="#000000", width=2,
                tags="usb"
            )
            # U盘接口（金属色，在U盘右侧，横置）
            main_canvas.create_rectangle(
                usb_x1 + usb_width - 15, usb_y1 + 10,
                usb_x1 + usb_width, usb_y1 + 50,
                fill="#f39c12", outline="#000000", width=1,
                tags="usb"
            )
            # U盘标识（横置居中）
            main_canvas.create_text(
                usb_x1 + usb_width/2, usb_y1 + usb_height/2,
                text="U盘", font=(font_family, 12), fill="#000000",
                tags="usb"
            )
            
            # 保存U盘ID和初始位置
            self.usb_id = usb_body
            main_canvas.usb_init_x = usb_x1
            main_canvas.usb_init_y = usb_y1
            main_canvas.usb_width = usb_width
            main_canvas.usb_height = usb_height
            
            # ========== 右侧区域：显示屏 + USB接口 ==========
            # 右侧显示屏（上2/3）
            screen_x1, screen_y1 = 300, 50
            screen_x2, screen_y2 = 650, 250
            main_canvas.create_rectangle(
                screen_x1, screen_y1, screen_x2, screen_y2,
                fill="#ecf0f1", outline="#000000", width=3,
                tags="screen"
            )
            # 显示屏标题
            main_canvas.create_text(
                (screen_x1 + screen_x2)/2, screen_y1 + 20,
                text="数据下载进度", font=(font_family, 14, "bold"), fill="#000000",
                tags="screen_text"
            )
            
            # 进度显示标签（在显示屏内）
            self.progress_label = tk.Label(
                root,
                text="0%",
                font=(font_family, 36, "bold"),
                fg="#27ae60",
                bg="#ecf0f1"
            )
            # 将标签放置在显示屏中央
            self.progress_label.place(
                x=(screen_x1 + screen_x2)/2 - 30, 
                y=(screen_y1 + screen_y2)/2 - 20
            )
            
            # 右侧USB接口（下1/3，横置接口）
            usb_port_x1, usb_port_y1 = 400, 300
            usb_port_x2, usb_port_y2 = 500, 350
            # 接口外框（横置）
            main_canvas.create_rectangle(
                usb_port_x1, usb_port_y1, usb_port_x2, usb_port_y2,
                fill="#bdc3c7", outline="#000000", width=2,
                tags="usb_port"
            )
            # 接口插槽（横置，匹配U盘尺寸）
            main_canvas.create_rectangle(
                usb_port_x1 + 5, usb_port_y1 + 5,
                usb_port_x2 - 5, usb_port_y2 - 5,
                fill="#7f8c8d", outline="#000000", width=1,
                tags="usb_port_slot"
            )
            # 接口标识
            main_canvas.create_text(
                (usb_port_x1 + usb_port_x2)/2, usb_port_y2 + 20,
                text="USB接口", font=(font_family, 12), fill="#ffffff"
            )
            
            # 保存接口位置信息
            main_canvas.usb_port_x1 = usb_port_x1
            main_canvas.usb_port_y1 = usb_port_y1
            main_canvas.usb_port_x2 = usb_port_x2
            main_canvas.usb_port_y2 = usb_port_y2
            
            # 任务状态标签
            status_label = tk.Label(
                root,
                text="任务状态：未完成（将U盘拖入USB接口开始下载）",
                font=(font_family, 12),
                fg="#ffffff",
                bg="#1a1a2e"
            )
            status_label.pack(pady=10)
            
            return main_canvas, status_label
        
        # U盘拖动事件处理
        def on_usb_click(event):
            """点击U盘开始拖动"""
            if self.usb_plugged or self.download_progress >= 100:
                return
            # 检查是否点击到U盘（通过tags判断）
            items = event.widget.find_overlapping(event.x, event.y, event.x, event.y)
            for item in items:
                if "usb" in event.widget.gettags(item):
                    self.usb_dragging = True
                    # 记录点击偏移量（基于U盘左上角）
                    event.widget.click_x = event.x - event.widget.coords(self.usb_id)[0]
                    event.widget.click_y = event.y - event.widget.coords(self.usb_id)[1]
                    # 提升U盘层级
                    event.widget.tag_raise("usb")
                    break
        
        def on_usb_drag(event):
            """拖动U盘"""
            if not self.usb_dragging or self.usb_plugged or self.download_progress >= 100:
                return
            canvas = event.widget
            # 计算新位置（基于点击偏移量）
            new_x = event.x - canvas.click_x
            new_y = event.y - canvas.click_y
            # 移动整个U盘（所有usb标签的图形）
            for item in canvas.find_withtag("usb"):
                if canvas.type(item) == "rectangle":
                    # 矩形（U盘主体/接口）：更新四个坐标
                    canvas.coords(item, new_x, new_y, new_x + canvas.usb_width, new_y + canvas.usb_height)
                elif canvas.type(item) == "text":
                    # 文字（U盘标识）：更新居中坐标
                    canvas.coords(item, new_x + canvas.usb_width/2, new_y + canvas.usb_height/2)
        
        def on_usb_release(event):
            """释放U盘，检测是否插入接口（精准吸附到接口上）"""
            if not self.usb_dragging or self.download_progress >= 100:
                self.usb_dragging = False
                return
            
            canvas = event.widget
            self.usb_dragging = False
            
            # 获取U盘当前位置
            usb_x, usb_y = canvas.coords(self.usb_id)[0], canvas.coords(self.usb_id)[1]
            # 获取接口位置
            port_x1 = canvas.usb_port_x1
            port_y1 = canvas.usb_port_y1
            port_x2 = canvas.usb_port_x2
            port_y2 = canvas.usb_port_y2
            
            # 检测是否拖入接口区域（吸附判定）
            if (usb_x + canvas.usb_width > port_x1 and 
                usb_x < port_x2 and 
                usb_y + canvas.usb_height > port_y1 and 
                usb_y < port_y2):
                # U盘精准吸附到USB接口上（居中）
                target_x = port_x1 + (port_x2 - port_x1 - canvas.usb_width) / 2  # 接口内水平居中
                target_y = port_y1 + (port_y2 - port_y1 - canvas.usb_height) / 2  # 接口内垂直居中
                # 移动U盘到接口正中央
                for item in canvas.find_withtag("usb"):
                    if canvas.type(item) == "rectangle":
                        canvas.coords(item, target_x, target_y, target_x + canvas.usb_width, target_y + canvas.usb_height)
                    elif canvas.type(item) == "text":
                        canvas.coords(item, target_x + canvas.usb_width/2, target_y + canvas.usb_height/2)
                self.usb_plugged = True
                # 开始下载进度
                self.start_download(canvas, status_label)
            else:
                # 未拖入接口，恢复初始位置
                for item in canvas.find_withtag("usb"):
                    if canvas.type(item) == "rectangle":
                        canvas.coords(item, canvas.usb_init_x, canvas.usb_init_y, 
                                     canvas.usb_init_x + canvas.usb_width, canvas.usb_init_y + canvas.usb_height)
                    elif canvas.type(item) == "text":
                        canvas.coords(item, canvas.usb_init_x + canvas.usb_width/2, canvas.usb_init_y + canvas.usb_height/2)
        
        # 创建UI并绑定事件
        main_canvas, status_label = create_ui()
        
        # 绑定U盘拖动事件
        main_canvas.bind("<ButtonPress-1>", on_usb_click)
        main_canvas.bind("<B1-Motion>", on_usb_drag)
        main_canvas.bind("<ButtonRelease-1>", on_usb_release)
        
        # 启动主循环（增加异常处理）
        try:
            root.mainloop()
        except Exception as e:
            print(f"数据下载任务GUI运行错误: {e}")
            self.task_completed = False
        
        # GUI关闭后，返回任务是否完成
        if self.task_completed:
            self.complete()  # 标记任务为已完成
            return True
        return False
    
    def _cleanup_window(self, root):
        """窗口清理函数"""
        # 取消进度更新定时器
        if self.download_after_id:
            root.after_cancel(self.download_after_id)
        self.usb_dragging = False
        self.usb_plugged = False
        if root:
            root.quit()
            root.destroy()
    
    def start_download(self, canvas, status_label):
        """开始下载进度更新（实例方法）"""
        if self.download_progress >= 100 or not self.usb_plugged:
            return
        
        # 更新进度（每秒涨10%）
        self.download_progress += 10
        if self.download_progress > 100:
            self.download_progress = 100
        
        # 更新进度显示
        if self.progress_label:
            self.progress_label.config(text=f"{self.download_progress}%")
        status_label.config(text=f"任务状态：下载中...{self.download_progress}%")
        
        # 进度到100%，完成任务
        if self.download_progress >= 100:
            self.complete_download(canvas, status_label)
            return
        
        # 继续更新进度（1秒后）
        self.download_after_id = canvas.after(1000, self.start_download, canvas, status_label)
    
    def complete_download(self, canvas, status_label):
        """完成下载任务（实例方法）"""
        self.usb_plugged = False
        status_label.config(text="任务状态：已完成！", fg="#00ff00")
        
        if self.progress_label:
            self.progress_label.config(text="100%", fg="#27ae60")
        
        # 禁用U盘拖动（解绑事件）
        canvas.unbind("<ButtonPress-1>")
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        
        self.task_completed = True
        # 弹出完成提示
        messagebox.showinfo("任务完成", "🎉 数据下载完成！")
        # 延迟关闭窗口（让用户看到提示）
        canvas.after(1000, lambda: self._cleanup_window(self.task_window))


class CalibrateDownEngineTask(Task):
    """下降引擎室校准任务（带图形化交互）"""
    
    def __init__(self):
        super().__init__("校准下降引擎", "下降引擎室", 2)
        self.task_completed = False  # 任务完成状态
        self.task_finalized = False  # 新增：标记任务是否最终确认完成
        # 阈值范围（40%-60%）
        self.threshold_min = 40
        self.threshold_max = 60
        # 四个滑块当前值（0-100）
        self.slider_values = [0, 0, 0, 0]
        # 四个圆环的颜色引用
        self.ring_ids = []
        self.task_window = None      # 任务窗口对象
        self.complete_after_id = None  # 完成检测定时器ID

    def run_task_gui(self, main_root=None) -> bool:
        """
        运行校准下降引擎的图形化任务界面
        :param main_root: 主窗口对象（可选）
        :return: 任务是否完成
        """
        # 重置状态（防止多次调用残留）
        self.task_completed = False
        self.task_finalized = False
        
        # 确保只创建一个任务窗口
        if self.task_window and (
            (isinstance(self.task_window, tk.Toplevel) and tk.Toplevel.winfo_exists(self.task_window)) or
            (isinstance(self.task_window, tk.Tk) and tk.Tk.winfo_exists(self.task_window))
        ):
            self.task_window.lift()
            return False
        
        # 创建窗口（优先使用Toplevel依附主窗口）
        if main_root and isinstance(main_root, tk.Tk):
            self.task_window = tk.Toplevel(main_root)
        else:
            self.task_window = tk.Tk()  # 无主窗口时创建独立窗口
        
        root = self.task_window
        root.title("下降引擎室 - 引擎校准")
        root.geometry("650x520")
        root.configure(bg="#ffffff")
        root.resizable(False, False)
        root.wm_attributes("-topmost", True)

        # 关键修复：窗口关闭协议只清理资源，不修改完成状态
        root.protocol("WM_DELETE_WINDOW", lambda: self._cleanup_window(root, False))

        # 中文字体（增加兼容性）
        font_family = "SimHei"
        try:
            tk.font.Font(family=font_family, size=12)
        except:
            font_family = "Arial"

        # 创建主画布
        main_canvas = tk.Canvas(
            root,
            width=630,
            height=500,
            bg="#ffffff",
            highlightthickness=0
        )
        main_canvas.pack(pady=8)

        # ========== 滑动条区域 ==========
        slider_frame = tk.Frame(root, bg="#ffffff")
        slider_frame.place(x=20, y=15, width=600, height=220)
        
        sliders = []
        slider_labels = []

        # 创建4个滑动条
        for i in range(4):
            slider_row = tk.Frame(slider_frame, bg="#ffffff")
            slider_row.pack(fill=tk.X, pady=2)  
            
            # 滑动条标签
            label = tk.Label(
                slider_row,
                text=f"引擎{i+1}：0%",
                font=(font_family, 10),
                bg="#ffffff",
                width=10
            )
            label.pack(side=tk.LEFT, padx=5)
            slider_labels.append(label)
            
            # 滑动条
            slider = tk.Scale(
                slider_row,
                from_=0,
                to=100,
                orient=tk.HORIZONTAL,
                length=480,
                bg="#ffffff",
                highlightthickness=0,
                troughcolor="#e0e0e0",
                sliderlength=20,
                command=lambda val, idx=i: self.on_slider_change(
                    val, idx, main_canvas, slider_labels, status_label
                )
            )
            slider.set(0)
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            sliders.append(slider)

        # ========== 圆环区域 ==========
        ring_radius = 32
        ring_center_y = 290
        ring_spacing = 130
        
        self.ring_ids = []
        for i in range(4):
            ring_center_x = 85 + i * ring_spacing
            # 外圆环
            outer_ring = main_canvas.create_oval(
                ring_center_x - ring_radius, ring_center_y - ring_radius,
                ring_center_x + ring_radius, ring_center_y + ring_radius,
                outline="#000000", width=4, fill=""
            )
            # 中间填充区域
            inner_circle = main_canvas.create_oval(
                ring_center_x - (ring_radius - 6), ring_center_y - (ring_radius - 6),
                ring_center_x + (ring_radius - 6), ring_center_y + (ring_radius - 6),
                fill="#cccccc", outline=""
            )
            self.ring_ids.append({
                "outer": outer_ring,
                "inner": inner_circle,
                "x": ring_center_x,
                "y": ring_center_y,
                "radius": ring_radius - 6
            })

        # ========== 状态标签 ==========
        status_label = tk.Label(
            root,
            text="任务状态：未完成（将4个滑块调整至40%-60%区间）",
            font=(font_family, 12, "bold"),
            bg="#ffffff",
            fg="#ff0000",
            wraplength=600
        )
        status_label.place(x=20, y=410, width=600, height=40)

        # 绑定滑动条释放事件
        for slider in sliders:
            slider.bind("<ButtonRelease-1>", lambda e: self.check_task_complete(sliders, status_label, root))

        # 启动主循环
        try:
            root.mainloop()
        except Exception as e:
            print(f"引擎校准任务GUI运行错误: {e}")

        # 关键修复：返回最终确认的完成状态，不受窗口关闭影响
        final_result = self.task_finalized
        # 重置状态，为下一次调用做准备
        self.task_finalized = False
        return final_result

    def on_slider_change(self, val, idx, canvas, labels, status_label):
        """滑动条值变化回调"""
        if self.task_finalized:  # 任务已最终完成，不再响应
            return
            
        # 更新滑块值
        val = int(float(val))
        self.slider_values[idx] = val
        
        # 更新标签
        labels[idx].config(text=f"引擎{idx+1}：{val}%")
        
        # 计算颜色
        if self.threshold_min <= val <= self.threshold_max:
            blue_intensity = 200 + int((abs(val - 50) / 10) * -55)
            blue_intensity = max(200, min(255, blue_intensity))
            fill_color = f"#{0:02x}{100:02x}{blue_intensity:02x}"
        elif val < self.threshold_min:
            gray_intensity = 200 - int(val / self.threshold_min * 150)
            gray_intensity = max(50, min(200, gray_intensity))
            fill_color = f"#{gray_intensity:02x}{gray_intensity:02x}{gray_intensity:02x}"
        else:
            red_intensity = 200 + int((val - self.threshold_max) / 40 * 55)
            red_intensity = max(200, min(255, red_intensity))
            fill_color = f"#{red_intensity:02x}{50:02x}{50:02x}"
        
        # 更新圆环颜色
        try:
            canvas.itemconfig(self.ring_ids[idx]["inner"], fill=fill_color)
        except IndexError:
            return
        
        # 更新状态提示
        all_in_range = all(self.threshold_min <= v <= self.threshold_max for v in self.slider_values)
        if all_in_range:
            status_label.config(
                text="任务状态：所有引擎校准完成！",
                fg="#00ff00"
            )
            # 取消之前的定时器
            if self.complete_after_id:
                canvas.after_cancel(self.complete_after_id)
            # 延迟检测完成
            self.complete_after_id = canvas.after(800, self.check_task_complete, 
                                                None, status_label, canvas.master)
        else:
            if self.complete_after_id:
                canvas.after_cancel(self.complete_after_id)
                self.complete_after_id = None
                
            in_range_count = sum(1 for v in self.slider_values if self.threshold_min <= v <= self.threshold_max)
            status_label.config(
                text=f"任务状态：{in_range_count}/4 引擎校准中（需40%-60%）",
                fg="#ff8800"
            )

    def check_task_complete(self, sliders=None, status_label=None, root=None):
        """检查任务是否完成"""
        if self.task_finalized:
            return
            
        all_in_range = all(self.threshold_min <= val <= self.threshold_max for val in self.slider_values)
        if all_in_range:
            self._finalize_task(sliders, status_label, root)

    def _finalize_task(self, sliders, status_label, root):
        """最终确认任务完成（核心修复）"""
        # 标记任务最终完成，防止后续修改
        self.task_finalized = True
        self.task_completed = True
        self.complete()  # 标记基础任务类的完成状态
        
        # 更新状态标签
        if status_label:
            status_label.config(
                text="任务状态：校准成功！",
                fg="#00ff00"
            )
        
        # 禁用所有滑动条
        if sliders:
            for slider in sliders:
                try:
                    slider.config(state=tk.DISABLED)
                except:
                    pass
        else:
            # 从root查找滑动条并禁用
            try:
                for frame in root.winfo_children():
                    if isinstance(frame, tk.Frame):
                        for child in frame.winfo_children():
                            if isinstance(child, tk.Frame):
                                for item in child.winfo_children():
                                    if isinstance(item, tk.Scale):
                                        item.config(state=tk.DISABLED)
            except:
                pass
        
        # 显示完成提示（使用root作为父窗口，避免阻塞问题）
        def show_complete_message():
            messagebox.showinfo("任务完成", "🎉 下降引擎校准成功！", parent=root)
            # 提示框关闭后，安全关闭窗口（不修改完成状态）
            self._cleanup_window(root, True)
        
        # 异步显示提示框，避免主循环阻塞
        root.after(100, show_complete_message)

    def _cleanup_window(self, root, is_completed=False):
        """
        窗口清理函数
        :param root: 窗口对象
        :param is_completed: 是否是完成后清理（不修改状态）
        """
        # 取消定时器
        if self.complete_after_id:
            try:
                root.after_cancel(self.complete_after_id)
            except:
                pass
            self.complete_after_id = None
        
        # 关键修复：只有非完成状态的关闭才重置状态
        if not is_completed and not self.task_finalized:
            self.task_completed = False
        else:
            # 完成状态下关闭窗口，保留完成标记
            pass
        
        # 安全关闭窗口
        if root:
            try:
                # 先退出主循环，再销毁窗口
                root.quit()
                # 延迟销毁，避免时序问题
                root.after(100, root.destroy)
            except:
                pass

class CalibrateUpEngineTask(Task):
    """上升引擎室校准任务（随机点位+手动连接燃料出口）"""
    
    def __init__(self):
        super().__init__(name="校准上升引擎", location="上升引擎室", difficulty=2)
        self.task_completed = False  # 任务完成状态
        self.pipe_connected = False  # 管道连接成功标记
        self.knob_states = [0, 0]    # 旋钮状态（0：未到位，1：到位）
        self.line_segments = []      # 管道分段ID列表
        self.current_segment = None  # 当前绘制的线段ID
        self.points = []             # 管道经过的四个随机点坐标
        self.current_point_idx = 0   # 当前需要吸附的点位索引
        self.status_label = None     # 状态标签实例变量
        self.task_window = None      # 任务窗口（改用Toplevel，避免影响主GUI）
        self.canvas = None           # 画布引用
        self.is_running = False      # 标记任务窗口是否正在运行
        self.window_closed = False   # 新增：标记窗口是否主动关闭
        # 新增：燃料出口和接口的判定范围
        self.fuel_out_radius = 15    # 燃料出口判定半径
        self.fuel_in_radius = 15     # 燃料接口判定半径

    def generate_random_points(self):
        """生成4个随机点位（每个点半径100像素内不重复）"""
        self.points = []
        # 生成区域范围（画布内，避开燃料出口和接口）
        min_x, max_x = 100, 500
        min_y, max_y = 50, 350
        
        # 生成第一个点（基础点）
        first_x = random.randint(min_x, max_x)
        first_y = random.randint(min_y, max_y)
        self.points.append((first_x, first_y))
        
        # 生成剩余3个点（确保与已有点距离>100）
        while len(self.points) < 4:
            new_x = random.randint(min_x, max_x)
            new_y = random.randint(min_y, max_y)
            # 检查与所有已有点的距离
            valid = True
            for (x, y) in self.points:
                distance = math.hypot(new_x - x, new_y - y)
                if distance <= 100:
                    valid = False
                    break
            if valid:
                self.points.append((new_x, new_y))

    def run_task_gui(self, main_root=None) -> bool:
        """
        运行校准上升引擎的图形化界面
        :param main_root: 主GUI的根窗口（用于关联Toplevel）
        :return: 任务完成状态
        """
        # 防止重复打开窗口
        if self.is_running:
            messagebox.showinfo("提示", "校准上升引擎任务窗口已打开！", parent=main_root)
            return self.task_completed
        
        # 重置所有状态
        self.task_completed = False
        self.pipe_connected = False
        self.knob_states = [0, 0]
        self.line_segments = []
        self.current_segment = None
        self.current_point_idx = 0
        self.window_closed = False
        self.is_running = True

        try:
            # 关键修改：使用Toplevel创建任务窗口（关联主GUI，不独立占用Tk实例）
            if main_root and isinstance(main_root, tk.Tk):
                self.task_window = tk.Toplevel(main_root)
            else:
                self.task_window = tk.Toplevel()  # 兜底：无主窗口时创建独立Toplevel
            
            # 任务窗口配置（核心：不设置为独立主循环）
            self.task_window.title("校准上升引擎")
            self.task_window.geometry("700x500")
            self.task_window.configure(bg="#ffffff")
            self.task_window.resizable(False, False)
            self.task_window.attributes('-topmost', True)
            self.task_window.transient(main_root)  # 设为临时窗口，依赖主GUI
            
            # 绑定窗口关闭事件（关键：只关闭任务窗口，不影响主GUI）
            self.task_window.protocol("WM_DELETE_WINDOW", self.safe_close_window)

            # 中文字体
            font_family = "SimHei"

            # 创建主画布
            self.canvas = tk.Canvas(
                self.task_window,
                width=680,
                height=480,
                bg="#ffffff",
                highlightthickness=0
            )
            self.canvas.pack(pady=10)

            # ========== 绘制核心元素 ==========
            # 1. 燃料出口（左上角绿色大方块）
            self.fuel_out_pos = (80, 80)
            self.fuel_out = self.canvas.create_rectangle(
                self.fuel_out_pos[0] - self.fuel_out_radius, self.fuel_out_pos[1] - self.fuel_out_radius,
                self.fuel_out_pos[0] + self.fuel_out_radius, self.fuel_out_pos[1] + self.fuel_out_radius,
                fill="#2ecc71", outline="#000000", width=3,
                tags="fuel_out"
            )
            self.canvas.create_text(
                self.fuel_out_pos[0], self.fuel_out_pos[1] - 30,
                text="燃料出口", font=(font_family, 12, "bold"), fill="#000000"
            )

            # 2. 生成并绘制4个随机磁吸点位
            self.generate_random_points()
            for idx, (x, y) in enumerate(self.points):
                self.canvas.create_oval(
                    x - 8, y - 8, x + 8, y + 8,
                    fill="#bdc3c7", outline="#000000", width=2,
                    tags=f"point_{idx}"
                )
                self.canvas.create_text(
                    x, y - 15,
                    text=f"点{idx+1}", font=(font_family, 10, "bold"), fill="#000000"
                )

            # 3. 燃料接口（右下角红色大方块）
            self.fuel_in_pos = (250, 350)
            self.fuel_in = self.canvas.create_rectangle(
                self.fuel_in_pos[0] - self.fuel_in_radius, self.fuel_in_pos[1] - self.fuel_in_radius,
                self.fuel_in_pos[0] + self.fuel_in_radius, self.fuel_in_pos[1] + self.fuel_in_radius,
                fill="#e74c3c", outline="#000000", width=3,
                tags="fuel_in"
            )
            self.canvas.create_text(
                self.fuel_in_pos[0], self.fuel_in_pos[1] + 30,
                text="燃料接口", font=(font_family, 12, "bold"), fill="#000000"
            )

            # ========== 状态标签 ==========
            self.status_label = tk.Label(
                self.task_window,
                text="任务状态：请将管道从燃料出口拖动至点位1（磁吸吸附）",
                font=(font_family, 12, "bold"),
                bg="#ffffff",
                fg="#ff0000",
                wraplength=680
            )
            self.status_label.place(x=20, y=420, width=650, height=40)

            # ========== 右侧旋钮 ==========
            knob_frame = tk.Frame(self.task_window, bg="#ffffff")
            knob_frame.place(x=450, y=150, width=200, height=220)

            # 旋钮1（上）
            self.knob1_canvas = tk.Canvas(knob_frame, width=100, height=100, bg="#ffffff", highlightthickness=0)
            self.knob1_canvas.pack(pady=10)
            self.knob1_arc = self.knob1_canvas.create_arc(
                10, 10, 90, 90,
                start=0, extent=180,
                fill="#bdc3c7", outline="#000000", width=3
            )
            self.knob1_canvas.create_text(
                50, 50,
                text="旋钮1", font=(font_family, 12, "bold"), fill="#000000"
            )
            self.knob1_canvas.bind("<Button-1>", lambda e: self.rotate_knob(0))
            self.knob1_canvas.config(state=tk.DISABLED)

            # 旋钮2（下）
            self.knob2_canvas = tk.Canvas(knob_frame, width=100, height=100, bg="#ffffff", highlightthickness=0)
            self.knob2_canvas.pack(pady=10)
            self.knob2_arc = self.knob2_canvas.create_arc(
                10, 10, 90, 90,
                start=0, extent=180,
                fill="#bdc3c7", outline="#000000", width=3
            )
            self.knob2_canvas.create_text(
                50, 50,
                text="旋钮2", font=(font_family, 12, "bold"), fill="#000000"
            )
            self.knob2_canvas.bind("<Button-1>", lambda e: self.rotate_knob(1))
            self.knob2_canvas.config(state=tk.DISABLED)

            # ========== 绑定交互事件 ==========
            self.canvas.bind("<Motion>", self.on_mouse_move)
            self.canvas.bind("<Button-1>", self.on_mouse_click)

            # 强制刷新窗口
            self.task_window.update_idletasks()
            self.task_window.lift()
            self.task_window.focus_force()

            # 关键修改：不调用mainloop/wait_window，让任务窗口依附主GUI的主循环
            # 改为通过变量监听窗口状态
            self.task_window.wait_visibility()  # 等待窗口可见

        except Exception as e:
            print(f"校准上升引擎任务窗口创建失败：{str(e)}")
            messagebox.showerror("错误", f"任务窗口创建失败：{str(e)}", parent=main_root)
            self.is_running = False
            self.window_closed = True
            return self.task_completed

        # 等待窗口关闭（非阻塞，不影响主GUI）
        self.task_window.wait_window()
        self.is_running = False
        return self.task_completed

    def safe_close_window(self):
        """安全关闭任务窗口（核心：只关闭子窗口，不终止主GUI）"""
        self.window_closed = True
        self.is_running = False
        if self.task_window:
            # 解绑所有事件，清理资源
            self.canvas.unbind("<Motion>")
            self.canvas.unbind("<Button-1>")
            # 关键：只destroy子窗口，不调用quit（避免终止主循环）
            self.task_window.destroy()
            self.task_window = None  # 清空引用

    def distance(self, pos1, pos2):
        """计算两点间距离"""
        return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

    def on_mouse_move(self, event):
        """鼠标移动：管道跟随，磁吸吸附点位/燃料接口"""
        if self.pipe_connected or self.task_completed or self.window_closed:
            return
        
        # 确定当前起始点
        if self.current_point_idx == 0:
            start_pos = self.fuel_out_pos
        elif self.current_point_idx <= len(self.points):
            start_pos = self.points[self.current_point_idx - 1]
        else:
            # 4个点都连接完成后，起始点为第4个点
            start_pos = self.points[-1]

        # 磁吸逻辑
        target_pos = (event.x, event.y)
        
        # 阶段1：连接1-4号点（磁吸点位）
        if self.current_point_idx < len(self.points):
            target_point = self.points[self.current_point_idx]
            if self.distance((event.x, event.y), target_point) < 20:
                target_pos = target_point
        # 阶段2：4号点连接完成后，磁吸燃料接口
        else:
            if self.distance((event.x, event.y), self.fuel_in_pos) < 20:
                target_pos = self.fuel_in_pos

        # 更新当前管道段
        if self.current_segment:
            self.canvas.delete(self.current_segment)
        self.current_segment = self.canvas.create_line(
            start_pos[0], start_pos[1],
            target_pos[0], target_pos[1],
            width=10,
            fill="#3498db",
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            tags="temp_pipe"
        )

    def on_mouse_click(self, event):
        """鼠标点击：确认吸附点位/燃料接口"""
        if self.pipe_connected or self.task_completed or self.window_closed:
            return
        
        # 阶段1：连接1-4号点
        if self.current_point_idx < len(self.points):
            target_point = self.points[self.current_point_idx]
            # 校验是否吸附到当前点位
            if self.distance((event.x, event.y), target_point) >= 20:
                messagebox.showwarning(
                    "操作提示", 
                    f"请先将管道吸附到点位{self.current_point_idx+1}！",
                    parent=self.task_window  # 弹窗关联任务窗口，不影响主GUI
                )
                return

            # 确认管道段（点位）
            start_pos = self.fuel_out_pos if self.current_point_idx == 0 else self.points[self.current_point_idx - 1]
            end_pos = target_point
            
            # 绘制永久管道段
            segment = self.canvas.create_line(
                start_pos[0], start_pos[1],
                end_pos[0], end_pos[1],
                width=10,
                fill="#3498db",
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
                tags="pipe_segment"
            )
            self.line_segments.append(segment)
            self.canvas.delete(self.current_segment)
            self.current_segment = None

            # 更新进度
            self.current_point_idx += 1
            
            # 更新状态提示（连接下一个点位）
            if self.current_point_idx < len(self.points):
                # 高亮目标点位
                for idx in range(len(self.points)):
                    self.canvas.itemconfig(f"point_{idx}", fill="#f39c12" if idx == self.current_point_idx else "#bdc3c7")
                # 更新状态提示
                self.status_label.config(
                    text=f"任务状态：已吸附点位{self.current_point_idx}，请拖动至点位{self.current_point_idx+1}",
                    fg="#ff8800"
                )
            else:
                # 4个点位都连接完成，提示连接燃料接口
                for idx in range(len(self.points)):
                    self.canvas.itemconfig(f"point_{idx}", fill="#f39c12")
                self.status_label.config(
                    text="任务状态：4个点位已连接！请将管道拖动至燃料接口并点击确认",
                    fg="#ff8800"
                )
        
        # 阶段2：4号点连接完成后，连接燃料接口
        else:
            # 校验是否吸附到燃料接口
            if self.distance((event.x, event.y), self.fuel_in_pos) >= 20:
                messagebox.showwarning(
                    "操作提示", 
                    "请先将管道吸附到燃料接口后再点击！",
                    parent=self.task_window
                )
                return

            # 确认管道段（燃料接口）
            start_pos = self.points[-1]
            end_pos = self.fuel_in_pos
            
            # 绘制永久管道段（最后一段到燃料接口）
            final_segment = self.canvas.create_line(
                start_pos[0], start_pos[1],
                end_pos[0], end_pos[1],
                width=10,
                fill="#3498db",
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
                tags="pipe_segment"
            )
            self.line_segments.append(final_segment)
            self.canvas.delete(self.current_segment)
            self.current_segment = None
            
            # 管道连接完成
            self.pipe_connected = True
            self.status_label.config(
                text="任务状态：管道连接成功！请点击两个旋钮完成校准",
                fg="#27ae60"
            )
            # 高亮元素
            self.canvas.itemconfig("fuel_out", fill="#27ae60")
            self.canvas.itemconfig("fuel_in", fill="#c0392b")
            # 启用旋钮
            self.knob1_canvas.config(state=tk.NORMAL)
            self.knob2_canvas.config(state=tk.NORMAL)
            # 取消鼠标移动事件（管道已连接完成）
            self.canvas.unbind("<Motion>")

    def rotate_knob(self, knob_idx):
        """旋转旋钮"""
        if not self.pipe_connected or self.task_completed or self.window_closed:
            return
        
        # 更新旋钮状态
        self.knob_states[knob_idx] = 1
        if knob_idx == 0:
            self.knob1_canvas.itemconfig(self.knob1_arc, extent=270, fill="#3498db", width=4)
        else:
            self.knob2_canvas.itemconfig(self.knob2_arc, extent=270, fill="#3498db", width=4)
        
        # 检查完成状态
        if all(self.knob_states):
            self.task_completed = True
            self.status_label.config(text="任务状态：校准成功！", fg="#00ff00")
            # 关键：弹窗关联任务窗口，且只关闭任务窗口，不影响主GUI
            messagebox.showinfo(
                "任务完成", 
                "🎉 上升引擎校准成功！",
                parent=self.task_window
            )
            # 安全关闭任务窗口（仅关闭子窗口）
            self.safe_close_window()
        else:
            self.status_label.config(
                text=f"任务状态：旋钮{knob_idx+1}已到位，还需调整另一个旋钮",
                fg="#ff8800"
            )


class RepairReactorTask(Task):
    """修复反应堆任务（完整可运行版）"""
    def __init__(self):
        # 核心修改：location 为 "反应堆" 而非 "反应堆室"
        super().__init__(name="修复反应堆", location="反应堆", difficulty=3)
        
        # 任务核心状态
        self.task_completed = False       # 任务是否真正完成（区别于基础类的is_completed）
        self.temperature = 500            # 初始温度
        self.temp_increase_rate = 100     # 每秒升温100℃
        self.cool_down_step = 50          # 点击风扇降温50℃
        self.min_temp = 100               # 停止升温阈值（100℃以下）
        self.is_temp_increasing = True    # 是否继续升温
        self.fan_rotating = False         # 风扇是否旋转
        self.fan_rotation_angle = 0       # 风扇旋转角度
        
        # 零件相关配置
        self.part_count = random.randint(3, 4)  # 随机3-4个零件
        self.parts = []                         # 存储零件信息
        self.parts_placed = 0                   # 已放入反应堆的零件数
        self.reactor_area = (100, 100, 250, 300)# 反应堆区域（x1,y1,x2,y2）
        
        # UI相关变量
        self.task_window = None          # 任务窗口
        self.canvas = None               # 主画布
        self.temp_label = None           # 温度显示标签
        self.status_label = None         # 状态提示标签
        self.is_running = False          # 窗口是否运行
        self.window_closed = False       # 窗口是否关闭
        self.fan_ring_id = None          # 风扇灰色圆环ID（仅圆环可点击）
        self.fan_blade_ids = []          # 扇叶ID列表
        self.drag_data = {               # 零件拖拽数据
            "part_id": None, 
            "x": 0, 
            "y": 0
        }
        self.fan_stop_timer = None       # 风扇旋转定时器

    def run_task_gui(self, main_root=None) -> bool:
        """
        运行修复反应堆GUI
        :param main_root: 主窗口引用（解决弹窗层级问题）
        :return: 任务是否真正完成（仅所有零件放入后返回True）
        """
        # 重置任务状态（关键：每次打开窗口都重置）
        self.task_completed = False
        self.temperature = 500
        self.is_temp_increasing = True
        self.parts_placed = 0
        self.fan_rotation_angle = 0
        self.fan_rotating = False
        self.window_closed = False
        self.parts = []
        self.fan_blade_ids = []
        
        # 检查窗口是否已打开
        if self.is_running:
            messagebox.showinfo("提示", "修复反应堆任务窗口已打开！", parent=main_root)
            return False
        
        self.is_running = True

        try:
            # 创建任务窗口（依赖主窗口，避免独立弹窗）
            if main_root and isinstance(main_root, tk.Tk):
                self.task_window = tk.Toplevel(main_root)
                self.task_window.transient(main_root)  # 设置为子窗口
            else:
                self.task_window = tk.Toplevel()
            
            # 窗口基础配置
            self.task_window.title("修复反应堆")
            self.task_window.geometry("800x500")
            self.task_window.configure(bg="#1a2b4a")  # 深蓝色背景
            self.task_window.resizable(False, False)  # 固定尺寸
            
            # 窗口关闭事件（关键：关闭时标记任务未完成）
            def on_window_close():
                self.window_closed = True
                self.is_running = False
                self.task_completed = False  # 关闭窗口=任务未完成
                self.task_window.destroy()
            
            self.task_window.protocol("WM_DELETE_WINDOW", on_window_close)

            # ========== 创建主画布（蓝色底板） ==========
            self.canvas = tk.Canvas(
                self.task_window,
                width=780,
                height=480,
                bg="#2c3e50",  # 浅蓝色底板
                highlightthickness=0
            )
            self.canvas.pack(pady=10)

            # ========== 绘制核心UI元素 ==========
            self.draw_reactor()       # 绘制左侧反应堆
            self.draw_fan()           # 绘制右侧风扇
            self.draw_parts()         # 绘制右侧零件

            # ========== 温度显示标签 ==========
            self.temp_label = tk.Label(
                self.task_window,
                text=f"反应堆温度：{self.temperature}℃",
                font=("SimHei", 16, "bold"),
                bg="#1a2b4a",
                fg="#ff3333"  # 红色字体
            )
            self.temp_label.place(x=50, y=20)

            # ========== 任务状态提示标签 ==========
            self.status_label = tk.Label(
                self.task_window,
                text="任务状态：点击风扇灰色圆环降低反应堆温度至100℃以下",
                font=("SimHei", 12, "bold"),
                bg="#1a2b4a",
                fg="#ffffff",
                wraplength=700
            )
            self.status_label.place(x=50, y=430, width=700, height=40)

            # ========== 绑定事件 ==========
            self.canvas.bind("<Button-1>", self.on_click)
            # 仅绑定风扇灰色圆环的点击事件（核心）
            if self.fan_ring_id:
                self.canvas.tag_bind(self.fan_ring_id, "<Button-1>", self.on_fan_click)
            # 零件拖拽事件
            self.canvas.tag_bind("part", "<ButtonPress-1>", self.on_part_drag_start)
            self.canvas.tag_bind("part", "<B1-Motion>", self.on_part_drag_move)
            self.canvas.tag_bind("part", "<ButtonRelease-1>", self.on_part_drag_end)

            # ========== 启动循环 ==========
            self.update_temperature()   # 温度更新循环
            self.update_fan_animation() # 风扇动画循环

            # 显示窗口并等待关闭
            self.task_window.update_idletasks()
            self.task_window.lift()
            self.task_window.focus_force()
            self.task_window.wait_window()  # 阻塞直到窗口关闭

            # ========== 任务完成后同步状态 ==========
            if self.task_completed:
                self.is_completed = True  # 同步基础类的完成状态

            # 返回最终任务状态（仅完成时返回True）
            return self.task_completed

        except Exception as e:
            print(f"修复反应堆任务执行异常：{str(e)}")
            messagebox.showerror("错误", f"任务窗口创建失败：{str(e)}", parent=main_root)
            self.is_running = False
            self.window_closed = True
            self.task_completed = False
            return False

    def draw_reactor(self):
        """绘制左侧简易反应堆形状"""
        rx1, ry1, rx2, ry2 = self.reactor_area
        
        # 反应堆主体（圆柱形）
        self.canvas.create_rectangle(
            rx1, ry1, rx2, ry2,
            fill="#34495e",
            outline="#ffffff",
            width=4,
            tags="reactor"
        )
        
        # 反应堆核心（圆形）
        core_x = (rx1 + rx2) / 2
        core_y = (ry1 + ry2) / 2
        self.canvas.create_oval(
            core_x - 50, core_y - 50,
            core_x + 50, core_y + 50,
            fill="#e74c3c",
            outline="#ffcc00",
            width=3,
            tags="reactor_core"
        )
        
        # 散热片（8片）
        for i in range(8):
            angle = math.radians(i * 45)
            x1 = core_x + 60 * math.cos(angle)
            y1 = core_y + 60 * math.sin(angle)
            x2 = core_x + 80 * math.cos(angle)
            y2 = core_y + 80 * math.sin(angle)
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill="#ffffff",
                width=2,
                tags="reactor_fin"
            )

    def draw_fan(self):
        """绘制右侧风扇（仅扇叶旋转，圆环固定）"""
        cx, cy = (600, 180)  # 风扇中心
        fan_radius = 60
        
        # 1. 风扇灰色圆环（仅这个可点击，单独记录ID）
        if not self.fan_ring_id:
            self.fan_ring_id = self.canvas.create_oval(
                cx - fan_radius - 5, cy - fan_radius - 5,
                cx + fan_radius + 5, cy + fan_radius + 5,
                fill="#7f8c8d",    # 灰色
                outline="#ffffff",
                width=2,
                tags="fan_frame"
            )
        
        # 2. 风扇轴心（仅绘制一次）
        if not self.canvas.find_withtag("fan_axis"):
            self.canvas.create_oval(
                cx - 8, cy - 8,
                cx + 8, cy + 8,
                fill="#2c3e50",
                outline="#ffffff",
                width=2,
                tags="fan_axis"
            )
        
        # 3. 扇叶（4片，每次绘制都删除旧扇叶）
        if self.fan_blade_ids:
            for blade_id in self.fan_blade_ids:
                self.canvas.delete(blade_id)
            self.fan_blade_ids = []
        
        for i in range(4):
            angle = math.radians(self.fan_rotation_angle + i * 90)
            x1 = cx + 10 * math.cos(angle)
            y1 = cy + 10 * math.sin(angle)
            x2 = cx + fan_radius * math.cos(angle)
            y2 = cy + fan_radius * math.sin(angle)
            
            # 绘制扇叶（多边形）
            blade = self.canvas.create_polygon(
                cx, cy,
                x1 + 15 * math.cos(angle + math.radians(30)),
                y1 + 15 * math.sin(angle + math.radians(30)),
                x2, y2,
                x1 + 15 * math.cos(angle - math.radians(30)),
                y1 + 15 * math.sin(angle - math.radians(30)),
                fill="#bdc3c7",
                outline="#ffffff",
                width=1,
                tags="fan_blade"
            )
            self.fan_blade_ids.append(blade)

    def draw_parts(self):
        """绘制3-4个螺母状零件（整体化设计，防止错位）"""
        start_x = 500
        start_y = 300
        part_size = 30
        
        for i in range(self.part_count):
            x = start_x + i * 80
            y = start_y
            part_group = []  # 存储单个零件的所有元素ID
            
            # 螺母外圈
            outer = self.canvas.create_oval(
                x - part_size, y - part_size,
                x + part_size, y + part_size,
                fill="#95a5a6",
                outline="#ffffff",
                width=2,
                tags=("part", f"part_{i}")
            )
            part_group.append(outer)
            
            # 螺母内圈
            inner = self.canvas.create_oval(
                x - 10, y - 10,
                x + 10, y + 10,
                fill="#7f8c8d",
                outline="#ffffff",
                width=1,
                tags=("part", f"part_{i}")
            )
            part_group.append(inner)
            
            # 螺母螺纹（4条线）
            for j in range(4):
                angle = math.radians(j * 90)
                line = self.canvas.create_line(
                    x + 12 * math.cos(angle), y + 12 * math.sin(angle),
                    x + 25 * math.cos(angle), y + 25 * math.sin(angle),
                    fill="#ffffff",
                    width=1,
                    tags=("part", f"part_{i}")
                )
                part_group.append(line)
            
            # 存储零件信息
            self.parts.append({
                "id": f"part_{i}",
                "group": part_group,
                "pos": (x, y),
                "placed": False  # 是否已放入反应堆
            })

    def update_temperature(self):
        """更新反应堆温度（每秒一次）"""
        if self.window_closed:
            return
        
        # 仅在温度≥100℃时升温
        if self.is_temp_increasing and self.temperature >= self.min_temp:
            self.temperature += self.temp_increase_rate
            self.temp_label.config(text=f"反应堆温度：{self.temperature}℃")
            
            # 高温警告（超过1000℃）
            if self.temperature > 1000:
                self.status_label.config(
                    text="警告：温度过高！立即点击风扇灰色圆环降温！",
                    fg="#ff3333"
                )
        elif self.temperature < self.min_temp and self.is_temp_increasing:
            # 温度降至安全值，停止升温
            self.is_temp_increasing = False
            self.status_label.config(
                text="任务状态：温度已降至安全值！请将所有零件拖入反应堆完成修复",
                fg="#2ecc71"
            )
        
        # 继续循环（1秒后更新）
        if not self.window_closed:
            self.task_window.after(1000, self.update_temperature)

    def update_fan_animation(self):
        """更新风扇旋转动画（每50ms一次）"""
        if self.window_closed:
            return
        
        # 仅在风扇旋转时更新扇叶
        if self.fan_rotating:
            self.fan_rotation_angle += 10
            if self.fan_rotation_angle >= 360:
                self.fan_rotation_angle = 0
            self.draw_fan()  # 重绘扇叶
        
        # 继续动画循环
        self.task_window.after(50, self.update_fan_animation)

    def on_fan_click(self, event):
        """点击风扇灰色圆环触发降温+旋转"""
        if self.window_closed or not self.is_temp_increasing:
            return
        
        # 降温（每次点击降50℃，最低0℃）
        self.temperature -= self.cool_down_step
        if self.temperature < 0:
            self.temperature = 0
        
        # 更新温度显示
        self.temp_label.config(text=f"反应堆温度：{self.temperature}℃")
        
        # 更新状态提示
        if self.temperature >= self.min_temp:
            self.status_label.config(
                text=f"任务状态：风扇已启动！当前温度{self.temperature}℃，继续点击圆环降温至100℃以下",
                fg="#3498db"
            )
        else:
            self.status_label.config(
                text="任务状态：温度已降至安全值！请将所有零件拖入反应堆完成修复",
                fg="#2ecc71"
            )
        
        # 启动风扇旋转（持续2秒，取消旧定时器避免叠加）
        self.fan_rotating = True
        if self.fan_stop_timer:
            self.task_window.after_cancel(self.fan_stop_timer)
        self.fan_stop_timer = self.task_window.after(2000, lambda: setattr(self, "fan_rotating", False))

    def on_part_drag_start(self, event):
        """开始拖拽零件"""
        if self.window_closed:
            return
        
        # 找到被点击的未放置零件
        for part in self.parts:
            if not part["placed"] and self.canvas.find_closest(event.x, event.y)[0] in part["group"]:
                self.drag_data["part_id"] = part["id"]
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                break

    def on_part_drag_move(self, event):
        """拖拽零件移动"""
        if not self.drag_data["part_id"] or self.window_closed:
            return
        
        # 计算偏移量
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        # 移动零件所有元素
        for part in self.parts:
            if part["id"] == self.drag_data["part_id"] and not part["placed"]:
                for item in part["group"]:
                    self.canvas.move(item, dx, dy)
                # 更新零件位置
                part["pos"] = (part["pos"][0] + dx, part["pos"][1] + dy)
                break
        
        # 更新拖拽起始位置
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_part_drag_end(self, event):
        """结束拖拽，检查是否放入反应堆"""
        if not self.drag_data["part_id"] or self.window_closed:
            self.drag_data = {"part_id": None, "x": 0, "y": 0}
            return
        
        rx1, ry1, rx2, ry2 = self.reactor_area
        
        # 检查零件是否拖入反应堆区域
        for part in self.parts:
            if part["id"] == self.drag_data["part_id"] and not part["placed"]:
                px, py = part["pos"]
                if rx1 <= px <= rx2 and ry1 <= py <= ry2:
                    # 标记零件为已放置
                    part["placed"] = True
                    self.parts_placed += 1
                    
                    # 锁定零件（不可再拖拽）
                    for item in part["group"]:
                        self.canvas.itemconfig(item, state=tk.DISABLED)
                    
                    # 更新状态提示
                    self.status_label.config(
                        text=f"任务状态：已放入{self.parts_placed}/{self.part_count}个零件，继续放入剩余零件",
                        fg="#3498db"
                    )
                    
                    # 检查是否所有零件都已放入（任务完成）
                    if self.parts_placed == self.part_count:
                        self.task_completed = True  # 标记任务完成
                        self.is_completed = True    # 同步基础类状态
                        self.status_label.config(
                            text="任务状态：所有零件已安装完成！反应堆修复成功！",
                            fg="#2ecc71"
                        )
                        # 关闭窗口并提示
                        messagebox.showinfo("任务完成", "🎉 反应堆修复成功！", parent=self.task_window)
                        self.task_window.destroy()
                        self.is_running = False
                        self.window_closed = True
        
        # 重置拖拽数据
        self.drag_data = {"part_id": None, "x": 0, "y": 0}

    def on_click(self, event):
        """通用点击事件（无操作）"""
        pass


class RefuelTask(Task):
    """燃料补给任务（带图形化交互）"""
    
    def __init__(self):
        super().__init__("燃料补给", "燃料室", 1)
        self.task_completed = False  # 任务完成状态
        self.task_window = None      # 任务窗口对象
        self.fuel_barrel_id = None   # 燃油桶ID（红色油桶）
        self.barrel_ids = []         # 所有油桶ID列表

    def run_task_gui(self, main_root=None) -> bool:
        """
        运行燃料补给的图形化任务界面
        :param main_root: 主窗口对象（可选）
        :return: 任务是否完成
        """
        # 重置状态
        self.task_completed = False
        self.fuel_barrel_id = None
        self.barrel_ids = []
        
        # 确保只创建一个任务窗口
        if self.task_window and (
            (isinstance(self.task_window, tk.Toplevel) and tk.Toplevel.winfo_exists(self.task_window)) or
            (isinstance(self.task_window, tk.Tk) and tk.Tk.winfo_exists(self.task_window))
        ):
            self.task_window.lift()
            return False
        
        # 创建窗口（优先使用Toplevel依附主窗口）
        if main_root and isinstance(main_root, tk.Tk):
            self.task_window = tk.Toplevel(main_root)
        else:
            self.task_window = tk.Tk()  # 无主窗口时创建独立窗口
        
        root = self.task_window
        root.title("燃料室 - 燃料补给")
        root.geometry("800x600")
        root.configure(bg="#1a1a2e")
        root.resizable(False, False)
        root.wm_attributes("-topmost", True)

        # 窗口关闭协议
        root.protocol("WM_DELETE_WINDOW", lambda: self._cleanup_window(root))

        # 中文字体（增加兼容性）
        font_family = "SimHei"
        try:
            tk.font.Font(family=font_family, size=12)
        except:
            font_family = "Arial"

        # ========== 主画布 ==========
        main_canvas = tk.Canvas(
            root,
            width=780,
            height=580,
            bg="#ffffff",
            highlightthickness=2,
            highlightbackground="#e94560"
        )
        main_canvas.pack(pady=10, padx=10)

        # ========== 绘制灰色底板（横向三等分） ==========
        # 底板整体尺寸
        board_x1, board_y1 = 40, 40
        board_x2, board_y2 = 740, 540
        board_width = board_x2 - board_x1
        board_height = board_y2 - board_y1
        
        # 绘制灰色底板
        main_canvas.create_rectangle(
            board_x1, board_y1, board_x2, board_y2,
            fill="#7f8c8d", outline="#000000", width=2,
            tags="board"
        )
        
        # 横向三等分，绘制5px宽黑色分隔条
        # 第一条分隔线（1/3位置）
        split1_y = board_y1 + board_height / 3
        main_canvas.create_rectangle(
            board_x1, split1_y - 2.5,  # 上下各2.5px，总宽度5px
            board_x2, split1_y + 2.5,
            fill="#000000", outline="",
            tags="split_line"
        )
        
        # 第二条分隔线（2/3位置）
        split2_y = board_y1 + 2 * board_height / 3
        main_canvas.create_rectangle(
            board_x1, split2_y - 2.5,
            board_x2, split2_y + 2.5,
            fill="#000000", outline="",
            tags="split_line"
        )

        # ========== 生成随机颜色列表（普通油桶用） ==========
        def generate_random_color():
            """生成随机柔和颜色（避免太亮/太暗）"""
            r = random.randint(100, 220)
            g = random.randint(100, 220)
            b = random.randint(100, 220)
            return f"#{r:02x}{g:02x}{b:02x}"
        
        # 生成8个随机颜色（9个油桶-1个燃油桶）
        random_colors = [generate_random_color() for _ in range(8)]

        # ========== 绘制9个长方形油桶（3行3列平均分配，所有油桶带棕色盖子） ==========
        # 计算每个油桶的位置和尺寸
        # 每行高度（减去分隔条）
        row_height = (board_height - 10) / 3  # 10=2条分隔条总高度
        # 每列宽度
        col_width = board_width / 3
        
        # 长方形油桶尺寸
        barrel_width = col_width * 0.7    # 宽度
        barrel_height = row_height * 0.7  # 高度
        # 统一的棕色盖子尺寸
        lid_height = barrel_height * 0.15  # 盖子高度
        lid_offset = barrel_width * 0.1    # 盖子左右偏移

        # 随机选择一个油桶作为燃油桶（红色）
        fuel_row = random.randint(0, 2)
        fuel_col = random.randint(0, 2)
        
        color_idx = 0  # 随机颜色索引
        # 绘制3行3列油桶
        for row in range(3):
            for col in range(3):
                # 计算油桶左上角坐标
                # 行偏移（考虑分隔条）
                row_offset = board_y1 + row * (row_height + 5) + (row_height - barrel_height) / 2
                # 列偏移
                col_offset = board_x1 + col * col_width + (col_width - barrel_width) / 2
                
                # 判断是否是燃油桶
                is_fuel = (row == fuel_row) and (col == fuel_col)
                
                # ========== 绘制长方形油桶主体 ==========
                if is_fuel:
                    # 燃油桶：红色主体
                    barrel_color = "#ff0000"  # 红色桶身
                    outline_color = "#cc0000"
                    barrel_id = main_canvas.create_rectangle(
                        col_offset, row_offset,
                        col_offset + barrel_width, row_offset + barrel_height,
                        fill=barrel_color, outline=outline_color, width=2,
                        tags="fuel_barrel"
                    )
                    self.fuel_barrel_id = barrel_id
                else:
                    # 普通油桶：随机颜色
                    barrel_color = random_colors[color_idx]
                    color_idx += 1
                    outline_color = "#333333"
                    barrel_id = main_canvas.create_rectangle(
                        col_offset, row_offset,
                        col_offset + barrel_width, row_offset + barrel_height,
                        fill=barrel_color, outline=outline_color, width=2,
                        tags="barrel"
                    )
                    self.barrel_ids.append(barrel_id)
                
                # ========== 为所有油桶添加统一的棕色盖子 ==========
                # 盖子底座（棕色，略窄于桶身）
                lid_x1 = col_offset + lid_offset
                lid_y1 = row_offset - lid_height
                lid_x2 = col_offset + barrel_width - lid_offset
                lid_y2 = row_offset
                main_canvas.create_rectangle(
                    lid_x1, lid_y1, lid_x2, lid_y2,
                    fill="#8B4513", outline="#5D2906", width=1,
                    tags="barrel_lid" if not is_fuel else "fuel_lid"
                )
                
                # ========== 盖子提手（所有油桶都有，燃油桶提手更粗） ==========
                handle_y = lid_y1 + lid_height / 2
                handle_x1 = lid_x1 + (lid_x2 - lid_x1) * 0.3
                handle_x2 = lid_x1 + (lid_x2 - lid_x1) * 0.7
                if is_fuel:
                    # 燃油桶提手更粗，颜色更深
                    main_canvas.create_line(
                        handle_x1, handle_y, handle_x2, handle_y,
                        fill="#5D2906", width=3,
                        tags="fuel_lid_handle"
                    )
                else:
                    # 普通油桶提手
                    main_canvas.create_line(
                        handle_x1, handle_y, handle_x2, handle_y,
                        fill="#5D2906", width=2,
                        tags="barrel_lid_handle"
                    )
                
                # ========== 油桶高光（模拟立体感） ==========
                highlight_width = barrel_width * 0.1
                highlight_height = barrel_height * 0.8
                main_canvas.create_rectangle(
                    col_offset + 5, row_offset + 5,
                    col_offset + 5 + highlight_width, row_offset + 5 + highlight_height,
                    fill="#ffffff", outline="", stipple="gray50",
                    tags="barrel_highlight"
                )

        # ========== 任务状态标签 ==========
        status_label = tk.Label(
            root,
            text="任务状态：未完成（找到并点击红色燃油桶）",
            font=(font_family, 14, "bold"),
            bg="#1a1a2e",
            fg="#ffffff",
            wraplength=780
        )
        status_label.pack(pady=5)

        # ========== 鼠标点击事件 ==========
        def on_barrel_click(event):
            """点击油桶事件处理"""
            if self.task_completed:
                return
                
            # 获取点击的对象
            clicked_items = main_canvas.find_closest(event.x, event.y)
            if not clicked_items:
                return
            
            clicked_id = clicked_items[0]
            
            # 检查是否点击了燃油桶（桶身/盖子/提手）
            tags = main_canvas.gettags(clicked_id)
            if "fuel_barrel" in tags or "fuel_lid" in tags or "fuel_lid_handle" in tags:
                # 标记任务完成
                self.task_completed = True
                self.complete()
                
                # 更新状态标签
                status_label.config(
                    text="任务状态：燃料补给成功！",
                    fg="#00ff00"
                )
                
                # 禁用所有油桶点击（修改光标样式）
                main_canvas.config(cursor="arrow")
                
                # 弹出完成提示
                def show_complete_msg():
                    messagebox.showinfo("任务完成", "🎉 燃料补给成功！", parent=root)
                    self._cleanup_window(root)
                
                # 异步显示提示框
                root.after(100, show_complete_msg)

        # 绑定点击事件
        main_canvas.bind("<Button-1>", on_barrel_click)
        # 设置手型光标
        main_canvas.config(cursor="hand2")

        # 启动主循环
        try:
            root.mainloop()
        except Exception as e:
            print(f"燃料补给任务GUI运行错误: {e}")
            self.task_completed = False

        # 返回任务完成状态
        final_result = self.task_completed
        # 重置窗口引用
        self.task_window = None
        return final_result

    def _cleanup_window(self, root):
        """窗口清理函数"""
        if root:
            try:
                root.quit()
                root.after(100, root.destroy)
            except:
                pass



class StartSatelliteTask(Task):
    """启动卫星任务（监控室 - 方向按键控制仿真卫星移动到空心红圈）"""
    def __init__(self):
        super().__init__(name="启动卫星", location="监控室", difficulty=3)
        
        # 任务核心状态
        self.task_completed = False       # 任务是否完成
        self.is_running = False           # 窗口是否运行
        self.window_closed = False        # 窗口是否关闭
        self.satellite_active = False     # 卫星是否启动（点击红色按钮后激活）
        
        # UI尺寸配置
        self.WINDOW_WIDTH = 800
        self.WINDOW_HEIGHT = 600
        self.TOP_AREA_HEIGHT = int(self.WINDOW_HEIGHT * 3/4)  # 上3/4区域高度
        self.BOTTOM_AREA_HEIGHT = self.WINDOW_HEIGHT - self.TOP_AREA_HEIGHT  # 下1/4区域高度
        
        # 颜色配置
        self.BASE_COLOR = "#0a1929"       # 深蓝色底板
        self.FRAME_COLOR = "#ffffff"      # 上区域边框颜色
        self.START_BUTTON_COLOR = "#ff3333"  # 红色启动按钮
        self.RED_CIRCLE_COLOR = "#ff0000" # 中心红圈
        self.SATELLITE_MAIN_COLOR = "#ffffff"  # 卫星主体颜色
        self.SATELLITE_WING_COLOR = "#cccccc"  # 卫星侧翼颜色
        self.DIR_BUTTON_COLOR = "#444444" # 方向按键底色
        self.DIR_BUTTON_PRESS = "#888888" # 方向按键按下色
        
        # 卫星配置（仿真样式：半圆+主体+侧翼）
        self.satellite_main_width = 40    # 卫星主体宽度
        self.satellite_main_height = 30   # 卫星主体高度
        self.satellite_wing_width = 25    # 侧翼宽度
        self.satellite_wing_height = 10   # 侧翼高度
        self.satellite_x = 0              # 卫星中心X坐标
        self.satellite_y = 0              # 卫星中心Y坐标
        self.satellite_speed = 8          # 卫星移动速度
        self.satellite_ids = []           # 卫星所有部件ID列表
        
        # 中心红圈配置（空心）
        self.circle_radius = 40           # 红圈半径
        self.circle_border_width = 4      # 红圈边框宽度
        self.circle_x = self.WINDOW_WIDTH // 2
        self.circle_y = self.TOP_AREA_HEIGHT // 2
        self.circle_id = None             # 红圈画布ID
        
        # 按钮配置
        self.start_button_id = None       # 启动按钮ID
        self.dir_buttons = {}             # 方向按键ID字典
        self.canvas = None                # 主画布
        self.task_window = None           # 任务窗口
        self.status_text_id = None        # 状态文本ID

    def run_task_gui(self, main_root=None) -> bool:
        """运行启动卫星GUI任务"""
        # 重置任务状态
        self.task_completed = False
        self.is_running = True
        self.window_closed = False
        self.satellite_active = False
        self.satellite_ids = []
        
        try:
            # 创建窗口（兼容主窗口/独立运行）
            if main_root and isinstance(main_root, tk.Tk):
                self.task_window = tk.Toplevel(main_root)
                self.task_window.transient(main_root)
                self.task_window.attributes('-topmost', True)
            else:
                self.task_window = tk.Tk()
            
            # 窗口配置
            self.task_window.title("启动卫星任务")
            self.task_window.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
            self.task_window.resizable(False, False)
            self.task_window.configure(bg=self.BASE_COLOR)
            
            # 关闭事件
            def on_close():
                self.window_closed = True
                self.is_running = False
                self.task_completed = False
                self.task_window.destroy()
                if not main_root:
                    self.task_window.quit()
            
            self.task_window.protocol("WM_DELETE_WINDOW", on_close)

            # 创建主画布
            self.canvas = tk.Canvas(
                self.task_window,
                width=self.WINDOW_WIDTH,
                height=self.WINDOW_HEIGHT,
                bg=self.BASE_COLOR,
                highlightthickness=0
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)

            # 初始化UI元素
            self._draw_top_frame()         # 绘制上3/4区域边框
            self._draw_red_circle()        # 绘制空心中心红圈
            self._generate_satellite()     # 随机生成卫星位置
            self._draw_satellite()         # 绘制仿真卫星
            self._draw_start_button()      # 绘制红色启动按钮
            self._draw_dir_buttons()       # 绘制上下左右方向按键
            self._bind_events()            # 绑定交互事件

            # 启动窗口循环
            if main_root:
                self.task_window.wait_window()
            else:
                self.task_window.mainloop()

            # 同步任务状态
            if self.task_completed:
                self.is_completed = True
            return self.task_completed

        except Exception as e:
            print(f"启动卫星任务异常: {str(e)}")
            messagebox.showerror("错误", f"任务启动失败：{str(e)}", parent=main_root if main_root else None)
            return False

    def _draw_top_frame(self):
        """绘制上3/4区域的边框"""
        self.canvas.create_rectangle(
            10, 10,
            self.WINDOW_WIDTH - 10, self.TOP_AREA_HEIGHT - 10,
            outline=self.FRAME_COLOR,
            width=3,
            tags="top_frame"
        )

    def _draw_red_circle(self):
        """绘制空心的中心红色圆圈（半径40像素，仅边框）"""
        # 空心红圈（仅绘制边框，无填充）
        self.circle_id = self.canvas.create_oval(
            self.circle_x - self.circle_radius, self.circle_y - self.circle_radius,
            self.circle_x + self.circle_radius, self.circle_y + self.circle_radius,
            outline=self.RED_CIRCLE_COLOR,
            fill="",  # 空心：无填充
            width=self.circle_border_width,  # 加粗边框
            tags="red_circle"
        )
        # 红圈中心小点（便于对齐）
        self.canvas.create_oval(
            self.circle_x - 3, self.circle_y - 3,
            self.circle_x + 3, self.circle_y + 3,
            fill=self.RED_CIRCLE_COLOR,
            width=1,
            tags="circle_center"
        )
        # 红圈辅助虚线（可选）
        self.canvas.create_line(
            self.circle_x - self.circle_radius - 10, self.circle_y,
            self.circle_x + self.circle_radius + 10, self.circle_y,
            fill=self.RED_CIRCLE_COLOR,
            width=1,
            dash=(2, 2),
            tags="circle_line"
        )
        self.canvas.create_line(
            self.circle_x, self.circle_y - self.circle_radius - 10,
            self.circle_x, self.circle_y + self.circle_radius + 10,
            fill=self.RED_CIRCLE_COLOR,
            width=1,
            dash=(2, 2),
            tags="circle_line"
        )

    def _generate_satellite(self):
        """随机生成卫星位置（限制在上3/4区域内）"""
        # 随机X坐标（避开边界，预留卫星尺寸）
        self.satellite_x = random.randint(
            self.satellite_main_width + 40,
            self.WINDOW_WIDTH - self.satellite_main_width - 40
        )
        # 随机Y坐标（限制在上3/4区域内）
        self.satellite_y = random.randint(
            self.satellite_main_height + 40,
            self.TOP_AREA_HEIGHT - self.satellite_main_height - 40
        )

    def _draw_satellite(self):
        """绘制仿真卫星（半圆+主体长方形+左右侧翼长方形）"""
        # 清空原有卫星部件
        for sid in self.satellite_ids:
            self.canvas.delete(sid)
        self.satellite_ids = []
        
        # ========== 1. 卫星主体：底部长方形 + 顶部半圆 ==========
        # 主体长方形（中心向下偏移，为半圆预留空间）
        rect_y_offset = self.satellite_main_height // 4
        main_rect = self.canvas.create_rectangle(
            self.satellite_x - self.satellite_main_width//2,
            self.satellite_y - self.satellite_main_height//2 + rect_y_offset,
            self.satellite_x + self.satellite_main_width//2,
            self.satellite_y + self.satellite_main_height//2 + rect_y_offset,
            fill=self.SATELLITE_MAIN_COLOR,
            outline="#000000",
            width=1,
            tags="satellite_main"
        )
        self.satellite_ids.append(main_rect)
        
        # 顶部半圆（覆盖长方形上边缘）
        semi_circle = self.canvas.create_arc(
            self.satellite_x - self.satellite_main_width//2,
            self.satellite_y - self.satellite_main_height//2 - self.satellite_main_height//2 + rect_y_offset,
            self.satellite_x + self.satellite_main_width//2,
            self.satellite_y + self.satellite_main_height//2 - self.satellite_main_height//2 + rect_y_offset,
            start=180, extent=180,  # 上半圆
            fill=self.SATELLITE_MAIN_COLOR,
            outline="#000000",
            width=1,
            tags="satellite_semicircle"
        )
        self.satellite_ids.append(semi_circle)
        
        # ========== 2. 左侧侧翼长方形 ==========
        left_wing_x = self.satellite_x - self.satellite_main_width//2 - self.satellite_wing_width
        left_wing = self.canvas.create_rectangle(
            left_wing_x,
            self.satellite_y - self.satellite_wing_height//2,
            left_wing_x + self.satellite_wing_width,
            self.satellite_y + self.satellite_wing_height//2,
            fill=self.SATELLITE_WING_COLOR,
            outline="#000000",
            width=1,
            tags="satellite_wing_left"
        )
        self.satellite_ids.append(left_wing)
        
        # ========== 3. 右侧侧翼长方形 ==========
        right_wing_x = self.satellite_x + self.satellite_main_width//2
        right_wing = self.canvas.create_rectangle(
            right_wing_x,
            self.satellite_y - self.satellite_wing_height//2,
            right_wing_x + self.satellite_wing_width,
            self.satellite_y + self.satellite_wing_height//2,
            fill=self.SATELLITE_WING_COLOR,
            outline="#000000",
            width=1,
            tags="satellite_wing_right"
        )
        self.satellite_ids.append(right_wing)
        
        # ========== 4. 卫星细节：天线小点 ==========
        antenna = self.canvas.create_oval(
            self.satellite_x - 2,
            self.satellite_y - self.satellite_main_height//2 - self.satellite_main_height//4 + rect_y_offset,
            self.satellite_x + 2,
            self.satellite_y - self.satellite_main_height//2 + rect_y_offset,
            fill="#000000",
            tags="satellite_antenna"
        )
        self.satellite_ids.append(antenna)

    def _draw_start_button(self):
        """绘制下1/4区域的红色启动按钮"""
        button_width = 120
        button_height = 60
        button_x = 80
        button_y = self.TOP_AREA_HEIGHT + self.BOTTOM_AREA_HEIGHT // 2
        
        # 按钮主体
        self.start_button_id = self.canvas.create_rectangle(
            button_x - button_width//2, button_y - button_height//2,
            button_x + button_width//2, button_y + button_height//2,
            fill=self.START_BUTTON_COLOR,
            outline="#ffffff",
            width=2,
            tags="start_button"
        )
        # 按钮文字
        self.canvas.create_text(
            button_x, button_y,
            text="启动卫星",
            fill="#ffffff",
            font=("SimHei", 14, "bold"),
            tags="start_button_text"
        )

    def _draw_dir_buttons(self):
        """绘制上下左右四个方向按键"""
        btn_size = 50  # 按键尺寸
        center_x = self.WINDOW_WIDTH - 150  # 方向按键组中心X
        center_y = self.TOP_AREA_HEIGHT + self.BOTTOM_AREA_HEIGHT // 2  # 中心Y
        
        # 上按键
        up_btn = self.canvas.create_rectangle(
            center_x - btn_size//2, center_y - btn_size - 10,
            center_x + btn_size//2, center_y - 10,
            fill=self.DIR_BUTTON_COLOR,
            outline="#ffffff",
            width=2,
            tags="dir_up"
        )
        self.canvas.create_text(
            center_x, center_y - btn_size//2 - 10,
            text="↑", fill="#ffffff", font=("SimHei", 16, "bold"), tags="dir_up_text"
        )
        self.dir_buttons['up'] = up_btn
        
        # 下按键
        down_btn = self.canvas.create_rectangle(
            center_x - btn_size//2, center_y + 10,
            center_x + btn_size//2, center_y + btn_size + 10,
            fill=self.DIR_BUTTON_COLOR,
            outline="#ffffff",
            width=2,
            tags="dir_down"
        )
        self.canvas.create_text(
            center_x, center_y + btn_size//2 + 10,
            text="↓", fill="#ffffff", font=("SimHei", 16, "bold"), tags="dir_down_text"
        )
        self.dir_buttons['down'] = down_btn
        
        # 左按键
        left_btn = self.canvas.create_rectangle(
            center_x - btn_size - 10, center_y - btn_size//2,
            center_x - 10, center_y + btn_size//2,
            fill=self.DIR_BUTTON_COLOR,
            outline="#ffffff",
            width=2,
            tags="dir_left"
        )
        self.canvas.create_text(
            center_x - btn_size//2 - 10, center_y,
            text="←", fill="#ffffff", font=("SimHei", 16, "bold"), tags="dir_left_text"
        )
        self.dir_buttons['left'] = left_btn
        
        # 右按键
        right_btn = self.canvas.create_rectangle(
            center_x + 10, center_y - btn_size//2,
            center_x + btn_size + 10, center_y + btn_size//2,
            fill=self.DIR_BUTTON_COLOR,
            outline="#ffffff",
            width=2,
            tags="dir_right"
        )
        self.canvas.create_text(
            center_x + btn_size//2 + 10, center_y,
            text="→", fill="#ffffff", font=("SimHei", 16, "bold"), tags="dir_right_text"
        )
        self.dir_buttons['right'] = right_btn

    def _bind_events(self):
        """绑定所有交互事件"""
        # 启动按钮点击事件
        self.canvas.tag_bind("start_button", "<Button-1>", self._on_start_click)
        self.canvas.tag_bind("start_button_text", "<Button-1>", self._on_start_click)
        
        # 方向按键点击事件（按下/释放）
        # 上按键
        self.canvas.tag_bind("dir_up", "<ButtonPress-1>", lambda e: self._on_dir_press('up'))
        self.canvas.tag_bind("dir_up_text", "<ButtonPress-1>", lambda e: self._on_dir_press('up'))
        self.canvas.tag_bind("dir_up", "<ButtonRelease-1>", lambda e: self._on_dir_release('up'))
        # 下按键
        self.canvas.tag_bind("dir_down", "<ButtonPress-1>", lambda e: self._on_dir_press('down'))
        self.canvas.tag_bind("dir_down_text", "<ButtonPress-1>", lambda e: self._on_dir_press('down'))
        self.canvas.tag_bind("dir_down", "<ButtonRelease-1>", lambda e: self._on_dir_release('down'))
        # 左按键
        self.canvas.tag_bind("dir_left", "<ButtonPress-1>", lambda e: self._on_dir_press('left'))
        self.canvas.tag_bind("dir_left_text", "<ButtonPress-1>", lambda e: self._on_dir_press('left'))
        self.canvas.tag_bind("dir_left", "<ButtonRelease-1>", lambda e: self._on_dir_release('left'))
        # 右按键
        self.canvas.tag_bind("dir_right", "<ButtonPress-1>", lambda e: self._on_dir_press('right'))
        self.canvas.tag_bind("dir_right_text", "<ButtonPress-1>", lambda e: self._on_dir_press('right'))
        self.canvas.tag_bind("dir_right", "<ButtonRelease-1>", lambda e: self._on_dir_release('right'))
        
        # 键盘方向键控制（备用）
        self.task_window.bind("<Up>", lambda e: self._move_satellite(0, -self.satellite_speed))
        self.task_window.bind("<Down>", lambda e: self._move_satellite(0, self.satellite_speed))
        self.task_window.bind("<Left>", lambda e: self._move_satellite(-self.satellite_speed, 0))
        self.task_window.bind("<Right>", lambda e: self._move_satellite(self.satellite_speed, 0))

    def _on_start_click(self, event):
        """点击启动按钮事件"""
        if self.window_closed or self.task_completed:
            return
        
        # 激活卫星
        self.satellite_active = True
        
        # 显示"正在启动卫星"文本
        if self.status_text_id:
            self.canvas.delete(self.status_text_id)
            self.canvas.delete("hint_text")
        self.status_text_id = self.canvas.create_text(
            self.WINDOW_WIDTH // 2, self.TOP_AREA_HEIGHT + 20,
            text="正在启动卫星...",
            fill="#ffffff",
            font=("SimHei", 16, "bold"),
            tags="status_text"
        )
        # 提示方向按键控制
        self.canvas.create_text(
            self.WINDOW_WIDTH // 2, self.TOP_AREA_HEIGHT + 50,
            text="点击方向按键控制卫星移动到空心红圈中心",
            fill="#ffffff",
            font=("SimHei", 12),
            tags="hint_text"
        )

    def _on_dir_press(self, direction):
        """按下方向按键事件"""
        if not self.satellite_active or self.window_closed or self.task_completed:
            return
        
        # 按键视觉反馈（变色）
        self.canvas.itemconfig(self.dir_buttons[direction], fill=self.DIR_BUTTON_PRESS)
        
        # 根据方向移动卫星
        if direction == 'up':
            self._move_satellite(0, -self.satellite_speed)
        elif direction == 'down':
            self._move_satellite(0, self.satellite_speed)
        elif direction == 'left':
            self._move_satellite(-self.satellite_speed, 0)
        elif direction == 'right':
            self._move_satellite(self.satellite_speed, 0)

    def _on_dir_release(self, direction):
        """释放方向按键事件"""
        if not self.satellite_active or self.window_closed or self.task_completed:
            return
        
        # 按键复位（恢复原色）
        self.canvas.itemconfig(self.dir_buttons[direction], fill=self.DIR_BUTTON_COLOR)

    def _move_satellite(self, dx, dy):
        """移动卫星并检测是否到达红圈中心"""
        if not self.satellite_active or self.window_closed or self.task_completed:
            return
        
        # 更新卫星坐标（限制在上3/4区域内）
        new_x = self.satellite_x + dx
        new_y = self.satellite_y + dy
        
        # 边界检测（严格限制在上3/4区域内）
        new_x = max(self.satellite_main_width + 30, min(new_x, self.WINDOW_WIDTH - self.satellite_main_width - 30))
        new_y = max(self.satellite_main_height + 30, min(new_y, self.TOP_AREA_HEIGHT - self.satellite_main_height - 30))
        
        # 计算移动偏移量
        move_dx = new_x - self.satellite_x
        move_dy = new_y - self.satellite_y
        
        # 移动所有卫星部件
        for sid in self.satellite_ids:
            self.canvas.move(sid, move_dx, move_dy)
        
        # 更新卫星坐标
        self.satellite_x = new_x
        self.satellite_y = new_y
        
        # 检测是否到达红圈中心（误差范围8像素）
        distance_to_center = math.hypot(
            self.satellite_x - self.circle_x,
            self.satellite_y - self.circle_y
        )
        if distance_to_center <= 8:
            self._complete_task()

    def _complete_task(self):
        """完成任务（卫星到达红圈中心）"""
        self.task_completed = True
        self.satellite_active = False
        
        # 更新状态文本为绿色"卫星已启动"
        if self.status_text_id:
            self.canvas.delete(self.status_text_id)
            self.canvas.delete("hint_text")
        self.status_text_id = self.canvas.create_text(
            self.WINDOW_WIDTH // 2, self.TOP_AREA_HEIGHT + 30,
            text="卫星已启动！",
            fill="#00ff00",
            font=("SimHei", 20, "bold"),
            tags="status_text"
        )
        
        # 提示任务完成
        messagebox.showinfo("任务成功", "🎉 卫星启动成功！启动卫星任务完成！", parent=self.task_window)
        self.task_window.destroy()
        if not self.task_window.master:
            self.task_window.quit()

import tkinter as tk
from tkinter import messagebox
import math
from tasks import Task  # 导入基础Task类

class OxygenRepairTask(Task):
    """修复氧气管道任务（适配游戏主窗口的模态弹窗版）"""
    def __init__(self):
        self.name = "修复氧气管道"
        self.location = "氧气室"  # 新增位置属性，适配游戏任务系统
        self.difficulty = 3       # 新增难度属性
        self.is_completed = False
        self.window_closed = False
        
        # 任务状态
        self.nut1_removed = False        # 螺母1是否卸下
        self.nut2_removed = False        # 螺母2是否卸下
        self.broken_pipe_removed = False # 断裂管道是否移除
        self.new_pipe_placed = False     # 新管道是否放置（吸附）
        self.nut1_installed = False      # 螺母1是否安装
        self.nut2_installed = False      # 螺母2是否安装
        
        # 拖动状态
        self.dragging_item = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_type = None  # 拖动类型：screwdriver/nut/broken_pipe/new_pipe
        
        # 基准位置（用于吸附）
        self.nut1_base_pos = (250, 300)  # 螺母1基准位置
        self.nut2_base_pos = (550, 300)  # 螺母2基准位置
        self.pipe_base_pos = (400, 300)  # 管道基准位置

    def _task_complete_handler(self, root):
        """任务完成处理（适配游戏主窗口的弹窗逻辑）"""
        # 弹出完成窗口（绑定到游戏主窗口）
        result = messagebox.showinfo(
            "任务完成",
            "🎉 修复氧气任务已完成！\n点击确认清除氧气任务",
            parent=root
        )
        
        if result == "ok":
            # 标记任务完成
            self.is_completed = True
            
            # 关闭任务窗口
            root.destroy()

    def run_task_gui(self, main_root=None):
        """
        运行任务窗口（适配游戏主窗口）
        :param main_root: 游戏主窗口（作为父窗口）
        :return: 是否完成任务
        """
        # 创建模态弹窗（绑定到游戏主窗口）
        root = tk.Toplevel(main_root) if main_root else tk.Tk()
        root.title("氧气管道修复任务")
        root.geometry("1000x700")
        root.configure(bg="#add8e6")
        root.resizable(False, False)
        
        # 设置为模态窗口（阻塞游戏主窗口操作）
        if main_root:
            root.transient(main_root)
            root.grab_set()
            root.wm_attributes("-topmost", True)

        # 画布
        canvas = tk.Canvas(root, width=980, height=680, bg="#add8e6", highlightthickness=0)
        canvas.pack(padx=10, pady=10)

        # ===================== 绘制元素（保留原有逻辑） =====================
        # 1. 背景连通管道（连接到屏幕边缘）
        # 左侧横向管道（到左边缘）
        canvas.create_line(
            0, 300, 250, 300,
            width=40, fill="#1a1a1a", capstyle=tk.ROUND, tags="bg_pipe"
        )
        # 右侧横向管道（到右边缘）
        canvas.create_line(
            550, 300, 980, 300,
            width=40, fill="#1a1a1a", capstyle=tk.ROUND, tags="bg_pipe"
        )
        # 顶部竖向管道（到上边缘）
        canvas.create_line(
            400, 0, 400, 300,
            width=40, fill="#1a1a1a", capstyle=tk.ROUND, tags="bg_pipe"
        )
        # 底部竖向管道（到下边缘）
        canvas.create_line(
            400, 300, 400, 680,
            width=40, fill="#1a1a1a", capstyle=tk.ROUND, tags="bg_pipe"
        )

        # 2. 断裂管道（放大版，两段连体：左段左下15°，右段右下15°）
        # 左段管道（左下15°）
        broken_pipe_left = canvas.create_line(
            self.pipe_base_pos[0]-150, self.pipe_base_pos[1],
            self.pipe_base_pos[0], self.pipe_base_pos[1]+50,
            width=50, fill="#222222", capstyle=tk.ROUND, tags="broken_pipe"
        )
        # 右段管道（右下15°）
        broken_pipe_right = canvas.create_line(
            self.pipe_base_pos[0], self.pipe_base_pos[1]+50,
            self.pipe_base_pos[0]+150, self.pipe_base_pos[1],
            width=50, fill="#222222", capstyle=tk.ROUND, tags="broken_pipe"
        )
        # 断裂缝标记（加粗）
        canvas.create_line(
            self.pipe_base_pos[0], self.pipe_base_pos[1]+50,
            self.pipe_base_pos[0], self.pipe_base_pos[1]+80,
            fill="#ff0000", width=4
        )
        canvas.create_text(
            self.pipe_base_pos[0], self.pipe_base_pos[1]+90,
            text="断裂", fill="#ff0000", font=("SimHei", 14, "bold")
        )

        # 3. 螺丝刀（左下角，可拖动）
        # 黄色手柄（竖直长方形）
        screwdriver_handle = canvas.create_rectangle(
            80, 550, 120, 650,
            fill="#ffcc00", outline="#e6b800", width=2, tags="screwdriver"
        )
        # 银色刀杆（更细，竖直长方形，连接手柄）
        screwdriver_rod = canvas.create_rectangle(
            90, 400, 110, 550,
            fill="#cccccc", outline="#999999", width=2, tags="screwdriver"
        )
        # 刀头标记（前1/4处）
        canvas.create_line(
            90, 400, 110, 400,
            fill="#ff0000", width=2, tags="screwdriver_tip"
        )
        canvas.create_text(90, 660, text="螺丝刀", fill="#000000", font=("SimHei", 12))

        # 4. 新管道（加长版，屏幕右下角，可拖动，水平）
        new_pipe = canvas.create_line(
            750, 550, 1000, 550,
            width=50, fill="#222222", capstyle=tk.ROUND, tags="new_pipe"
        )

        # 5. 螺母（放大版，可拖动，最后绘制置顶显示）
        nut1 = canvas.create_oval(
            self.nut1_base_pos[0]-15, self.nut1_base_pos[1]-15,
            self.nut1_base_pos[0]+15, self.nut1_base_pos[1]+15,
            fill="#888888", outline="#000000", width=3, tags="nut1 nut"
        )
        nut2 = canvas.create_oval(
            self.nut2_base_pos[0]-15, self.nut2_base_pos[1]-15,
            self.nut2_base_pos[0]+15, self.nut2_base_pos[1]+15,
            fill="#888888", outline="#000000", width=3, tags="nut2 nut"
        )

        # 强制将螺母置于最顶层（双重保障）
        canvas.tag_raise("nut", "all")

        # 6. 底部提示文本框
        tip_label = tk.Label(
            root, text="", bg="#add8e6", font=("SimHei", 14), fg="#006600"
        )
        tip_label.place(x=450, y=650, anchor=tk.CENTER)

        # 7. 顶部操作提示
        canvas.create_text(450, 20, text="操作流程：1.拖螺丝刀头到螺母（卸螺丝）→ 2.拖螺母移开", fill="#000000", font=("SimHei", 12))
        canvas.create_text(450, 40, text="3.拖断裂管道移除 → 4.拖新管道吸附 → 5.拖螺母吸附 → 6.拖螺丝刀装螺母", fill="#000000", font=("SimHei", 12))

        # ===================== 核心逻辑函数（保留原有逻辑） =====================
        def distance(pos1, pos2):
            """计算两点距离"""
            return math.hypot(pos1[0]-pos2[0], pos1[1]-pos2[1])

        def get_screwdriver_tip_pos():
            """获取螺丝刀头（前1/4处）位置"""
            rod_coords = canvas.coords(screwdriver_rod)
            tip_x = (rod_coords[0] + rod_coords[2]) / 2
            tip_y = rod_coords[1] + (rod_coords[3] - rod_coords[1]) * 0.25
            return (tip_x, tip_y)

        def start_drag(event):
            """开始拖动"""
            item = canvas.find_closest(event.x, event.y)[0]
            tags = canvas.gettags(item)
            
            # 判断拖动类型
            if "screwdriver" in tags:
                self.dragging_item = "screwdriver"
                self.drag_type = "screwdriver"
            elif "nut" in tags:
                if ("nut1" in tags and self.nut1_removed) or ("nut2" in tags and self.nut2_removed):
                    self.dragging_item = item
                    self.drag_type = "nut"
            elif "broken_pipe" in tags and self.nut1_removed and self.nut2_removed:
                self.dragging_item = "broken_pipe"
                self.drag_type = "broken_pipe"
            elif "new_pipe" in tags and self.broken_pipe_removed:
                self.dragging_item = item
                self.drag_type = "new_pipe"
            
            if self.dragging_item:
                self.drag_start_x = event.x
                self.drag_start_y = event.y

        def drag(event):
            """拖动元素"""
            if not self.dragging_item:
                return
            
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # 根据类型拖动
            if self.drag_type == "screwdriver":
                canvas.move("screwdriver", dx, dy)
            elif self.drag_type == "nut":
                canvas.move(self.dragging_item, dx, dy)
                canvas.tag_raise(self.dragging_item, "all")
            elif self.drag_type == "broken_pipe":
                canvas.move("broken_pipe", dx, dy)
            elif self.drag_type == "new_pipe":
                canvas.move(self.dragging_item, dx, dy)
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y

            # 实时检测螺丝刀头是否接触螺母
            if self.drag_type == "screwdriver":
                tip_pos = get_screwdriver_tip_pos()
                # 检测螺母1
                if not self.nut1_removed and distance(tip_pos, self.nut1_base_pos) < 25:
                    tip_label.config(text="正在卸除螺丝钉...")
                # 检测螺母2
                elif not self.nut2_removed and distance(tip_pos, self.nut2_base_pos) < 25:
                    tip_label.config(text="正在卸除螺丝钉...")
                # 检测安装螺母1
                elif self.new_pipe_placed and not self.nut1_installed and distance(tip_pos, self.nut1_base_pos) < 25:
                    tip_label.config(text="正在安装螺丝钉...")
                # 检测安装螺母2
                elif self.new_pipe_placed and not self.nut2_installed and distance(tip_pos, self.nut2_base_pos) < 25:
                    tip_label.config(text="正在安装螺丝钉...")
                else:
                    tip_label.config(text="")

        def stop_drag(event):
            """停止拖动"""
            if not self.dragging_item:
                self.drag_type = None
                return

            # 1. 螺丝刀卸螺丝逻辑
            if self.drag_type == "screwdriver":
                tip_pos = get_screwdriver_tip_pos()
                
                # 卸螺母1
                if not self.nut1_removed and distance(tip_pos, self.nut1_base_pos) < 25:
                    root.after(1000, lambda: remove_nut(1))
                # 卸螺母2
                elif not self.nut2_removed and distance(tip_pos, self.nut2_base_pos) < 25:
                    root.after(1000, lambda: remove_nut(2))
                # 装螺母1
                elif self.new_pipe_placed and not self.nut1_installed and distance(tip_pos, self.nut1_base_pos) < 25:
                    root.after(1500, lambda: install_nut(1))
                # 装螺母2
                elif self.new_pipe_placed and not self.nut2_installed and distance(tip_pos, self.nut2_base_pos) < 25:
                    root.after(1500, lambda: install_nut(2))
                else:
                    tip_label.config(text="")

            # 2. 新管道拖到基准位置：自动吸附
            elif self.drag_type == "new_pipe":
                pipe_pos = canvas.coords(self.dragging_item)
                pipe_center = ((pipe_pos[0]+pipe_pos[2])/2, (pipe_pos[1]+pipe_pos[3])/2)
                if distance(pipe_center, self.pipe_base_pos) < 60:
                    canvas.coords(
                        self.dragging_item,
                        self.pipe_base_pos[0]-175, self.pipe_base_pos[1],
                        self.pipe_base_pos[0]+175, self.pipe_base_pos[1]
                    )
                    self.new_pipe_placed = True
                    tip_label.config(text="✅ 新管道已吸附到位")
                    root.after(2000, lambda: tip_label.config(text=""))

            # 3. 螺母拖到基准位置：自动吸附
            elif self.drag_type == "nut" and self.new_pipe_placed:
                nut_pos = canvas.coords(self.dragging_item)
                nut_center = ((nut_pos[0]+nut_pos[2])/2, (nut_pos[1]+nut_pos[3])/2)
                
                # 吸附到螺母1位置
                if "nut1" in canvas.gettags(self.dragging_item) and distance(nut_center, self.nut1_base_pos) < 25:
                    canvas.coords(
                        self.dragging_item,
                        self.nut1_base_pos[0]-15, self.nut1_base_pos[1]-15,
                        self.nut1_base_pos[0]+15, self.nut1_base_pos[1]+15
                    )
                    canvas.tag_raise(self.dragging_item, "all")
                    tip_label.config(text="✅ 螺母1已吸附到位")
                    root.after(2000, lambda: tip_label.config(text=""))
                # 吸附到螺母2位置
                elif "nut2" in canvas.gettags(self.dragging_item) and distance(nut_center, self.nut2_base_pos) < 25:
                    canvas.coords(
                        self.dragging_item,
                        self.nut2_base_pos[0]-15, self.nut2_base_pos[1]-15,
                        self.nut2_base_pos[0]+15, self.nut2_base_pos[1]+15
                    )
                    canvas.tag_raise(self.dragging_item, "all")
                    tip_label.config(text="✅ 螺母2已吸附到位")
                    root.after(2000, lambda: tip_label.config(text=""))

            # 4. 断裂管道拖动后标记为移除
            elif self.drag_type == "broken_pipe":
                pipe_pos = canvas.coords(broken_pipe_left)
                pipe_center = ((pipe_pos[0]+pipe_pos[2])/2, (pipe_pos[1]+pipe_pos[3])/2)
                if distance(pipe_center, self.pipe_base_pos) > 120:
                    self.broken_pipe_removed = True
                    tip_label.config(text="✅ 断裂管道已移除")
                    root.after(2000, lambda: tip_label.config(text=""))

            self.dragging_item = None
            self.drag_type = None

        def remove_nut(nut_num):
            """卸下螺母"""
            if nut_num == 1:
                self.nut1_removed = True
                canvas.itemconfig(nut1, fill="#aaaaaa")
                canvas.tag_raise(nut1, "all")
                tip_label.config(text="✅ 螺母1已卸下（可拖动）")
            else:
                self.nut2_removed = True
                canvas.itemconfig(nut2, fill="#aaaaaa")
                canvas.tag_raise(nut2, "all")
                tip_label.config(text="✅ 螺母2已卸下（可拖动）")
            root.after(2000, lambda: tip_label.config(text=""))

        def install_nut(nut_num):
            """安装螺母（触发完成弹窗）"""
            if nut_num == 1:
                self.nut1_installed = True
                canvas.itemconfig(nut1, fill="#888888")
                canvas.tag_raise(nut1, "all")
                tip_label.config(text="✅ 螺母1已安装")
            else:
                self.nut2_installed = True
                canvas.itemconfig(nut2, fill="#888888")
                canvas.tag_raise(nut2, "all")
                tip_label.config(text="✅ 螺母2已安装")
            
            # 检查是否全部安装完成 → 触发弹窗
            if self.nut1_installed and self.nut2_installed:
                tip_label.config(text="🎉 正在完成任务...")
                # 1秒后弹出完成窗口
                root.after(1000, lambda: self._task_complete_handler(root))
            else:
                root.after(2000, lambda: tip_label.config(text=""))

        # ===================== 绑定事件 =====================
        canvas.bind("<Button-1>", start_drag)
        canvas.bind("<B1-Motion>", drag)
        canvas.bind("<ButtonRelease-1>", stop_drag)
        
        # 窗口关闭处理
        def on_close():
            self.window_closed = True
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_close)

        # 运行窗口（适配模态模式）
        if main_root:
            root.wait_window()  # 阻塞直到窗口关闭
        else:
            root.mainloop()
            
        return self.is_completed
    
    def complete(self):
        """基础Task类的完成方法（适配游戏任务系统）"""
        self.is_completed = True
        return True

import tkinter as tk
from tkinter import messagebox
import math
from tasks import Task  # 导入基础Task类
class MorseCodeTask(Task):
    """摩斯密码解锁任务（带图形化交互）"""
    
    def __init__(self):
        super().__init__("破解摩斯密码", "主控室", 3)
        self.task_completed = False  # 记录GUI任务是否完成
        self.task_window = None
    
    def run_task_gui(self, main_root=None) -> bool:
        """
        运行摩斯密码解锁的图形化任务界面
        :param main_root: 主窗口对象（可选）
        :return: 任务是否完成
        """
        # 确保只创建一个任务窗口
        if self.task_window and tk.Toplevel.winfo_exists(self.task_window):
            self.task_window.lift()
            return False
        
        # 创建窗口（优先使用Toplevel依附主窗口）
        if main_root and isinstance(main_root, tk.Tk):
            self.task_window = tk.Toplevel(main_root)
            # 设置为模态窗口
            self.task_window.transient(main_root)
            self.task_window.grab_set()
        else:
            self.task_window = tk.Tk()  # 无主窗口时创建独立窗口
        
        root = self.task_window
        root.title("主控室 - 摩斯密码解锁任务")
        root.geometry("1000x1000")
        root.configure(bg="#add8e6")
        root.resizable(True, True)
        
        # 确保窗口关闭时正确清理
        def on_close():
            self.task_completed = False
            if main_root:
                self.task_window.destroy()
            else:
                root.quit()
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_close)
        
        # 创建摩斯密码解锁游戏实例
        import haikediannao  # 导入海克迪脑模块
        game_instance = haikediannao.MorseCodeUnlockGame(root)
        
        # 运行窗口（适配模态模式）
        if main_root:
            root.wait_window()  # 阻塞直到窗口关闭
        else:
            root.mainloop()
        
        # 检查游戏是否成功完成
        self.is_completed = game_instance.ending == 1
        self.task_completed = game_instance.ending == 1
        return self.task_completed

# 测试入口
if __name__ == "__main__":
    task = BodyScanTask()
    task.run_task_gui()
    print(f"任务完成状态：{task.is_completed}")
class TaskGenerator:
    """任务生成器：负责生成随机任务列表"""
    
    # 完整任务池（包含所有图形化任务+普通任务）
    TASK_POOL = [
        # 图形化交互任务
        WireFixTask(),               # 电力室 - 修复电线
        FilterCleanTask(),           # 氧气室 - 清理过滤器
        BodyScanTask(),              # 医疗室 - 扫描身体
        DownloadDataTask(),          # 通讯室 - 下载数据
        CalibrateDownEngineTask(),   # 下降引擎室 - 校准下降引擎
        CalibrateUpEngineTask(),     # 上升引擎室 - 校准上升引擎
        RepairReactorTask(),         # 反应堆室 - 修复反应堆
        RefuelTask(),            # 燃料室 - 补充燃料
        StartSatelliteTask(),
        MorseCodeTask(),
    ]
    
    @staticmethod
    def generate_tasks(num_tasks: int) -> List[Task]:
        """
        生成指定数量的任务
        :param num_tasks: 需要生成的任务数量
        :return: 任务列表（深拷贝，避免共享状态）
        """
        # 如果需要的任务数量超过任务池，允许重复生成
        if num_tasks > len(TaskGenerator.TASK_POOL):
            tasks = []
            for i in range(num_tasks):
                # 随机选择任务模板
                task_template = random.choice(TaskGenerator.TASK_POOL)
                # 深拷贝任务实例（避免多个任务共享同一状态）
                new_task = TaskGenerator._copy_task(task_template)
                tasks.append(new_task)
            return tasks
        else:
            # 否则随机选择不重复的任务
            selected_templates = random.sample(TaskGenerator.TASK_POOL, num_tasks)
            tasks = []
            for template in selected_templates:
                new_task = TaskGenerator._copy_task(template)
                tasks.append(new_task)
            return tasks
    
    @staticmethod
    def _copy_task(task_template: Task) -> Task:
        """
        深拷贝任务实例（针对不同任务类型做适配）
        :param task_template: 任务模板
        :return: 新的任务实例
        """
        # 图形化任务单独拷贝（保持类实例特性）
        if isinstance(task_template, WireFixTask):
            return WireFixTask()
        elif isinstance(task_template, FilterCleanTask):
            return FilterCleanTask()
        elif isinstance(task_template, BodyScanTask):
            return BodyScanTask()
        elif isinstance(task_template, DownloadDataTask):
            return DownloadDataTask()
        elif isinstance(task_template, CalibrateDownEngineTask):
            return CalibrateDownEngineTask()
        elif isinstance(task_template, CalibrateUpEngineTask):
            return CalibrateUpEngineTask()
        elif isinstance(task_template, RepairReactorTask):
            return RepairReactorTask()
        elif isinstance(task_template, RefuelTask):
            return RefuelTask()
        elif isinstance(task_template, StartSatelliteTask):
            return StartSatelliteTask()
        elif isinstance(task_template, MorseCodeTask):
            return MorseCodeTask()
        # 普通Task类直接创建新实例
        else:
            return Task(
                name=task_template.name,
                location=task_template.location,
                difficulty=task_template.difficulty
            )
#requests