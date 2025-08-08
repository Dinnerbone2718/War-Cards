import global_vals
import render
import pygame
import json
import os

class Settings:
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefix = f"{script_dir}/"
        self.tick = 0

        self.screen_sizes = [
            "1024x768", 
            "1280x720",
            "1366x768",
            "1920x1080",
            "2560x1440"
        ]
        self.screen_size_index = 2

        self.master_volume = 75
        self.music_volume = 60
        self.game_volume = 80

        self.select_pos = 0
        self.max_options = 6
        self.key_reset = 0

        self.option_select_spots = [
            (80, 160, 15, 30),
            (80, 210, 15, 30),
            (80, 260, 15, 30),
            (80, 310, 15, 30),
            (80, 400, 15, 30),
            (80, 450, 15, 30),

        ]

        self.get_current_settings()

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
            "SAT_CONEC: ONLINE",
            "GAME: UNFINISHED", 
            "LUPUS: NEVER"
        ]
        
        for i, status in enumerate(statuses):
            x_pos = 30 + i * 250
            color = (0, 255, 0) if "ONLINE" in status or "READY" in status or "ACTIVE" in status else (255, 100, 0)
            render.draw_text(self.ctx, status, (x_pos, status_y), color, font_size=20, font_path="font\Tektur-Black.ttf")

    def draw_command_prompt(self):
        prompt_y = self.HEIGHT - 40
        render.draw_text(self.ctx, "C:\\STONEWALL\\CONFIG.SYS> _", (30, prompt_y), (0, 255, 0), font_size=25, font_path="font\Tektur-Black.ttf")

    def draw_volume_bar(self, x, y, volume, width=300, height=20):

        x+= 60
        y+=10

        render.draw_rect(self.ctx, (x, y, width, height), (50, 50, 50), self.line_prog, True)
        
        fill_width = int((volume / 100.0) * width)
        if fill_width > 0:
            bar_color = (0, 255, 0) if volume > 20 else (255, 100, 0) if volume > 0 else (100, 100, 100)
            render.draw_rect(self.ctx, (x, y, fill_width, height), bar_color, self.line_prog, True)
        
        render.draw_rect(self.ctx, (x-1, y-1, width+2, height+2), (0, 180, 0), self.line_prog, False)

    def render_settings_menu(self):
        render.draw_text(self.ctx, ">> SYSTEM CONFIGURATION <<", (100, 30), (0, 255, 0), font_size=50, font_path="font\Tektur-Black.ttf")
        render.draw_text(self.ctx, "ARROW KEYS: NAVIGATE | LEFT/RIGHT: ADJUST | SPACE: BACK", (100, 110), (0, 255, 0), font_size=20, font_path="font\Tektur-Black.ttf")

        screen_text = f"> display.cfg: {self.screen_sizes[self.screen_size_index]}"
        render.draw_text(self.ctx, screen_text, (100, 150), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        master_text = f"> master_vol.dat: {self.master_volume}%"
        render.draw_text(self.ctx, master_text, (100, 200), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")
        self.draw_volume_bar(450, 205, self.master_volume)

        music_text = f"> music_vol.cfg: {self.music_volume}%"
        render.draw_text(self.ctx, music_text, (100, 250), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")
        self.draw_volume_bar(450, 255, self.music_volume)

        game_text = f"> sfx_vol.sys: {self.game_volume}%"
        render.draw_text(self.ctx, game_text, (100, 300), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")
        self.draw_volume_bar(450, 305, self.game_volume)


        render.draw_text(self.ctx, "> apply.exe", (100, 390), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")
        render.draw_text(self.ctx, "> return.exe", (100, 440), (0, 255, 0), font_size=35, font_path="font\Tektur-Black.ttf")

        if self.tick % 40 < 20:
            render.draw_rect(self.ctx, self.option_select_spots[self.select_pos], (0, 255, 0), self.line_prog, True)

    def adjust_setting(self, direction):
        if self.select_pos == 0:
            self.screen_size_index = (self.screen_size_index + direction) % len(self.screen_sizes)
        elif self.select_pos == 1:
            self.master_volume = max(0, min(100, self.master_volume + (direction * 5)))
        elif self.select_pos == 2:
            self.music_volume = max(0, min(100, self.music_volume + (direction * 5)))
        elif self.select_pos == 3:
            self.game_volume = max(0, min(100, self.game_volume + (direction * 5)))

    def handle_input(self, keys, gamestates, main):
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
                main.current_state = gamestates.MENU
            elif self.select_pos == 4:
                self.apply_settings()

        if keys[pygame.K_ESCAPE] and self.key_reset > 30:
            self.key_reset = 0
            main.current_state = gamestates.MENU

    def apply_settings(self):
        print(self.screen_sizes[self.screen_size_index])
        global_vals.SCREEN_SIZE = [int(x) for x in self.screen_sizes[self.screen_size_index].split('x')]

        with open(f"{self.prefix}save_data.json", "r") as f:
            data = json.load(f)
        
        data["screen_size"] = self.screen_size_index
        data["master_vol"] = self.master_volume
        data["music_volume"] = self.music_volume
        data["game_volume"] = self.game_volume
        data["size"] = global_vals.SCREEN_SIZE

        with open(f"{self.prefix}save_data.json", "w") as f:
            json.dump(data, f)


        print(global_vals.SCREEN_SIZE)
        pass

    def get_current_settings(self):
        with open(f"{self.prefix}save_data.json", "r") as f:
            data = json.load(f)
        
        self.screen_size_index = data["screen_size"]
        self.master_volume = data["master_vol"]
        self.music_volume = data["music_volume"]
        self.game_volume = data["game_volume"]

    def render_menu(self, gamestates, main, events=None):
        self.tick += 1
        self.key_reset += 1

        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        for i in range(0, self.HEIGHT, 8):
            if (self.tick + i) % 120 < 50:
                render.draw_rect(self.ctx, (0, i, self.WIDTH, 1), (0, 50, 0), self.line_prog, True)

        self.draw_terminal_border()

        keys = pygame.key.get_pressed()
        self.handle_input(keys, gamestates, main)

        self.render_settings_menu()

        self.draw_system_status()
        self.draw_command_prompt()
