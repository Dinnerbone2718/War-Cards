import pygame
import numpy as np
import map_func as mf
import render
import math
import entity as e
import re
from global_vals import bullet_entities, explosive_entities
from BetterAI import AI
from card import EntityCard, TankEntityCard
import tkinter as tk
from card_global import cards_in_deck, card_instances
import random
import copy
import json
import global_vals
import os
import time

class Button:
    def __init__(self, x, y, width, height, text, color=(0, 100, 200), hover_color=(0, 150, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.is_clicked = False
        
    def draw(self, ctx, line_prog):
        current_color = self.hover_color if self.is_hovered else self.color
        render.draw_rect(ctx, (self.rect.x, self.rect.y, self.rect.width, self.rect.height), 
                         current_color, line_prog, True)
        
        render.draw_rect(ctx, (self.rect.x, self.rect.y, self.rect.width, self.rect.height), 
                         (255, 255, 255), line_prog, False)
        
        render.draw_text(ctx, self.text, 
                        (self.rect.x, self.rect.y + self.rect.height // 2 - 10), 
                        (255, 255, 255), font_size=30)
        
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
        
    def check_click(self, mouse_pressed, mouse_released):
        if self.is_hovered and mouse_pressed and not mouse_released:
            self.is_clicked = True
        
        if self.is_clicked and mouse_released:
            self.is_clicked = False
            return True
        return False

class Game:
    def __init__(self, ctx, line_prog, width, height, board_size=50, seed=70, starting_money=0, money_multiplier=1, fog_of_war=False, num_cities=2, win_condition = None, biome = "grass", game_og = "sandbox", ai_deck = None, online = False, role = "client"):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefix = f"{script_dir}/"
        self.num_cities = max(1, min(3, num_cities))  # Clamp between 1-3

        self.board_size = board_size

        self.camera_position = [board_size*3/2, -10.0, 0.0]
        self.camera_rotation = [0.5, 0.0, 0.0]
        self.camera_speed = 0.1
        self.rotation_speed = 0.02
        self.camera_movement_mode = "fixed"
        self.key_release_counter = 0

        self.fog_of_war = fog_of_war
        
        self.seed = seed
        self.map_update_count = 0
        
        if biome != "beach" and biome != "ocean":
            self.ground_vertices, self.ground_edges = mf.get_ground(grid_size=board_size, scale=3, height_variation=board_size*.3, seed=self.seed)
        elif biome == "beach":
            self.ground_vertices, self.ground_edges = mf.get_shoreline(grid_size=board_size, scale=3, height_variation=board_size*.3, seed=self.seed)
            self.water_vertices, self.water_edges = mf.get_water_surface(grid_size=board_size, scale=3, height_variation=board_size*.3, seed=self.seed)
            self.water_edge_vertices = render.create_vertex_data(self.water_vertices, self.water_edges)
        elif biome == "ocean":
            pass

        

        self.walkable_ground_vertices = []
        self.walkable_water_vertices = []  



        self.tile_types = {}

        for vertex in self.ground_vertices:
            cord = (round(vertex[0]), round(vertex[2]))
            self.tile_types[cord] = "land"

        for x in range(0, board_size*3, 3):
            for y in range(0, board_size*3, 3):
                cord = (x, y)
                if cord not in self.tile_types.keys():
                    self.tile_types[cord] = "water"



        cloud_thickness = 10

        if board_size == 75:
            cloud_thickness = 3
        elif board_size == 100:
            cloud_thickness = 1

        cloud_vertices, cloud_edges = mf.get_clouds(grid_size=board_size, scale=3, height_variation=board_size*.3, seed=self.seed, cloud_layers=cloud_thickness)

        self.cloud_edge_vertices = render.create_vertex_data(cloud_vertices, cloud_edges)

        self.initialize_base(board_size*3)
        self.tick = 0

        all_bases = [self.player_base, self.enemy_base] + self.cities

        for base in all_bases:
            base.y = base._get_terrain_height(self.ground_vertices)
            base_x, base_z = base.x, base.z
            base_height = base.y

            for i in range(len(self.ground_vertices)):
                x, y, z = self.ground_vertices[i]
                if base_x - 5 <= x <= base_x + 5 and base_z - 5 <= z <= base_z + 5:
                    height_adjustment = base_height + (3 if base in self.cities else 0)
                    self.ground_vertices[i] = (x, height_adjustment, z)

        self.player_points = starting_money
        self.enemy_points = starting_money
        self.money_multiplier = money_multiplier

        self.city_captures = ["None"] * self.num_cities
        self.player_base_capture = "Player"
        self.enemy_base_capture = "Enemy"

        self.ground_edge_vertices = render.create_vertex_data(self.ground_vertices, self.ground_edges)
        
        self.bob = AI([self.player_base, self.enemy_base] + self.cities, self.ground_vertices)  # AI uses first city for now
        
        self.initialize_entities()
        
        self.target_button = Button(40, 600, 200, 50, "      Select Target")
        self.transport_button = Button(30, 600, 200, 50, "           Pickup")

        self.placement_mode = False
        self.entity_to_place = None
        self.placement_buttons = []
        self.target_selection_mode = False
        
        self.selected_entities = []
        self.selected_card = None
        self.mouse_pressed = False
        self.mouse_released = False
        self.mouse_press_started_on_entity = False
        
        self.marker = e.marker(0, 0, 0, True)

        self.box_selection_active = False
        self.box_selection_start = None
        self.box_selection_end = None

        highest_vertice = max(self.ground_vertices, key=lambda v: v[1])
        lowest_vertice = min(self.ground_vertices, key=lambda v: v[1])
        print(f"Highest vertice: {highest_vertice}")
        print(f"Lowest vertice: {lowest_vertice}")
    
        self.capture_timers = {self.player_base: 0, self.enemy_base: 0}
        for city in self.cities:
            self.capture_timers[city] = 0
        
        self.capture_threshold = 300  
        self.capture_range = 5 

        self.player_cards = []

        for x in cards_in_deck.keys():
            for y in range(cards_in_deck[x]):
                self.player_cards.append(copy.copy(card_instances[x]))

        self.player_cards.sort(key=lambda card: random.random())




        if ai_deck == None:
            with open(f"{self.prefix}deck_saves/ai.deck", 'r') as f:
                enemy_card_in_deck = json.load(f)

        else:
            enemy_card_in_deck = ai_deck

        self.enemy_cards = []

        for x in enemy_card_in_deck.keys():
            for _ in range(enemy_card_in_deck[x]):
                self.enemy_cards.append(copy.copy(card_instances[x]))

        self.enemy_cards.sort(key=lambda card: random.random())


        self.game_over = False
        button_width = 200
        button_height = 60
        button_x = self.WIDTH // 2 - button_width // 2
        button_y = self.HEIGHT // 2 + 150
        self.back_button = Button(button_x, button_y, button_width, button_height, 
                                "   Back to Menu", (100, 100, 100), (150, 150, 150))






        if online:
            self.online = True
            self.role = role
        else:
            self.online = False
            self.role = None



        self.quene_units = []








        self.win_condition = win_condition

        self.enemy_score = 0
        self.player_score = 0

        self.biome = biome

        self.special_entities = []

        self.water_map = False

        if self.biome == "desert":
            building_positions = []
            
            building_positions.append((self.player_base.x, self.player_base.z))
            
            building_positions.append((self.enemy_base.x, self.enemy_base.z))
            
            for city in self.cities:
                building_positions.append((city.x, city.z))
            
            min_distance_from_buildings = 15 
            min_distance_between_cacti = 8    
            grid_spacing = 12                 
            max_attempts = 1000             
            
            placed_cacti = []
            target_cactus_count = int(board_size / 5)
            
            grid_size = int((board_size * 3) / grid_spacing)
            
            potential_positions = []
            for i in range(grid_size):
                for j in range(grid_size):
                    base_x = i * grid_spacing + random.randint(-grid_spacing//3, grid_spacing//3)
                    base_z = j * grid_spacing + random.randint(-grid_spacing//3, grid_spacing//3)
                    
                    if 0 <= base_x <= board_size * 3 and 0 <= base_z <= board_size * 3:
                        potential_positions.append((base_x, base_z))
            
            random.shuffle(potential_positions)
            
            def is_valid_position(x, z):
                for bx, bz in building_positions:
                    distance = ((x - bx) ** 2 + (z - bz) ** 2) ** 0.5
                    if distance < min_distance_from_buildings:
                        return False
                
                for cx, cz in placed_cacti:
                    distance = ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5
                    if distance < min_distance_between_cacti:
                        return False
                
                return True
            
            for x, z in potential_positions:
                if len(placed_cacti) >= target_cactus_count:
                    break
                    
                if is_valid_position(x, z):
                    placed_cacti.append((x, z))
                    self.special_entities.append(e.cactus(x, z, 20, True))
            
            attempts = 0
            while len(placed_cacti) < target_cactus_count and attempts < max_attempts:
                x = random.randint(0, board_size * 3)
                z = random.randint(0, board_size * 3)
                
                if is_valid_position(x, z):
                    placed_cacti.append((x, z))
                    self.special_entities.append(e.cactus(x, z, 20, True))
                
                attempts += 1
            
            print(f"Placed {len(placed_cacti)} cacti out of {target_cactus_count} target")

            self.shader = self.ctx.program(
            vertex_shader='''
                    #version 330
                    in vec2 in_vert;
                    uniform float time;

                    void main() {
                        float wave_strength = 0.005;
                        float frequency = 15.0;
                        float speed = .05;

                        // Apply horizontal sine wave distortion based on vertical position
                        float x_offset = sin(in_vert.y * frequency + time/10 * speed) * wave_strength;

                        vec2 displaced_pos = vec2(in_vert.x + x_offset, in_vert.y);
                        gl_Position = vec4(displaced_pos, 0.0, 1.0);
                    }
                ''',
                fragment_shader='''
                    #version 330
                    uniform vec3 color;
                    out vec4 fragColor;

                    void main() {
                        fragColor = vec4(color, 1.0);
                    }
                '''
            )
        elif self.biome == "beach":
            self.water_map = True
            self.shader = self.ctx.program(
                vertex_shader='''
                    #version 330
                    in vec2 in_vert;
                    out float v_wave;
                    uniform float time;

                    void main() {
                        float wave_strength = 0.01;
                        float frequency = 2.0;
                        float speed = .01;

                        // Simulate water waves using sine and cosine
                        float y_wave = sin(in_vert.x * frequency + time * speed) * wave_strength;
                        float x_wave = cos(in_vert.y * frequency + time * speed * 0.8) * wave_strength * 0.7;

                        v_wave = y_wave; // Pass y_wave to fragment shader

                        vec2 displaced_pos = vec2(in_vert.x + x_wave, in_vert.y + y_wave);
                        gl_Position = vec4(displaced_pos, 0.0, 1.0);
                    }
                ''',
                fragment_shader='''
                    #version 330
                    in float v_wave;
                    uniform vec3 color;
                    uniform float time;
                    out vec4 fragColor;
                    void main() {
                        // Map v_wave from [-wave_strength, wave_strength] to [0, 1]
                        float wave_strength = 0.01;
                        float normalized_wave = (v_wave / wave_strength) * 0.5 + 0.5;
                        float brightness = 0.4 + 0.6 * normalized_wave;
                        vec3 animated_color = color * brightness;
                        fragColor = vec4(animated_color, 0.5);
                    }
                '''
            )
        else:
            self.shader = self.line_prog


        self.game_og = game_og

        
        self.lose_button = Button(10, 10, 100, 20, 
                                "   Leave", (0, 0, 0), (0, 100, 0))
        
        self.real_money_earned = 0

    def initialize_base(self, board_size=150):
        self.player_base = e.base(board_size//2, 7.5, True)
        self.enemy_base = e.base(board_size//2, board_size-10, False)
        
        self.cities = []
        
        if self.num_cities == 1:
            self.cities.append(e.city(board_size//2, board_size//2 - 5, True))
        elif self.num_cities == 2:
            offset = board_size // 6
            self.cities.append(e.city(board_size//2 - offset, board_size//2 - 5, True))
            self.cities.append(e.city(board_size//2 + offset, board_size//2 - 5, True))
        elif self.num_cities == 3:
            center_x, center_z = board_size//2, board_size//2 - 5
            offset = board_size // 4
            
            self.cities.append(e.city(center_x, center_z, True))
            self.cities.append(e.city(center_x - offset, center_z - offset, True))
            self.cities.append(e.city(center_x + offset, center_z + offset, True))

    def initialize_entities(self):
        #Just doing this for testing
        self.player_entities = []
        self.enemy_entities = [
            #e.smallTank(15, 90, False),
            #e.stealthPlane(25, 90, False, [(self.enemy_base.x, self.enemy_base.z), (self.player_base.x, self.player_base.z)]),
            #e.artillery(35, 90, False),
            #e.infantry(45, 90, False),
            #e.supplyTruck(55, 90, False),
            #e.smallPlane(65, 90, False),
            #e.sniper(75, 90, False),
            #e.antiAir(85, 90, False),
            #e.tHelicopter(95, 90, False),
            #e.attHelicopter(105, 90, False)
        ]
    
    def update_dimensions(self, width, height):
        self.WIDTH = width
        self.HEIGHT = height

    def handle_input(self):
        keys = pygame.key.get_pressed()

        self.camera_speed = .5
        if keys[pygame.K_e]:
            self.camera_speed = 3

        forward = np.array([
            math.sin(self.camera_rotation[1]) * math.cos(self.camera_rotation[0]),
            -math.sin(self.camera_rotation[0]),
            -math.cos(self.camera_rotation[1]) * math.cos(self.camera_rotation[0])
        ])

        up = np.array([0, 1, 0])

        right = np.array([
            math.cos(self.camera_rotation[1]),
            0,
            math.sin(self.camera_rotation[1])
        ])

        if keys[pygame.K_w]:  
            self.camera_position -= forward * self.camera_speed
        if keys[pygame.K_s]:  
            self.camera_position += forward * self.camera_speed
        if keys[pygame.K_a]: 
            self.camera_position -= right * self.camera_speed
        if keys[pygame.K_d]:
            self.camera_position += right * self.camera_speed
        if keys[pygame.K_LSHIFT]:  
            self.camera_position += up * self.camera_speed
        if keys[pygame.K_SPACE]: 
            self.camera_position -= up * self.camera_speed

        self.key_release_counter += 1

        if keys[pygame.K_q]:
            if self.key_release_counter > 10:
                self.camera_movement_mode = "free" if self.camera_movement_mode == "fixed" else "fixed"
                self.key_release_counter = 0
                pygame.mouse.set_pos((self.WIDTH//2, self.HEIGHT//2))

        if self.camera_movement_mode == "free":


            pygame.mouse.set_visible(False)

            mouse_pos = pygame.mouse.get_pos()

            self.camera_rotation[1] -= (mouse_pos[0] - self.WIDTH//2) / self.WIDTH * .5 * math.pi
            self.camera_rotation[0] += (mouse_pos[1] - self.HEIGHT//2) / self.HEIGHT * .5 * math.pi

            if self.tick % 4 == 0:
                pygame.mouse.set_pos((self.WIDTH//2, self.HEIGHT//2))

        else:
            pygame.mouse.set_visible(True)

            if keys[pygame.K_LEFT]:
                self.camera_rotation[1] += self.rotation_speed
            if keys[pygame.K_RIGHT]:
                self.camera_rotation[1] -= self.rotation_speed
            if keys[pygame.K_UP]:
                self.camera_rotation[0] -= self.rotation_speed
            if keys[pygame.K_DOWN]:
                self.camera_rotation[0] += self.rotation_speed



        self.camera_rotation[0] = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.camera_rotation[0]))

        if keys[pygame.K_ESCAPE]:
            self.selected_entities = []
            self.placement_mode = False
            self.entity_to_place = None
            self.target_selection_mode = False

    def apply_camera_transform(self, vertices):
        if len(vertices) == 0:
            return np.array([])

        verts = np.asarray(vertices, dtype=np.float32)

        verts = verts - np.array(self.camera_position)

        pitch, yaw, roll = self.camera_rotation[0], self.camera_rotation[1], self.camera_rotation[2]
        
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        cos_r, sin_r = math.cos(roll), math.sin(roll)

        x_temp = verts[:, 0] * cos_y + verts[:, 2] * sin_y
        z_temp = -verts[:, 0] * sin_y + verts[:, 2] * cos_y
        verts[:, 0] = x_temp
        verts[:, 2] = z_temp

        y_temp = verts[:, 1] * cos_p - verts[:, 2] * sin_p
        z_temp = verts[:, 1] * sin_p + verts[:, 2] * cos_p
        verts[:, 1] = y_temp
        verts[:, 2] = z_temp

        if roll != 0:
            x_temp = verts[:, 0] * cos_r - verts[:, 1] * sin_r
            y_temp = verts[:, 0] * sin_r + verts[:, 1] * cos_r
            verts[:, 0] = x_temp
            verts[:, 1] = y_temp

        return verts
    
    def handle_mouse_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        keys = pygame.key.get_pressed()
        ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        if self.selected_entities and not self.target_selection_mode:
            self.target_button.check_hover(mouse_pos)
            if self.target_button.check_click(self.mouse_pressed, self.mouse_released) and len(self.selected_entities) == 1 and self.selected_entities[0].can_set_target:
                self.target_selection_mode = True
                return
            
            self.transport_button.check_hover(mouse_pos)
            if self.transport_button.check_click(self.mouse_pressed, self.mouse_released) and len(self.selected_entities) == 1 and self.selected_entities[0].unit_type == "transport" and self.selected_entities[0].in_air == False:
                self.selected_entities[0].target = None
                print(self.transport_button.text)
                if self.transport_button.text == "           Deploy":
                    print("Deploy")
                    self.selected_entities[0].deploy(self.player_entities, self.enemy_entities, self.ground_vertices)
                else:
                    print("Pickup")
                    self.selected_entities[0].pickup(self.player_entities, self.enemy_entities)
                    
                return

        if mouse_buttons[0]:  
            if self.target_selection_mode:
                if not self.mouse_pressed: 
                    hovered_vertex = render.get_hovered_vertex(
                        self.ctx, self.ground_vertices, mouse_pos, 500, self.apply_camera_transform
                    )
                    if hovered_vertex and len(self.selected_entities) == 1:
                        if self.selected_entities[0].check_move_validity(hovered_vertex['position'][0], hovered_vertex['position'][2], self.tile_types):
                            self.selected_entities[0].target = (hovered_vertex['position'][0], hovered_vertex['position'][2])

                            if self.selected_entities[0].state != "attacking":
                                self.selected_entities[0].state = "moving"
                            self.target_selection_mode = False 
                    
                    if not hovered_vertex and self.water_map:
                        hovered_vertex = render.get_hovered_vertex(
                            self.ctx, self.water_vertices, mouse_pos, 500, self.apply_camera_transform
                        )
                        if hovered_vertex and len(self.selected_entities) == 1:
                            if self.selected_entities[0].check_move_validity(hovered_vertex['position'][0], hovered_vertex['position'][2], self.tile_types):
                                self.selected_entities[0].target = (hovered_vertex['position'][0], hovered_vertex['position'][2])

                                if self.selected_entities[0].state != "attacking":
                                    self.selected_entities[0].state = "moving"
                                self.target_selection_mode = False 

            elif not self.placement_mode and not (len(self.selected_entities) == 1 and self.selected_entities[0].can_set_target):
                if not self.mouse_pressed:
                    self.mouse_press_started_on_entity = False

                    for entity in self.player_entities:
                        if entity.hover:
                            self.mouse_press_started_on_entity = True

                            if not ctrl_pressed:
                                if entity in self.selected_entities and len(self.selected_entities) == 1:
                                    self.selected_entities = [] 
                                else:
                                    self.selected_entities = [entity] if not entity.util else []
                            else:
                                if entity in self.selected_entities:
                                    self.selected_entities.remove(entity) 
                                elif not entity.util:
                                    self.selected_entities.append(entity)
                            break
                    
                    if not self.mouse_press_started_on_entity and len(self.selected_entities) == 0 and mouse_pos[1] < self.HEIGHT*.8:
                        self.box_selection_active = True
                        self.box_selection_start = mouse_pos
                        self.box_selection_end = mouse_pos

            if self.box_selection_active:
                self.box_selection_end = mouse_pos

            self.mouse_pressed = True
            self.mouse_released = False

        else:  
            if self.mouse_pressed:
                self.mouse_released = True
                self.mouse_pressed = False

                if self.box_selection_active:
                    if self.box_selection_start and self.box_selection_end:
                        self.get_stuff_from_box_selection(self.box_selection_start, self.box_selection_end)
                    self.box_selection_active = False
                    self.box_selection_start = None
                    self.box_selection_end = None

                if not self.placement_mode and not self.target_selection_mode and not self.mouse_press_started_on_entity:
                    if self.selected_entities:
                        if all(entity.grass_capeable for entity in self.selected_entities):
                            hovered_vertex = render.get_hovered_vertex(
                                self.ctx, self.ground_vertices, mouse_pos, 500, self.apply_camera_transform
                            )
                            if hovered_vertex:
                                pos = hovered_vertex['position']
                                for selected_entity in self.selected_entities:
                                    if selected_entity.check_move_validity(pos[0], pos[2], self.tile_types):
                                        selected_entity.target = (pos[0], pos[2])
                                        if selected_entity.state != "attacking":
                                            selected_entity.state = "moving"
                        elif all(entity.water_capeable for entity in self.selected_entities):
                            hovered_vertex = render.get_hovered_vertex(
                                self.ctx, self.water_vertices, mouse_pos, 500, self.apply_camera_transform
                            )
                            if hovered_vertex:
                                pos = hovered_vertex['position']
                                for selected_entity in self.selected_entities:
                                    if selected_entity.check_move_validity(pos[0], pos[2], self.tile_types):
                                        selected_entity.target = (pos[0], pos[2])
                                        if selected_entity.state != "attacking":
                                            selected_entity.state = "moving"
    def draw_box_selection(self):
        if self.box_selection_active and self.box_selection_start and self.box_selection_end:
            start_x, start_y = self.box_selection_start
            end_x, end_y = self.box_selection_end
            
            min_x = min(start_x, end_x)
            max_x = max(start_x, end_x)
            min_y = min(start_y, end_y)
            max_y = max(start_y, end_y)
            
            width = max_x - min_x
            height = max_y - min_y
            
            render.draw_rect(self.ctx, (min_x, min_y, width, height), (0, 255, 0), self.line_prog, False)

    def handle_menu(self):
        if self.target_selection_mode:
            render.draw_text(self.ctx, "Select Target", (self.WIDTH // 2 - 100, 50), (255, 255, 255), font_size=50)
            return
            
        render.draw_rect(self.ctx, (0, 0, self.WIDTH/5, self.HEIGHT - 2), (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, (1, 1, self.WIDTH/5, self.HEIGHT - 2), (0, 0, 255), self.line_prog, False)

        if len(self.selected_entities) == 1:
            entity = self.selected_entities[0]
            render.draw_text(self.ctx, f"{re.sub(r'(?<!^)(?=[A-Z])', ' ', entity.__class__.__name__).capitalize()}", (30, 50), (255, 255, 255), font_size=50)
            render.draw_text(self.ctx, f"{re.sub(r'(?<!^)(?=[A-Z])', ' ', entity.state).capitalize()}", (30, 200), (255, 255, 255), font_size=50)

            if entity.unit_type == "attack" or entity.unit_type == "artillery":
                render.draw_text(self.ctx, f"Ammo: {entity.supply}", (40, 350), (255, 255, 255), font_size=50)
                render.draw_text(self.ctx, f"Health: {entity.health}", (40, 500), (255, 255, 255), font_size=50)
            else:
                render.draw_text(self.ctx, f"Health: {entity.health}", (40, 350), (255, 255, 255), font_size=50)
        
        elif len(self.selected_entities) > 1:
            render.draw_text(self.ctx, f"Group Selected", (30, 50), (255, 255, 255), font_size=50)
            render.draw_text(self.ctx, f"Units: {len(self.selected_entities)}", (30, 130), (255, 255, 255), font_size=40)
            
            unit_counts = {}
            for entity in self.selected_entities:
                class_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', entity.__class__.__name__).capitalize()
                if class_name in unit_counts:
                    unit_counts[class_name] += 1
                else:
                    unit_counts[class_name] = 1
            
            y_offset = 200
            for unit_type, count in unit_counts.items():
                render.draw_text(self.ctx, f"{unit_type}: {count}", (40, y_offset), (255, 255, 255), font_size=30)
                y_offset += 50
        
        if len(self.selected_entities) == 1 and self.selected_entities[0].can_set_target and self.selected_entities[0].target == None:
            self.target_button.draw(self.ctx, self.line_prog)
        if len(self.selected_entities) == 1 and self.selected_entities[0].unit_type == "transport":
            self.transport_button.draw(self.ctx, self.line_prog)
            if len(self.selected_entities[0].units_carried) == 0:
                self.transport_button.text = "           Pickup"
            else:
                self.transport_button.text = "           Deploy"



    def heal_entities_near_bases(self):
        healing_range = 8
        healing_rate = 1
        
        healing_locations = []
        
        if self.player_base_capture == "Player":
            healing_locations.append(self.player_base)
        
        if self.enemy_base_capture == "Enemy":
            healing_locations.append(self.enemy_base)
        
        for i, city in enumerate(self.cities):
            if self.city_captures[i] in ["Player", "Enemy"]:
                healing_locations.append((city, self.city_captures[i]))
        
        for entity in self.player_entities:
            if entity.health < entity.max_health*.75:  
                for location in healing_locations:
                    if isinstance(location, tuple):
                        base, control = location
                        if control != "Player":
                            continue
                    else:
                        base = location
                        if base == self.enemy_base:
                            continue
                    
                    distance = math.sqrt((entity.x - base.x)**2 + (entity.z - base.z)**2)
                    if distance <= healing_range:
                        entity.health = min(entity.max_health, entity.health + healing_rate)
                        break  
        
        for entity in self.enemy_entities:
            if entity.health < entity.max_health*.75:
                for location in healing_locations:
                    if isinstance(location, tuple):
                        base, control = location
                        if control != "Enemy":
                            continue
                    else:
                        base = location
                        if base == self.player_base:
                            continue
                    
                    distance = math.sqrt((entity.x - base.x)**2 + (entity.z - base.z)**2)
                    if distance <= healing_range:
                        entity.health = min(entity.max_health, entity.health + healing_rate)
                        break  



    def update_entities(self):
        if self.tick % 60 == 0:
            self.heal_entities_near_bases()

            self.visible_enemy_entities = []
            self.visible_player_entities = []

            for player_entity in self.player_entities:
                seen_enemies = player_entity.has_line_of_sight(self.enemy_entities)
                for enemy in seen_enemies:
                    if enemy not in self.visible_enemy_entities:
                        self.visible_enemy_entities.append(enemy)
                
                

            for enemy_entity in self.enemy_entities:
                seen_players = enemy_entity.has_line_of_sight(self.player_entities)
                for player in seen_players:
                    if player not in self.visible_player_entities:
                        self.visible_player_entities.append(player)

        for entity in self.player_entities:
            if entity in self.selected_entities:
                entity.color = (0, 255, 255)  
            elif entity in self.visible_player_entities:
                entity.color = (255, 128, 0) 
            else:
                entity.color = (0, 0, 255)  
            
            entity.move(self.visible_enemy_entities, self.player_entities + self.enemy_entities)

        for entity in self.enemy_entities:
            if self.fog_of_war:
                if entity in self.visible_enemy_entities:
                    entity.color = (255, 0, 0)  
                else:
                    entity.color = (0, 255, 0)  
            else:
                entity.color = (255, 0, 0)

            entity.move(self.visible_player_entities, self.player_entities + self.enemy_entities)
        
        for entity in bullet_entities:
            entity.move(self.player_entities + self.enemy_entities)

        for entity in explosive_entities:
            entity.move()


        if self.win_condition == "KILLS":
            self.player_score += sum([e.danger for e in self.enemy_entities if e.health <= 0]) * 5
            self.enemy_score += sum([e.danger for e in self.player_entities if e.health <= 0]) * 5



        self.player_entities = [e for e in self.player_entities if e.health > 0]
        self.enemy_entities = [e for e in self.enemy_entities if e.health > 0]
        
        self.selected_entities = [e for e in self.selected_entities if e in self.player_entities]




    def render_terrain(self):
        transformed_ground = self.apply_camera_transform(self.ground_edge_vertices)
        if self.biome == "grass":
            render.render(self.ctx, transformed_ground, (0, 255, 0), 500, self.line_prog)
        elif self.biome == "desert":
            self.shader['time'].value = self.tick
            render.render(self.ctx, transformed_ground, (255, 190, 0), 500, self.shader)
        elif self.biome == "beach":
            self.shader['time'].value = self.tick
            transformed_water = self.apply_camera_transform(self.water_edge_vertices)
            render.render(self.ctx, transformed_ground, (0, 255, 0), 500, self.line_prog)            
            render.render(self.ctx, transformed_water, (0, 0, 255), 500, self.shader)
        
    def render_entities(self):
        if self.placement_mode and self.entity_to_place:
            hovered_vertex = render.get_hovered_vertex(self.ctx, self.ground_vertices, 
                                                    pygame.mouse.get_pos(), 
                                                    500, self.apply_camera_transform)
            if hovered_vertex:
                pos = hovered_vertex['position']
                self.marker.x = pos[0]
                self.marker.z = pos[2]
                self.marker.color = (0, 255, 255)
                self.marker.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)
        

        if self.placement_mode and self.selected_card and self.selected_card[0].entity.grass_capeable:
            hovered_vertex = render.get_hovered_vertex(self.ctx, self.ground_vertices, 
                                                    pygame.mouse.get_pos(), 
                                                    500, self.apply_camera_transform)
            if hovered_vertex:
                pos = hovered_vertex['position']
                self.marker.x = pos[0]
                self.marker.z = pos[2]
                
                x, z = pos[0], pos[2]
                is_valid_placement = False
                
                all_bases = [self.player_base, self.enemy_base] + self.cities
                for base in all_bases:
                    distance = math.sqrt((base.x - x)**2 + (base.z - z)**2)
                    if distance < 10:
                        if base.color == (0, 0, 255): 
                            is_contested = self.is_base_contested(base)
                            if not is_contested:
                                is_valid_placement = True
                            break
                
                if is_valid_placement:
                    self.marker.color = (0, 255, 0)
                else:
                    self.marker.color = (255, 0, 0) 
                    
                self.marker.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)

        elif self.placement_mode and self.selected_card and self.selected_card[0].entity.water_capeable and self.water_map:
            hovered_vertex = render.get_hovered_vertex(self.ctx, self.water_vertices, 
                                                    pygame.mouse.get_pos(), 
                                                    500, self.apply_camera_transform)
            if hovered_vertex:
                pos = hovered_vertex['position']
                self.marker.x = pos[0]
                self.marker.z = pos[2]

                x, z = pos[0], pos[2]
                is_valid_placement = False

                all_bases = [self.player_base] + [city for i, city in enumerate(self.cities) if self.city_captures[i] == "Player"]
                if self.player_base_capture == "Player":
                    all_bases = [self.player_base] + [city for i, city in enumerate(self.cities) if self.city_captures[i] == "Player"]
                else:
                    all_bases = [city for i, city in enumerate(self.cities) if self.city_captures[i] == "Player"]

                if all_bases:
                    furthest_base = max(all_bases, key=lambda b: b.z)
                    if z <= furthest_base.z + 5:
                        is_valid_placement = True

                if is_valid_placement:
                    self.marker.color = (0, 255, 0) 
                else:
                    self.marker.color = (255, 0, 0) 

                self.marker.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)

        if self.target_selection_mode:
            hovered_vertex = render.get_hovered_vertex(self.ctx, self.ground_vertices, 
                                                    pygame.mouse.get_pos(), 
                                                    500, self.apply_camera_transform)
            if hovered_vertex:
                pos = hovered_vertex['position']
                self.marker.x = pos[0]
                self.marker.z = pos[2]
                self.marker.color = (255, 0, 0)
                self.marker.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)

            if self.water_map and not hovered_vertex:
                hovered_vertex = render.get_hovered_vertex(self.ctx, self.water_vertices, 
                                                        pygame.mouse.get_pos(), 
                                                        500, self.apply_camera_transform)
                if hovered_vertex:
                    pos = hovered_vertex['position']
                    self.marker.x = pos[0]
                    self.marker.z = pos[2]
                    self.marker.color = (255, 0, 0)
                    self.marker.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)
                    

        for entity in self.player_entities:
            if entity.util == False: 
                entity.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)
            
            if entity in self.selected_entities:
                if len(self.selected_entities) == 1 and not self.target_selection_mode:
                    self.marker.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)
                    if entity.target:
                        self.marker.x = entity.target[0]
                        self.marker.z = entity.target[1]

        if self.fog_of_war == False:
            for entity in self.enemy_entities:
                entity.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)
        else:
            for entity in self.enemy_entities:
                if entity.color == (255, 0, 0):
                    entity.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)

        for entity in bullet_entities:
            entity.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)

        for entity in explosive_entities:
            entity.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)


        if self.biome == "desert":
            self.player_base.draw(self.ctx, self.shader, self.ground_vertices, self.apply_camera_transform, 500)
            self.enemy_base.draw(self.ctx, self.shader, self.ground_vertices, self.apply_camera_transform, 500)
            
            for city in self.cities:
                city.draw(self.ctx, self.shader, self.ground_vertices, self.apply_camera_transform, 500)

        else:
            self.player_base.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)
            self.enemy_base.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)
            
            for city in self.cities:
                city.draw(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500)


        self.draw_base_capture_indicators()

        for i, city in enumerate(self.cities):
            if self.city_captures[i] == "None":
                city.color = (255, 255, 0)
            elif self.city_captures[i] == "Player":
                city.color = (0, 0, 255)
            elif self.city_captures[i] == "Enemy":
                city.color = (255, 0, 0)

        if self.player_base_capture == "None":
            self.player_base.color = (255, 255, 0)
        elif self.player_base_capture == "Player":
            self.player_base.color = (0, 0, 255)
        elif self.player_base_capture == "Enemy":
            self.player_base.color = (255, 0, 0)
        
        if self.enemy_base_capture == "None":
            self.enemy_base.color = (255, 255, 0)
        elif self.enemy_base_capture == "Player":
            self.enemy_base.color = (0, 0, 255)
        elif self.enemy_base_capture == "Enemy":
            self.enemy_base.color = (255, 0, 0)

    def draw_base_capture_indicators(self):
        bases_info = [
            (self.player_base, self.player_base_capture),
            (self.enemy_base, self.enemy_base_capture)
        ]
        
        for i, city in enumerate(self.cities):
            bases_info.append((city, self.city_captures[i]))
        
        for base, capture_status in bases_info:
            nearby_player_units = 0
            nearby_enemy_units = 0
            
            for entity in self.player_entities:
                if not entity.util:
                    distance = math.sqrt((entity.x - base.x)**2 + (entity.z - base.z)**2)
                    if distance <= self.capture_range:
                        nearby_player_units += 1
            
            for entity in self.enemy_entities:
                if not entity.util:
                    distance = math.sqrt((entity.x - base.x)**2 + (entity.z - base.z)**2)
                    if distance <= self.capture_range:
                        nearby_enemy_units += 1
            
            if nearby_player_units > 0 and nearby_enemy_units > 0:
                self.draw_floating_indicator(base, "Player", 2) 
                self.draw_floating_indicator(base, "Enemy", 2, opposite=True) 
            elif nearby_player_units > nearby_enemy_units and nearby_player_units > 0:
                self.draw_floating_indicator(base, "Player", 2)
                self.draw_floating_indicator(base, "Player", 0, opposite=True)
            elif nearby_enemy_units > nearby_player_units and nearby_enemy_units > 0:
                self.draw_floating_indicator(base, "Enemy", 2)
                self.draw_floating_indicator(base, "Enemy", 0, opposite=True)


    def draw_floating_indicator(self, base, capture_status, height_offset=0, opposite=False):
        if capture_status == "None":
            color = (255, 255, 0)  
        elif capture_status == "Player":
            color = (0, 0, 255) 
        elif capture_status == "Enemy":
            color = (255, 0, 0)   
        else:
            return  
        
        circle_center = [base.x, base.y + height_offset + np.sin(self.tick/20) * 5, base.z]
        if opposite:
            circle_center[1] *= -1
        circle_vertices = []
        circle_edges = []
        
        num_points = 12
        radius = 8
        
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            x = circle_center[0] + radius * math.cos(angle)
            z = circle_center[2] + radius * math.sin(angle)
            circle_vertices.append([x, circle_center[1], z])
            next_i = (i + 1) % num_points
            circle_edges.append([i, next_i])
        
        if circle_vertices:
            circle_edge_vertices = render.create_vertex_data(circle_vertices, circle_edges)
            transformed_circle = self.apply_camera_transform(circle_edge_vertices)
            render.render(self.ctx, transformed_circle, color, 500, self.line_prog)


    def update_game_state(self):
        self.tick += 1 
        if self.tick % 100 == 0:
            for city_capture in self.city_captures:
                if city_capture == "Player":
                    self.player_points += .25 * self.money_multiplier
                elif city_capture == "Enemy":
                    self.enemy_points += .25 * self.money_multiplier 

            if self.player_base_capture == "Player":
                self.player_points += 1 * self.money_multiplier
            elif self.player_base_capture == "Enemy":
                self.enemy_points += 1 * self.money_multiplier
            
            if self.enemy_base_capture == "Player":
                self.player_points += 1 * self.money_multiplier
            elif self.enemy_base_capture == "Enemy":
                self.enemy_points += 1 * self.money_multiplier
        
        self.player_points = min(100, self.player_points)
        self.enemy_points = min(100, self.enemy_points)

    def draw_ui(self):
        if self.win_condition == "CAPTURE":
            self.draw_capture_progress_bar()
        elif self.win_condition == "KILLS":
            self.draw_point_advantage_bar()
        
        money_bar_max_width = int(0.21875 * self.WIDTH)
        money_bar_x = self.WIDTH - money_bar_max_width - 20  
        money_bar_y = int(0.01 * self.HEIGHT)

        render.draw_rect(self.ctx, 
                        (money_bar_x, money_bar_y, int((self.player_points / 100) * money_bar_max_width), 0.07 * self.HEIGHT), 
                        (0, 255, 0), 
                        self.line_prog, 
                        True)
        
        render.draw_rect(self.ctx, 
                        (money_bar_x, money_bar_y, money_bar_max_width, 0.07 * self.HEIGHT), 
                        (0, 255, 0), 
                        self.line_prog, 
                        False)

        render.draw_text(self.ctx, 
                        "$" + str(int(self.player_points)), 
                        (money_bar_x, money_bar_y + int(0.07 * self.HEIGHT) + 10), 
                        (0, 255, 0), 
                        font_size=30)

        if len(self.selected_entities) == 0:
            render.draw_rect(self.ctx, (0, self.HEIGHT*.8, self.WIDTH, self.HEIGHT*.21), (0, 0, 0), self.line_prog, True)
            render.draw_rect(self.ctx, (0, self.HEIGHT*.8, self.WIDTH, self.HEIGHT*.21), (0, 255, 0), self.line_prog, False)
            mouse_pos = pygame.mouse.get_pos()
            cards_to_display = self.player_cards[:5]
            card_info = []

            total_card_width = len(cards_to_display) * 180
            start_x = (self.WIDTH - total_card_width) // 2

            for i, card in enumerate(cards_to_display):
                x_position = start_x + i * 180
                is_hovered = card.is_point_inside(mouse_pos[0], mouse_pos[1], x_position, int(0.83 * self.HEIGHT))
                card_info.append((card, i, is_hovered, x_position))

                if is_hovered:
                    if pygame.mouse.get_pressed()[0] and self.mouse_released:
                        if self.selected_card == (card, i):
                            self.selected_card = None
                            self.placement_mode = False
                        else:
                            self.selected_card = (card, i)
                            self.placement_mode = True

            card_info.sort(key=lambda x: x[2])

            for card, original_index, is_hovered, x_position in card_info:
                if self.selected_card == (card, original_index):
                    y_position = int(0.42 * self.HEIGHT)
                elif is_hovered:
                    y_position = int(0.56 * self.HEIGHT)
                else:
                    y_position = int(0.83 * self.HEIGHT)

                card.draw(self.ctx, self.line_prog, x_position, y_position)

        self.lose_button.draw(self.ctx, self.line_prog)

        self.lose_button.check_hover(mouse_pos = pygame.mouse.get_pos())

        if self.lose_button.check_click(self.mouse_pressed, self.mouse_released):
            self.game_over = "Enemy"

    def draw_capture_progress_bar(self):

        player_captures = 0
        enemy_captures = 0
        neutral_captures = 0
        
        if self.player_base_capture == "Player":
            player_captures += 1
        elif self.player_base_capture == "Enemy":
            enemy_captures += 1
        else:
            neutral_captures += 1
        
        if self.enemy_base_capture == "Player":
            player_captures += 1
        elif self.enemy_base_capture == "Enemy":
            enemy_captures += 1
        else:
            neutral_captures += 1
        
        for city_capture in self.city_captures:
            if city_capture == "Player":
                player_captures += 1
            elif city_capture == "Enemy":
                enemy_captures += 1
            else:
                neutral_captures += 1
        
        total_bases = 2 + len(self.cities)  
        
        bar_width = int(0.4 * self.WIDTH) 
        bar_height = 30
        bar_x = (self.WIDTH - bar_width) // 2 
        bar_y = 20  
        
        player_width = int((player_captures / total_bases) * bar_width)
        enemy_width = int((enemy_captures / total_bases) * bar_width)
        neutral_width = bar_width - player_width - enemy_width
        
        if player_width > 0:
            render.draw_rect(self.ctx, (bar_x, bar_y, player_width, bar_height), 
                            (0, 0, 255), self.line_prog, True)
        
        if enemy_width > 0:
            render.draw_rect(self.ctx, (bar_x + player_width, bar_y, enemy_width, bar_height), 
                            (255, 0, 0), self.line_prog, True)
        
        if neutral_width > 0:
            render.draw_rect(self.ctx, (bar_x + player_width + enemy_width, bar_y, neutral_width, bar_height), 
                            (255, 255, 0), self.line_prog, True)
        
        render.draw_rect(self.ctx, (bar_x, bar_y, bar_width, bar_height), 
                        (0, 255, 0), self.line_prog, False)
        
    def draw_point_advantage_bar(self):
        point_difference = int(self.player_score - self.enemy_score)
        clamped_difference = max(-100, min(100, point_difference))
        bar_width = int(0.4 * self.WIDTH)
        bar_height = 30
        bar_x = (self.WIDTH - bar_width) // 2
        bar_y = 60
        center_x = bar_x + bar_width // 2
        if clamped_difference >= 0:
            player_advantage_width = int((clamped_difference / 100) * (bar_width // 2))
            enemy_advantage_width = 0
        else:
            player_advantage_width = 0
            enemy_advantage_width = int((abs(clamped_difference) / 100) * (bar_width // 2))
        if enemy_advantage_width > 0:
            render.draw_rect(self.ctx, (center_x - enemy_advantage_width, bar_y, enemy_advantage_width, bar_height),
                            (255, 0, 0), self.line_prog, True)
        if player_advantage_width > 0:
            render.draw_rect(self.ctx, (center_x, bar_y, player_advantage_width, bar_height),
                            (0, 0, 255), self.line_prog, True)
        render.draw_rect(self.ctx, (bar_x, bar_y, bar_width, bar_height),
                        (0, 255, 0), self.line_prog, False)
        render.draw_rect(self.ctx, (center_x - 1, bar_y, 2, bar_height),
                        (255, 255, 255), self.line_prog, True)
        difference_text = f"Point Advantage: {point_difference:+d}"
        text_x = bar_x + (bar_width // 2) - 80
        text_y = bar_y + bar_height + 10
        text_color = (0, 0, 255) if point_difference >= 0 else (255, 0, 0)
        render.draw_text(self.ctx, difference_text, (text_x, text_y), text_color, font_size=25)

    def update_base_captures(self):
        bases = [
            (self.player_base, 'player_base_capture'),
            (self.enemy_base, 'enemy_base_capture')
        ]

        for base, capture_attr in bases:
            nearby_player_units = 0
            nearby_enemy_units = 0
            
            for entity in self.player_entities:
                if not entity.util:  
                    distance = math.sqrt((entity.x - base.x)**2 + (entity.z - base.z)**2)
                    if distance <= self.capture_range:
                        nearby_player_units += 1
            
            for entity in self.enemy_entities:
                if not entity.util:
                    distance = math.sqrt((entity.x - base.x)**2 + (entity.z - base.z)**2)
                    if distance <= self.capture_range:
                        nearby_enemy_units += 1
            
            current_capture = getattr(self, capture_attr)
            
            if nearby_player_units > nearby_enemy_units and nearby_player_units > 0:
                if current_capture != "Player":
                    self.capture_timers[base] += 1
                    if self.capture_timers[base] >= self.capture_threshold:
                        setattr(self, capture_attr, "Player")
                        self.capture_timers[base] = 0
            elif nearby_enemy_units > nearby_player_units and nearby_enemy_units > 0:
                if current_capture != "Enemy":
                    self.capture_timers[base] += 1
                    if self.capture_timers[base] >= self.capture_threshold:
                        setattr(self, capture_attr, "Enemy")
                        self.capture_timers[base] = 0
            else:
                self.capture_timers[base] = 0

        for i, city in enumerate(self.cities):
            nearby_player_units = 0
            nearby_enemy_units = 0
            
            for entity in self.player_entities:
                if not entity.util:  
                    distance = math.sqrt((entity.x - city.x)**2 + (entity.z - city.z)**2)
                    if distance <= self.capture_range:
                        nearby_player_units += 1
            
            for entity in self.enemy_entities:
                if not entity.util:
                    distance = math.sqrt((entity.x - city.x)**2 + (entity.z - city.z)**2)
                    if distance <= self.capture_range:
                        nearby_enemy_units += 1
            
            current_capture = self.city_captures[i]
            
            if nearby_player_units > nearby_enemy_units and nearby_player_units > 0:
                if current_capture != "Player":
                    self.capture_timers[city] += 1
                    if self.capture_timers[city] >= self.capture_threshold:
                        self.city_captures[i] = "Player"
                        self.capture_timers[city] = 0
            elif nearby_enemy_units > nearby_player_units and nearby_enemy_units > 0:
                if current_capture != "Enemy":
                    self.capture_timers[city] += 1
                    if self.capture_timers[city] >= self.capture_threshold:
                        self.city_captures[i] = "Enemy"
                        self.capture_timers[city] = 0
            else:
                self.capture_timers[city] = 0




    def check_placement(self):
        if not self.selected_card or not self.placement_mode:
            return
        
        card, index = self.selected_card
        mouse_pos = pygame.mouse.get_pos()

        if pygame.mouse.get_pressed()[0] and self.mouse_released and mouse_pos[1] < self.HEIGHT*.8:
            if card.entity.grass_capeable == True:
                hovered_vertex = render.get_hovered_vertex(self.ctx, self.ground_vertices, mouse_pos, 500, self.apply_camera_transform)
                if hovered_vertex:
                    pos = hovered_vertex['position']
                    x, z, = pos[0], pos[2]

                    self.selected_card = None
                    self.placement_mode = False

                    is_near_base = False

                    all_bases = [self.player_base, self.enemy_base] + self.cities
                    for base in all_bases:
                        distance = math.sqrt((base.x - x)**2 + (base.z - z)**2)
                        if distance < 10:
                            if base.color == (0, 0, 255): 
                                is_contested = self.is_base_contested(base)
                                if not is_contested:
                                    is_near_base = True
                                break

                    if is_near_base and self.player_points >= card.price:
                        self.player_points -= card.price

                        placed_entity = copy.deepcopy(card.entity)
                        placed_entity.x = x
                        placed_entity.z = z
                        if self.online:
                            self.quene_units.append(placed_entity)
                            placed_entity.id = time.time_ns()

                        else:
                            self.player_entities.append(placed_entity)                        
                        placed_entity.target = None
                        placed_entity.target_entity = None

                        self.player_cards.append(self.player_cards.pop(index))
                        
            elif card.entity.water_capeable == True and self.water_map:
                hovered_vertex = render.get_hovered_vertex(self.ctx, self.water_vertices, mouse_pos, 500, self.apply_camera_transform)
                if hovered_vertex:
                    pos = hovered_vertex['position']
                    x, z = pos[0], pos[2]

                    self.selected_card = None
                    self.placement_mode = False

                    is_valid_placement = False

                    all_bases = [self.player_base] + [city for i, city in enumerate(self.cities) if self.city_captures[i] == "Player"]
                    if self.player_base_capture == "Player":
                        all_bases = [self.player_base] + [city for i, city in enumerate(self.cities) if self.city_captures[i] == "Player"]
                    else:
                        all_bases = [city for i, city in enumerate(self.cities) if self.city_captures[i] == "Player"]

                    if all_bases:
                        furthest_base = max(all_bases, key=lambda b: b.z)
                        if z <= furthest_base.z + 5:
                            is_valid_placement = True

                    if is_valid_placement and self.player_points >= card.price:
                        self.player_points -= card.price

                        placed_entity = copy.deepcopy(card.entity)
                        placed_entity.x = x
                        placed_entity.z = z
                        if self.online:
                            self.quene_units.append(placed_entity)
                            placed_entity.id = time.time_ns()
                        else:
                            self.player_entities.append(placed_entity)
                        placed_entity.target = None

    def is_base_contested(self, base):
        nearby_player_units = 0
        nearby_enemy_units = 0
        
        for entity in self.player_entities:
            if not entity.util:
                distance = math.sqrt((entity.x - base.x)**2 + (entity.z - base.z)**2)
                if distance <= self.capture_range:
                    nearby_player_units += 1
        
        for entity in self.enemy_entities:
            if not entity.util:
                distance = math.sqrt((entity.x - base.x)**2 + (entity.z - base.z)**2)
                if distance <= self.capture_range:
                    nearby_enemy_units += 1
        
        return nearby_player_units > 0 and nearby_enemy_units > 0
                    

    
    def get_stuff_from_box_selection(self, start_pos, end_pos):
        start_x = min(start_pos[0], end_pos[0])
        start_y = min(start_pos[1], end_pos[1])
        end_x = max(start_pos[0], end_pos[0])
        end_y = max(start_pos[1], end_pos[1])

        selected_entities = []

        x_dif = abs(start_x - end_x)
        y_dif = abs(start_y - end_y)

        if x_dif * y_dif < 1000:
            dist = 2
        elif x_dif * y_dif < 5000:
            dist = 5
        elif x_dif * y_dif < 10000:
            dist = 10
        else:
            dist = 20



        for entity in self.player_entities:
            if entity.unit_type == "bomber":
                continue 
            for x in range(int(start_x), int(end_x), dist):
                for y in range(int(start_y), int(end_y), dist):
                    if entity.is_hovered(self.ctx, self.line_prog, self.ground_vertices, self.apply_camera_transform, 500, (x, y)):
                        selected_entities.append(entity)
        
        selected_entities = list(set(selected_entities))

        self.selected_entities = selected_entities
                        
    def draw_clouds(self):
        transformed_ground = self.apply_camera_transform(self.cloud_edge_vertices)
        
        render.render(self.ctx, transformed_ground, (255, 255, 255), 500, self.line_prog) 


    def update_game_over(self):
        if self.win_condition == "CAPTURE":
            player_cities = sum(1 for capture in self.city_captures if capture == "Player")
            enemy_cities = sum(1 for capture in self.city_captures if capture == "Enemy")
            total_cities = len(self.cities)

            if player_cities == total_cities and self.enemy_base_capture == "Player":
                print("GAME OVER - Player Wins! All cities captured!")
                self.game_over = "Player"
            elif enemy_cities == total_cities and self.player_base_capture == "Enemy":
                print("GAME OVER - Enemy Wins! All cities captured!")
                self.game_over = "Enemy"
        elif self.win_condition == "KILLS":
            score_dif = int(self.player_score - self.enemy_score)


            if self.tick%360 == 0:
                self.player_score += sum(1 for capture in self.city_captures if capture == "Player")
                self.enemy_score += sum(1 for capture in self.city_captures if capture == "Enemy")

            elif abs(score_dif) > 100:
                if score_dif > 100:
                    self.game_over = "Player"
                else:
                    self.game_over = "Enemy"

    def draw_special(self):
        for entity in self.special_entities:
            entity.draw(self.ctx, self.shader, self.ground_vertices, self.apply_camera_transform, 500)

    def draw_unit_range(self):
        for entity in self.selected_entities:
            if entity.unit_type == "bomber":
                continue
            if entity.range > 0:
                circle_center = [entity.x, entity.y + 0.1, entity.z]
                
                num_points = 12
                
                circle_vertices = []
                circle_edges = []
                
                for i in range(num_points):
                    angle = (2 * math.pi * i) / num_points
                    
                    dx = math.cos(angle)
                    dz = math.sin(angle)
                    
                    modifier = entity.y
                    max_range = max(0, (-modifier + entity.range))
                    
                    x = circle_center[0] + max_range * dx
                    z = circle_center[2] + max_range * dz
                    circle_vertices.append([x, circle_center[1], z])
                    
                    next_i = (i + 1) % num_points
                    circle_edges.append([i, next_i])
                
                if circle_vertices:
                    circle_edge_vertices = render.create_vertex_data(circle_vertices, circle_edges)
                    transformed_circle = self.apply_camera_transform(circle_edge_vertices)
                    
                    color = [255, 255, 255]
                    
                    render.render(self.ctx, transformed_circle, color, 500, self.line_prog)



    def draw_skybox(self):
        depth = 60   


        #Honestly dont know where tf 6 and diving by 2 come from but somehow that shit works so

        min_x = 0
        max_x = self.board_size * 6
        min_z = 0
        max_z = self.board_size * 6
        top_y = 0
        bottom_y = -depth

        cam_x, cam_y, cam_z = self.camera_position

        if (min_x <= cam_x <= max_x/2 and
            bottom_y + 20<= cam_y <= top_y and
            min_z <= cam_z <= max_z/2):
            return 

        corners = [
            [min_x, top_y, min_z],
            [max_x, top_y, min_z],
            [max_x, top_y, max_z],
            [min_x, top_y, max_z],
            [min_x, bottom_y, min_z],
            [max_x, bottom_y, min_z],
            [max_x, bottom_y, max_z],
            [min_x, bottom_y, max_z],
        ]

        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],
            [4, 5], [5, 6], [6, 7], [7, 4],
            [0, 4], [1, 5], [2, 6], [3, 7]
        ]

        num_side_lines = 8
        for i in range(num_side_lines):
            t = i / num_side_lines
            x = min_x + (max_x - min_x) * t
            z = min_z
            edges.append([len(corners), len(corners) + 1])
            corners.append([x, top_y, z])
            corners.append([x, bottom_y, z])
            z = max_z
            edges.append([len(corners), len(corners) + 1])
            corners.append([x, top_y, z])
            corners.append([x, bottom_y, z])
            x = min_x
            z = min_z + (max_z - min_z) * t
            edges.append([len(corners), len(corners) + 1])
            corners.append([x, top_y, z])
            corners.append([x, bottom_y, z])
            x = max_x
            edges.append([len(corners), len(corners) + 1])
            corners.append([x, top_y, z])
            corners.append([x, bottom_y, z])

        inv_cam_pos = [-cam_x, -cam_y, -cam_z]
        corners = [[x + inv_cam_pos[0], y + inv_cam_pos[1], z + inv_cam_pos[2]] for x, y, z in corners]

        if corners:
            box_edge_vertices = render.create_vertex_data(corners, edges)
            transformed_box = self.apply_camera_transform(box_edge_vertices)
            render.render(self.ctx, transformed_box, (100, 150, 255), 500, self.line_prog)

    def ai_update(self):
        capture_status = {
            self.player_base: self.player_base_capture,
            self.enemy_base: self.enemy_base_capture,

        }
        for i, city in enumerate(self.cities):
            capture_status[city] = self.city_captures[i]

        if self.tick % 20 == 0:
            self.bob.make_move(self.visible_player_entities, self.enemy_entities, capture_status)

        if self.tick % 30 == 0:
            self.enemy_points, self.enemy_entities = self.bob.place(self.enemy_cards, self.enemy_entities, self.enemy_points, self.player_entities)


    def update(self):
        self.handle_input()
        self.handle_mouse_events()
        if self.game_over == False:
            self.update_entities()
            self.ai_update()
            self.update_game_state()
            self.update_base_captures()




    def decompile_data_client(self, data):
            print(f"Client Received: {data}")
        
            if data.get('units'):
                existing_player_entities = {entity.id: entity for entity in self.player_entities}
                existing_enemy_entities = {entity.id: entity for entity in self.enemy_entities}
                
                self.player_entities.clear()
                self.enemy_entities.clear()
            
                for unit_data in data['units']:
                    entity_id = unit_data['id']
                    team = unit_data['player_team']
                    
                    existing_entities = existing_player_entities if team else existing_enemy_entities
                    
                    if entity_id in existing_entities:
                        entity = existing_entities[entity_id]
                        entity.x = unit_data['x']
                        entity.z = unit_data['z']
                        entity.health = unit_data['health']
                        entity.supply = unit_data['supply']
                        entity.team = unit_data['player_team']
                        
                        if unit_data['target']:
                            entity.target = unit_data['target']
                        else:
                            entity.target = None
                    else:
                        entity_obj = getattr(e, unit_data['name'])
                        entity = entity_obj(unit_data['x'], unit_data['z'], unit_data['player_team'])
                        entity.health = unit_data['health']
                        entity.supply = unit_data['supply']
                        entity.id = unit_data['id']
                        
                        if unit_data['target']:
                            entity.target = unit_data['target']
                        else:
                            entity.target = None
                        
                    if entity.team:
                        self.player_entities.append(entity)
                    else:
                        self.enemy_entities.append(entity)
            
            if data.get('all_targets'):
                for entity in self.player_entities + self.enemy_entities:
                    for entity_set in data['all_targets']:
                        if entity_set[1] != None and entity_set[0] == entity.id:
                            entity.target = entity_set[1]
                            print("test")
                        elif entity_set[1] == None and entity_set[0] == entity.id:
                            entity.target = None
                        
            if 'blue_money' in data:
                self.player_points = data['blue_money']
            if 'red_money' in data:
                self.enemy_points = data['red_money']

    def decompile_data_server(self, data):
        print(f"Server Received: {data}")
    
        if data.get('camera_cords'):
            pass
    
        if data.get('units_placed'):
            existing_player_entities = {entity.id: entity for entity in self.player_entities}
            existing_enemy_entities = {entity.id: entity for entity in self.enemy_entities}
            
            for unit_data in data['units_placed']:
                entity_id = unit_data['id']
                team = unit_data['player_team']
                
                existing_entities = existing_player_entities if team else existing_enemy_entities
                
                if entity_id not in existing_entities:
                    entity_obj = getattr(e, unit_data['name'])
                    entity = entity_obj(unit_data['x'], unit_data['z'], unit_data['player_team'])
                    entity.health = unit_data['health']
                    entity.supply = unit_data['supply']
                    entity.id = unit_data['id']
                    entity.health = unit_data['health']
                    entity.supply = unit_data['supply']
                    entity.team = unit_data['player_team']
                    entity.id = unit_data['id']
                
                    if unit_data['target']:
                        entity.target = unit_data['target']
                    else:
                        entity.target = None
                
                    if entity.team:
                        self.player_entities.append(entity)
                    else:
                        self.enemy_entities.append(entity)
        if data.get('updated_targets'):
            for entity in self.player_entities + self.enemy_entities:
                for entity_set in data['updated_targets']:
                    if entity_set[1] != None and entity_set[0] == entity.id:
                        entity.target = entity_set[1]
                    

    def online_update_client(self):
        self.handle_input()
        self.handle_mouse_events()
        self.update_entities()

        self.tick += 1
        result = {'camera_cords': (round(self.camera_position[0]), round(self.camera_position[1]), round(self.camera_position[2])),
                'units_placed': [entity.serialize() for entity in self.quene_units] if self.quene_units else None,
                'updated_targets': [(entity.id, (float(entity.target[0]), float(entity.target[1])) if entity.target else None) for entity in self.player_entities] if self.player_entities else None
        }
        return str(result)

    def online_update_server(self):
        self.update_entities()
        self.update_game_state()
        self.update_base_captures()  
        result = {"blue_money": self.player_points, "red_money": self.enemy_points,
                'units': [entity.serialize() for entity in self.player_entities + self.enemy_entities] if len(self.player_entities + self.enemy_entities) > 0 else None,
                'all_targets': [(entity.id, (float(entity.target[0]), float(entity.target[1])) if entity.target else None) for entity in self.player_entities + self.enemy_entities] if self.player_entities + self.enemy_entities else None}
        return str(result)
    
    def render(self, gamestates, main, events=None):

        self.draw_skybox()
        self.render_terrain()
        self.render_entities()
        if self.biome == "grass":
            self.draw_clouds()
        elif self.biome == "desert":
            self.draw_special()
        self.update_game_over()
        if self.game_over == False:
            if self.camera_movement_mode == "fixed":
                if self.selected_entities or self.target_selection_mode:
                    self.draw_unit_range()
                    self.handle_menu()
                self.draw_ui()
                self.draw_box_selection()
                if self.selected_card:
                    self.placement_mode = True
                    self.check_placement()
            
            if self.tick % 120 == 0:
                self.real_money_earned += 1

        else:
            if self.draw_end_screen():
                global_vals.money += self.real_money_earned
                self.real_money_earned = 0
                if self.game_og == "sandbox":
                    main.current_state = gamestates.MENU
                else:
                    main.current_state = gamestates.CAMPAIGN

        



    def draw_end_screen(self):

        overlay_rect = (self.WIDTH/4, self.HEIGHT/4, self.WIDTH/2, self.HEIGHT/2)
        render.draw_rect(self.ctx, overlay_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, overlay_rect, (0, 255, 0), self.line_prog, False)

        if self.game_over == "Enemy":
            winner_text = "ENEMY WINS!"
            winner_color = (255, 0, 0)
            subtitle_text = "Better luck next time!"
        else:
            winner_text = "PLAYER WINS!"
            winner_color = (0, 255, 0)
            subtitle_text = "Good work Commander!"
        
        title_x = self.WIDTH // 2 - 200
        title_y = self.HEIGHT // 2 - 150
        render.draw_text(self.ctx, winner_text, (title_x, title_y), winner_color, font_size=80)
        
        subtitle_x = self.WIDTH // 2 - 150
        subtitle_y = self.HEIGHT // 2 - 80
        render.draw_text(self.ctx, subtitle_text, (subtitle_x, subtitle_y), (255, 255, 255), font_size=40)
        
        stats_x = self.WIDTH // 2 - 200
        stats_y = self.HEIGHT // 2 - 20
        
        player_cities = sum(1 for capture in self.city_captures if capture == "Player")
        enemy_cities = sum(1 for capture in self.city_captures if capture == "Enemy")
        
        stats_text = [
            f"Money Earned: ${self.real_money_earned}!",
        ]
        
        for i, stat in enumerate(stats_text):
            render.draw_text(self.ctx, stat, (stats_x, stats_y + i * 40), (255, 255, 255), font_size=30)
        

        
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        
        global_vals.winner = self.game_over

        if self.back_button.check_click(self.mouse_pressed, self.mouse_released):
            return True 
        
        self.back_button.draw(self.ctx, self.line_prog)
        
        return False  
