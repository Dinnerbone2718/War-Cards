import render
import pygame
import math
from game import Game
import global_vals
import json
import os
from card_global import cards_in_deck, owned_cards
import entity as e
import card_global
from card import EntityCard
import random


level_data = {
    1: {
        "board_size": 50,
        "seed": 67,
        "starting_money": 100,
        "money_multiplier": 1,
        "fog_of_war": False,
        "num_of_cities": 1,
        "win_condition": "CAPTURE",
        "biome": "beach",
        "ai_deck": {
            "small_tank": 0, "supply_truck": 3, "small_plane": 2, "infantry": 9,
            "artillery": 0, "stealth_plane": 0, "sniper": 0, "anti_air": 0,
            "helicopter": 0, "attack_helicopter": 0, "bomber": 0
        }
    },
    2: {
        "board_size": 100,
        "seed": 2,
        "starting_money": 25,
        "money_multiplier": 2,
        "fog_of_war": False,
        "num_of_cities": 2,
        "win_condition": "KILLS",
        "biome": "grass",
        "ai_deck": {
            "small_tank": 1, "supply_truck": 2, "small_plane": 2, "infantry": 8,
            "artillery": 1, "stealth_plane": 0, "sniper": 5, "anti_air": 0,
            "helicopter": 0, "attack_helicopter": 0, "bomber": 0
        }
    },
    3: {
        "board_size": 60,
        "seed": 13,
        "starting_money": 40,
        "money_multiplier": 0.5,
        "fog_of_war": False,
        "num_of_cities": 3,
        "win_condition": "CAPTURE",
        "biome": "grass",
        "ai_deck": {
            "small_tank": 2, "supply_truck": 2, "small_plane": 2, "infantry": 7,
            "artillery": 1, "stealth_plane": 0, "sniper": 4, "anti_air": 1,
            "helicopter": 0, "attack_helicopter": 0, "bomber": 1
        }
    },
    4: {
        "board_size": 70,
        "seed": 99,
        "starting_money": 60,
        "money_multiplier": 0.75,
        "fog_of_war": False,
        "num_of_cities": 1,
        "win_condition": "KILLS",
        "biome": "grass",
        "ai_deck": {
            "small_tank": 3, "supply_truck": 2, "small_plane": 2, "infantry": 6,
            "artillery": 2, "stealth_plane": 0, "sniper": 3, "anti_air": 1,
            "helicopter": 1, "attack_helicopter": 0, "bomber": 1
        }
    },
    5: {
        "board_size": 80,
        "seed": 42,
        "starting_money": 30,
        "money_multiplier": 1.25,
        "fog_of_war": False,
        "num_of_cities": 2,
        "win_condition": "CAPTURE",
        "biome": "grass",
        "ai_deck": {
            "small_tank": 3, "supply_truck": 2, "small_plane": 3, "infantry": 5,
            "artillery": 2, "stealth_plane": 0, "sniper": 2, "anti_air": 2,
            "helicopter": 1, "attack_helicopter": 0, "bomber": 2
        }
    },
    6: {
        "board_size": 90,
        "seed": 77,
        "starting_money": 85,
        "money_multiplier": 1.5,
        "fog_of_war": False,
        "num_of_cities": 3,
        "win_condition": "KILLS",
        "biome": "grass",
        "ai_deck": {
            "small_tank": 4, "supply_truck": 2, "small_plane": 3, "infantry": 4,
            "artillery": 2, "stealth_plane": 0, "sniper": 2, "anti_air": 2,
            "helicopter": 2, "attack_helicopter": 1, "bomber": 2
        }
    },
    7: {
        "board_size": 100,
        "seed": 21,
        "starting_money": 50,
        "money_multiplier": 1.75,
        "fog_of_war": False,
        "num_of_cities": 1,
        "win_condition": "CAPTURE",
        "biome": "grass",
        "ai_deck": {
            "small_tank": 4, "supply_truck": 2, "small_plane": 3, "infantry": 3,
            "artillery": 3, "stealth_plane": 0, "sniper": 1, "anti_air": 3,
            "helicopter": 2, "attack_helicopter": 1, "bomber": 2
        }
    },
    8: {
        "board_size": 110,
        "seed": 56,
        "starting_money": 70,
        "money_multiplier": 2,
        "fog_of_war": False,
        "num_of_cities": 2,
        "win_condition": "KILLS",
        "biome": "desert",
        "ai_deck": {
            "small_tank": 4, "supply_truck": 2, "small_plane": 3, "infantry": 2,
            "artillery": 3, "stealth_plane": 1, "sniper": 1, "anti_air": 3,
            "helicopter": 2, "attack_helicopter": 1, "bomber": 2
        }
    },
    9: {
        "board_size": 120,
        "seed": 88,
        "starting_money": 20,
        "money_multiplier": 0.25,
        "fog_of_war": True,
        "num_of_cities": 1,
        "win_condition": "CAPTURE",
        "biome": "desert",
        "ai_deck": {
            "small_tank": 4, "supply_truck": 2, "small_plane": 3, "infantry": 2,
            "artillery": 3, "stealth_plane": 2, "sniper": 1, "anti_air": 3,
            "helicopter": 2, "attack_helicopter": 2, "bomber": 2
        }
    },
    10: {
        "board_size": 130,
        "seed": 101,
        "starting_money": 95,
        "money_multiplier": 0.5,
        "fog_of_war": True,
        "num_of_cities": 3,
        "win_condition": "KILLS",
        "biome": "desert",
        "ai_deck": {
            "small_tank": 5, "supply_truck": 2, "small_plane": 3, "infantry": 1,
            "artillery": 3, "stealth_plane": 3, "sniper": 1, "anti_air": 3,
            "helicopter": 2, "attack_helicopter": 3, "bomber": 2
        }
    }
}

class Level:
    def __init__(self, x, y, level, pre_req, name, dif, description=""):
        self.x = x
        self.y = y
        self.rect = (x-40, y-40, 80, 80)
        self.level_num = level
        self.pre_req = pre_req
        self.name = name
        self.difficulty = dif
        self.description = description
        self.completed = False
        self.color = (255, 255, 255)
        self.border_color = (100, 100, 100)
        self.text_color = (0, 0, 0)
        self.hovered = False
        self.pulse_timer = 0
        
    def get_center(self):
        return (self.x, self.y)
    
    def is_available(self):
        if self.pre_req is None:
            return True
        for level in self.pre_req:
            if not level.completed:
                return False
        return True
    
    def update(self, mouse_pos, offset_x, offset_y):
        self.pulse_timer += 1
        adjusted_rect = (
            self.rect[0] + offset_x, 
            self.rect[1] + offset_y, 
            self.rect[2], 
            self.rect[3]
        )
        self.hovered = (
            adjusted_rect[0] <= mouse_pos[0] <= adjusted_rect[0] + adjusted_rect[2] and
            adjusted_rect[1] <= mouse_pos[1] <= adjusted_rect[1] + adjusted_rect[3]
        )
        if self.completed:
            self.color = (50, 200, 50)
            self.border_color = (0, 255, 0)
            self.text_color = (255, 255, 255)
        elif self.is_available():
            if self.hovered:
                pulse = abs(math.sin(self.pulse_timer * 0.1)) * 50
                self.color = (200 + pulse, 200 + pulse, 200)
                self.border_color = (150, 150, 150)
            else:
                self.color = (255, 255, 255)
                self.border_color = (200, 200, 200)
            self.text_color = (0, 0, 0)
        else:
            self.color = (100, 50, 50)
            self.border_color = (255, 0, 0)
            self.text_color = (200, 100, 100)
    
    def is_clicked(self, mouse_pos, offset_x, offset_y):
        adjusted_rect = (
            self.rect[0] + offset_x, 
            self.rect[1] + offset_y, 
            self.rect[2], 
            self.rect[3]
        )
        return (
            adjusted_rect[0] <= mouse_pos[0] <= adjusted_rect[0] + adjusted_rect[2] and
            adjusted_rect[1] <= mouse_pos[1] <= adjusted_rect[1] + adjusted_rect[3]
        )

class Campaign_Menu:
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height
        self.levels = []
        self.x = 0
        self.y = 0
        self.selected_level = None
        self.scroll_speed = 8
        self.setup_levels()
        self.info_panel_width = 300
        self.show_info_panel = False
        
        self.back_button_rect = (20, self.HEIGHT - 60, 80, 40)
        self.back_button_hovered = False
        self.back_button_clicked = False
        
        self.save_button_rect = (120, self.HEIGHT - 60, 100, 40)
        self.load_button_rect = (240, self.HEIGHT - 60, 100, 40)
        self.save_button_hovered = False
        self.load_button_hovered = False
        
        self.deck_selection_button_rect = (self.WIDTH - 200, 20, 180, 40)
        self.deck_selection_dropdown_open = False
        self.selected_deck_name = "deck1"
        self.available_decks = {}
        self.load_available_decks()
        
        self.load_campaign_progress()
        self.continents = [
            self.generate_continent(center=(500.0, 500.0), radius=500, seed=0, irregularity=0.1),
            self.generate_continent(center=(2000.0, 1050.0), radius=220, seed=1, irregularity=0.1),
            self.generate_continent(center=(1200.0, -200.0), radius=300, seed=0, irregularity=0.1),

        ]

    def setup_levels(self):
        level1 = Level(250, 450, 1, None, "Boot Camp", 1, "temp")
        
        level2 = Level(400, 230, 2, [level1], "First Contact", 1, "temp")
        
        level3 = Level(450, 700, 3, [level1], "Defensive Stand", 2, "temp")
        
        level4 = Level(600, 350, 4, [level2], "Air Superiority", 2, "temp")
        
        level5 = Level(650, 600, 5, [level3], "Grass Storm", 2, "temp")
        
        level6 = Level(800, 250, 6, [level4], "Steel Thunder", 3, "temp")
        
        level7 = Level(800, 500, 7, [level5], "Shadow Operations", 3, "temp")
        
        level8 = Level(1100, -250, 8, [level6, level7], "Ghost Protocol", 4, "temp")
        
        level9 = Level(1200, -100, 9, [level8], "Fog of War", 4, "temp")
        
        level10 = Level(1400, -200, 10, [level9], "Final Assault", 5, "temp")

        self.levels = [
            level1, level2, level3, level4, level5, level6, level7, level8, level9, level10
        ]

    '''
        challenge1 = Level(1900, 950, "A", [], "Challenge 1", 5, "First challenge.")
        challenge2 = Level(2100, 950, "B", [], "Challenge 2", 5, "Second challenge.")
        challenge3 = Level(1900, 1150, "C", [], "Challenge 3", 5, "Third challenge.")
        challenge4 = Level(2100, 1150, "D", [], "Challenge 4", 5, "Fourth challenge.")
        challengeF = Level(
            2000, 1050, "Z",
            [challenge1, challenge2, challenge3, challenge4],
            "Final", 5, "The ultimate challenge."
        )

        self.levels += [
            challenge1, challenge2, challenge3, challenge4, challengeF
        ]
    '''
    def save_campaign_progress(self):
        progress_data = {}
        
        for level in self.levels:
            progress_data[str(level.level_num)] = level.completed
        
        global_vals.campaign_progress = progress_data
        
        try:
            try:
                with open("campaign_save.json", "r") as f:
                    save_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                save_data = {}
            
            save_data["campaign_progress"] = progress_data
            
            with open("campaign_save.json", "w") as f:
                json.dump(save_data, f, indent=2)
            
            print("Campaign progress saved successfully!")
            
        except Exception as e:
            print(f"Error saving campaign progress: {e}")
    
    def load_campaign_progress(self):
        try:
            if hasattr(global_vals, 'campaign_progress') and global_vals.campaign_progress:
                progress_data = global_vals.campaign_progress
            else:
                try:
                    with open("campaign_save.json", "r") as f:
                        save_data = json.load(f)
                        progress_data = save_data.get("campaign_progress", {})
                except (FileNotFoundError, json.JSONDecodeError):
                    progress_data = {}
            
            for level in self.levels:
                level_key = str(level.level_num)
                if level_key in progress_data:
                    level.completed = progress_data[level_key]
            
            global_vals.campaign_progress = progress_data
            
            if progress_data:
                print("Campaign progress loaded successfully!")
            
        except Exception as e:
            print(f"Error loading campaign progress: {e}")
    
    def draw_connection_lines(self):
        for level in self.levels:
            if level.pre_req:
                level_center = level.get_center()
                level_screen_pos = (level_center[0] + self.x, level_center[1] + self.y)
                for prereq in level.pre_req:
                    prereq_center = prereq.get_center()
                    prereq_screen_pos = (prereq_center[0] + self.x, prereq_center[1] + self.y)
                    if prereq.completed:
                        line_color = (0, 200, 0)
                    else:
                        line_color = (200, 0, 0)

                    render.draw_line(self.ctx, prereq_screen_pos, level_screen_pos, line_color, self.line_prog)
    
    def draw_line(self, start_pos, end_pos, color, thickness):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            return
        segments = int(length / 5) + 1
        for i in range(segments):
            t = i / segments
            x = start_pos[0] + dx * t
            y = start_pos[1] + dy * t
            render.draw_rect(self.ctx, (x-thickness//2, y-thickness//2, thickness, thickness), color, self.line_prog, True)
    
    def draw_terminal_border(self):
        border_color = (0, 180, 0)
        border_thickness = 3
        render.draw_rect(self.ctx, (0, 0, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, self.HEIGHT - border_thickness, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.WIDTH - border_thickness, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)
    
    def draw_back_button(self):
        mouse_pos = pygame.mouse.get_pos()
        
        self.back_button_hovered = (
            self.back_button_rect[0] <= mouse_pos[0] <= self.back_button_rect[0] + self.back_button_rect[2] and
            self.back_button_rect[1] <= mouse_pos[1] <= self.back_button_rect[1] + self.back_button_rect[3]
        )
        
        if self.back_button_hovered:
            button_color = (60, 60, 60)
            border_color = (0, 255, 0)
            text_color = (255, 255, 255)
        else:
            button_color = (40, 40, 40)
            border_color = (0, 180, 0)
            text_color = (200, 200, 200)
        
        render.draw_rect(self.ctx, self.back_button_rect, button_color, self.line_prog, True)
        
        border_thickness = 2
        render.draw_rect(self.ctx, (self.back_button_rect[0], self.back_button_rect[1], self.back_button_rect[2], border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.back_button_rect[0], self.back_button_rect[1] + self.back_button_rect[3] - border_thickness, self.back_button_rect[2], border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.back_button_rect[0], self.back_button_rect[1], border_thickness, self.back_button_rect[3]), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.back_button_rect[0] + self.back_button_rect[2] - border_thickness, self.back_button_rect[1], border_thickness, self.back_button_rect[3]), border_color, self.line_prog, True)
        
        text_x = self.back_button_rect[0] + self.back_button_rect[2] // 2 - 20
        text_y = self.back_button_rect[1] + self.back_button_rect[3] // 2 - 8
        render.draw_text(self.ctx, "BACK", (text_x, text_y), text_color, font_size=16, font_path="font/Tektur-Black.ttf")
    
    def draw_save_load_buttons(self):
        mouse_pos = pygame.mouse.get_pos()
        
        self.save_button_hovered = (
            self.save_button_rect[0] <= mouse_pos[0] <= self.save_button_rect[0] + self.save_button_rect[2] and
            self.save_button_rect[1] <= mouse_pos[1] <= self.save_button_rect[1] + self.save_button_rect[3]
        )
        
        if self.save_button_hovered:
            save_button_color = (60, 60, 60)
            save_border_color = (0, 255, 0)
            save_text_color = (255, 255, 255)
        else:
            save_button_color = (40, 40, 40)
            save_border_color = (0, 180, 0)
            save_text_color = (200, 200, 200)
        
        render.draw_rect(self.ctx, self.save_button_rect, save_button_color, self.line_prog, True)
        
        border_thickness = 2
        render.draw_rect(self.ctx, (self.save_button_rect[0], self.save_button_rect[1], self.save_button_rect[2], border_thickness), save_border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.save_button_rect[0], self.save_button_rect[1] + self.save_button_rect[3] - border_thickness, self.save_button_rect[2], border_thickness), save_border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.save_button_rect[0], self.save_button_rect[1], border_thickness, self.save_button_rect[3]), save_border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.save_button_rect[0] + self.save_button_rect[2] - border_thickness, self.save_button_rect[1], border_thickness, self.save_button_rect[3]), save_border_color, self.line_prog, True)
        
        save_text_x = self.save_button_rect[0] + self.save_button_rect[2] // 2 - 20
        save_text_y = self.save_button_rect[1] + self.save_button_rect[3] // 2 - 8
        render.draw_text(self.ctx, "SAVE", (save_text_x, save_text_y), save_text_color, font_size=16, font_path="font/Tektur-Black.ttf")
        
        self.load_button_hovered = (
            self.load_button_rect[0] <= mouse_pos[0] <= self.load_button_rect[0] + self.load_button_rect[2] and
            self.load_button_rect[1] <= mouse_pos[1] <= self.load_button_rect[1] + self.load_button_rect[3]
        )
        
        if self.load_button_hovered:
            load_button_color = (60, 60, 60)
            load_border_color = (0, 255, 0)
            load_text_color = (255, 255, 255)
        else:
            load_button_color = (40, 40, 40)
            load_border_color = (0, 180, 0)
            load_text_color = (200, 200, 200)
        
        render.draw_rect(self.ctx, self.load_button_rect, load_button_color, self.line_prog, True)
        
        render.draw_rect(self.ctx, (self.load_button_rect[0], self.load_button_rect[1], self.load_button_rect[2], border_thickness), load_border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.load_button_rect[0], self.load_button_rect[1] + self.load_button_rect[3] - border_thickness, self.load_button_rect[2], border_thickness), load_border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.load_button_rect[0], self.load_button_rect[1], border_thickness, self.load_button_rect[3]), load_border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.load_button_rect[0] + self.load_button_rect[2] - border_thickness, self.load_button_rect[1], border_thickness, self.load_button_rect[3]), load_border_color, self.line_prog, True)
        
        load_text_x = self.load_button_rect[0] + self.load_button_rect[2] // 2 - 20
        load_text_y = self.load_button_rect[1] + self.load_button_rect[3] // 2 - 8
        render.draw_text(self.ctx, "LOAD", (load_text_x, load_text_y), load_text_color, font_size=16, font_path="font/Tektur-Black.ttf")
    
    def is_back_button_clicked(self, mouse_pos):
        return (
            self.back_button_rect[0] <= mouse_pos[0] <= self.back_button_rect[0] + self.back_button_rect[2] and
            self.back_button_rect[1] <= mouse_pos[1] <= self.back_button_rect[1] + self.back_button_rect[3]
        )
    
    def is_save_button_clicked(self, mouse_pos):
        return (
            self.save_button_rect[0] <= mouse_pos[0] <= self.save_button_rect[0] + self.save_button_rect[2] and
            self.save_button_rect[1] <= mouse_pos[1] <= self.save_button_rect[1] + self.save_button_rect[3]
        )
    
    def is_load_button_clicked(self, mouse_pos):
        return (
            self.load_button_rect[0] <= mouse_pos[0] <= self.load_button_rect[0] + self.load_button_rect[2] and
            self.load_button_rect[1] <= mouse_pos[1] <= self.load_button_rect[1] + self.load_button_rect[3]
        )
    
    def draw_levels(self):
        mouse_pos = pygame.mouse.get_pos()
        self.draw_connection_lines()
        for level in self.levels:
            level.update(mouse_pos, self.x, self.y)
            level_rect = (
                level.rect[0] + self.x, 
                level.rect[1] + self.y, 
                level.rect[2], 
                level.rect[3]
            )
            render.draw_rect(self.ctx, level_rect, level.color, self.line_prog, True)
            border_thickness = 3
            render.draw_rect(self.ctx, (level_rect[0], level_rect[1], level_rect[2], border_thickness), level.border_color, self.line_prog, True)
            render.draw_rect(self.ctx, (level_rect[0], level_rect[1] + level_rect[3] - border_thickness, level_rect[2], border_thickness), level.border_color, self.line_prog, True)
            render.draw_rect(self.ctx, (level_rect[0], level_rect[1], border_thickness, level_rect[3]), level.border_color, self.line_prog, True)
            render.draw_rect(self.ctx, (level_rect[0] + level_rect[2] - border_thickness, level_rect[1], border_thickness, level_rect[3]), level.border_color, self.line_prog, True)
            text_x = level_rect[0] + level_rect[2] // 2 - 10
            text_y = level_rect[1] + level_rect[3] // 2 - 10
            render.draw_text(self.ctx, str(level.level_num), (text_x, text_y), level.text_color, font_size=20, font_path="font/Tektur-Black.ttf")
            name_x = level_rect[0] + level_rect[2] // 2 - len(level.name) * 4
            name_y = level_rect[1] + level_rect[3] + 10
            render.draw_text(self.ctx, level.name, (name_x, name_y), (255, 255, 255), font_size=16, font_path="font/Tektur-Black.ttf")
            star_y = name_y + 20
            for i in range(5):
                star_x = level_rect[0] + level_rect[2] // 2 - 30 + i * 12
                star_color = (255, 255, 0) if i < level.difficulty else (100, 100, 100)
                render.draw_text(self.ctx, "*", (star_x, star_y), star_color, font_size=16, font_path="font/Tektur-Black.ttf")
    
    def draw_info_panel(self):
        if not self.selected_level:
            return
        panel_x = self.WIDTH - self.info_panel_width
        panel_color = (20, 20, 40)
        render.draw_rect(self.ctx, (panel_x, 0, self.info_panel_width, self.HEIGHT), panel_color, self.line_prog, True)
        border_color = (0, 180, 0)
        render.draw_rect(self.ctx, (panel_x, 0, 3, self.HEIGHT), border_color, self.line_prog, True)
        y_offset = 50
        render.draw_text(self.ctx, self.selected_level.name, (panel_x + 20, y_offset), (255, 255, 255), font_size=24, font_path="font/Tektur-Black.ttf")
        y_offset += 40
        render.draw_text(self.ctx, f"Mission {self.selected_level.level_num}", (panel_x + 20, y_offset), (0, 255, 0), font_size=18, font_path="font/Tektur-Black.ttf")
        y_offset += 30
        render.draw_text(self.ctx, f"Difficulty: {self.selected_level.difficulty}/5", (panel_x + 20, y_offset), (255, 200, 0), font_size=16, font_path="font/Tektur-Black.ttf")
        y_offset += 40
        render.draw_text(self.ctx, "Description:", (panel_x + 20, y_offset), (200, 200, 200), font_size=16, font_path="font/Tektur-Black.ttf")
        y_offset += 25
        words = self.selected_level.description.split()
        line = ""
        for word in words:
            if len(line + word) > 25:
                render.draw_text(self.ctx, line, (panel_x + 20, y_offset), (180, 180, 180), font_size=14, font_path="font/Tektur-Black.ttf")
                y_offset += 20
                line = word + " "
            else:
                line += word + " "
        if line:
            render.draw_text(self.ctx, line, (panel_x + 20, y_offset), (180, 180, 180), font_size=14, font_path="font/Tektur-Black.ttf")
        y_offset += 40
        status_text = "COMPLETED" if self.selected_level.completed else ("AVAILABLE" if self.selected_level.is_available() else "LOCKED")
        status_color = (0, 255, 0) if self.selected_level.completed else ((255, 255, 0) if self.selected_level.is_available() else (255, 0, 0))
        render.draw_text(self.ctx, f"Status: {status_text}", (panel_x + 20, y_offset), status_color, font_size=16, font_path="font/Tektur-Black.ttf")
        if self.selected_level.pre_req:
            y_offset += 40
            render.draw_text(self.ctx, "Prerequisites:", (panel_x + 20, y_offset), (200, 200, 200), font_size=16, font_path="font/Tektur-Black.ttf")
            y_offset += 25
            for prereq in self.selected_level.pre_req:
                prereq_color = (0, 255, 0) if prereq.completed else (255, 0, 0)
                render.draw_text(self.ctx, f"{prereq.name}", (panel_x + 30, y_offset), prereq_color, font_size=14, font_path="font/Tektur-Black.ttf")
                y_offset += 20

    def update_controls(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y -= self.scroll_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y += self.scroll_speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x += self.scroll_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x -= self.scroll_speed
        
        if keys[pygame.K_ESCAPE]:
            self.selected_level = None
    
    def handle_mouse_click(self, mouse_pos, gamestates, main):
        if self.is_back_button_clicked(mouse_pos):
            print("Back button clicked!")
            main.current_state = gamestates.MENU
            return True
        
        if self.is_save_button_clicked(mouse_pos):
            print("Save button clicked!")
            self.save_campaign_progress()
            return True
        
        if self.is_load_button_clicked(mouse_pos):
            print("Load button clicked!")
            self.load_campaign_progress()
            return True
        
        if self.handle_deck_selection_click(mouse_pos):
            return True

        for level in self.levels:
            if level.is_clicked(mouse_pos, self.x, self.y):
                if self.selected_level == level and level.is_available():
                    data = (level_data[level.level_num])

                    card_global.updated_base_cords = [((data["board_size"]*3)/2, (data["board_size"]*3)-10), ((data["board_size"]*3)/2, 7.5)]
                    print(card_global.updated_base_cords)
                    card_global.card_instances["stealth_plane"] = EntityCard(e.stealthPlane(1, 1, True, card_global.updated_base_cords), 50, scale=.3)
                    card_global.card_instances["bomber"] = EntityCard(e.bomber(1, 1, True, card_global.updated_base_cords), 75, scale= .4)

                    main.game = Game(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT, data["board_size"], data["seed"],
                                     data["starting_money"], data["money_multiplier"], data["fog_of_war"], data["num_of_cities"],
                                     data["win_condition"], data["biome"], "campaign", data["ai_deck"]
                                     
                                     )
                    main.current_state = gamestates.PLAYING
                self.selected_level = level
                return True
        return False
    



    def load_available_decks(self):
        """Load all available deck files"""
        self.available_decks = {}
        

        
        if os.path.exists("deck_saves"):
            for deck_file in os.listdir("deck_saves"):
                if deck_file.endswith(".deck") and not deck_file.startswith("ai"):
                    deck_name = deck_file[:-5] 
                    try:
                        with open(f"deck_saves/{deck_file}", "r") as f:
                            deck_data = json.load(f)
                            self.available_decks[deck_name] = deck_data
                    except (FileNotFoundError, json.JSONDecodeError):
                        continue



    def draw_deck_selection_button(self):
        """Draw the deck selection dropdown button"""
        mouse_pos = pygame.mouse.get_pos()
        
        button_hovered = (
            self.deck_selection_button_rect[0] <= mouse_pos[0] <= self.deck_selection_button_rect[0] + self.deck_selection_button_rect[2] and
            self.deck_selection_button_rect[1] <= mouse_pos[1] <= self.deck_selection_button_rect[1] + self.deck_selection_button_rect[3]
        )
        
        if button_hovered:
            button_color = (60, 60, 60)
            border_color = (0, 255, 0)
            text_color = (255, 255, 255)
        else:
            button_color = (40, 40, 40)
            border_color = (0, 180, 0)
            text_color = (200, 200, 200)
        
        render.draw_rect(self.ctx, self.deck_selection_button_rect, button_color, self.line_prog, True)
        
        border_thickness = 2
        render.draw_rect(self.ctx, (self.deck_selection_button_rect[0], self.deck_selection_button_rect[1], self.deck_selection_button_rect[2], border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.deck_selection_button_rect[0], self.deck_selection_button_rect[1] + self.deck_selection_button_rect[3] - border_thickness, self.deck_selection_button_rect[2], border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.deck_selection_button_rect[0], self.deck_selection_button_rect[1], border_thickness, self.deck_selection_button_rect[3]), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.deck_selection_button_rect[0] + self.deck_selection_button_rect[2] - border_thickness, self.deck_selection_button_rect[1], border_thickness, self.deck_selection_button_rect[3]), border_color, self.line_prog, True)
        
        text_x = self.deck_selection_button_rect[0] + 10
        text_y = self.deck_selection_button_rect[1] + 10
        display_text = f"Deck: {self.selected_deck_name}"
        if len(display_text) > 20:
            display_text = display_text[:17] + "..."
        render.draw_text(self.ctx, display_text, (text_x, text_y), text_color, font_size=14, font_path="font/Tektur-Black.ttf")
        
        arrow_x = self.deck_selection_button_rect[0] + self.deck_selection_button_rect[2] - 20
        arrow_y = self.deck_selection_button_rect[1] + self.deck_selection_button_rect[3] // 2 - 5
        render.draw_text(self.ctx, "V", (arrow_x, arrow_y), text_color, font_size=12, font_path="font/Tektur-Black.ttf")



    def draw_deck_selection_dropdown(self):
        """Draw the deck selection dropdown menu"""
        if not self.deck_selection_dropdown_open or not self.available_decks:
            return
        
        dropdown_height = min(len(self.available_decks) * 35, 200)
        dropdown_rect = (
            self.deck_selection_button_rect[0],
            self.deck_selection_button_rect[1] + self.deck_selection_button_rect[3] + 5,
            self.deck_selection_button_rect[2],
            dropdown_height
        )
        
        render.draw_rect(self.ctx, dropdown_rect, (20, 20, 40), self.line_prog, True)
        render.draw_rect(self.ctx, dropdown_rect, (0, 180, 0), self.line_prog, False)
        
        mouse_pos = pygame.mouse.get_pos()
        for i, deck_name in enumerate(self.available_decks.keys()):
            option_rect = (
                dropdown_rect[0],
                dropdown_rect[1] + i * 35,
                dropdown_rect[2],
                35
            )
            
            if (option_rect[0] <= mouse_pos[0] <= option_rect[0] + option_rect[2] and
                option_rect[1] <= mouse_pos[1] <= option_rect[1] + option_rect[3]):
                render.draw_rect(self.ctx, option_rect, (0, 100, 0), self.line_prog, True)
            
            text_color = (255, 255, 255) if deck_name == self.selected_deck_name else (200, 200, 200)
            render.draw_text(self.ctx, deck_name, (option_rect[0] + 10, option_rect[1] + 8), text_color, font_size=14, font_path="font/Tektur-Black.ttf")

    def is_deck_selection_button_clicked(self, mouse_pos):
        """Check if the deck selection button was clicked"""
        return (
            self.deck_selection_button_rect[0] <= mouse_pos[0] <= self.deck_selection_button_rect[0] + self.deck_selection_button_rect[2] and
            self.deck_selection_button_rect[1] <= mouse_pos[1] <= self.deck_selection_button_rect[1] + self.deck_selection_button_rect[3]
        )

    def get_clicked_deck_option(self, mouse_pos):
        """Get the deck name that was clicked in the dropdown"""
        if not self.deck_selection_dropdown_open or not self.available_decks:
            return None
        
        dropdown_height = min(len(self.available_decks) * 35, 200)
        dropdown_rect = (
            self.deck_selection_button_rect[0],
            self.deck_selection_button_rect[1] + self.deck_selection_button_rect[3] + 5,
            self.deck_selection_button_rect[2],
            dropdown_height
        )
        
        if (dropdown_rect[0] <= mouse_pos[0] <= dropdown_rect[0] + dropdown_rect[2] and
            dropdown_rect[1] <= mouse_pos[1] <= dropdown_rect[1] + dropdown_rect[3]):
            
            relative_y = mouse_pos[1] - dropdown_rect[1]
            option_index = relative_y // 35
            
            if 0 <= option_index < len(self.available_decks):
                return list(self.available_decks.keys())[option_index]
        
        return None

    def load_selected_deck(self):
        """Load the selected deck into the global cards_in_deck"""
        global cards_in_deck, owned_cards
        
        for card_id in cards_in_deck:
            cards_in_deck[card_id] = 0
        
        if self.selected_deck_name in self.available_decks:
            deck_data = self.available_decks[self.selected_deck_name]
            for card_id, amount in deck_data.items():
                if card_id in cards_in_deck:
                    cards_in_deck[card_id] = amount

    def save_selected_deck(self):
        """Save the currently selected deck to save data"""
        try:
            with open("save_data.json", "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        
        data["last_campaign_deck"] = self.selected_deck_name
        
        with open("save_data.json", "w") as f:
            json.dump(data, f)

    def handle_deck_selection_click(self, mouse_pos):
        """Handle clicks related to deck selection"""
        if self.is_deck_selection_button_clicked(mouse_pos):
            self.deck_selection_dropdown_open = not self.deck_selection_dropdown_open
            return True
        elif self.deck_selection_dropdown_open:
            clicked_deck = self.get_clicked_deck_option(mouse_pos)
            if clicked_deck:
                self.selected_deck_name = clicked_deck
                self.deck_selection_dropdown_open = False
                self.load_selected_deck()
                self.save_selected_deck()
                return True
            else:
                self.deck_selection_dropdown_open = False
                return False
        
        return False


    
    def draw(self, gamestates, main, events=None):
        if global_vals.winner != None:
            if global_vals.winner == "Player":
                self.selected_level.completed = True
            global_vals.winner = None

        if events:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_mouse_click(event.pos, gamestates, main)
        grid_color = (10, 30, 10)
        for i in range(0, self.WIDTH, 50):
            for j in range(0, self.HEIGHT, 50):
                if (i + j) % 100 == 0:
                    render.draw_rect(self.ctx, (i, j, 1, 1), grid_color, self.line_prog, True)

        for idx, shape in enumerate(self.continents):
            self.draw_continent_outline(shape, color = (0,255,0) if idx != 2 else (255, 255, 0))

        self.draw_levels()
        self.update_controls()
        if self.selected_level:
            self.draw_info_panel()
        else:
            self.draw_deck_selection_button()
            self.draw_deck_selection_dropdown()
            self.draw_save_load_buttons()

        self.draw_terminal_border()
        self.draw_back_button()
        render.draw_text(self.ctx, ">> CAMPAIGN MISSIONS <<", (50, 30), (0, 255, 0), font_size=40, font_path="font/Tektur-Black.ttf")




    def generate_continent(self, center=(0.0, 0.0), radius=1000, point_count=50, irregularity=0.3, seed=0):

        cx, cy = center
        points = []
        rng = random.Random(seed)
        for i in range(point_count):
            angle = (2 * math.pi / point_count) * i
            r = radius * (1 + rng.uniform(-irregularity, irregularity))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        return points


    def draw_continent_outline(self, points, color=(0, 255, 0), line_width=1.0):

        if len(points) < 2:
            return 

        for i in range(len(points)):
            start = (points[i][0] + self.x, points[i][1] + self.y)
            end = (points[(i + 1) % len(points)][0] + self.x, points[(i + 1) % len(points)][1] + self.y)
            render.draw_line(self.ctx, start, end, color, self.line_prog, line_width)








if __name__ == "__main__":
    pygame.init()
    WIDTH, HEIGHT = 1280, 720
    screen, ctx, line_prog = render.initialize_context(WIDTH, HEIGHT)
    campaign = Campaign_Menu(ctx, line_prog, WIDTH, HEIGHT)
    Clock = pygame.time.Clock()
    running = True
    while running:
        ctx.clear(0, 0, 0)
        Clock.tick(60)
        events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            events.append(event)
        campaign.draw(None, None, events)
        pygame.display.flip()
    pygame.quit()