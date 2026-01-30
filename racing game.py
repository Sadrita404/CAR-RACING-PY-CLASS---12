import pygame
import math
import sys
import os
import random
import sqlite3

# --- PATH FIX ---
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_path)

# --- CONFIGURATION ---
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 720
FPS = 60
TOTAL_LAPS = 3

# COLORS
WHITE = (255, 255, 255)
BLACK = (10, 10, 15)
RED = (220, 20, 60)
BLUE = (30, 144, 255)
GREEN = (34, 100, 34) 
ASPHALT = (40, 40, 45) 
KERB_RED = (200, 0, 0)
KERB_WHITE = (220, 220, 220)
YELLOW = (255, 215, 0)
GREY = (40, 40, 50)
NEON_CYAN = (0, 255, 255)
NEON_ORANGE = (255, 140, 0) 
NEON_TEAL = (0, 200, 200)
GLASS_BG = (20, 20, 30, 230)

# --- GLOBAL HELPER FUNCTIONS ---
def draw_glass_panel(screen, x, y, w, h, color):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(GLASS_BG)
    screen.blit(s, (x, y))
    pygame.draw.rect(screen, color, (x, y, w, h), 2)

def draw_text(screen, text, font, color, x, y, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    screen.blit(surf, rect)

# --- STATS & AUDIO MAPPING ---
CHASSIS_STATS = {
    "F1":       {"base_spd": 19.5, "accel": 0.6, "turn": 2.4, "base_grip": 0.99, "mass": 800,  "sfx": "eng_v10"},
    "SUPER":    {"base_spd": 20.0, "accel": 0.55, "turn": 2.0, "base_grip": 0.96, "mass": 1400, "sfx": "eng_w16"},
    "NASCAR":   {"base_spd": 18.5, "accel": 0.50, "turn": 1.8, "base_grip": 0.97, "mass": 1800, "sfx": "eng_v8"},
    "LE_MANS":  {"base_spd": 16.0, "accel": 0.45, "turn": 1.9, "base_grip": 0.98, "mass": 1000, "sfx": "eng_v6"},
    "DRIFT":    {"base_spd": 15.0, "accel": 0.7, "turn": 2.5, "base_grip": 0.90, "mass": 1200, "sfx": "eng_v6"},
}

ENGINES = [
    {"name": "V6 Turbo",   "spd_mult": 1.0, "acc_mult": 1.0},
    {"name": "V8 Super",   "spd_mult": 1.1, "acc_mult": 1.1},
    {"name": "V10 Race",   "spd_mult": 1.2, "acc_mult": 1.2},
    {"name": "W16 Quad",   "spd_mult": 1.3, "acc_mult": 1.3}
]

TYRES = [
    {"name": "Street",     "grip_mult": 1.0,  "turn_mult": 1.0},
    {"name": "Semi-Slick", "grip_mult": 1.1,  "turn_mult": 1.0},
    {"name": "Racing Slick", "grip_mult": 1.2, "turn_mult": 1.0},
    {"name": "Drift Comp", "grip_mult": 0.85, "turn_mult": 1.2} 
]

BRAKES = [
    {"name": "Steel",      "power": 0.05},
    {"name": "Ceramic",    "power": 0.08},
    {"name": "Carbon",     "power": 0.12}
]

# --- DATABASE ---
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('racing_data.db')
        self.create_table()
    def create_table(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS race_results
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      winner_name TEXT, car_type TEXT, lap_time TEXT, 
                      date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()
    def save_result(self, name, car, time_str):
        c = self.conn.cursor()
        c.execute("INSERT INTO race_results (winner_name, car_type, lap_time) VALUES (?, ?, ?)", 
                  (name, car, time_str))
        self.conn.commit()

# --- ASSETS ---
class AssetManager:
    def __init__(self, screen):
        self.screen = screen
        self.font_header = pygame.font.SysFont("Impact", 60)
        self.font_ui = pygame.font.SysFont("Arial", 20)
        self.font_big = pygame.font.SysFont("Arial", 30, bold=True)
        self.sounds = SoundManager()
        self.car_sprites = {}
        self.car_previews = {}
        self.scenery_objects = [] 
        
        self.screen.fill(BLACK)
        txt = self.font_header.render("INITIALIZING...", True, NEON_ORANGE)
        self.screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//2))
        pygame.display.flip()

        self.load_cars()
        
        # Load Tree
        self.tree_img = None
        for t_name in ["tree.png", "tree.jpg"]:
            if os.path.exists(t_name):
                try:
                    raw_tree = pygame.image.load(t_name)
                    raw_tree = self.aggressive_clean_image(raw_tree)
                    self.tree_img = self.scale_keep_aspect(raw_tree, 180, 180)
                    break
                except: pass

        self.track_data = self.generate_procedural_track()
        
        if self.tree_img:
            self.generate_scenery(self.track_data["mask"], 1500)

    def aggressive_clean_image(self, image):
        image = image.convert_alpha()
        width, height = image.get_size()
        for x in range(width):
            for y in range(height):
                r, g, b, a = image.get_at((x, y))
                if r > 200 and g > 200 and b > 200:
                    image.set_at((x, y), (0, 0, 0, 0)) 
        return image

    def scale_keep_aspect(self, image, max_w, max_h, rotate=False):
        rect = image.get_rect()
        ratio = min(max_w / rect.width, max_h / rect.height)
        new_size = (int(rect.width * ratio), int(rect.height * ratio))
        img = pygame.transform.smoothscale(image, new_size)
        if rotate: img = pygame.transform.rotate(img, -90)
        return img

    def load_cars(self):
        car_files = {
            "F1": "f1.png", "LE_MANS": "lemans.png",
            "NASCAR": "nascar.png", "SUPER": "super.png", "DRIFT": "drift.png"
        }
        for type_key, filename in car_files.items():
            if os.path.exists(filename):
                try:
                    raw = pygame.image.load(filename)
                    raw = self.aggressive_clean_image(raw) 
                    self.car_sprites[type_key] = self.scale_keep_aspect(raw, 55, 100, rotate=True)
                    self.car_previews[type_key] = self.scale_keep_aspect(raw, 180, 300, rotate=False)
                except: self.car_sprites[type_key] = None
            else: self.car_sprites[type_key] = None

    def catmull_rom_spline(self, points, steps=30):
        points = [points[-1]] + points + [points[0], points[1]]
        curve = []
        for i in range(len(points) - 3):
            p0, p1, p2, p3 = points[i], points[i+1], points[i+2], points[i+3]
            for t in range(steps):
                t /= steps
                q0 = -t**3 + 2*t**2 - t
                q1 = 3*t**3 - 5*t**2 + 2
                q2 = -3*t**3 + 4*t**2 + t
                q3 = t**3 - t**2
                x = 0.5 * (p0[0]*q0 + p1[0]*q1 + p2[0]*q2 + p3[0]*q3)
                y = 0.5 * (p0[1]*q0 + p1[1]*q1 + p2[1]*q2 + p3[1]*q3)
                curve.append((x, y))
        return curve

    def paint_track(self, surface, color, points, width):
        radius = width // 2
        for p in points:
            pygame.draw.circle(surface, color, (int(p[0]), int(p[1])), radius)

    def generate_scenery(self, mask_surface, num_trees):
        width, height = mask_surface.get_size()
        count = 0
        attempts = 0
        while count < num_trees and attempts < num_trees * 10:
            attempts += 1
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            try:
                col = mask_surface.get_at((x, y))
                if col[0] < 20 and col[1] < 20 and col[2] < 20:
                    scale = random.uniform(0.7, 1.1)
                    self.scenery_objects.append({"pos": (x, y), "scale": scale})
                    count += 1
            except: pass

    def generate_procedural_track(self):
        MAP_SIZE = 20000
        TRACK_WIDTH = 400 
        KERB_WIDTH = 480

        vis = pygame.Surface((MAP_SIZE, MAP_SIZE))
        mask_surf = pygame.Surface((MAP_SIZE, MAP_SIZE))
        vis.fill(GREEN) 
        mask_surf.fill(BLACK) 
        
        # --- TRACK LAYOUT ---
        points = [
            (14125, 7475),
            (14125, 13300),
            (13950, 14400),
            (13275, 15225),
            (10300, 16200),
            (3325, 16225),
            (1375, 13325),
            (2525, 11325),
            (9900, 12200),
            (12475, 11725),
            (13225, 10600),
            (12950, 9650),
            (12125, 9300),
            (2625, 9900),
            (1625, 9075),
            (1450, 7900),
            (2025, 6875),
            (1975, 5575),
            (2100, 3325),
            (2500, 2475),
            (3325, 1725),
            (4925, 1500),
            (6600, 1900),
            (8250, 2575),
            (14125, 7475),
        ]
        smooth_points = self.catmull_rom_spline(points, steps=100)
        
        self.paint_track(vis, KERB_RED, smooth_points, KERB_WIDTH)
        self.paint_track(vis, KERB_WHITE, smooth_points, KERB_WIDTH - 40)
        self.paint_track(vis, ASPHALT, smooth_points, TRACK_WIDTH)
        self.paint_track(mask_surf, WHITE, smooth_points, 550) 
        
        dash_length = 80   
        gap_length = 80    
        cycle_length = dash_length + gap_length
        current_distance = 0
        
        for i in range(len(smooth_points) - 1):
            p1 = smooth_points[i]
            p2 = smooth_points[i+1]
            dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            if (current_distance % cycle_length) < dash_length:
                pygame.draw.line(vis, WHITE, p1, p2, 12) 
            current_distance += dist

        # --- AUTO-CROP & MODERN MINIMAP ---
        all_x = [p[0] for p in smooth_points]
        all_y = [p[1] for p in smooth_points]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        padding = 500
        crop_x = max(0, min_x - padding)
        crop_y = max(0, min_y - padding)
        crop_w = min(MAP_SIZE - crop_x, (max_x - min_x) + padding * 2)
        crop_h = min(MAP_SIZE - crop_y, (max_y - min_y) + padding * 2)
        
        # Transparent surface
        minimap_surf = pygame.Surface((crop_w, crop_h), pygame.SRCALPHA)
        offset_points = [(p[0] - crop_x, p[1] - crop_y) for p in smooth_points]
        
        # Draw single smooth white line for the GPS look (Thicker: 120px)
        pygame.draw.lines(minimap_surf, (255, 255, 255, 255), True, offset_points, 120)
        minimap = pygame.transform.smoothscale(minimap_surf, (250, 250))
        
        # --- START LINE & SPAWN ---
        p0 = smooth_points[0]
        p1 = smooth_points[5] 
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        
        track_angle = math.degrees(math.atan2(-dy, dx))
        car_spawn_angle = track_angle 
        line_rot_angle = track_angle - 90

        length = math.hypot(dx, dy)
        dir_x = dx / length
        dir_y = dy / length
        right_x = -dir_y
        right_y = dir_x
        
        spacing = 60
        spawn_1 = (p0[0] - right_x * spacing, p0[1] - right_y * spacing)
        spawn_2 = (p0[0] + right_x * spacing, p0[1] + right_y * spacing)

        check_size = 40
        line_thickness = 80
        line_surf = pygame.Surface((TRACK_WIDTH, line_thickness), pygame.SRCALPHA)
        for x in range(0, TRACK_WIDTH, check_size):
            for y in range(0, line_thickness, check_size):
                color = WHITE if (x // check_size + y // check_size) % 2 == 0 else BLACK
                pygame.draw.rect(line_surf, color, (x, y, check_size, check_size))
        
        rot_line = pygame.transform.rotate(line_surf, line_rot_angle)
        line_rect = rot_line.get_rect(center=(int(p0[0]), int(p0[1])))
        vis.blit(rot_line, line_rect)

        mid_index = len(smooth_points) // 2
        mid_p = smooth_points[mid_index]

        meta = {
            "start_rect": pygame.Rect(p0[0]-200, p0[1]-200, 400, 400), 
            "check_rect": pygame.Rect(mid_p[0]-300, mid_p[1]-300, 600, 600), 
            "spawn_p1": spawn_1, 
            "spawn_p2": spawn_2, 
            "start_angle": car_spawn_angle,
            "crop_offset": (crop_x, crop_y),
            "crop_size": (crop_w, crop_h)
        }
        
        return {"vis": vis, "mask": mask_surf, "mini": minimap, "meta": meta}

# --- SOUND ---
class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        # Checks for .wav, .mp3, and .ogg
        self.extensions = [".wav", ".mp3", ".ogg"]
        self.sound_files = {
            "drift": "skid", 
            "crash": "crash",
            "start": "start", 
            "eng_v6": "eng_v6", 
            "eng_v8": "eng_v8",
            "eng_v10": "eng_v10",
            "eng_w16": "eng_w16"
        }
        
        for name, filename in self.sound_files.items():
            loaded = False
            for ext in self.extensions:
                full_path = filename + ext
                if os.path.exists(full_path):
                    try:
                        # print(f"Loading sound: {full_path}")
                        s = pygame.mixer.Sound(full_path)
                        if "drift" in name: s.set_volume(0.4)
                        else: s.set_volume(0.7)
                        self.sounds[name] = s
                        loaded = True
                        break
                    except Exception as e:
                        print(f"Error loading {full_path}: {e}")
            if not loaded:
                self.sounds[name] = None
            
    def play(self, name):
        if self.sounds.get(name): self.sounds[name].play()
        
    def get(self, name):
        return self.sounds.get(name)

# --- UI CLASSES ---
class TextInput:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.font = font
        self.active = True
        
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 10: 
                self.text += event.unicode
                
    def draw(self, screen):
        color = NEON_CYAN if self.active else GREY
        pygame.draw.rect(screen, color, self.rect, 2)
        txt_surf = self.font.render(self.text, True, WHITE)
        screen.blit(txt_surf, (self.rect.x + 10, self.rect.y + 10))

class Button:
    def __init__(self, x, y, w, h, text, font, color=NEON_CYAN):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.base_color = color
        self.hovered = False
        
    def draw(self, screen):
        s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        fill_col = (*self.base_color, 150) if self.hovered else (40, 40, 50, 200)
        s.fill(fill_col)
        screen.blit(s, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, self.base_color, self.rect, 2)
        txt_surf = self.font.render(self.text, True, WHITE)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)
        
    def check_click(self, pos):
        return self.rect.collidepoint(pos)

# --- CAR CLASS ---
class Car:
    def __init__(self, x, y, angle, car_type, color, controls, parts, audio, sprite):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.angle = angle 
        self.type = car_type
        self.controls = controls
        self.audio = audio
        self.sprite = sprite 
        self.color = color
        
        stats = CHASSIS_STATS[car_type]
        eng = ENGINES[parts['eng']]
        tyre = TYRES[parts['tyre']]
        brk = BRAKES[parts['brk']]
        
        self.mass = stats["mass"]
        self.max_speed = stats["base_spd"] * eng["spd_mult"]
        self.accel = stats["accel"] * eng["acc_mult"] 
        self.grip = stats["base_grip"] * tyre["grip_mult"] 
        self.turn_rate = stats["turn"] * tyre["turn_mult"] 
        self.brake_power = brk["power"]
        
        # --- AUDIO SYSTEM ---
        self.engine_sound_name = stats["sfx"]
        self.sound_obj = self.audio.get(self.engine_sound_name)
        
        self.channel_id = 0 if controls == "P1" else 1
        self.engine_channel = pygame.mixer.Channel(self.channel_id)
        
        if self.sound_obj:
            self.engine_channel.play(self.sound_obj, loops=-1)
            self.engine_channel.set_volume(0) 
        
        self.mouse_throttle = 0.0
        self.laps = 1
        self.checkpoint_passed = False
        self.finished = False

    def stop_audio(self):
        if self.engine_channel:
            self.engine_channel.fadeout(500)

    def update(self, mask_surface, meta_data):
        if self.finished:
            self.vel *= 0.95
            self.pos += self.vel
            self.engine_channel.set_volume(0)
            return

        keys = pygame.key.get_pressed()
        turning = 0
        throttle = 0 
        brake = False
        
        if self.controls == "P1":
            if keys[pygame.K_a]: turning = 1
            if keys[pygame.K_d]: turning = -1
            if keys[pygame.K_w]: throttle = 1  
            if keys[pygame.K_s]: brake = True  
        elif self.controls == "P2": 
            if keys[pygame.K_LEFT]: turning = 1
            if keys[pygame.K_RIGHT]: turning = -1
            if keys[pygame.K_UP]: throttle = 1    
            if keys[pygame.K_DOWN]: brake = True 
            m_but = pygame.mouse.get_pressed()
            if m_but[0]: turning = 1
            if m_but[2]: turning = -1
            if m_but[1]: brake = True
            if throttle == 0 and not brake:
                if self.mouse_throttle > 0: throttle = self.mouse_throttle

        rad = math.radians(self.angle)
        forward = pygame.math.Vector2(math.cos(rad), -math.sin(rad))
        right = pygame.math.Vector2(-math.sin(rad), -math.cos(rad))
        
        # --- ENGINE VOLUME LOGIC ---
        speed_ratio = self.vel.length() / self.max_speed
        if self.sound_obj:
            if throttle > 0:
                vol = 0.3 + (speed_ratio * 0.7)
            else:
                vol = speed_ratio * 0.5
            
            if self.vel.length() < 0.5:
                vol = 0
                
            self.engine_channel.set_volume(min(1.0, vol))

        if throttle > 0:
            self.vel += forward * self.accel * throttle
        
        if brake:
            if self.vel.dot(forward) > 0.5: 
                self.vel -= self.vel * self.brake_power
            else: 
                self.vel -= forward * (self.accel * 0.5)

        if throttle == 0 and not brake:
            self.vel *= 0.99

        if self.vel.length() > 0.5:
            d = 1 if self.vel.dot(forward) > -0.1 else -1
            self.angle += turning * self.turn_rate * (self.vel.length() / (self.max_speed * 0.8)) * d

        vel_forward = self.vel.dot(forward)
        vel_lateral = self.vel.dot(right)
        vel_lateral *= (1.0 - self.grip) 
        if abs(vel_lateral) > 2.0:
            if random.randint(0, 100) < 10: self.audio.play("drift")
        self.vel = (forward * vel_forward) + (right * vel_lateral)

        if self.vel.length() > self.max_speed: 
            self.vel.scale_to_length(self.max_speed)

        next_pos = self.pos + self.vel
        try:
            if 0 <= next_pos.x < mask_surface.get_width() and 0 <= next_pos.y < mask_surface.get_height():
                col = mask_surface.get_at((int(next_pos.x), int(next_pos.y)))
                if col[0] < 50: 
                    self.vel *= -0.5
                    self.audio.play("crash")
        except: self.vel *= -0.5

        self.pos += self.vel

        car_rect = pygame.Rect(self.pos.x, self.pos.y, 40, 40)
        if car_rect.colliderect(meta_data["check_rect"]): self.checkpoint_passed = True
        if car_rect.colliderect(meta_data["start_rect"]) and self.checkpoint_passed:
            self.laps += 1
            self.checkpoint_passed = False

    def draw(self, surface, cam_x, cam_y):
        if self.sprite:
            rot_img = pygame.transform.rotate(self.sprite, self.angle)
            new_rect = rot_img.get_rect(center=(self.pos.x - cam_x, self.pos.y - cam_y))
            surface.blit(rot_img, new_rect.topleft)
        else:
            w, h = 50, 90
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(s, self.color, (0, 0, w, h), border_radius=5)
            pygame.draw.rect(s, BLACK, (5, 20, 40, 20))
            rot_img = pygame.transform.rotate(s, self.angle - 90)
            rect = rot_img.get_rect(center=(self.pos.x - cam_x, self.pos.y - cam_y))
            surface.blit(rot_img, rect.topleft)

# --- GAME ENGINE ---
class Game:
    def __init__(self):
        pygame.init()
        # Allocate enough channels (2 for cars + 6 for SFX)
        pygame.mixer.set_num_channels(8)
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Speed Show - Modern Edition")
        self.clock = pygame.time.Clock()
        self.assets = AssetManager(self.screen)
        self.db = DatabaseManager()
        self.state = "MENU"
        
        self.p1_data = {"name": "", "type": "F1", "parts": {"eng": 0, "tyre": 1, "brk": 0}}
        self.p2_data = {"name": "", "type": "DRIFT", "parts": {"eng": 0, "tyre": 1, "brk": 0}}
        
        self.race_start_time = 0
        self.start_sequence_time = 0
        self.race_active = False 
        self.car1 = None
        self.car2 = None
        self.winner = None
        self.win_time_str = ""
        self.saved_db = False 
        
        cx = SCREEN_WIDTH // 2
        self.input_p1 = TextInput(cx - 100, 220, 200, 40, self.assets.font_big)
        self.input_p2 = TextInput(cx - 100, 220, 200, 40, self.assets.font_big)
        
        self.btn_start = Button(cx-100, 400, 200, 60, "START", self.assets.font_big, NEON_ORANGE)
        self.btn_exit = Button(cx-100, 500, 200, 60, "EXIT", self.assets.font_big, GREY)
        self.btn_p1_next = Button(cx-100, 650, 200, 50, "NEXT >", self.assets.font_big, NEON_ORANGE)
        self.btn_p2_race = Button(cx-100, 650, 200, 50, "RACE!", self.assets.font_big, NEON_TEAL)
        self.btn_car_prev = Button(cx-250, 300, 50, 150, "<", self.assets.font_header)
        self.btn_car_next = Button(cx+200, 300, 50, 150, ">", self.assets.font_header)
        
        self.part_btns = []
        self.part_btns.append({"btn": Button(cx-180, 480, 40, 40, "<", self.assets.font_ui), "act": "eng_d"})
        self.part_btns.append({"btn": Button(cx+140, 480, 40, 40, ">", self.assets.font_ui), "act": "eng_u"})
        self.part_btns.append({"btn": Button(cx-180, 530, 40, 40, "<", self.assets.font_ui), "act": "tyr_d"})
        self.part_btns.append({"btn": Button(cx+140, 530, 40, 40, ">", self.assets.font_ui), "act": "tyr_u"})
        self.part_btns.append({"btn": Button(cx-180, 580, 40, 40, "<", self.assets.font_ui), "act": "brk_d"})
        self.part_btns.append({"btn": Button(cx+140, 580, 40, 40, ">", self.assets.font_ui), "act": "brk_u"})

    def run(self):
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if self.state == "P1_SETUP": self.input_p1.handle_event(event)
                if self.state == "P2_SETUP": self.input_p2.handle_event(event)
                if event.type == pygame.KEYDOWN and self.state == "RACE" and event.key == pygame.K_ESCAPE:
                    # FIX: Stop engine sounds when returning to menu
                    if self.car1: self.car1.stop_audio()
                    if self.car2: self.car2.stop_audio()
                    self.state = "MENU"

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "MENU":
                        if self.btn_start.check_click((mx, my)): self.state = "P1_SETUP"
                        if self.btn_exit.check_click((mx, my)): running = False
                    elif self.state == "P1_SETUP":
                        if self.btn_p1_next.check_click((mx, my)):
                            self.p1_data["name"] = self.input_p1.text if self.input_p1.text else "Player 1"
                            self.state = "P2_SETUP"
                        if self.btn_car_prev.check_click((mx, my)): self.cycle_car(1, -1)
                        if self.btn_car_next.check_click((mx, my)): self.cycle_car(1, 1)
                        for item in self.part_btns:
                            if item["btn"].check_click((mx, my)): self.cycle_part(1, item["act"])
                    elif self.state == "P2_SETUP":
                        if self.btn_p2_race.check_click((mx, my)):
                            self.p2_data["name"] = self.input_p2.text if self.input_p2.text else "Player 2"
                            self.start_race()
                        if self.btn_car_prev.check_click((mx, my)): self.cycle_car(2, -1)
                        if self.btn_car_next.check_click((mx, my)): self.cycle_car(2, 1)
                        for item in self.part_btns:
                            if item["btn"].check_click((mx, my)): self.cycle_part(2, item["act"])
                    elif self.state == "WIN":
                        if pygame.mouse.get_pressed()[0]: self.state = "MENU"

            self.screen.fill(BLACK)
            if self.state == "MENU": self.draw_menu(mx, my)
            elif self.state == "P1_SETUP": self.draw_setup_screen(mx, my, 1)
            elif self.state == "P2_SETUP": self.draw_setup_screen(mx, my, 2)
            elif self.state == "RACE": 
                self.update_race()
                self.draw_race()
            elif self.state == "WIN":
                self.draw_win()

            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def cycle_car(self, p_num, direction):
        keys = list(CHASSIS_STATS.keys())
        data = self.p1_data if p_num == 1 else self.p2_data
        curr = keys.index(data["type"])
        data["type"] = keys[(curr + direction) % len(keys)]

    def cycle_part(self, p_num, act):
        data = self.p1_data if p_num == 1 else self.p2_data
        parts = data["parts"]
        if "eng" in act: parts["eng"] = (parts["eng"] + (1 if "u" in act else -1)) % len(ENGINES)
        if "tyr" in act: parts["tyre"] = (parts["tyre"] + (1 if "u" in act else -1)) % len(TYRES)
        if "brk" in act: parts["brk"] = (parts["brk"] + (1 if "u" in act else -1)) % len(BRAKES)

    def start_race(self):
        meta = self.assets.track_data["meta"]
        s1 = self.assets.car_sprites.get(self.p1_data["type"])
        s2 = self.assets.car_sprites.get(self.p2_data["type"])
        self.car1 = Car(*meta["spawn_p1"], meta["start_angle"], self.p1_data["type"], NEON_ORANGE, "P1", self.p1_data["parts"], self.assets.sounds, s1)
        self.car2 = Car(*meta["spawn_p2"], meta["start_angle"], self.p2_data["type"], NEON_TEAL, "P2", self.p2_data["parts"], self.assets.sounds, s2)
        self.start_sequence_time = pygame.time.get_ticks()
        self.race_active = False 
        self.state = "RACE"
        # PLAY START SOUND ONCE
        self.assets.sounds.play("start")

    def update_race(self):
        now = pygame.time.get_ticks()
        time_diff = now - self.start_sequence_time
        
        # Countdown Logic (Visual only, Sound is played in start_race)
        if time_diff < 4000: # Assuming 4 sec audio file
            pass # Waiting for Go
        elif not self.race_active:
            self.race_active = True
            self.race_start_time = now 
        
        mask = self.assets.track_data["mask"]
        meta = self.assets.track_data["meta"]
        
        if self.race_active:
            self.car1.update(mask, meta)
            self.car2.update(mask, meta)
        
        if self.car1.pos.distance_to(self.car2.pos) < 45:
            col_vec = (self.car1.pos - self.car2.pos).normalize()
            force = 10.0
            total = self.car1.mass + self.car2.mass
            self.car1.vel += col_vec * (force * (self.car2.mass/total))
            self.car2.vel -= col_vec * (force * (self.car1.mass/total))
            self.car1.pos += col_vec * 5
            self.assets.sounds.play("crash")

        elapsed = now - self.race_start_time
        if self.car1.laps > TOTAL_LAPS: 
            self.winner = self.p1_data["name"]; self.win_car = self.p1_data["type"]
            self.finish_race(elapsed)
        elif self.car2.laps > TOTAL_LAPS: 
            self.winner = self.p2_data["name"]; self.win_car = self.p2_data["type"]
            self.finish_race(elapsed)

    def finish_race(self, elapsed_ms):
        mins = elapsed_ms // 60000
        secs = (elapsed_ms // 1000) % 60
        mils = (elapsed_ms % 1000) // 10
        self.win_time_str = f"{mins:02}:{secs:02}:{mils:02}"
        
        # FIX: Stop engine sounds immediately on win
        if self.car1: self.car1.stop_audio()
        if self.car2: self.car2.stop_audio()
        
        if not self.saved_db:
            self.db.save_result(self.winner, self.win_car, self.win_time_str)
            self.saved_db = True
        self.state = "WIN"

    def draw_menu(self, mx, my):
        draw_text(self.screen, "SPEED SHOW", self.assets.font_header, YELLOW, SCREEN_WIDTH//2, 150, True)
        draw_text(self.screen, "MODERN EDITION", self.assets.font_ui, WHITE, SCREEN_WIDTH//2, 220, True)
        for btn in [self.btn_start, self.btn_exit]:
            btn.hovered = btn.check_click((mx, my))
            btn.draw(self.screen)

    def draw_setup_screen(self, mx, my, player_num):
        cx = SCREEN_WIDTH // 2
        color = NEON_ORANGE if player_num == 1 else NEON_TEAL
        data = self.p1_data if player_num == 1 else self.p2_data
        
        draw_glass_panel(self.screen, cx-300, 50, 600, 620, color)
        draw_text(self.screen, f"PLAYER {player_num} SETUP", self.assets.font_header, color, cx, 100, True)
        draw_text(self.screen, "DRIVER NAME:", self.assets.font_ui, WHITE, cx, 180, True)
        if player_num == 1: self.input_p1.draw(self.screen)
        else: self.input_p2.draw(self.screen)
        
        prev = self.assets.car_previews.get(data["type"])
        if prev: 
            r = prev.get_rect(center=(cx, 370))
            self.screen.blit(prev, r)
        else:
            draw_text(self.screen, "NO IMAGE", self.assets.font_ui, WHITE, cx, 370, True)

        draw_text(self.screen, data["type"], self.assets.font_big, WHITE, cx, 280, True)
        
        self.btn_car_prev.hovered = self.btn_car_prev.check_click((mx, my))
        self.btn_car_prev.draw(self.screen)
        self.btn_car_next.hovered = self.btn_car_next.check_click((mx, my))
        self.btn_car_next.draw(self.screen)
        
        parts = data["parts"]
        draw_text(self.screen, f"ENGINE: {ENGINES[parts['eng']]['name']}", self.assets.font_ui, WHITE, cx, 500, True)
        draw_text(self.screen, f"TYRES: {TYRES[parts['tyre']]['name']}", self.assets.font_ui, WHITE, cx, 550, True)
        draw_text(self.screen, f"BRAKES: {BRAKES[parts['brk']]['name']}", self.assets.font_ui, WHITE, cx, 600, True)
        
        for item in self.part_btns:
            item["btn"].hovered = item["btn"].check_click((mx, my))
            item["btn"].draw(self.screen)
            
        btn = self.btn_p1_next if player_num == 1 else self.btn_p2_race
        btn.hovered = btn.check_click((mx, my))
        btn.draw(self.screen)

    def draw_race(self):
        vis = self.assets.track_data["vis"]
        
        # --- PLAYER 1 VIEW ---
        cam1_x = self.car1.pos.x - SCREEN_WIDTH/4
        cam1_y = self.car1.pos.y - SCREEN_HEIGHT/2
        self.screen.set_clip(pygame.Rect(0, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
        self.screen.blit(vis, (-cam1_x, -cam1_y))
        
        if self.assets.tree_img:
            for tree in self.assets.scenery_objects:
                tx, ty = tree['pos']
                if abs(tx - self.car1.pos.x) < 1000 and abs(ty - self.car1.pos.y) < 800:
                    t_rect = self.assets.tree_img.get_rect(center=(tx - cam1_x, ty - cam1_y))
                    self.screen.blit(self.assets.tree_img, t_rect)

        self.car1.draw(self.screen, cam1_x, cam1_y)
        self.car2.draw(self.screen, cam1_x, cam1_y)
        
        draw_glass_panel(self.screen, 10, 10, 250, 90, NEON_ORANGE)
        draw_text(self.screen, self.p1_data["name"], self.assets.font_big, NEON_ORANGE, 20, 20)
        draw_text(self.screen, f"LAP: {self.car1.laps}/{TOTAL_LAPS}", self.assets.font_ui, WHITE, 20, 60)
        speed = min(1.0, self.car1.vel.length() / 60.0)
        pygame.draw.rect(self.screen, GREY, (20, 85, 200, 8))
        pygame.draw.rect(self.screen, NEON_ORANGE, (20, 85, 200*speed, 8))
        draw_text(self.screen, f"{int(self.car1.vel.length()*3)} KMH", self.assets.font_ui, WHITE, 230, 80)
        
        # --- PLAYER 2 VIEW ---
        cam2_x = self.car2.pos.x - SCREEN_WIDTH*3/4
        cam2_y = self.car2.pos.y - SCREEN_HEIGHT/2
        self.screen.set_clip(pygame.Rect(SCREEN_WIDTH//2, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
        self.screen.blit(vis, (-cam2_x, -cam2_y))
        
        if self.assets.tree_img:
            for tree in self.assets.scenery_objects:
                tx, ty = tree['pos']
                if abs(tx - self.car2.pos.x) < 1000 and abs(ty - self.car2.pos.y) < 800:
                    t_rect = self.assets.tree_img.get_rect(center=(tx - cam2_x, ty - cam2_y))
                    self.screen.blit(self.assets.tree_img, t_rect)

        self.car1.draw(self.screen, cam2_x, cam2_y)
        self.car2.draw(self.screen, cam2_x, cam2_y)
        
        hud_x = SCREEN_WIDTH - 260
        draw_glass_panel(self.screen, hud_x, 10, 250, 90, NEON_TEAL)
        draw_text(self.screen, self.p2_data["name"], self.assets.font_big, NEON_TEAL, hud_x+10, 20)
        draw_text(self.screen, f"LAP: {self.car2.laps}/{TOTAL_LAPS}", self.assets.font_ui, WHITE, hud_x+10, 60)
        speed2 = min(1.0, self.car2.vel.length() / 60.0)
        pygame.draw.rect(self.screen, GREY, (hud_x+10, 85, 200, 8))
        pygame.draw.rect(self.screen, NEON_TEAL, (hud_x+10, 85, 200*speed2, 8))
        draw_text(self.screen, f"{int(self.car2.vel.length()*3)} KMH", self.assets.font_ui, WHITE, hud_x-80, 80)

        self.screen.set_clip(None)
        pygame.draw.line(self.screen, BLACK, (SCREEN_WIDTH//2, 0), (SCREEN_WIDTH//2, SCREEN_HEIGHT), 5)
        
        self.draw_minimap()
        
        elapsed = pygame.time.get_ticks() - self.start_sequence_time
        if elapsed < 3000:
            box_x = SCREEN_WIDTH//2 - 120
            draw_glass_panel(self.screen, box_x, 150, 240, 100, BLACK)
            lights = 1 if elapsed < 1000 else (2 if elapsed < 2000 else 3)
            for i in range(3):
                col = RED if i < lights else (50, 0, 0)
                pygame.draw.circle(self.screen, col, (box_x + 40 + i*80, 200), 30)
        elif elapsed < 4000:
            box_x = SCREEN_WIDTH//2 - 120
            draw_glass_panel(self.screen, box_x, 150, 240, 100, BLACK)
            for i in range(3):
                pygame.draw.circle(self.screen, GREEN, (box_x + 40 + i*80, 200), 30)
            self.draw_timer()
        else:
            self.draw_timer()

    def draw_timer(self):
        race_time = pygame.time.get_ticks() - self.race_start_time
        mins = race_time // 60000
        secs = (race_time // 1000) % 60
        mils = (race_time % 1000) // 10
        timer_str = f"{mins:02}:{secs:02}:{mils:02}"
        draw_glass_panel(self.screen, SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT-60, 200, 50, BLACK)
        draw_text(self.screen, timer_str, self.assets.font_big, YELLOW, SCREEN_WIDTH//2, SCREEN_HEIGHT-35, True)

    def draw_minimap(self):
        track_mini = self.assets.track_data["mini"]
        meta = self.assets.track_data["meta"]
        
        map_w, map_h = track_mini.get_size()
        real_w, real_h = meta["crop_size"]
        offset_x, offset_y = meta["crop_offset"]
        
        map_x = (SCREEN_WIDTH // 2) - (map_w // 2)
        map_y = 10
        
        # --- NEW: NO BLACK BOX, JUST THE TRANSPARENT TRACK ---
        self.screen.blit(track_mini, (map_x, map_y))
        
        scale_x = map_w / real_w 
        scale_y = map_h / real_h
        
        p1_x = map_x + ((self.car1.pos.x - offset_x) * scale_x)
        p1_y = map_y + ((self.car1.pos.y - offset_y) * scale_y)
        pygame.draw.circle(self.screen, NEON_ORANGE, (int(p1_x), int(p1_y)), 5)
        
        p2_x = map_x + ((self.car2.pos.x - offset_x) * scale_x)
        p2_y = map_y + ((self.car2.pos.y - offset_y) * scale_y)
        pygame.draw.circle(self.screen, NEON_TEAL, (int(p2_x), int(p2_y)), 5)

    def draw_win(self):
        draw_glass_panel(self.screen, SCREEN_WIDTH//2-300, 200, 600, 300, BLACK)
        draw_text(self.screen, f"{self.winner} WINS!", self.assets.font_header, NEON_CYAN, SCREEN_WIDTH//2, 250, True)
        draw_text(self.screen, f"TIME: {self.win_time_str}", self.assets.font_big, WHITE, SCREEN_WIDTH//2, 320, True)
        draw_text(self.screen, "Stats Saved!", self.assets.font_ui, GREEN, SCREEN_WIDTH//2, 400, True)
        draw_text(self.screen, "Click to Menu", self.assets.font_ui, WHITE, SCREEN_WIDTH//2, 450, True)

if __name__ == "__main__":
    Game().run()