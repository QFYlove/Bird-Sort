import tkinter as tk
from tkinter import messagebox
import random

class BirdSortGame:
    def __init__(self):
        # 主窗口设置
        self.root = tk.Tk()
        self.root.title("鸟类排序 (Bird Sort)")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        
        # 颜色定义
        self.bird_colors = ['red', 'blue', 'green', 'yellow', 'pink', 'orange', 'purple', 'cyan']
        self.bg_color = '#87CEEB'
        self.branch_color = '#8B4513'
        
        # 游戏状态
        self.main_branches = []  # 8根树枝，每根最多4只鸟
        self.nests = []  # 5个暂存窝
        self.score = 0
        self.moves = 0
        self.selected_item = None  # {"type": "branch"/"nest", "index": int, "bird_index": int}
        self.cheat_moves_left = 3
        self.cheat_mode_active = False  # 作弊模式状态
        self.add_branch_left = 2
        self.cheat_button = None  # 作弊按钮引用
        
        # 暂存窝位置信息
        self.nest_positions = []
        # 树枝位置信息
        self.branch_positions = []
        
        # Canvas对象ID存储
        self.bird_canvas_ids = {}  # {(type, index, bird_index): canvas_id}
        self.selection_indicator = None
        
        # 初始化游戏
        self.init_ui()
        self.init_game_state()
        self.draw_game()
        
    def init_ui(self):
        """初始化用户界面"""
        # 区域A: 顶部控制栏
        control_frame = tk.Frame(self.root, bg='#DDDDDD', height=50)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # 按钮
        tk.Button(control_frame, text="撤回(Undo)", command=self.undo_action, 
                  width=10, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="增加空树枝", command=self.add_branch,
                  width=10, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="打乱(Shuffle)", command=self.shuffle_birds,
                  width=10, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.cheat_button = tk.Button(control_frame, text=f"作弊移动({self.cheat_moves_left})", 
                  command=self.cheat_move, width=12, font=('Arial', 10))
        self.cheat_button.pack(side=tk.LEFT, padx=5)
        
        # 标签
        self.score_label = tk.Label(control_frame, text=f"Score: {self.score}", 
                                    font=('Arial', 12, 'bold'), bg='#DDDDDD')
        self.score_label.pack(side=tk.RIGHT, padx=20)
        self.moves_label = tk.Label(control_frame, text=f"Moves: {self.moves}", 
                                    font=('Arial', 12, 'bold'), bg='#DDDDDD')
        self.moves_label.pack(side=tk.RIGHT, padx=20)
        
        # 区域B和C: Canvas
        self.canvas = tk.Canvas(self.root, width=1000, height=640, bg=self.bg_color)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定点击事件
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
    def init_game_state(self):
        """初始化游戏状态"""
        # 初始化8根树枝
        self.main_branches = []
        # 创建初始鸟的分布：4种颜色，每种4只，分布在6根树枝上
        birds = []
        colors = self.bird_colors[:4]  # 使用4种颜色
        for color in colors:
            birds.extend([color] * 4)
        random.shuffle(birds)
        
        # 分配到6根树枝（前6根有鸟，后2根空）
        for i in range(6):
            branch = birds[i*4:(i+1)*4]
            self.main_branches.append(branch)
        self.main_branches.append([])
        self.main_branches.append([])
        
        # 初始化5个暂存窝
        self.nests = []
        for i in range(5):
            if i == 0:
                self.nests.append({"bird": None, "unlocked": True})
            else:
                self.nests.append({"bird": None, "unlocked": False})
        
        # 计算位置
        self.calculate_positions()
        
    def calculate_positions(self):
        """计算所有元素的位置"""
        # 暂存窝位置 (Y: 80~180, 居中)
        nest_start_x = 100
        self.nest_positions = []
        for i in range(5):
            x = nest_start_x + i * 160
            y = 80
            self.nest_positions.append((x, y))
        
        # 树枝位置 (双列布局)
        self.branch_positions = []
        # 左列: 起始X=150, 4根树枝
        for i in range(4):
            x = 150
            y = 280 + i * 100
            self.branch_positions.append((x, y))
        # 右列: 起始X=600, 4根树枝
        for i in range(4):
            x = 600
            y = 280 + i * 100
            self.branch_positions.append((x, y))
    
    def draw_game(self):
        """绘制整个游戏界面"""
        self.canvas.delete("all")
        self.bird_canvas_ids.clear()
        
        # 绘制暂存窝
        self.draw_nests()
        
        # 绘制树枝和鸟
        self.draw_branches_and_birds()
        
        # 检查死局
        self.check_stuck()
        
    def draw_nests(self):
        """绘制暂存窝区域"""
        for i, (x, y) in enumerate(self.nest_positions):
            nest = self.nests[i]
            
            if not nest["unlocked"]:
                # 锁定状态：灰色，显示🔒 AD
                self.canvas.create_rectangle(x, y, x+80, y+80, 
                                            fill='gray', outline='black', width=2)
                self.canvas.create_text(x+40, y+40, text="🔒 AD", 
                                       font=('Arial', 12, 'bold'), fill='white')
            elif nest["bird"] is None:
                # 解锁且空：白色
                self.canvas.create_rectangle(x, y, x+80, y+80, 
                                            fill='white', outline='black', width=2)
            else:
                # 有鸟：白色背景，中间画鸟
                self.canvas.create_rectangle(x, y, x+80, y+80, 
                                            fill='white', outline='black', width=2)
                bird_id = self.canvas.create_oval(x+20, y+20, x+60, y+60, 
                                                  fill=nest["bird"], outline='black', width=2)
                self.bird_canvas_ids[("nest", i, 0)] = bird_id
    
    def draw_branches_and_birds(self):
        """绘制树枝和鸟"""
        for i, (x, y) in enumerate(self.branch_positions):
            if i >= len(self.main_branches):
                break
                
            # 绘制树枝（棕色矩形）
            self.canvas.create_rectangle(x, y, x+240, y+15, 
                                        fill=self.branch_color, outline='black', width=2)
            
            # 绘制鸟
            branch = self.main_branches[i]
            for j, bird_color in enumerate(branch):
                # 鸟的坐标：Y = branch_y - 20, X = branch_x + 30 + j * 50
                bird_x = x + 30 + j * 50
                bird_y = y - 20
                
                # 检查是否是选中的鸟
                is_selected = (self.selected_item and 
                              self.selected_item["type"] == "branch" and 
                              self.selected_item["index"] == i and 
                              j == len(branch) - 1)
                
                if is_selected:
                    # 选中状态：向上跳动10像素，黄色粗边框
                    bird_y -= 10
                    bird_id = self.canvas.create_oval(bird_x-20, bird_y-20, 
                                                      bird_x+20, bird_y+20,
                                                      fill=bird_color, 
                                                      outline='yellow', width=4)
                else:
                    bird_id = self.canvas.create_oval(bird_x-20, bird_y-20, 
                                                      bird_x+20, bird_y+20,
                                                      fill=bird_color, 
                                                      outline='black', width=2)
                
                self.bird_canvas_ids[("branch", i, j)] = bird_id
    
    def on_canvas_click(self, event):
        """处理Canvas点击事件"""
        x, y = event.x, event.y
        
        # 检查是否点击了暂存窝
        nest_index = self.get_clicked_nest(x, y)
        if nest_index is not None:
            self.handle_nest_click(nest_index)
            return
        
        # 检查是否点击了树枝
        branch_index = self.get_clicked_branch(x, y)
        if branch_index is not None:
            self.handle_branch_click(branch_index)
            return
    
    def get_clicked_nest(self, x, y):
        """检测点击的暂存窝"""
        for i, (nx, ny) in enumerate(self.nest_positions):
            if nx <= x <= nx+80 and ny <= y <= ny+80:
                return i
        return None
    
    def get_clicked_branch(self, x, y):
        """检测点击的树枝（包括鸟的区域）"""
        for i, (bx, by) in enumerate(self.branch_positions):
            # 热区：树枝本身及其上方60像素（鸟的区域）
            if bx <= x <= bx+240 and (by-60) <= y <= by+15:
                return i
        return None
    
    def handle_nest_click(self, nest_index):
        """处理暂存窝点击"""
        nest = self.nests[nest_index]
        
        # 如果是锁定的窝
        if not nest["unlocked"]:
            self.unlock_nest(nest_index)
            return
        
        # 如果没有选中任何东西
        if self.selected_item is None:
            # 选择有鸟的窝
            if nest["bird"] is not None:
                self.selected_item = {"type": "nest", "index": nest_index}
                self.draw_game()
        else:
            # 尝试移动到这个窝
            if nest["bird"] is None:
                self.move_to_nest(nest_index)
            else:
                # 目标不为空，取消选择
                self.selected_item = None
                self.draw_game()
    
    def handle_branch_click(self, branch_index):
        """处理树枝点击"""
        branch = self.main_branches[branch_index]
        
        if self.selected_item is None:
            # 选择有鸟的树枝
            if len(branch) > 0:
                self.selected_item = {"type": "branch", "index": branch_index}
                self.draw_game()
        else:
            # 尝试移动到这个树枝
            self.move_to_branch(branch_index)
    
    def unlock_nest(self, nest_index):
        """解锁暂存窝"""
        result = messagebox.askyesno("解锁", "观看一段视频即可解锁此空位？")
        if result:
            self.nests[nest_index]["unlocked"] = True
            self.draw_game()
    
    def get_consecutive_birds_count(self, branch):
        """计算树枝最外侧连续同色鸟的数量"""
        if len(branch) == 0:
            return 0, None
        
        last_color = branch[-1]
        count = 0
        for i in range(len(branch) - 1, -1, -1):
            if branch[i] == last_color:
                count += 1
            else:
                break
        return count, last_color
    
    def move_to_nest(self, nest_index):
        """移动鸟到暂存窝（只能移动1只）"""
        source = self.selected_item
        bird = None
        
        # 从源获取鸟（只能移动1只）
        if source["type"] == "branch":
            branch = self.main_branches[source["index"]]
            if len(branch) > 0:
                bird = branch.pop()
        elif source["type"] == "nest":
            # 窝到窝的移动
            source_nest = self.nests[source["index"]]
            bird = source_nest["bird"]
            source_nest["bird"] = None
        
        if bird:
            self.nests[nest_index]["bird"] = bird
            self.moves += 1
            self.update_labels()
        
        self.selected_item = None
        self.draw_game()
    
    def move_to_branch(self, target_index):
        """移动鸟到目标树枝（支持连续同色鸟整体移动）"""
        source = self.selected_item
        target_branch = self.main_branches[target_index]
        
        # 检查目标树枝是否已满
        if len(target_branch) >= 4:
            self.selected_item = None
            self.draw_game()
            return
        
        # 从暂存窝移动到树枝
        if source["type"] == "nest":
            source_nest = self.nests[source["index"]]
            bird = source_nest["bird"]
            
            if bird is None:
                self.selected_item = None
                self.draw_game()
                return
            
            # 检查移动规则（作弊模式下跳过颜色检查）
            if not self.cheat_mode_active:
                if len(target_branch) > 0 and target_branch[-1] != bird:
                    # 颜色不匹配，非法移动
                    self.selected_item = None
                    self.draw_game()
                    return
            
            # 执行移动
            source_nest["bird"] = None
            target_branch.append(bird)
            self.moves += 1
            self.update_labels()
            self.check_elimination()
            
            # 作弊模式下重置状态
            if self.cheat_mode_active:
                self.cheat_moves_left -= 1
                self.cheat_mode_active = False
                self.cheat_button.config(text=f"作弊移动({self.cheat_moves_left})", bg='SystemButtonFace')
            
            self.selected_item = None
            self.draw_game()
            return
        
        # 从树枝移动到树枝
        if source["type"] == "branch":
            source_branch = self.main_branches[source["index"]]
            
            if len(source_branch) == 0:
                self.selected_item = None
                self.draw_game()
                return
            
            # 作弊模式下只移动1只鸟
            if self.cheat_mode_active:
                bird = source_branch.pop()
                target_branch.append(bird)
                self.moves += 1
                self.update_labels()
                self.check_elimination()
                
                # 重置作弊状态
                self.cheat_moves_left -= 1
                self.cheat_mode_active = False
                self.cheat_button.config(text=f"作弊移动({self.cheat_moves_left})", bg='SystemButtonFace')
            else:
                # 正常模式：计算连续同色鸟的数量
                consecutive_count, bird_color = self.get_consecutive_birds_count(source_branch)
                
                # 计算目标树枝剩余空位
                empty_slots = 4 - len(target_branch)
                
                # 计算实际移动数量
                move_count = min(consecutive_count, empty_slots)
                
                # 检查移动规则
                if len(target_branch) > 0 and target_branch[-1] != bird_color:
                    # 颜色不匹配，非法移动
                    self.selected_item = None
                    self.draw_game()
                    return
                
                # 执行移动
                for _ in range(move_count):
                    bird = source_branch.pop()
                    target_branch.append(bird)
                
                if move_count > 0:
                    self.moves += 1
                    self.update_labels()
                    self.check_elimination()
        
        self.selected_item = None
        self.draw_game()
    
    def check_elimination(self):
        """检查并消除4只同色鸟（整根树枝移除）"""
        branches_to_remove = []
        
        for i, branch in enumerate(self.main_branches):
            if len(branch) == 4 and len(set(branch)) == 1:
                # 4只同色鸟，标记为待移除
                branches_to_remove.append(i)
        
        # 从后往前移除，避免索引问题
        for index in reversed(branches_to_remove):
            self.main_branches.pop(index)
            self.score += 100
        
        if branches_to_remove:
            self.update_labels()
            messagebox.showinfo("消除！", f"消除 {len(branches_to_remove)} 组，获得 {len(branches_to_remove) * 100} 分！")
    
    def check_stuck(self):
        """检查是否死局"""
        # 检查是否还有合法移动
        has_valid_move = False
        
        # 检查树枝间的移动
        for i in range(len(self.main_branches)):
            for j in range(len(self.main_branches)):
                if i != j and self.can_move_between_branches(i, j):
                    has_valid_move = True
                    break
            if has_valid_move:
                break
        
        # 如果没有合法移动，检查暂存区
        if not has_valid_move:
            has_nest_space = any(
                nest["unlocked"] and nest["bird"] is None 
                for nest in self.nests
            )
            if has_nest_space:
                # 在Canvas中央显示提示
                self.canvas.create_text(500, 240, 
                                       text="*** 卡住了？试试把鸟移到顶部的暂存窝里！ ***",
                                       font=('Arial', 14, 'bold'), fill='red')
    
    def can_move_between_branches(self, from_idx, to_idx):
        """检查是否可以从一个树枝移动到另一个"""
        from_branch = self.main_branches[from_idx]
        to_branch = self.main_branches[to_idx]
        
        if len(from_branch) == 0 or len(to_branch) >= 4:
            return False
        
        if len(to_branch) == 0:
            return True
        
        return from_branch[-1] == to_branch[-1]
    
    def update_labels(self):
        """更新分数和步数标签"""
        self.score_label.config(text=f"Score: {self.score}")
        self.moves_label.config(text=f"Moves: {self.moves}")
    
    def undo_action(self):
        """撤回操作（简化版本）"""
        messagebox.showinfo("撤回", "撤回功能需要记录历史，此版本暂未实现完整撤回")
    
    def add_branch(self):
        """增加空树枝"""
        if self.add_branch_left > 0:
            self.main_branches.append([])
            self.calculate_positions()
            self.add_branch_left -= 1
            self.draw_game()
            messagebox.showinfo("增加树枝", f"已添加空树枝，剩余 {self.add_branch_left} 次")
        else:
            messagebox.showwarning("无法添加", "增加树枝次数已用完！")
    
    def shuffle_birds(self):
        """打乱鸟的顺序"""
        # 收集所有鸟
        all_birds = []
        for branch in self.main_branches:
            all_birds.extend(branch)
            branch.clear()
        
        random.shuffle(all_birds)
        
        # 重新分配
        idx = 0
        for branch in self.main_branches:
            while len(branch) < 4 and idx < len(all_birds):
                branch.append(all_birds[idx])
                idx += 1
        
        self.draw_game()
        messagebox.showinfo("打乱", "鸟的位置已重新打乱！")
    
    def cheat_move(self):
        """作弊移动：切换作弊模式"""
        if self.cheat_moves_left <= 0:
            messagebox.showwarning("无法作弊", "作弊次数已用完！")
            return
        
        if not self.cheat_mode_active:
            # 激活作弊模式
            self.cheat_mode_active = True
            self.cheat_button.config(text=f"取消作弊(剩{self.cheat_moves_left}次)", bg='yellow')
            messagebox.showinfo("作弊模式", "作弊模式已激活！下次移动可无视颜色规则")
        else:
            # 取消作弊模式
            self.cheat_mode_active = False
            self.cheat_button.config(text=f"作弊移动({self.cheat_moves_left})", bg='SystemButtonFace')
    
    def run(self):
        """运行游戏"""
        self.root.mainloop()


if __name__ == "__main__":
    game = BirdSortGame()
    game.run()