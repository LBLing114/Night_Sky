import math
import random
import shutil
import sys
import time

class Star:
    def __init__(self, width, height):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        # z 轴代表深度，用于实现视差滚动效果 (越小离得越远)
        self.z = random.uniform(0.2, 1.5)  
        self.char = self._assign_char()
        self.color = random.randint(238, 255) # ANSI 灰度色阶

    def _assign_char(self):
        """根据距离远近分配不同的星星形态"""
        if self.z > 1.2: return '+'
        if self.z > 0.8: return '*'
        return '.' if self.z > 0.5 else '·'

    def update(self, width, height):
        # 远慢近快
        self.x -= self.z * 0.5  
        if self.x < 0:
            self.x = width
            self.y = random.uniform(0, height)

class Meteor:
    def __init__(self):
        self.active = False
        self.tail = []

    def spawn(self, width, height):
        if not self.active and random.random() < 0.015:
            self.active = True
            self.x = random.uniform(width * 0.3, width)
            self.y = random.uniform(0, height * 0.4)
            self.speed_x = -random.uniform(2.0, 4.0)
            self.speed_y = random.uniform(0.5, 1.5)
            self.tail = []

    def update(self, width, height):
        if not self.active:
            return

        # 记录历史轨迹，用于渲染粒子拖尾
        self.tail.insert(0, (self.x, self.y))
        if len(self.tail) > 6:
            self.tail.pop()
        
        self.x += self.speed_x
        self.y += self.speed_y
        
        # 越界检查
        if self.x < 0 or self.y > height:
            self.active = False
            self.tail = []

def draw_dynamic_sky():
    # 隐藏光标并清屏
    sys.stdout.write("\x1b[2J\x1b[?25l")
    
    width, height = shutil.get_terminal_size((80, 24))
    stars = [Star(width, height) for _ in range(int(width * height * 0.04))]
    meteors = [Meteor() for _ in range(2)]

    # 月牙的 ASCII 阵列
    moon = [
        "    _.._    ",
        "  .' .-'    ",
        " /  /       ",
        " |  |       ",
        " \\  \\       ",
        "  '. '._    ",
        "    `\"--'   "
    ]
    
    # 流星拖尾字符过渡
    trail_chars = ['@', 'o', '*', '.', '·', ' ']

    try:
        while True:
            # 自适应终端窗口大小
            w, h = shutil.get_terminal_size((80, 24))
            if w != width or h != height:
                width, height = w, h
                stars = [Star(width, height) for _ in range(int(width * height * 0.04))]

            # 初始化画布
            buffer = [[' ' for _ in range(width)] for _ in range(height)]
            
            # 1. 渲染月亮 (左上角)
            moon_x, moon_y = 4, 2
            
            angle = math.radians(5) * math.sin(time.time() * 3)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            cx, cy = 6.0, 3.0 # 旋转中心点

            for my, row in enumerate(moon):
                for mx, char in enumerate(row):
                    if char != ' ':
                        rx, ry = mx - cx, my - cy
                        nx = rx * cos_a - ry * sin_a * 1.6
                        ny = rx * sin_a / 1.6 + ry * cos_a
                        
                        fx = round(moon_x + cx + nx)
                        fy = round(moon_y + cy + ny)
                        
                        if 0 <= fy < height and 0 <= fx < width:
                            buffer[fy][fx] = f"\x1b[38;5;228m{char}\x1b[0m"

            # 2. 渲染背景群星
            for star in stars:
                star.update(width, height)
                x_idx, y_idx = int(star.x), int(star.y)
                
                if 0 <= y_idx < height and 0 <= x_idx < width:
                    # 避免覆盖月亮
                    if buffer[y_idx][x_idx] == ' ':
                        # 3% 的概率产生闪烁随机空白
                        char = ' ' if random.random() < 0.03 else f"\x1b[38;5;{star.color}m{star.char}\x1b[0m"
                        buffer[y_idx][x_idx] = char

            # 3. 渲染流星粒子系统
            for meteor in meteors:
                meteor.spawn(width, height)
                meteor.update(width, height)
                if meteor.active:
                    for i, (mx, my) in enumerate(meteor.tail):
                        x_idx, y_idx = int(mx), int(my)
                        if 0 <= y_idx < height and 0 <= x_idx < width:
                            char_idx = min(i, len(trail_chars) - 1)
                            buffer[y_idx][x_idx] = f"\x1b[38;5;226m{trail_chars[char_idx]}\x1b[0m"

            # 将缓冲区拼接为整帧一次性输出，防止画面闪烁撕裂
            frame = "\x1b[H" + "\n".join("".join(row) for row in buffer)
            sys.stdout.write(frame)
            sys.stdout.flush()
            
            time.sleep(0.05) # 维持在 20 FPS 左右

    except KeyboardInterrupt:
        sys.stdout.write("\x1b[?25h\x1b[0m\x1b[2J\x1b[H")

if __name__ == "__main__":
    draw_dynamic_sky()