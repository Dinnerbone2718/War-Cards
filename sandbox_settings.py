import render
import pygame
import numpy as np
import math
import time
import moderngl
from entity import baseEntity
from game import Game
import map_func as mf
import entity as e
import random
from card_global import updated_base_cords, card_instances
from card import EntityCard

class Button:
    def __init__(self, x, y, width, height, text, size, ctx, line_prog, draw_border=False, color=(0, 255, 0)):
        self.ctx = ctx
        self.line_prog = line_prog
        self.rect = (x, y, width, height)
        self.text = text
        self.size = size
        self.hovered = False
        self.color = color

    def draw(self):
        render.draw_text(self.ctx, self.text, (self.rect[0] + 10, self.rect[1] + 10), self.color, font_size=self.size, font_path="font\Tektur-Black.ttf")

class menuEntity(baseEntity):
    def __init__(self):
        super().__init__(0, 0, 10, False, "game_models/bomb.txt")
        self.rotation = 180
        self.start_time = time.time()
        self.rotation_speed = 20  
        self.current_rotation = 0
        self.model_offset = np.array([0, 0, 0])
        self.preview_scale = 1200
        
    def update_rotation(self):
        current_time = time.time()
        elapsed = current_time - self.start_time
        self.current_rotation = (elapsed * self.rotation_speed) % 360
        
    def _get_rotation_matrix(self, angle_degrees):
        angle_radians = math.radians(angle_degrees)
        cos_theta = math.cos(angle_radians)
        sin_theta = math.sin(angle_radians)
        return np.array([
            [cos_theta, 0, sin_theta],
            [0, 1, 0],
            [-sin_theta, 0, cos_theta]
        ])
    
    def _apply_offset_to_vertices(self, vertices):
        if len(vertices) == 0:
            return vertices
        return vertices + self.model_offset
    
    def _project_to_screen_space(self, vertices, center_x, center_y):
        if len(vertices) == 0:
            return np.array([])
        
        z_values = np.maximum(vertices[:, 2] + 3, 0.1)
        factor = self.preview_scale / z_values
        
        screen_x = center_x + vertices[:, 0] * factor * 0.4
        screen_y = center_y + vertices[:, 1] * factor * 0.4
        
        return np.column_stack((screen_x, screen_y))
    
    def _render_model_edges(self, ctx, line_prog, center_x, center_y):
        self.update_rotation()
        
        rotation_matrix = self._get_rotation_matrix(self.current_rotation)
        
        offset_vertices = self._apply_offset_to_vertices(self.local_vertices)
        rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
        
        projected_points = self._project_to_screen_space(rotated_vertices, center_x, center_y)
        
        if len(projected_points) == 0:
            return
        
        edge_vertices = []
        for start_idx, end_idx in self.edges:
            if start_idx < len(projected_points) and end_idx < len(projected_points):
                edge_vertices.extend([
                    projected_points[start_idx],
                    projected_points[end_idx]
                ])
        
        if not edge_vertices:
            return
        
        viewport_width, viewport_height = ctx.viewport[2:4]
        normalized_vertices = []
        for point in edge_vertices:
            norm_x = (point[0] / viewport_width) * 2 - 1
            norm_y = -((point[1] / viewport_height) * 2 - 1)
            normalized_vertices.extend([norm_x, norm_y])
        
        line_prog['color'].value = (self.color[0]/255.0, self.color[1]/255.0, self.color[2]/255.0)
        vertices_array = np.array(normalized_vertices, dtype='f4')
        vbo = ctx.buffer(vertices_array.tobytes())
        vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
        ctx.line_width = 2.0
        vao.render(moderngl.LINES)
        vao.release()
        vbo.release()
    
    def render_3d_model(self, ctx, line_prog, center_x, center_y):
        self._render_model_edges(ctx, line_prog, center_x, center_y)

class Sandbox_Menu:
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height

        self.counter = 0

        self.map_sizes = ["SMALL", "MEDIUM", "LARGE", "HUGE"]
        self.map_size_index = 1

        self.starting_money = 100
        
        self.money_multipliers = ["0.25x", "0.5x", "1.0x", "1.5x", "2.0x"]
        self.money_mult_index = 2

        self.fog_of_war = False

        self.win_conditions = ["CAPTURE", "KILLS", "OBJECTIVES (NOT MADE)", "WAVES (NOT MADE)", "NO VICTORY (NOT MADE)"]
        self.win_condition_index = 0

        self.seed = random.randint(0, 100)
        self.seed_input = str(self.seed)
        self.seed_editing = False
        self.seed_cursor_pos = len(self.seed_input)

        self.menu_entity = menuEntity()

        self.select_pos = 0
        self.max_options = 9

        self.option_select_spots = [
            (80, 160, 15, 30),
            (80, 210, 15, 30),
            (80, 260, 15, 30),
            (80, 310, 15, 30),
            (80, 360, 15, 30),
            (80, 410, 15, 30),
            (80, 460, 15, 30),
            (80, 540, 15, 30),
            (80, 590, 15, 30)
        ]

        self.key_reset = 0

    def update_game_vals(self, main):
        global updated_base_cords, card_instances
        if self.map_sizes[self.map_size_index] == "SMALL":
            size = 25
        elif self.map_sizes[self.map_size_index] == "MEDIUM":
            size = 50
        elif self.map_sizes[self.map_size_index] == "LARGE":
            size = 75
        elif self.map_sizes[self.map_size_index] == "HUGE":
            size = 100

        try:
            seed_value = int(self.seed_input) if self.seed_input else self.seed
        except ValueError:
            seed_value = self.seed

        updated_base_cords = [((size*3)/2, (size*3)-10), ((size*3)/2, 7.5)]

        card_instances["stealth_plane"] = EntityCard(e.stealthPlane(1, 1, True, updated_base_cords), 50, scale=.3)
        card_instances["bomber"] = EntityCard(e.bomber(1, 1, True, updated_base_cords), 75, scale= .4)

        main.game = Game(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT, board_size=size, seed=seed_value, 
                         starting_money=self.starting_money, money_multiplier=float(self.money_multipliers[self.money_mult_index][:-1]),
                         fog_of_war=self.fog_of_war, win_condition = self.win_conditions[self.win_condition_index])


    def draw_terminal_border(self):
        border_color = (0, 180, 0)
        border_thickness = 3
        
        render.draw_rect(self.ctx, (0, 0, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, self.HEIGHT - border_thickness, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.WIDTH - border_thickness, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)

    def draw_system_status(self):
        status_y = self.HEIGHT - 80
        
        statuses = [
            "CONFIG_SYS: ONLINE",
            "SETTINGS_DB: READY", 
            "MEMORY_SYS: ACTIVE"
        ]
        
        for i, status in enumerate(statuses):
            x_pos = 30 + i * 250
            color = (0, 255, 0) if "ONLINE" in status or "READY" in status or "ACTIVE" in status else (255, 100, 0)
            render.draw_text(self.ctx, status, (x_pos, status_y), color, font_size=20, font_path="font\Tektur-Black.ttf")

    def draw_command_prompt(self):
        prompt_y = self.HEIGHT - 40
        render.draw_text(self.ctx, "C:\\STONEWALL\\MISSIONS\\SANDBOX\\CONFIG> _", (30, prompt_y), (0, 255, 0), font_size=25, font_path="font\Tektur-Black.ttf")

    def generate_random_seed(self):
        self.seed = random.randint(0, 100)
        self.seed_input = str(self.seed)
        self.seed_cursor_pos = len(self.seed_input)

    def handle_seed_input(self, event):
        if not self.seed_editing:
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                self.seed_editing = False
                try:
                    self.seed = int(self.seed_input) if self.seed_input else 0
                except ValueError:
                    self.seed_input = str(self.seed)
            elif event.key == pygame.K_BACKSPACE:
                if self.seed_cursor_pos > 0:
                    self.seed_input = self.seed_input[:self.seed_cursor_pos-1] + self.seed_input[self.seed_cursor_pos:]
                    self.seed_cursor_pos -= 1
            elif event.key == pygame.K_DELETE:
                if self.seed_cursor_pos < len(self.seed_input):
                    self.seed_input = self.seed_input[:self.seed_cursor_pos] + self.seed_input[self.seed_cursor_pos+1:]
            elif event.key == pygame.K_LEFT:
                self.seed_cursor_pos = max(0, self.seed_cursor_pos - 1)
            elif event.key == pygame.K_RIGHT:
                self.seed_cursor_pos = min(len(self.seed_input), self.seed_cursor_pos + 1)
            elif event.unicode.isdigit() and len(self.seed_input) < 10:
                self.seed_input = self.seed_input[:self.seed_cursor_pos] + event.unicode + self.seed_input[self.seed_cursor_pos:]
                self.seed_cursor_pos += 1

    def render_options_menu(self):
        render.draw_text(self.ctx, ">> MISSION PARAMETERS <<", (100, 30), (0, 255, 0), font_size=50, font_path="font\Tektur-Black.ttf")
        render.draw_text(self.ctx, "ARROW KEYS: NAVIGATE | LEFT/RIGHT: ADJUST | SPACE: SELECT/BACK", (100, 110), (0, 255, 0), font_size=20, font_path="font\Tektur-Black.ttf")

        map_size_text = f"> map_size.cfg: {self.map_sizes[self.map_size_index]}"
        render.draw_text(self.ctx, map_size_text, (100, 150), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        money_text = f"> start_funds.dat: ${self.starting_money}"
        render.draw_text(self.ctx, money_text, (100, 200), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        mult_text = f"> income_rate.cfg: {self.money_multipliers[self.money_mult_index]}"
        render.draw_text(self.ctx, mult_text, (100, 250), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        fog_text = f"> fog_of_war.sys: {'ENABLED' if self.fog_of_war else 'DISABLED'}"
        render.draw_text(self.ctx, fog_text, (100, 300), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        win_text = f"> game_type.exe: {self.win_conditions[self.win_condition_index]}"
        render.draw_text(self.ctx, win_text, (100, 350), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        seed_display = self.seed_input if self.seed_editing else str(self.seed)
        seed_color = (255, 255, 0) if self.seed_editing else (0, 255, 0)
        seed_text = f"> map_seed.hex: {seed_display}"
        
        if self.seed_editing and self.counter % 60 < 30:
            cursor_pos = len(f"> map_seed.hex: ") + self.seed_cursor_pos
            seed_text = seed_text[:len(f"> map_seed.hex: ") + self.seed_cursor_pos] + "|" + seed_text[len(f"> map_seed.hex: ") + self.seed_cursor_pos:]
        
        render.draw_text(self.ctx, seed_text, (100, 400), seed_color, font_size=35, font_path="font\Tektur-Black.ttf")

        render.draw_text(self.ctx, "> randomize_seed.bat", (100, 450), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        render.draw_text(self.ctx, "> start.cmd", (100, 530), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")
        render.draw_text(self.ctx, "> return.exe", (100, 580), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        if self.counter % 40 < 20 and not self.seed_editing:
            render.draw_rect(self.ctx, self.option_select_spots[self.select_pos], (0, 255, 0), self.line_prog, True)

    def handle_options_input(self, keys, gamestates, main):
        if self.seed_editing:
            return
            
        if keys[pygame.K_DOWN] and self.key_reset > 15:
            self.key_reset = 0
            self.select_pos = (self.select_pos + 1) % self.max_options

        if keys[pygame.K_UP] and self.key_reset > 15:
            self.key_reset = 0
            self.select_pos = (self.select_pos - 1) % self.max_options

        if keys[pygame.K_LEFT] and self.key_reset > 15:
            self.key_reset = 0
            self.adjust_setting(-1)

        if keys[pygame.K_RIGHT] and self.key_reset > 15:
            self.key_reset = 0
            self.adjust_setting(1)

        if keys[pygame.K_SPACE] and self.key_reset > 30:
            self.key_reset = 0
            if self.select_pos == 5:
                self.seed_editing = True
                self.seed_input = str(self.seed)
                self.seed_cursor_pos = len(self.seed_input)
            elif self.select_pos == 6:
                self.generate_random_seed()
            elif self.select_pos == 7:
                self.update_game_vals(main)
                main.current_state = gamestates.PLAYING
            elif self.select_pos == 8:
                main.current_state = gamestates.MENU

    def adjust_setting(self, direction):
        if self.select_pos == 0:
            self.map_size_index = (self.map_size_index + direction) % len(self.map_sizes)
        elif self.select_pos == 1:
            self.starting_money = max(0, min(100, self.starting_money + (direction * 5)))
        elif self.select_pos == 2:
            self.money_mult_index = (self.money_mult_index + direction) % len(self.money_multipliers)
        elif self.select_pos == 3:
            self.fog_of_war = not self.fog_of_war
        elif self.select_pos == 4:
            self.win_condition_index = (self.win_condition_index + direction) % len(self.win_conditions)
        elif self.select_pos == 5:
            try:
                current_seed = int(self.seed_input) if self.seed_input else self.seed
                new_seed = max(0, min(999999, current_seed + (direction * 1000)))
                self.seed = new_seed
                self.seed_input = str(new_seed)
            except ValueError:
                pass

    def get_current_settings(self):
        multiplier_values = [0.25, 0.5, 1.0, 1.5, 2.0]
        try:
            seed_value = int(self.seed_input) if self.seed_input else self.seed
        except ValueError:
            seed_value = self.seed
            
        return {
            'map_size': self.map_sizes[self.map_size_index].lower(),
            'starting_money': self.starting_money,
            'money_multiplier': multiplier_values[self.money_mult_index],
            'fog_of_war': self.fog_of_war,
            'win_condition': self.win_conditions[self.win_condition_index].lower(),
            'seed': seed_value
        }

    def render_menu(self, gamestates, main, events=None):
        self.key_reset += 1
        self.counter += 1

        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        for i in range(0, self.HEIGHT, 8):
            if (self.counter + i) % 120 < 50:
                render.draw_rect(self.ctx, (0, i, self.WIDTH, 1), (0, 50, 0), self.line_prog, True)

        self.draw_terminal_border()

        if events:
            for event in events:
                self.handle_seed_input(event)

        keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()

        model_center_x = self.WIDTH - 300  
        model_center_y = self.HEIGHT // 2  
        self.menu_entity.render_3d_model(self.ctx, self.line_prog, model_center_x, model_center_y)

        self.handle_options_input(keys, gamestates, main)
        self.render_options_menu()

        self.draw_system_status()
        self.draw_command_prompt()
