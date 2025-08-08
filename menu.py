import render
import pygame
import numpy as np
import math
import time
import moderngl
from entity import baseEntity
from game import Game

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
        super().__init__(0, 0, 10, False, "game_models/dudeAtBoard.txt")
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

class Menu:
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height

        self.counter = 0

        self.menu_state = "MAIN"

        self.play_button = Button(100, self.HEIGHT // 2 - 50, 200, 50, "> missions.cmd", 45, ctx, line_prog)
        self.options_button = Button(100, self.HEIGHT // 2 + 20, 200, 50, "> config.sys", 45, ctx, line_prog)
        self.deck_button = Button(100, self.HEIGHT // 2 + 90, 200, 50, "> loadout.dat", 45, ctx, line_prog)
        self.terminal_button = Button(100, self.HEIGHT // 2 + 160, 200, 50, "> terminal.exe", 45, ctx, line_prog)
        self.shop_button = Button(100, self.HEIGHT // 2 + 230, 200, 50, "> shop.net", 45, ctx, line_prog)

        self.sandbox_button = Button(100, self.HEIGHT // 2 - 50, 200, 50, "> sandbox.exe", 45, ctx, line_prog)
        self.campaign_button = Button(100, self.HEIGHT // 2 + 20, 200, 50, "> campaign.exe", 45, ctx, line_prog)
        self.multiplayer_button = Button(100, self.HEIGHT // 2 + 90, 200, 50, "> multiplayer.exe (NOT DONE)", 45, ctx, line_prog)
        self.back_button = Button(100, self.HEIGHT // 2 + 160, 200, 50, "> back.cmd", 45, ctx, line_prog)

        self.menu_entity = menuEntity()

        self.select_pos = 0

        self.main_select_spots = [
            (80, self.HEIGHT // 2 - 20, 15, 30),
            (80, self.HEIGHT // 2 + 50, 15, 30),
            (80, self.HEIGHT // 2 + 120, 15, 30),
            (80, self.HEIGHT // 2 + 190, 15, 30),
            (80, self.HEIGHT // 2 + 260, 15, 30)
        ]

        self.mission_select_spots = [
            (80, self.HEIGHT // 2 - 20, 15, 30),
            (80, self.HEIGHT // 2 + 50, 15, 30),
            (80, self.HEIGHT // 2 + 120, 15, 30),
            (80, self.HEIGHT // 2 + 190, 15, 30)
        ]

        self.key_reset = 0

    def draw_terminal_border(self):
        border_color = (0, 180, 0)
        border_thickness = 3
        
        render.draw_rect(self.ctx, (0, 0, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, self.HEIGHT - border_thickness, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.WIDTH - border_thickness, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)

    def draw_terminal_header(self):
        header_y = 20
        render.draw_text(self.ctx, "OPERATION STONEWALL TACTICAL TERMINAL v6.7", (20, header_y), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")
        render.draw_text(self.ctx, f"SYSTEM TIME: {time.strftime('%H:%M:%S')}", (self.WIDTH - 300, header_y), (0, 255, 0), font_size=25, font_path="font\Tektur-Black.ttf")
        separator_y = header_y + 50
        for i in range(0, self.WIDTH - 40, 20):
            render.draw_text(self.ctx, "-", (20 + i, separator_y), (0, 150, 0), font_size=25, font_path="font\Tektur-Black.ttf")

    def draw_system_status(self):
        status_y = self.HEIGHT - 80
        
        statuses = [
            "TACTICAL_NET: ONLINE",
            "WEAPONS_SYS: READY", 
            "COMM_LINK: ACTIVE"
        ]
        
        for i, status in enumerate(statuses):
            x_pos = 30 + i * 250
            color = (0, 255, 0) if "ONLINE" in status or "READY" in status or "ACTIVE" in status else (255, 100, 0)
            render.draw_text(self.ctx, status, (x_pos, status_y), color, font_size=20, font_path="font\Tektur-Black.ttf")

    def draw_command_prompt(self):
        prompt_y = self.HEIGHT - 40
        if self.menu_state == "MAIN":
            render.draw_text(self.ctx, "C:\\STONEWALL> _", (30, prompt_y), (0, 255, 0), font_size=25, font_path="font\Tektur-Black.ttf")
        else:
            render.draw_text(self.ctx, "C:\\STONEWALL\\MISSIONS> _", (30, prompt_y), (0, 255, 0), font_size=25, font_path="font\Tektur-Black.ttf")

    def render_main_menu(self):
        render.draw_text(self.ctx, ">> Operation Stonewall <<", (100, 120), (0, 255, 0), font_size=50, font_path="font\Tektur-Black.ttf")
        render.draw_text(self.ctx, "USE ARROW KEYS TO NAVIGATE | SPACE TO EXECUTE", (100, 180), (0, 255, 0), font_size=25, font_path="font\Tektur-Black.ttf")

        self.play_button.draw()
        self.options_button.draw()
        self.deck_button.draw()
        self.terminal_button.draw()
        self.shop_button.draw()

        if self.counter % 40 < 20:
            render.draw_rect(self.ctx, self.main_select_spots[self.select_pos], (0, 255, 0), self.line_prog, True)

    def render_mission_select_menu(self):
        self.sandbox_button.draw()
        self.campaign_button.draw()
        self.multiplayer_button.draw()
        self.back_button.draw()

        if self.counter % 40 < 20:
            render.draw_rect(self.ctx, self.mission_select_spots[self.select_pos], (0, 255, 0), self.line_prog, True)

    def handle_main_menu_input(self, keys, gamestates, main):
        if keys[pygame.K_DOWN] and self.key_reset > 30:
            self.key_reset = 0
            self.select_pos = (self.select_pos + 1) % 5  

        if keys[pygame.K_UP] and self.key_reset > 30:
            self.key_reset = 0
            self.select_pos = (self.select_pos - 1) % 5  

        if keys[pygame.K_SPACE] and self.key_reset > 30:
            self.key_reset = 0
            if self.select_pos == 0:
                self.menu_state = "MISSION_SELECT"
                self.select_pos = 0
            elif self.select_pos == 1:
                main.current_state = gamestates.OPTIONS
            elif self.select_pos == 2:
                main.current_state = gamestates.DECK_BUILD
            elif self.select_pos == 3:
                main.current_state = gamestates.TERMINAL
            elif self.select_pos == 4:
                main.current_state = gamestates.SHOP

    def handle_mission_select_input(self, keys, gamestates, main):
        if keys[pygame.K_DOWN] and self.key_reset > 30:
            self.key_reset = 0
            self.select_pos = (self.select_pos + 1) % 4

        if keys[pygame.K_UP] and self.key_reset > 30:
            self.key_reset = 0
            self.select_pos = (self.select_pos - 1) % 4

        if keys[pygame.K_SPACE] and self.key_reset > 30:
            self.key_reset = 0
            if self.select_pos == 0:
                main.game = Game(main.ctx, main.line_prog, main.WIDTH, main.HEIGHT)
                main.current_state = gamestates.SANDBOX_MENU
            elif self.select_pos == 1:
                main.game = Game(main.ctx, main.line_prog, main.WIDTH, main.HEIGHT)
                main.current_state = gamestates.CAMPAIGN
            elif self.select_pos == 2:
                #main.current_state = gamestates.MULTIPLAYER_MENU
                print("This is where multiplayer wouldve been")
            elif self.select_pos == 3:
                self.menu_state = "MAIN"
                self.select_pos = 0

    def render_menu(self, gamestates, main):
        self.key_reset += 1
        self.counter += 1

        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        for i in range(0, self.HEIGHT, 8):
            if (self.counter + i) % 120 < 50:
                render.draw_rect(self.ctx, (0, i, self.WIDTH, 1), (0, 50, 0), self.line_prog, True)

        self.draw_terminal_border()

        keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()

        self.draw_terminal_header()

        model_center_x = self.WIDTH - 300  
        model_center_y = self.HEIGHT // 2  
        self.menu_entity.render_3d_model(self.ctx, self.line_prog, model_center_x, model_center_y)

        if self.menu_state == "MAIN":
            self.handle_main_menu_input(keys, gamestates, main)
            self.render_main_menu()
        elif self.menu_state == "MISSION_SELECT":
            self.handle_mission_select_input(keys, gamestates, main)
            self.render_mission_select_menu()

        self.draw_system_status()
        self.draw_command_prompt()