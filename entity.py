import pygame
from pygame.locals import *
import moderngl
import numpy as np
import math
from render import *
from global_vals import bullet_entities, explosive_entities
import random
import copy
import time
import os

#Note to whoever reads this, The casing doesnt matter I got lazy so some are camal and some arent lowkey just up to u 💔
#Also I did use ai to speed up making new units so some comments that dont look like me are NOT me. Trust tho they were still mostly done by me


#                             #########
#                            #         #
#                          #            #
#                          #   Whats     #
#                          #    Good    #
#                          #            #
#         #####             #         #
#       #########            #########
#      ###########         #
#     ####     ####      #
#     ###       ###    #
#     ###  # #  ###                
#     ###  ###  ###      
#     ###       ###   
#     ####     ####
#     ###########
#      #########
#        #####
#        ###
#        ###
#        ###
#      #######
#     #########
#    ###     ###
#   ###       ###
#  ###         ###
#
#
# ^ spaghetti code sam



class baseEntity:
    def __init__(self, x, z, health, team, shape=None):

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefix = f"{script_dir}/"


        self.id = time.time_ns()
        self.x = x
        self.z = z
        self.max_health = health
        self.team = team
        self.health = health
        self.size = 0.5
        self.y = 0.0
        self.danger = 1
        self.damage = 0.0
        self.armor = 1.0
        self.can_target_air = False
        self.supply = 10
        self.max_supply = self.supply
        if team:
            self.rotation = 0
        else:
            self.rotation = 180
        self.attack_speed = 0
        self.attack_count = 0
        self.range = 30
        self.visibility = 1
        self.unit_type = "None"
        self.accuracy = 1.0
        self.target_entity = None
        self.target = None
        self.speed = 0.5
        self.state = "idle"
        self.on_screen_center = (0, 0)
        self.util = False
        self.hover = False
        self.color = (0, 0, 255) if self.team else (255, 0, 0)
        self.in_air = False
        
        self.grass_capeable = True
        self.water_capeable = False

        #Exclusive to bomber/some artillery
        self.can_set_target = False


        #AI
        self.has_been_moved = 1000

        # Cache for rotation matrices
        self._rotation_matrix_cache = {}
        
        if shape is None:
            self.local_vertices, self.edges = self._initialize_placeholder()
        else:
            self.local_vertices, self.edges = self._initialize_shape(shape)

        # Precompute edge pairs for drawing
        self.edge_pairs = [(self.local_vertices[start_idx], self.local_vertices[end_idx]) 
                          for start_idx, end_idx in self.edges]

    def _initialize_placeholder(self):
        """Precompute the cube's local-space vertices and edges"""
        s = self.size
        local_vertices = np.array([
            [-s, -s, -s], [s, -s, -s], [s, -s, s], [-s, -s, s],  
            [-s, s, -s],  [s, s, -s],  [s, s, s],  [-s, s, s],   
        ])

        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0), 
            (4, 5), (5, 6), (6, 7), (7, 4), 
            (0, 4), (1, 5), (2, 6), (3, 7) 
        ]
        
        return local_vertices, edges

    def _update_state(self):
            if self.target_entity is not None:
                self.state = "attacking"
            elif self.target is not None:
                self.state = "moving"
            else:
                self.state = "idle"


    def _initialize_shape(self, location):
        vertices = []

        with open(f"{self.prefix}{location}", 'r') as file:
            for line in file:
                # Parse each line as a 3D point
                parts = line.strip().split()
                if len(parts) == 3:
                    x, y, z = map(float, parts)
                    vertices.append([x, -y, -z])

        
        local_vertices = np.array(vertices)

        num_vertices = len(local_vertices)
        edges = []
        for i in range(0, num_vertices, 2):
            if i+1 < num_vertices:
                edges.append((i, i+1))
                
        return local_vertices, edges
    
    def _get_rotation_matrix(self, angle_degrees):
        """Create a rotation matrix for Y-axis rotation with caching"""
        # Round to avoid floating point precision issues in cache
        angle_degrees = round(angle_degrees, 2) % 360
        
        if angle_degrees not in self._rotation_matrix_cache:
            angle_radians = math.radians(angle_degrees)
            cos_theta = math.cos(angle_radians)
            sin_theta = math.sin(angle_radians)
            
            # Y-axis rotation matrix
            self._rotation_matrix_cache[angle_degrees] = np.array([
                [cos_theta, 0, sin_theta],
                [0, 1, 0],
                [-sin_theta, 0, cos_theta]
            ])
        
        return self._rotation_matrix_cache[angle_degrees]



    def is_hovered(self, ctx, line_prog, terrain_heights, camera_transform, scale, mouse_pos = None):
        y = self._get_terrain_height(terrain_heights)
        self.y = y
        
        # Apply rotation to local vertices
        rotation_matrix = self._get_rotation_matrix(self.rotation)
        
        # Vectorized rotation and translation
        rotated_vertices = np.dot(self.local_vertices, rotation_matrix.T)
        translated_vertices = rotated_vertices + np.array([self.x, y, self.z])

        # Extract vertices for edges
        edge_vertices = []
        for start_idx, end_idx in self.edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])

        # Transform vertices to screen space
        transformed_vertices = camera_transform(np.array(edge_vertices))

        if len(transformed_vertices) > 0:
            if mouse_pos is None:
                mouse_pos = pygame.mouse.get_pos()  
            return is_entity_hovered(ctx, transformed_vertices, mouse_pos, scale)



    def draw(self, ctx, line_prog, terrain_heights, camera_transform, scale):
        y = self._get_terrain_height(terrain_heights)
        self.has_been_moved += 1
        self.y = y
        
        # Apply rotation to local vertices
        rotation_matrix = self._get_rotation_matrix(self.rotation)
        
        # Vectorized rotation and translation
        rotated_vertices = np.dot(self.local_vertices, rotation_matrix.T)
        translated_vertices = rotated_vertices + np.array([self.x, y, self.z])

        # Extract vertices for edges
        edge_vertices = []
        for start_idx, end_idx in self.edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])

        # Transform vertices to screen space
        transformed_vertices = camera_transform(np.array(edge_vertices))

        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()  
            self.hover = render_with_hover(ctx, transformed_vertices, self.color, scale, line_prog, mouse_pos)

    def _get_terrain_height(self, terrain_vertices):
        """Optimized version to find height at entity position"""
        if len(terrain_vertices) == 0:
            return 0.0

        min_dist = float('inf')
        height = 0.0

        # Use numpy operations for better performance
        entity_pos = np.array([self.x, 0, self.z])
        terrain_positions = terrain_vertices[:, [0, 2]]  # Extract x,z coords
        entity_xz = np.array([self.x, self.z])
        
        # Calculate squared distances efficiently
        distances = np.sum((terrain_positions - entity_xz)**2, axis=1)
        nearest_idx = np.argmin(distances)
        
        return terrain_vertices[nearest_idx, 1]  # Return y-value at nearest point

    def has_line_of_sight(self, entities):
        if not entities:
            return []
            
        in_sight = []
        entity_pos = np.array([self.x, self.z])
        
        for entity in entities:
            target_pos = np.array([entity.x, entity.z])

            modifier = self.y

            dist = np.sqrt(np.sum((entity_pos - target_pos)**2))
            
            if dist * (1/entity.visibility) < -modifier + self.range:
                in_sight.append(entity)
                
        return in_sight

    def move(self, any, _):
        return

    def check_move_validity(self, target_x, target_z, valid_vertices):
        start_x, start_z = round(self.x), round(self.z)
        target_x, target_z = round(target_x), round(target_z)

        dx = target_x - start_x
        dz = target_z - start_z
        distance = math.hypot(dx, dz)
        if distance == 0:
            return [(start_x, start_z)]

        dir_x = dx / distance
        dir_z = dz / distance

        step_size = 1
        num_steps = int(distance / step_size) + 1

        # Use a set for fast lookup and deduplication
        points_within_range = set()

        valid_vertex_set = set(valid_vertices.keys())

        for i in range(num_steps + 1):
            current_distance = min(i * step_size, distance)
            line_x = round(start_x + dir_x * current_distance)
            line_z = round(start_z + dir_z * current_distance)
            # Only check the closest grid point
            candidate = (line_x, line_z)
            if candidate in valid_vertex_set:
                points_within_range.add(candidate)

        points_within_range.add((start_x, start_z))
        points_within_range.add((target_x, target_z))

        for point in points_within_range:
            if point in valid_vertex_set:
                terrain = valid_vertices[point]
                if (not self.water_capeable and terrain == "water") or (not self.grass_capeable and terrain == "land"):
                    return False

        return True


    def __str__(self):
        return f"Entity: {self.__class__.__name__}, Position: ({self.x}, {self.z}), Target Entity: {self.target_entity.__class__.__name__  if self.target_entity else None}, Team: {self.team}, State: {self.state}, Target: {self.target}"

    def shoot(self, target):
        self.supply -= 1
        bullet(self.x, self.z, self.y, self.team, target, self.accuracy, self.damage)

    def pickup(self, player_entities_o, enemy_entities_o):
        counter = 0
        
        if self.team:
            entities_to_check = player_entities_o
        else:
            entities_to_check = enemy_entities_o
            
        entities_to_remove = []
        
        for entity in entities_to_check:
            if not entity.in_air and entity != self and (entity.__class__.__name__ == "infantry" or entity.__class__.__name__ == "sniper"):
                dist = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                if dist < 10 and counter < 5:
                    entity_copy = copy.deepcopy(entity)
                    self.units_carried.append(entity_copy)
                    entities_to_remove.append(entity)
                    counter += 1
        
        for entity in entities_to_remove:
            entities_to_check.remove(entity)

    def deploy(self, player_entities, enemy_entities, ground_vertices):
        # Had ai optimize because genuinely could not do ts effiecently
        units_to_deploy = self.units_carried.copy()
        self.units_carried.clear()
        
        target_list = player_entities if self.team else enemy_entities
        
        vertices = ground_vertices #np.array(ground_vertices)

        for entity in units_to_deploy:
            entity.x = self.x + random.randint(-4, 4)
            entity.z = self.z + random.randint(-4, 4)

            diffs = vertices[:, [0, 2]] - np.array([entity.x, entity.z])
            distances = np.einsum('ij,ij->i', diffs, diffs)
            closest_idx = np.argmin(distances)
            closest_vertex = vertices[closest_idx]

            entity.x = closest_vertex[0]
            entity.z = closest_vertex[2]

            target_list.append(entity)
    
    def serialize(self):
        data = {
            "name": self.__class__.__name__,
            "x": float(round(self.x, 2)),
            "z": float(round(self.z, 2)),
            "health": int(self.health),
            "supply": int(self.supply),
            "target_entity_ref": (float(round(self.target_entity.x, 2)),float(round(self.target_entity.z, 2))) if self.target_entity else None,
            "target": (float(self.target[0]), float(self.target[1])) if self.target else None,
            "player_team": self.team,
            "id": self.id
        }

        return data


class smallTank(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 100, player_team, "game_models/lightTank/lightTank.txt")
        self.tank_vertices, self.tank_edges = self._initialize_shape("game_models/lightTank/cannon.txt")
        self.tank_vertices[:, 1] -= 0.4 
        self.range = 20
        self.speed = 0.03
        self.damage = 30
        self.armor = 0.5
        self.danger = 4
        self.accuracy = .95
        self.supply = 30
        self.attack_speed = 120
        self.turret_rotation = 0 
        self.rotation += 180
        self.target = (x, z)
        self.state = "idle"
        self.unit_type = "attack"
        self.max_supply = self.supply

        self.tank_edge_pairs = [(self.tank_vertices[start_idx], self.tank_vertices[end_idx]) 
                               for start_idx, end_idx in self.tank_edges]
  
    def move(self, known_entities, all_entities):
        # Always search for targets first
        self._find_target(known_entities)
        
        # Update state based on current situation
        if self.target_entity is not None:
            # Check if target is still in range
            if (abs(self.x - self.target_entity.x) < self.range and 
                abs(self.z - self.target_entity.z) < self.range and 
                self.target_entity in known_entities):
                self.state = "attacking"
            

        elif self.target is not None:
            self.state = "moving"
        else:
            self.state = "idle"
        
        # Handle turret rotation for any state if we have a target entity
        if self.target_entity is not None and self.target_entity in known_entities:
            # Point turret at target entity regardless of state
            target_x, target_z = self.target_entity.x, self.target_entity.z
            angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
            target_turret_rotation = (angle_to_target + 180) % 360
            
            # Smooth turret rotation
            diff = (target_turret_rotation - self.turret_rotation % 360 + 180) % 360 - 180
            self.turret_rotation = (self.turret_rotation + diff * 0.1) % 360
        
        # Movement logic - now happens in both moving and attacking states if we have a target location
        if self.target is not None and (self.state == "moving" or (self.state == "attacking" and self.target_entity is not None)):
            target_x, target_z = self.target

            
            if abs(self.x - target_x) < 0.5 and abs(self.z - target_z) < 0.5:
                if self.target_entity is None:
                    self.state = "idle"
                    self.target = None
            else:
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_rotation = (angle_to_target + 180) % 360
                
                diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                self.rotation = (self.rotation + diff * 0.1) % 360


                move_x = self.speed * math.sin(math.radians(-self.rotation))
                move_z = self.speed * math.cos(math.radians(self.rotation-180))
                self.x += move_x
                self.z += move_z


        # Handle attack logic if we're in attacking state
        if self.state == "attacking":
            if self.target_entity is None or self.target_entity not in known_entities:
                # Lost the target, reset state
                self.target_entity = None
                self.state = "idle"
                return
            
            # Fire when ready
            self.attack_count += 1
            if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                self.shoot(self.target_entity)
                    
    def _find_target(self, known_entities):
        """Find the highest danger target within range"""
        if not known_entities:
            return
            
        # Clear target if it's no longer valid
        if self.target_entity and (
            self.target_entity not in known_entities or 
            self.target_entity.health <= 0 or
            self.target_entity.team == self.team or self.target_entity.in_air
        ):
            self.target_entity = None
        
        # Look for new targets
        potential_targets = []
        for entity in known_entities:
            if (entity.team != self.team and 
                entity.health > 0 and 
                not entity.util and
                not entity.in_air):
                
                # Calculate distance to target
                distance = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                
                if distance < self.range:
                    potential_targets.append((entity, entity.danger, distance))
            

        # Sort targets by danger (primary) and distance (secondary)
        potential_targets.sort(key=lambda x: (-x[1], x[2]))
        
        if potential_targets:
            # Take the highest priority target
            new_target = potential_targets[0][0]
            
            # If we have a new target or no current target
            if not self.target_entity or new_target.danger > self.target_entity.danger:
                self.target_entity = new_target
                self.attack_count = 0

    def draw(self, ctx, line_prog, terrain_vertices, camera_transform, scale):
        super().draw(ctx, line_prog, terrain_vertices, camera_transform, scale)

        y = self._get_terrain_height(terrain_vertices)
        
        # Get the rotation matrix for the turret
        turret_rotation_matrix = self._get_rotation_matrix(self.turret_rotation)
        
        # Optimized rotation and translation
        rotated_cannon_vertices = np.dot(self.tank_vertices, turret_rotation_matrix.T)
        translated_vertices = rotated_cannon_vertices + np.array([self.x, y, self.z])

        # Extract vertices for edges
        edge_vertices = []
        for start_idx, end_idx in self.tank_edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])
            
        transformed_vertices = camera_transform(np.array(edge_vertices))
        
        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()  
            render_with_hover(ctx, transformed_vertices, self.color, scale, line_prog, mouse_pos)

    def shoot(self, target):
        move_x = 1 * math.sin(math.radians(-self.turret_rotation))
        move_z = 1 * math.cos(math.radians(self.turret_rotation-180))
        self.supply -= 1
        bullet(self.x + move_x, self.z + move_z, self.y-.5, self.team, target, self.accuracy, self.damage)

class supplyTruck(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 20, player_team, "game_models/truck.txt")
        self.visibility = 1
        self.rotation += 180
        self.speed = 0.05
        self.unit_type = "support"
        self.target = None
        self.state = "idle"
        self.range = 10
        self.resupply_amount = 10  
        self.resupply_cooldown = 60 
        self.resupply_counter = 0
        self.supply = 100 
        self.max_supply = self.supply

        self.danger = 2

    def move(self, known_entities, all_entities):
        self.resupply_counter += 1
        
        self._update_state()

        
        if self.state == "idle" or self.state == "supplying":
            for entity in all_entities:
                if entity.team == self.team and abs(entity.x - self.x) < self.range and abs(entity.z - self.z) < self.range and self.resupply_counter >= self.resupply_cooldown and entity != self:
                    entity.supply += 5
                    self.supply -= 1
                    self.resupply_counter = 0
                    self.state = "supplying"
                    continue

            return
        
        elif self.state == "moving" and self.target is not None:
            target_x, target_z = self.target
            
            angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
            target_rotation = (angle_to_target + 180) % 360
            diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
            self.rotation = (self.rotation + diff * 0.1) % 360
            
            move_x = self.speed * math.sin(math.radians(-self.rotation))
            move_z = self.speed * math.cos(math.radians(self.rotation-180))
            self.x += move_x
            self.z += move_z
            
            if abs(self.x - target_x) < 1.0 and abs(self.z - target_z) < 1.0:
                self.state = "idle"
                self.target = None
                self.target_entity = None



class smallPlane(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 20, player_team, "game_models/lightPlane.txt")
        self.visibility = 1
        self.speed = 0.2
        self.rotation += 180
        self.danger = 2
        self.in_air = True
        self.unit_type = "intel"


    def _get_terrain_height(self, terrain_vertices):
        return -10
    
    def move(self, known_entites, _):
        self._update_state()

        if self.state == "moving" and self.target is not None:
            target_x, target_z = self.target
            angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
            
            current_rotation = self.rotation % 360
            target_rotation = (angle_to_target + 180) % 360
            
            diff = (target_rotation - current_rotation + 180) % 360 - 180
            self.rotation = (current_rotation + diff * 0.01) % 360

            self.x += self.speed * math.sin(math.radians(-self.rotation))
            self.z += self.speed * math.cos(math.radians(self.rotation-180))


class base(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 1000, player_team, "game_models/base.txt")
        self.visibility = 10
        self.unit_type = "building"


class marker(baseEntity):
    def __init__(self, x, z, health, player_team):
        super().__init__(x, z, health, player_team, "game_models/marker.txt")
        self.visibility = 10000
        self.color = (255, 255, 255)
        self.util = True
    
    def move(self, _, not_Used):
        self.state = "none"


class bullet(baseEntity):
    def __init__(self, x, z, y, player_team, target: baseEntity, accuracy = 1.0, damage = 10):
        super().__init__(x, z, 1, player_team, "game_models/bullet.txt")
        self.visibility = 0.1
        self.util = True
        self.damage = damage
        self.speed = .3
        self.state = "moving"
        self.in_air = True
        self.color = (255, 255, 0)
        self.target = target
        self.creation_time = pygame.time.get_ticks()  
        self.lifetime = 2000 
        bullet_entities.append(self)

        self.start_pos = [x, y, z]
        self.end_pos = [target.x, target.y, target.z]
        
        self.y = y
        
        if target:
            angle_to_target = math.degrees(math.atan2(target.x - x, target.z - z))
            self.rotation = (angle_to_target + 180 + ((1.0 - accuracy) * random.randint(-45, 45))) % 360
    
    def _get_terrain_height(self, terrain_vertices):
        dy =  self.end_pos[1] - self.start_pos[1]
        self.percentage_distance_to_target()
        return self.start_pos[1] + dy * self.percentage_distance_to_target()
    
    def percentage_distance_to_target(self):
        if self.target:
            target_distance = math.sqrt((self.target.x - self.start_pos[0])**2 + (self.target.z - self.start_pos[2])**2)
            current_distance = math.sqrt((self.x - self.start_pos[0])**2 + (self.z - self.start_pos[2])**2)
            return current_distance / target_distance if target_distance != 0 else 1.0
        return 1.0




    def move(self, known_entities):
        current_time = pygame.time.get_ticks()
        if current_time - self.creation_time > self.lifetime:
            self._delete()
            return
            
        if self.state == "moving":

                
            move_x = self.speed * math.sin(math.radians(-self.rotation))
            move_z = self.speed * math.cos(math.radians(self.rotation-180))
            
            self.x += move_x
            self.z += move_z
            
            
            self._check_collision(known_entities)
    
    def _check_collision(self, known_entities):
        """Check if bullet has hit any entity"""
        for entity in known_entities:
            if entity.team == self.team or entity.util or entity is self:
                continue
                
            distance = math.sqrt((self.x - entity.x)**2 + (self.y - entity.y)**2 + (self.z - entity.z)**2)       

            if distance < 1.5:  
                entity.health -= self.damage*entity.armor
                print(entity.health)
                self._delete()
                break
    
    def _delete(self):
        """Remove the bullet from the bullet_entities list"""
        if self in bullet_entities:
            bullet_entities.remove(self)


class infantry(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 20, player_team, "game_models/infantry.txt")
        self.range = 5
        self.speed = 0.04
        self.damage = 2
        self.visibility = 1
        self.armor = 1
        self.danger = 2
        self.accuracy = .90
        self.supply = 100
        self.max_supply = self.supply

        self.attack_speed = 30
        self.rotation += 180
        self.target = (x, z)
        self.state = "idle"
        self.unit_type = "attack"
      
    def _get_terrain_height(self, terrain_vertices):
        return super()._get_terrain_height(terrain_vertices) - 1
    
    def move(self, known_entities, all_entities):
        # Always search for targets first
        self._find_target(known_entities)
        
        # Update state based on current situation
        if self.target_entity is not None:
            # Check if target is still in range
            if (abs(self.x - self.target_entity.x) < self.range and 
                abs(self.z - self.target_entity.z) < self.range and 
                self.target_entity in known_entities):
                self.state = "attacking"

        elif self.target is not None:
            self.state = "moving"
        else:
            self.state = "idle"
        
        # Movement logic - now happens in both moving and attacking states if we have a target location
        if self.target is not None and (self.state == "moving" or (self.state == "attacking" and self.target_entity is not None)):
            target_x, target_z = self.target
            
            if abs(self.x - target_x) < 0.5 and abs(self.z - target_z) < 0.5:
                if self.target_entity is None:
                    self.state = "idle"
                    self.target = None
            else:
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_rotation = (angle_to_target + 180) % 360
                
                diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                self.rotation = (self.rotation + diff * 0.1) % 360

                move_x = self.speed * math.sin(math.radians(-self.rotation))
                move_z = self.speed * math.cos(math.radians(self.rotation-180))
                self.x += move_x
                self.z += move_z

        # Handle attack logic if we're in attacking state
        if self.state == "attacking":
            if self.target_entity is None or self.target_entity not in known_entities:
                # Lost the target, reset state
                self.target_entity = None
                self.state = "idle"
                return
            
            # Fire when ready
            self.attack_count += 1
            if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                self.shoot(self.target_entity)
                    
    def _find_target(self, known_entities):
        """Find the highest danger target within range"""
        if not known_entities:
            return
            
        # Clear target if it's no longer valid
        if self.target_entity and (
            self.target_entity not in known_entities or 
            self.target_entity.health <= 0 or
            self.target_entity.team == self.team or self.target_entity.in_air
        ):
            self.target_entity = None
        
        # Look for new targets
        potential_targets = []
        for entity in known_entities:
            if (entity.team != self.team and 
                entity.health > 0 and 
                not entity.util and
                not entity.in_air):
                
                # Calculate distance to target
                distance = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                
                if distance < self.range:
                    potential_targets.append((entity, entity.danger, distance))

        # Sort targets by danger (primary) and distance (secondary)
        potential_targets.sort(key=lambda x: (-x[1], x[2]))
        
        if potential_targets:
            # Take the highest priority target
            new_target = potential_targets[0][0]
            
            # If we have a new target or no current target
            if not self.target_entity or new_target.danger > self.target_entity.danger:
                self.target_entity = new_target
                self.attack_count = 0


class artillery(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 50, player_team, "game_models/artillery/body.txt")
        self.cannon_vertices, self.cannon_edges = self._initialize_shape("game_models/artillery/cannon.txt")
        self.cannon_vertices[:, 1] -= 0.5
        self.cannon_vertices[:, 2] -= .3
        self.cannon_offset = 0.4
        self.range = 70
        self.speed = 0.02  
        self.damage = 50
        self.armor = 0.9
        self.danger = 5
        self.accuracy = 0.9
        self.supply = 20
        self.max_supply = self.supply

        self.cannon_rotation = 0 
        self.cannon_power = 0.5
        self.rotation += 180
        self.attack_speed = 120
        
        self.target = (x, z)
        self.state = "idle"
        self.unit_type = "artillery"

        self.cannon_edge_pairs = [(self.cannon_vertices[start_idx], self.cannon_vertices[end_idx]) 
                                for start_idx, end_idx in self.cannon_edges]
  
    def move(self, known_entities, all_entities):
        self._find_target(known_entities)
        
        if self.target_entity is not None:
            distance_to_target = math.sqrt((self.x - self.target_entity.x)**2 + (self.z - self.target_entity.z)**2)
            if (distance_to_target < self.range and 
                distance_to_target > 10 and  
                self.target_entity in known_entities):
                self.state = "attacking"
        elif self.target is not None:
            self.state = "moving"
        else:
            self.state = "idle"
        
        if self.target_entity is not None and self.target_entity in known_entities:
            distance_to_target = math.sqrt((self.x - self.target_entity.x)**2 + (self.z - self.target_entity.z)**2)
            if distance_to_target < self.range and distance_to_target > 10:
                target_x, target_z = self.target_entity.x, self.target_entity.z
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_cannon_rotation = (angle_to_target + 180) % 360
                
                diff = (target_cannon_rotation - self.cannon_rotation % 360 + 180) % 360 - 180
                self.cannon_rotation = (self.cannon_rotation + diff * 0.1) % 360
                
                self.attack_count += 1
                if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                    self.shoot(self.target_entity)
        
        if self.target is not None and (self.state == "moving" or (self.state == "attacking" and self.target_entity is not None)):
            target_x, target_z = self.target
            
            if abs(self.x - target_x) < 0.5 and abs(self.z - target_z) < 0.5:
                if self.target_entity is None:
                    self.state = "idle"
                    self.target = None
            else:
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_rotation = (angle_to_target + 180) % 360
                
                diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                self.rotation = (self.rotation + diff * 0.1) % 360

                move_x = self.speed * math.sin(math.radians(-self.rotation))
                move_z = self.speed * math.cos(math.radians(self.rotation-180))
                self.x += move_x
                self.z += move_z

    def draw(self, ctx, line_prog, terrain_vertices, camera_transform, scale):

        super().draw(ctx, line_prog, terrain_vertices, camera_transform, scale)
        y = self._get_terrain_height(terrain_vertices)
        
        
        body_rotation_rad = math.radians(self.rotation)
        offset_x = self.cannon_offset * math.sin(body_rotation_rad)
        offset_z = self.cannon_offset * math.cos(body_rotation_rad)
        
        cannon_rotation_matrix = self._get_rotation_matrix(self.cannon_rotation)
        
        rotated_cannon_vertices = np.dot(self.cannon_vertices, cannon_rotation_matrix.T)
        
        translated_vertices = rotated_cannon_vertices + np.array([
            self.x + offset_x, 
            y, 
            self.z + offset_z
        ])
        
        edge_vertices = []
        for start_idx, end_idx in self.cannon_edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])
        
        transformed_vertices = camera_transform(np.array(edge_vertices))
        
        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()
            render_with_hover(ctx, transformed_vertices, self.color, scale, line_prog, mouse_pos)
    
    def _find_target(self, known_entities):
        """Find the highest danger target within range"""
        if not known_entities:
            return
            
        # Clear target if it's no longer valid
        if self.target_entity and (
            self.target_entity not in known_entities or 
            self.target_entity.health <= 0 or
            self.target_entity.team == self.team or
            math.sqrt((self.x - self.target_entity.x)**2 + (self.z - self.target_entity.z)**2) <= 10 or self.target_entity.in_air
        ):
            self.target_entity = None
        
        potential_targets = []
        for entity in known_entities:
            if (entity.team != self.team and 
                entity.health > 0 and 
                not entity.util and
                not entity.in_air):
                
                distance = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                
                if distance < self.range and distance > 10:
                    potential_targets.append((entity, entity.danger, distance))
            

        potential_targets.sort(key=lambda x: (-x[1], x[2]))
        
        if potential_targets:
            new_target = potential_targets[0][0]
            
            if not self.target_entity or new_target.danger > self.target_entity.danger:
                self.target_entity = new_target
                self.attack_count = 0


    def shoot(self, target):
        move_x = 1 * math.sin(math.radians(-self.cannon_rotation))
        move_z = 1 * math.cos(math.radians(self.cannon_rotation-180))
        self.supply -= 1
        artillery_bullet(self.x + move_x, self.z + move_z, self.y-.5, self.team, target, self.damage)


class artillery_bullet(baseEntity):
    def __init__(self, x, z, y, player_team, target: baseEntity, damage = 10):
        super().__init__(x, z, 1, player_team, "game_models/largeBullet.txt")
        self.visibility = 0.1
        self.util = True
        self.damage = damage
        self.speed = .3
        self.state = "moving"
        self.in_air = True
        self.color = (255, 255, 0)
        self.target = target
        self.vertical_angle = 0
        self.creation_time = pygame.time.get_ticks()  
        self.lifetime = 5000 
        bullet_entities.append(self)

        self.start_pos = [x, y, z]
        self.end_pos = [target.x, target.y, target.z]
        
        self.y = y

        self.velocity = 30
        self.grav = 9.81
        self.flight_time = 0

        if target:
            angle_to_target = math.degrees(math.atan2(target.x - x, target.z - z))
            self.rotation = (angle_to_target + 180) % 360
            
            self.distance = math.sqrt((target.x - x)**2 + (target.z - z)**2)
            self.velocity = 20

            height_diff = target.y - y
            

            
            launch_angle = 45  
            
            if self.distance > 40:
                launch_angle = 40 
            elif self.distance > 20:
                launch_angle = 0
            
            self.vertical_angle = launch_angle
            

            self.total_flight_time = (2 * self.velocity * math.sin(math.radians(self.vertical_angle))) / self.grav
            
            self.vx = self.velocity * math.cos(math.radians(self.vertical_angle))
            self.vy = self.velocity * math.sin(math.radians(self.vertical_angle))
            
            self.total_flight_time += 1

            self.speed = self.distance / (self.total_flight_time * 60)
            
            self.real_terrain_height = 0

    def _get_terrain_height(self, terrain_vertices):
        self.real_terrain_height = super()._get_terrain_height(terrain_vertices)

        self.flight_time += 1
        
        time_factor = self.flight_time / 60  
        
        height = self.start_pos[1] - (self.vy * time_factor) + (0.5 * self.grav * time_factor * time_factor)
        
        progress = self.percentage_distance_to_target()
        

        distance_factor = min(self.distance / 50.0, 1.0) 
        parabolic_factor = 4 * progress * (1 - progress)  
        arc_height = -15 * parabolic_factor * distance_factor

        
        return self.start_pos[1] + arc_height
    
    def percentage_distance_to_target(self):
        if self.target:
            current_distance = math.sqrt((self.x - self.start_pos[0])**2 + (self.z - self.start_pos[2])**2)
            return min(current_distance / self.distance, 1.0) if self.distance != 0 else 1.0
        return 1.0

    def move(self, known_entities):
        current_time = pygame.time.get_ticks()

        if current_time - self.creation_time > self.lifetime:
            self._delete()
            return
        
        if self.y+.5 > self.real_terrain_height or 1 > math.sqrt((self.x - self.end_pos[0])**2 + (self.z - self.end_pos[2])**2):
            self._delete()
            return
            
        if self.state == "moving":
            move_x = self.speed * math.sin(math.radians(-self.rotation))
            move_z = self.speed * math.cos(math.radians(self.rotation-180))
            
            self.x += move_x
            self.z += move_z
            
            self._check_collision(known_entities)
        
    def _check_collision(self, known_entities):
        for entity in known_entities:
            if entity.team == self.team or entity.util or entity is self or entity.in_air:
                continue
                
            distance = math.sqrt((self.x - entity.x)**2 + (self.y - entity.y)**2 + (self.z - entity.z)**2)   

            if distance < 4:  
                entity.health -= self.damage*entity.armor
                self._delete()
                break
    
    def _delete(self):
        if self in bullet_entities:
            explosion(self.x, self.z)
            bullet_entities.remove(self)


class explosion(baseEntity):
    def __init__(self, x, z):

        self.size_explosion = 0.5

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefix = f"{script_dir}/"        
        with open(f"{self.prefix}game_models/explosionTemp.txt", "w") as file:
            for _ in range(40):
                temp_x = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                temp_y = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                temp_z = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                file.write(f"{temp_x:.4f} {temp_y:.4f} {temp_z:.4f}\n")


        super().__init__(x, z, 1, None, "game_models/explosionTemp.txt")
        self.util = True
        self.time_alive = 0

        
        explosive_entities.append(self)

    def draw(self, ctx, line_prog, terrain_heights, camera_transform, scale):
        y = self._get_terrain_height(terrain_heights)
        self.y = y

        rotation_matrix = self._get_rotation_matrix(self.rotation)
        rotated_vertices = np.dot(self.local_vertices, rotation_matrix.T)
        translated_vertices = rotated_vertices + np.array([self.x, y, self.z])

        edge_vertices = []
        for start_idx, end_idx in self.edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])

        transformed_vertices = camera_transform(np.array(edge_vertices))

        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()
            render_with_hover(ctx, transformed_vertices, (255, 165, 0), scale, line_prog, mouse_pos)


   
    def move(self):
        self.time_alive += 1
        self.size_explosion = 2 * (1 - math.exp(-0.2 * self.time_alive))        
        if self.time_alive > 20:
            self._delete()
            return
    def _delete(self):
        if self in explosive_entities:
            explosive_entities.remove(self)




class stealthPlane(baseEntity):
    def __init__(self, x, z, player_team, base_cords):
        super().__init__(x, z, 5, player_team, "game_models/stealthBomber.txt")
        self.visibility = 0.5
        self.speed = 0.3
        self.rotation += 180
        self.damage = 100
        self.danger = 7
        self.in_air = True
        self.unit_type = "bomber"
        self.can_set_target = True
        
        self.velocity = np.array([0.0, 0.0])  
        self.max_speed = 0.4
        self.acceleration = 0.01
        self.turn_rate = 1.5
        self.min_speed = 0.15
        
        self.mission_state = "patrol" 
        self.approach_vector = None
        self.bomb_target = None
        self.egress_target = None

        self.team = player_team
        self.base_cords = base_cords
        
        self.bomb_release_distance = 8.0
        self.has_dropped_bomb = False
        self.rtb_target = (0, 0)
        
        self.patrol_center = self.rtb_target
        self.patrol_radius = 25
        self.patrol_angle = 0
        self.patrol_speed = 0.02

    def _get_terrain_height(self, terrain_vertices):
        return -10

    def move(self, known_entities, all_entities):
        if not self.team:
            self.rtb_target = self.base_cords[0]
        else:
            self.rtb_target = self.base_cords[1]
        self.patrol_center = self.rtb_target

        self._update_flight_physics()

        if self.mission_state == "patrol":
            self._patrol_behavior()
        elif self.mission_state == "approach":
            self._approach_target()
        elif self.mission_state == "bomb_run":
            self._bomb_run()
        elif self.mission_state == "egress":
            self._egress_behavior()
        elif self.mission_state == "rtb":
            self._return_to_base()
            
        self._apply_movement()

    def _update_flight_physics(self):

        desired_vx = self.speed * math.sin(math.radians(-self.rotation))
        desired_vz = self.speed * math.cos(math.radians(self.rotation - 180))
        desired_velocity = np.array([desired_vx, desired_vz])
        
        self.velocity = self.velocity * 0.9 + desired_velocity * 0.1
        
        current_speed = np.linalg.norm(self.velocity)
        if current_speed < self.min_speed and current_speed > 0:
            self.velocity = (self.velocity / current_speed) * self.min_speed

    def _patrol_behavior(self):
        if self.target is None:
            self.patrol_angle += self.patrol_speed
            
            patrol_x = self.patrol_center[0] + self.patrol_radius * math.cos(self.patrol_angle)
            patrol_z = self.patrol_center[1] + self.patrol_radius * math.sin(self.patrol_angle)
            
            self._turn_towards_point(patrol_x, patrol_z)
            self.speed = min(self.speed + self.acceleration, self.max_speed * 0.7)
        else:
            self.mission_state = "approach"
            self.bomb_target = self.target
            self._calculate_approach_vector()

    def _calculate_approach_vector(self):
        if self.bomb_target is None:
            return
            
        target_x, target_z = self.bomb_target
        
        approach_distance = 25
        
        current_angle = math.atan2(target_z - self.z, target_x - self.x)
        approach_angle = current_angle + math.pi  
        
        approach_x = target_x + approach_distance * math.cos(approach_angle)
        approach_z = target_z + approach_distance * math.sin(approach_angle)
        
        self.approach_vector = (approach_x, approach_z)

    def _approach_target(self):
        if self.approach_vector is None:
            self.mission_state = "patrol"
            return
            
        approach_x, approach_z = self.approach_vector
        
        self._turn_towards_point(approach_x, approach_z)
        
        self.speed = min(self.speed + self.acceleration, self.max_speed)
        
        distance_to_approach = math.sqrt((self.x - approach_x)**2 + (self.z - approach_z)**2)
        if distance_to_approach < 5.0:
            self.mission_state = "bomb_run"
            self.has_dropped_bomb = False

    def _bomb_run(self):
        if self.bomb_target is None:
            self.mission_state = "egress"
            return
            
        target_x, target_z = self.bomb_target
        
        self._turn_towards_point(target_x, target_z, aggressive=True)
        self.speed = min(self.speed + self.acceleration, self.max_speed)
        
        distance_to_target = math.sqrt((self.x - target_x)**2 + (self.z - target_z)**2)
        
        if distance_to_target <= self.bomb_release_distance and not self.has_dropped_bomb:
            bomb(self.x, self.z, self.y + 0.5, self.team, target_x, target_z, self.damage)
            self.has_dropped_bomb = True
            
            egress_distance = 20
            current_heading = math.radians(self.rotation)
            egress_x = self.x + egress_distance * math.sin(-current_heading)
            egress_z = self.z + egress_distance * math.cos(current_heading - math.pi)
            self.egress_target = (egress_x, egress_z)
            
            self.mission_state = "egress"

    def _egress_behavior(self):
        if self.egress_target is None:
            self.mission_state = "rtb"
            return
            
        egress_x, egress_z = self.egress_target
        
        self._turn_towards_point(egress_x, egress_z)
        self.speed = min(self.speed + self.acceleration * 1.5, self.max_speed)
        
        distance_to_egress = math.sqrt((self.x - egress_x)**2 + (self.z - egress_z)**2)
        if distance_to_egress < 3.0:
            self.mission_state = "rtb"

    def _return_to_base(self):
        rtb_x, rtb_z = self.rtb_target
        
        self._turn_towards_point(rtb_x, rtb_z)
        self.speed = max(self.speed - self.acceleration * 0.5, self.max_speed * 0.8)
        
        distance_to_base = math.sqrt((self.x - rtb_x)**2 + (self.z - rtb_z)**2)
        if distance_to_base < 5.0:
            self.mission_state = "patrol"
            self.target = None
            self.bomb_target = None
            self.approach_vector = None
            self.egress_target = None
            self.has_dropped_bomb = False

    def _turn_towards_point(self, target_x, target_z, aggressive=False):
        angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
        target_rotation = (angle_to_target + 180) % 360
        current_rotation = self.rotation % 360
        
        diff = (target_rotation - current_rotation + 180) % 360 - 180
        
        max_turn = self.turn_rate * (2.0 if aggressive else 1.0)
        actual_turn = max(-max_turn, min(max_turn, diff))
        
        self.rotation = (current_rotation + actual_turn) % 360

    def _apply_movement(self):
        self.x += self.velocity[0]
        self.z += self.velocity[1]

    def __str__(self):
        return (f"Stealth Bomber: Position: ({self.x:.1f}, {self.z:.1f}), "
                f"Mission: {self.mission_state}, Speed: {self.speed:.2f}, "
                f"Target: {self.bomb_target}, Team: {self.team}")

class bomb(baseEntity):
    def __init__(self, x, z, y, player_team, target_x, target_z, damage = 10, size = 1):
        super().__init__(x, z, 1, player_team, "game_models/bomb.txt")
        self.local_vertices *= size
        self.visibility = 0.1
        self.util = True
        self.damage = damage
        self.speed = .3
        self.state = "moving"
        self.in_air = True
        self.color = (255, 255, 0)
        self.creation_time = pygame.time.get_ticks()  
        self.lifetime = 5000 
        self.real_terrain_height = 0

        self.start_pos = [x, y, z]
        self.end_pos = [target_x, 0, target_z]
        
        self.y = y
        self.rotation = (math.degrees(math.atan2(x - target_x, z - target_z)) + 180) % 360
        bullet_entities.append(self)

    def interpolate_point(start_y, end_y, percentage):
        y = start_y + (end_y - start_y) * percentage
        return y
    
    def _get_terrain_height(self, terrain_vertices):
        
        self.real_terrain_height = super()._get_terrain_height(terrain_vertices)
        current_distance = math.sqrt((self.x - self.start_pos[0])**2 + (self.z - self.start_pos[2])**2)
        total_distance = math.sqrt((self.end_pos[0] - self.start_pos[0])**2 + (self.end_pos[2] - self.start_pos[2])**2)
        percentage = min(current_distance / total_distance, 1.0) if total_distance != 0 else 1.0

        self.y = bomb.interpolate_point(self.start_pos[1], self.end_pos[1], percentage)



        return bomb.interpolate_point(self.start_pos[1], self.end_pos[1], percentage)
        
        
    def move(self, known_entities):
        self.rotation = (self.rotation + 180) % 360
        move_x = self.speed * math.sin(math.radians(-self.rotation))
        move_z = self.speed * math.cos(math.radians(self.rotation-180))

        self.rotation = (self.rotation + 180) % 360

        self.x += move_x
        self.z += move_z

        if abs(self.y - self.real_terrain_height) < 0.6:
            self._delete(known_entities)
        pass

    def _delete(self, known_entities):
        for entity in known_entities:
            if entity.team != self.team and entity.health > 0 and not entity.util and not entity.in_air:
                if abs(self.x - entity.x) < 7 and abs(self.z - entity.z) < 7:
                    entity.health -= self.damage*entity.armor



        if self in bullet_entities:
            bomb_explosion(self.x, self.z)
            bullet_entities.remove(self)





class bomb_explosion(baseEntity):
    def __init__(self, x, z):

        self.size_explosion = 5

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefix = f"{script_dir}/"
        with open(f"{self.prefix}game_models/explosionTemp.txt", "w") as file:
            for _ in range(40):
                temp_x = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                temp_y = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                temp_z = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                file.write(f"{temp_x:.4f} {temp_y:.4f} {temp_z:.4f}\n")


        super().__init__(x, z, 1, None, "game_models/explosionTemp.txt")
        self.util = True
        self.time_alive = 0

        
        explosive_entities.append(self)

    def draw(self, ctx, line_prog, terrain_heights, camera_transform, scale):
        y = self._get_terrain_height(terrain_heights)
        self.y = y

        rotation_matrix = self._get_rotation_matrix(self.rotation)
        rotated_vertices = np.dot(self.local_vertices, rotation_matrix.T)
        translated_vertices = rotated_vertices + np.array([self.x, y, self.z])

        edge_vertices = []
        for start_idx, end_idx in self.edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])

        transformed_vertices = camera_transform(np.array(edge_vertices))

        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()
            render_with_hover(ctx, transformed_vertices, (255, 165, 0), scale, line_prog, mouse_pos)


   
    def move(self):

        super().__init__(self.x, self.z, 1, None, "game_models/explosionTemp.txt")
        self.time_alive += 1

        if self.time_alive > 20:
            self._delete()
            return
    def _delete(self):
        if self in explosive_entities:
            explosive_entities.remove(self)


class city(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 1000, player_team, "game_models/city.txt")
        self.visibility = 10
        self.unit_type = "building"


    def _get_terrain_height(self, terrain_vertices):
        return super()._get_terrain_height(terrain_vertices) - 2.5




class sniper(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 5, player_team, "game_models/sniper.txt")
        self.range = 10
        self.speed = 0.03
        self.damage = 5
        self.visibility = .5
        self.armor = 1
        self.danger = 4
        self.accuracy = .98
        self.supply = 100
        self.max_supply = self.supply

        self.attack_speed = 50
        self.rotation += 180
        self.target = (x, z)
        self.state = "idle"
        self.unit_type = "attack"
    
    def _get_terrain_height(self, terrain_vertices):
        return super()._get_terrain_height(terrain_vertices) - 1

    def move(self, known_entities, all_entities):
        # Always search for targets first
        self._find_target(known_entities)
        
        # Update state based on current situation
        if self.target_entity is not None:
            # Check if target is still in range
            if (abs(self.x - self.target_entity.x) < self.range and 
                abs(self.z - self.target_entity.z) < self.range and 
                self.target_entity in known_entities):
                self.state = "attacking"

        elif self.target is not None:
            self.state = "moving"
        else:
            self.state = "idle"
        
        # Movement logic - now happens in both moving and attacking states if we have a target location
        if self.target is not None and (self.state == "moving" or (self.state == "attacking" and self.target_entity is not None)):
            target_x, target_z = self.target
            
            if abs(self.x - target_x) < 0.5 and abs(self.z - target_z) < 0.5:
                if self.target_entity is None:
                    self.state = "idle"
                    self.target = None
            else:
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_rotation = (angle_to_target + 180) % 360
                
                diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                self.rotation = (self.rotation + diff * 0.1) % 360

                move_x = self.speed * math.sin(math.radians(-self.rotation))
                move_z = self.speed * math.cos(math.radians(self.rotation-180))
                self.x += move_x
                self.z += move_z

        # Handle attack logic if we're in attacking state
        if self.state == "attacking":
            if self.target_entity is None or self.target_entity not in known_entities:
                # Lost the target, reset state
                self.target_entity = None
                self.state = "idle"
                return
            
            # Fire when ready
            self.attack_count += 1
            if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                self.shoot(self.target_entity)
                    
    def _find_target(self, known_entities):
        """Find the highest danger target within range"""
        if not known_entities:
            return
            
        # Clear target if it's no longer valid
        if self.target_entity and (
            self.target_entity not in known_entities or 
            self.target_entity.health <= 0 or
            self.target_entity.team == self.team or self.target_entity.in_air
        ):
            self.target_entity = None
        
        # Look for new targets
        potential_targets = []
        for entity in known_entities:
            if (entity.team != self.team and 
                entity.health > 0 and 
                not entity.util and
                not entity.in_air):
                
                # Calculate distance to target
                distance = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                
                if distance < self.range:
                    potential_targets.append((entity, entity.danger, distance))

        # Sort targets by danger (primary) and distance (secondary)
        potential_targets.sort(key=lambda x: (-x[1], x[2]))
        
        if potential_targets:
            # Take the highest priority target
            new_target = potential_targets[0][0]
            
            # If we have a new target or no current target
            if not self.target_entity or new_target.danger > self.target_entity.danger:
                self.target_entity = new_target
                self.attack_count = 0





class antiAir(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 20, player_team, "game_models/antiAir.txt")
        self.local_vertices[:, 0] += .6
        self.range = 40
        self.speed = 0
        self.damage = 10
        self.visibility = 1
        self.armor = 1
        self.danger = 3
        self.accuracy = .75
        self.supply = 5000
        self.max_supply = self.supply

        self.attack_speed = 20
        self.rotation += 180
        self.target = (x, z)
        self.state = "idle"
        self.can_target_air = True
        self.unit_type = "defense"
  
    def move(self, known_entities, all_entities):
        self._find_target(known_entities)
        
        if self.target_entity is not None:
            if (abs(self.x - self.target_entity.x) < self.range and 
                abs(self.z - self.target_entity.z) < self.range and 
                self.target_entity in known_entities):
                self.state = "attacking"
            else:
                self.target_entity = None
                self.state = "idle"
        else:
            self.state = "idle"

        if self.state == "attacking":
            if self.target_entity is None or self.target_entity not in known_entities:
                self.target_entity = None
                self.state = "idle"
                return
            
            target_angle = (math.degrees(math.atan2(self.target_entity.x - self.x, self.target_entity.z - self.z)) + 270) % 360
            delta = (target_angle - self.rotation + 540) % 360 - 180
            self.rotation = (self.rotation + delta * 0.1) % 360

            self.attack_count += 1
            if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                self.shoot(self.target_entity)
        else:
            self.rotation = (self.rotation + 1) % 360

    def shoot(self, target):
        self.supply -= 1
        antiAirShell(self.x, self.z, self.y, self.team, target, self.accuracy, self.damage)

    def _find_target(self, known_entities):
        if not known_entities:
            return
            
        if self.target_entity and (
            self.target_entity not in known_entities or 
            self.target_entity.health <= 0 or
            self.target_entity.team == self.team
        ):
            self.target_entity = None
        
        potential_targets = []
        for entity in known_entities:
            if (entity.team != self.team and 
                entity.health > 0 and 
                not entity.util and
                entity.in_air):
                
                distance = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                
                if distance < self.range:
                    potential_targets.append((entity, entity.danger, distance))

        potential_targets.sort(key=lambda x: (-x[1], x[2]))
        
        if potential_targets:
            new_target = potential_targets[0][0]
            
            if not self.target_entity or new_target.danger > self.target_entity.danger:
                self.target_entity = new_target
                self.attack_count = 0
            
    def _get_terrain_height(self, terrain_vertices):
        return super()._get_terrain_height(terrain_vertices) - 1



class antiAirShell(baseEntity):
    def __init__(self, x, z, y, player_team, target: baseEntity, accuracy = 1.0, damage = 10):
        super().__init__(x, z, 1, player_team, "game_models/bullet.txt")
        self.visibility = 0.1
        self.util = True
        self.damage = damage
        self.speed = .5
        self.state = "moving"
        self.in_air = True
        self.color = (255, 255, 0)
        self.target = target
        self.creation_time = pygame.time.get_ticks()  
        self.lifetime = 2000 
        bullet_entities.append(self)

        self.start_pos = [x, y, z]
        self.end_pos = [target.x, target.y, target.z]
        
        self.y = y

        
        if target:
            angle_to_target = math.degrees(math.atan2(target.x - x, target.z - z))
            self.rotation = (angle_to_target + 180 + ((1.0 - accuracy) * random.randint(-45, 45))) % 360
    
    def _get_terrain_height(self, terrain_vertices):
        dy =  self.end_pos[1] - self.start_pos[1]
        self.percentage_distance_to_target()
        return self.start_pos[1] + dy * self.percentage_distance_to_target()
    
    def percentage_distance_to_target(self):
        if self.target:
            target_distance = math.sqrt((self.target.x - self.start_pos[0])**2 + (self.target.z - self.start_pos[2])**2)
            current_distance = math.sqrt((self.x - self.start_pos[0])**2 + (self.z - self.start_pos[2])**2)
            return current_distance / target_distance if target_distance != 0 else 1.0
        return 1.0




    def move(self, known_entities):
        current_time = pygame.time.get_ticks()
        if current_time - self.creation_time > self.lifetime:
            self._delete()
            return
            
        if self.state == "moving":

                
            move_x = self.speed * math.sin(math.radians(-self.rotation))
            move_z = self.speed * math.cos(math.radians(self.rotation-180))
            
            self.x += move_x
            self.z += move_z
            
            
            self._check_collision(known_entities)
    
    def _check_collision(self, known_entities):
        for entity in known_entities:
            if entity.team == self.team or entity.util or entity is self:
                continue
                
            distance = math.sqrt((self.x - entity.x)**2 + (self.y - entity.y)**2 + (self.z - entity.z)**2)       

            if distance < 1.5 or (self.y - self.target.y) < -1:  
                self._delete()
                break
    
    def _delete(self):
        if self in bullet_entities:     
            explosion_air(self.x, self.z, self.y)       
            bullet_entities.remove(self)

            if np.sqrt((self.x - self.target.x)**2 + (self.z - self.target.z)**2) < 2:
                self.target.health -= self.damage*self.target.armor




class explosion_air(baseEntity):
    def __init__(self, x, z, y):

        self.size_explosion = 0.5

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefix = f"{script_dir}/"
        with open(f"{self.prefix}game_models/explosionTemp.txt", "w") as file:
            for _ in range(40):
                temp_x = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                temp_y = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                temp_z = round(random.uniform(-self.size_explosion, self.size_explosion), 4)
                file.write(f"{temp_x:.4f} {temp_y:.4f} {temp_z:.4f}\n")

        super().__init__(x, z, 1, None, "game_models/explosionTemp.txt")
        self.util = True
        self.time_alive = 0

        self.y = y
        self.ogY = y
        

        explosive_entities.append(self)

    def draw(self, ctx, line_prog, terrain_heights, camera_transform, scale):

        rotation_matrix = self._get_rotation_matrix(self.rotation)
        rotated_vertices = np.dot(self.local_vertices, rotation_matrix.T)
        translated_vertices = rotated_vertices + np.array([self.x, self.y, self.z])

        edge_vertices = []
        for start_idx, end_idx in self.edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])

        transformed_vertices = camera_transform(np.array(edge_vertices))

        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()
            render_with_hover(ctx, transformed_vertices, (255, 165, 0), scale, line_prog, mouse_pos)

    def _get_terrain_height(self, terrain_vertices):
        return self.ogY
   
    def move(self):
        self.y = self.ogY
        self.time_alive += 1
        self.size_explosion = self.size * (1 - math.exp(-0.2 * self.time_alive))
        if self.time_alive > 10:
            self._delete()
            return
    def _delete(self):
        if self in explosive_entities:
            explosive_entities.remove(self)
    


class tHelicopter(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 50, player_team, "game_models/helicopter/helicopter.txt")
        self.blade_vertices, self.blade_edges = self._initialize_shape("game_models/helicopter/blade.txt")
        self.blade_offset = -.3
        self.range = 10
        self.max_speed = 0.08
        self.current_speed = 0  
        self.acceleration = 0.002  
        self.deceleration = 0.004
        self.damage = 0
        self.armor = 1
        self.danger = 5
        self.accuracy = 0.9
        self.supply = 20
        self.max_supply = self.supply

        self.blade_rotation = 0
        self.attack_speed = 120
        self.target = (x, z)
        self.state = "idle"
        self.unit_type = "transport"
        self.in_air = True
        self.y = 0

        self.y_off_ground = 0
        self.blade_speed = 0
        self.max_blade_speed = 15
        self.blade_acceleration = 0.3
        self.blade_deceleration = 0.1
        
        self.velocity_x = 0
        self.velocity_z = 0
        self.max_rotation_speed = 3
        
        self.target_altitude = 0
        self.altitude_speed = 0
        self.max_altitude_speed = 0.15
        self.altitude_acceleration = 0.008

        self.units_carried = []

        self.blade_edge_pairs = [(self.blade_vertices[start_idx], self.blade_vertices[end_idx])
                                 for start_idx, end_idx in self.blade_edges]

    def move(self, known_entities, all_entities):
        self.rotation += 180

        if self.y_off_ground == 0:
            self.in_air = False
        else:
            self.in_air = True




        if self.target is not None or self.state == "moving":
            if self.blade_speed < self.max_blade_speed:
                self.blade_speed += self.blade_acceleration
                self.blade_speed = min(self.blade_speed, self.max_blade_speed)
        else:
            if self.blade_speed > 0:
                self.blade_speed -= self.blade_deceleration
                self.blade_speed = max(self.blade_speed, 0)

        self.blade_rotation = (self.blade_rotation + self.blade_speed) % 360

        if self.target is not None:
            self.state = "moving"
            self.target_altitude = 10 
        else:
            self.state = "idle"
            self.target_altitude = 0 

        altitude_diff = self.target_altitude - self.y_off_ground
        if abs(altitude_diff) > 0.1:
            if altitude_diff > 0: 
                self.altitude_speed += self.altitude_acceleration
            else: 
                self.altitude_speed -= self.altitude_acceleration
            
            self.altitude_speed = max(-self.max_altitude_speed, 
                                    min(self.altitude_speed, self.max_altitude_speed))
            
            self.y_off_ground += self.altitude_speed
            self.y_off_ground = max(0, self.y_off_ground) 
        else:
            self.altitude_speed *= 0.9
            if abs(self.altitude_speed) < 0.01:
                self.altitude_speed = 0
                self.y_off_ground = self.target_altitude

        if self.target is not None and self.state == "moving":
            if self.y_off_ground > 8:
                target_x, target_z = self.target

                if abs(self.x - target_x) < 0.5 and abs(self.z - target_z) < 0.5:
                    if self.target_entity is None:
                        self.state = "idle"
                        self.target = None
                        self.current_speed *= 0.95
                else:
                    angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                    target_rotation = (angle_to_target + 180) % 360

                    diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                    
                    max_rotation_this_frame = self.max_rotation_speed
                    if abs(diff) > max_rotation_this_frame:
                        diff = max_rotation_this_frame if diff > 0 else -max_rotation_this_frame
                    
                    self.rotation = (self.rotation + diff * 0.3) % 360

                    if self.current_speed < self.max_speed:
                        self.current_speed += self.acceleration
                        self.current_speed = min(self.current_speed, self.max_speed)

                    move_x = self.current_speed * math.sin(math.radians(-self.rotation))
                    move_z = self.current_speed * math.cos(math.radians(self.rotation - 180))
                    
                    self.velocity_x = self.velocity_x * 0.8 + move_x * 0.2
                    self.velocity_z = self.velocity_z * 0.8 + move_z * 0.2
                    
                    self.x += self.velocity_x
                    self.z += self.velocity_z
            else:
                target_x, target_z = self.target
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_rotation = (angle_to_target + 180) % 360

                diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                self.rotation = (self.rotation + diff * 0.01) % 360

        if self.target is None and self.state == "idle":
            if self.current_speed > 0:
                self.current_speed -= self.deceleration
                self.current_speed = max(self.current_speed, 0)
                
                move_x = self.current_speed * math.sin(math.radians(-self.rotation))
                move_z = self.current_speed * math.cos(math.radians(self.rotation - 180))
                
                self.velocity_x = self.velocity_x * 0.9 + move_x * 0.1
                self.velocity_z = self.velocity_z * 0.9 + move_z * 0.1
                
                self.x += self.velocity_x
                self.z += self.velocity_z
            else:
                self.velocity_x *= 0.95
                self.velocity_z *= 0.95
                
                if abs(self.velocity_x) < 0.001:
                    self.velocity_x = 0
                if abs(self.velocity_z) < 0.001:
                    self.velocity_z = 0

        self.rotation -= 180

    def draw(self, ctx, line_prog, terrain_vertices, camera_transform, scale):
        super().draw(ctx, line_prog, terrain_vertices, camera_transform, scale)
        y = self._get_terrain_height(terrain_vertices)

        blade_rotation_matrix = self._get_rotation_matrix_y(self.blade_rotation)
        spinning_blade_vertices = np.dot(self.blade_vertices, blade_rotation_matrix.T)
        
        front_offset = .8
        offset_blade_vertices = spinning_blade_vertices + np.array([0, self.blade_offset, front_offset])
        
        helicopter_rotation_matrix = self._get_rotation_matrix(self.rotation)
        rotated_blade_vertices = np.dot(offset_blade_vertices, helicopter_rotation_matrix.T)
        
        translated_vertices = rotated_blade_vertices + np.array([
            self.x,
            y,
            self.z
        ])

        edge_vertices = []
        for start_idx, end_idx in self.blade_edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])

        transformed_vertices = camera_transform(np.array(edge_vertices))

        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()
            render_with_hover(ctx, transformed_vertices, self.color, scale, line_prog, mouse_pos)

    def _get_rotation_matrix_y(self, angle_degrees):
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        return np.array([
            [cos_a,  0, sin_a],
            [0,      1, 0    ],
            [-sin_a, 0, cos_a]
        ])



    def _get_terrain_height(self, terrain_vertices):
        if self.y_off_ground == 0:
            return super()._get_terrain_height(terrain_vertices)
        else:
            return ((super()._get_terrain_height(terrain_vertices) - self.y_off_ground) + self.y * 99) / 100







class attHelicopter(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 50, player_team, "game_models/helicopter/aHelicopter.txt")
        self.blade_vertices, self.blade_edges = self._initialize_shape("game_models/helicopter/blade.txt")
        self.blade_offset = -.3
        self.range = 25
        self.max_speed = 0.15
        self.current_speed = 0  
        self.acceleration = 0.002  
        self.deceleration = 0.004
        self.damage = 1
        self.armor = 0.75
        self.danger = 10
        self.accuracy = 0.9
        self.supply = 5000
        self.max_supply = self.supply

        self.blade_rotation = 0
        self.attack_speed = 10
        self.target = (x, z)
        self.state = "idle"
        self.unit_type = "attack"
        self.can_target_air = True
        self.in_air = True
        self.y = 0

        self.y_off_ground = 0
        self.blade_speed = 0
        self.max_blade_speed = 15
        self.blade_acceleration = 0.3
        self.blade_deceleration = 0.1
        
        self.velocity_x = 0
        self.velocity_z = 0
        self.max_rotation_speed = 3
        
        self.target_altitude = 0
        self.altitude_speed = 0
        self.max_altitude_speed = 0.15
        self.altitude_acceleration = 0.008

        self.units_carried = []

        # Add deceleration zone parameters
        self.deceleration_distance = 15  # Start slowing down when 15 units away
        self.min_approach_speed = 0.02   # Minimum speed when approaching target

        self.blade_edge_pairs = [(self.blade_vertices[start_idx], self.blade_vertices[end_idx])
                                 for start_idx, end_idx in self.blade_edges]

    def move(self, known_entities, all_entities):
        self.rotation += 180

        if self.y_off_ground == 0:
            self.in_air = False
        else:
            self.in_air = True

            self._find_target(known_entities)

            if self.target_entity is not None:
                self.attack_count += 1
                if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                    self.shoot(self.target_entity)


        if self.target is not None or self.state == "moving":
            if self.blade_speed < self.max_blade_speed:
                self.blade_speed += self.blade_acceleration
                self.blade_speed = min(self.blade_speed, self.max_blade_speed)
            
            if self.target != None:
                dist = math.sqrt((self.x - self.target[0])**2 + (self.z - self.target[1])**2)

                if dist < 1:
                    self.target = None

        else:
            if self.blade_speed > 0:
                self.blade_speed -= self.blade_deceleration
                self.blade_speed = max(self.blade_speed, 0)

        self.blade_rotation = (self.blade_rotation + self.blade_speed) % 360

        if self.target is not None:
            self.state = "moving"
            self.target_altitude = 10 
        else:
            self.current_speed = 0




        altitude_diff = self.target_altitude - self.y_off_ground
        if abs(altitude_diff) > 0.1:
            if altitude_diff > 0: 
                self.altitude_speed += self.altitude_acceleration
            else: 
                self.altitude_speed -= self.altitude_acceleration
            
            self.altitude_speed = max(-self.max_altitude_speed, 
                                    min(self.altitude_speed, self.max_altitude_speed))
            
            self.y_off_ground += self.altitude_speed
            self.y_off_ground = max(0, self.y_off_ground) 
        else:
            self.altitude_speed *= 0.9
            if abs(self.altitude_speed) < 0.01:
                self.altitude_speed = 0
                self.y_off_ground = self.target_altitude

        if self.target is not None and self.state == "moving":
            if self.y_off_ground > 8:
                target_x, target_z = self.target
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_rotation = (angle_to_target + 180) % 360

                diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                
                max_rotation_this_frame = self.max_rotation_speed
                if abs(diff) > max_rotation_this_frame:
                    diff = max_rotation_this_frame if diff > 0 else -max_rotation_this_frame
                
                self.rotation = (self.rotation + diff * 0.3) % 360

                # Calculate distance to target for deceleration
                dist_to_target = math.sqrt((self.x - target_x)**2 + (self.z - target_z)**2)
                
                # Calculate target speed based on distance
                if dist_to_target <= self.deceleration_distance:
                    # Linear interpolation for smooth deceleration
                    speed_ratio = max(dist_to_target / self.deceleration_distance, 
                                    self.min_approach_speed / self.max_speed)
                    target_speed = self.max_speed * speed_ratio
                else:
                    target_speed = self.max_speed

                # Adjust current speed towards target speed
                if self.current_speed < target_speed:
                    self.current_speed += self.acceleration
                    self.current_speed = min(self.current_speed, target_speed)
                elif self.current_speed > target_speed:
                    self.current_speed -= self.deceleration
                    self.current_speed = max(self.current_speed, target_speed)

                move_x = self.current_speed * math.sin(math.radians(-self.rotation))
                move_z = self.current_speed * math.cos(math.radians(self.rotation - 180))
                
                self.velocity_x = self.velocity_x * 0.8 + move_x * 0.2
                self.velocity_z = self.velocity_z * 0.8 + move_z * 0.2
                
                self.x += self.velocity_x
                self.z += self.velocity_z
            else:
                target_x, target_z = self.target
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_rotation = (angle_to_target + 180) % 360

                diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                self.rotation = (self.rotation + diff * 0.01) % 360

        if self.target is None and self.state == "idle":
            if self.current_speed > 0:
                self.current_speed -= self.deceleration
                self.current_speed = max(self.current_speed, 0)
                
                move_x = self.current_speed * math.sin(math.radians(-self.rotation))
                move_z = self.current_speed * math.cos(math.radians(self.rotation - 180))
                
                self.velocity_x = self.velocity_x * 0.9 + move_x * 0.1
                self.velocity_z = self.velocity_z * 0.9 + move_z * 0.1
                
                self.x += self.velocity_x
                self.z += self.velocity_z


        self.rotation -= 180

    def draw(self, ctx, line_prog, terrain_vertices, camera_transform, scale):
        super().draw(ctx, line_prog, terrain_vertices, camera_transform, scale)
        y = self._get_terrain_height(terrain_vertices)

        blade_rotation_matrix = self._get_rotation_matrix_y(self.blade_rotation)
        spinning_blade_vertices = np.dot(self.blade_vertices, blade_rotation_matrix.T)
        
        front_offset = .8
        offset_blade_vertices = spinning_blade_vertices + np.array([0, self.blade_offset, front_offset])
        
        helicopter_rotation_matrix = self._get_rotation_matrix(self.rotation)
        rotated_blade_vertices = np.dot(offset_blade_vertices, helicopter_rotation_matrix.T)
        
        translated_vertices = rotated_blade_vertices + np.array([
            self.x,
            y,
            self.z
        ])

        edge_vertices = []
        for start_idx, end_idx in self.blade_edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])

        transformed_vertices = camera_transform(np.array(edge_vertices))

        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()
            render_with_hover(ctx, transformed_vertices, self.color, scale, line_prog, mouse_pos)

    def _get_rotation_matrix_y(self, angle_degrees):
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        return np.array([
            [cos_a,  0, sin_a],
            [0,      1, 0    ],
            [-sin_a, 0, cos_a]
        ])



    def _get_terrain_height(self, terrain_vertices):
        if self.y_off_ground == 0:
            return super()._get_terrain_height(terrain_vertices)
        else:
            return ((super()._get_terrain_height(terrain_vertices) - self.y_off_ground) + self.y * 99) / 100




    def _find_target(self, known_entities):
        if not known_entities:
            self.target_entity = None
            return
            
        if self.target_entity and (
            self.target_entity not in known_entities or 
            self.target_entity.health <= 0 or
            self.target_entity.team == self.team
        ):
            self.target_entity = None
        
        potential_targets = []
        for entity in known_entities:
            if (entity.team != self.team and 
                entity.health > 0 and 
                not entity.util):
                
                distance = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                
                if distance < self.range:
                    potential_targets.append((entity, entity.danger, distance))

        potential_targets.sort(key=lambda x: (-x[1], x[2]))
        
        if potential_targets:
            new_target = potential_targets[0][0]
            
            if not self.target_entity or new_target.danger > self.target_entity.danger:
                self.target_entity = new_target
                self.attack_count = 0





class bomber(baseEntity):
    def __init__(self, x, z, player_team, base_cords):
        super().__init__(x, z, 100, player_team, "game_models/bigBomber.txt")
        self.visibility = 1.50
        self.speed = 0.3
        self.damage = 20
        self.danger = 7
        self.in_air = True
        self.unit_type = "bomber"
        self.can_set_target = True
        
        self.velocity = np.array([0.0, 0.0])  
        self.max_speed = 0.4
        self.acceleration = 0.01
        self.turn_rate = 1.5
        self.min_speed = 0.15
        
        self.mission_state = "patrol" 
        self.approach_vector = None
        self.bomb_target = None
        self.egress_target = None
        if not player_team:
            self.rtb_target = base_cords[0]
        else:
            self.rtb_target = base_cords[1]
        
        self.base_cords = base_cords
        
        self.bomb_release_distance = 30.0
        self.has_dropped_bomb = False
        
        self.patrol_center = self.rtb_target
        self.patrol_radius = 25
        self.patrol_angle = 0
        self.patrol_speed = 0.02

        self.bomb_drop = 0
        self.time_between = 0 

    def _get_terrain_height(self, terrain_vertices):
        return -20

    def move(self, known_entities, all_entities):
        if not self.team:
            self.rtb_target = self.base_cords[0]
        else:
            self.rtb_target = self.base_cords[1]
        self.patrol_center = self.rtb_target


        self._update_flight_physics()

        if self.mission_state == "patrol":
            self._patrol_behavior()
        elif self.mission_state == "approach":
            self._approach_target()
        elif self.mission_state == "bomb_run":
            self._bomb_run()
        elif self.mission_state == "egress":
            self._egress_behavior()
        elif self.mission_state == "rtb":
            self._return_to_base()
            
        self._apply_movement()

    def _update_flight_physics(self):

        desired_vx = self.speed * math.sin(math.radians(-self.rotation))
        desired_vz = self.speed * math.cos(math.radians(self.rotation - 180))
        desired_velocity = np.array([desired_vx, desired_vz])
        
        self.velocity = self.velocity * 0.9 + desired_velocity * 0.1
        
        current_speed = np.linalg.norm(self.velocity)
        if current_speed < self.min_speed and current_speed > 0:
            self.velocity = (self.velocity / current_speed) * self.min_speed

    def _patrol_behavior(self):
        if self.target is None:
            self.patrol_angle += self.patrol_speed
            
            patrol_x = self.patrol_center[0] + self.patrol_radius * math.cos(self.patrol_angle)
            patrol_z = self.patrol_center[1] + self.patrol_radius * math.sin(self.patrol_angle)
            
            self._turn_towards_point(patrol_x, patrol_z)
            self.speed = min(self.speed + self.acceleration, self.max_speed * 0.7)
        else:
            self.mission_state = "approach"
            self.bomb_target = self.target
            self._calculate_approach_vector()

    def _calculate_approach_vector(self):
        if self.bomb_target is None:
            return
            
        target_x, target_z = self.bomb_target
        
        approach_distance = 25
        
        current_angle = math.atan2(target_z - self.z, target_x - self.x)
        approach_angle = current_angle + math.pi  
        
        approach_x = target_x + approach_distance * math.cos(approach_angle)
        approach_z = target_z + approach_distance * math.sin(approach_angle)
        
        self.approach_vector = (approach_x, approach_z)

    def _approach_target(self):
        if self.approach_vector is None:
            self.mission_state = "patrol"
            return
            
        approach_x, approach_z = self.approach_vector
        
        self._turn_towards_point(approach_x, approach_z)
        
        self.speed = min(self.speed + self.acceleration, self.max_speed)
        
        distance_to_approach = math.sqrt((self.x - approach_x)**2 + (self.z - approach_z)**2)
        if distance_to_approach < 5.0:
            self.mission_state = "bomb_run"
            self.has_dropped_bomb = False

    def draw(self, ctx, line_prog, terrain_heights, camera_transform, scale):
        self.rotation += 180
        super().draw(ctx, line_prog, terrain_heights, camera_transform, scale)
        self.rotation -= 180

    def _bomb_run(self):
        self.time_between += 1
        if self.bomb_target is None:
            self.mission_state = "egress"
            return
            
        target_x, target_z = self.bomb_target
        

        
        distance_to_target = math.sqrt((self.x - target_x)**2 + (self.z - target_z)**2)
        
        if distance_to_target >= self.bomb_release_distance:
            self._turn_towards_point(target_x, target_z, aggressive=True)
            self.speed = min(self.speed + self.acceleration, self.max_speed)

        if distance_to_target <= self.bomb_release_distance and not self.has_dropped_bomb and self.time_between > 10:
            dumbBomb(self.x, self.z, self.y + 0.5, self.team, self.rotation+180, self.damage, .5)
            

            if self.bomb_drop > 4:
                self.has_dropped_bomb = True
                egress_distance = 20
                current_heading = math.radians(self.rotation)
                egress_x = self.x + egress_distance * math.sin(-current_heading)
                egress_z = self.z + egress_distance * math.cos(current_heading - math.pi)
                self.egress_target = (egress_x, egress_z)
                
                self.mission_state = "egress"
            else:
                self.bomb_drop += 1
                self.time_between = 0

    def _egress_behavior(self):
        if self.egress_target is None:
            self.mission_state = "rtb"
            return
            
        egress_x, egress_z = self.egress_target
        
        self._turn_towards_point(egress_x, egress_z)
        self.speed = min(self.speed + self.acceleration * 1.5, self.max_speed)
        
        distance_to_egress = math.sqrt((self.x - egress_x)**2 + (self.z - egress_z)**2)
        if distance_to_egress < 3.0:
            self.mission_state = "rtb"

    def _return_to_base(self):
        rtb_x, rtb_z = self.rtb_target
        
        self._turn_towards_point(rtb_x, rtb_z)
        self.speed = max(self.speed - self.acceleration * 0.5, self.max_speed * 0.8)
        
        distance_to_base = math.sqrt((self.x - rtb_x)**2 + (self.z - rtb_z)**2)
        if distance_to_base < 5.0:
            self.bomb_drop = 0
            self.mission_state = "patrol"
            self.target = None
            self.bomb_target = None
            self.approach_vector = None
            self.egress_target = None
            self.has_dropped_bomb = False

    def _turn_towards_point(self, target_x, target_z, aggressive=False):
        angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
        target_rotation = (angle_to_target + 180) % 360
        current_rotation = self.rotation % 360
        
        diff = (target_rotation - current_rotation + 180) % 360 - 180
        
        max_turn = self.turn_rate * (2.0 if aggressive else 1.0)
        actual_turn = max(-max_turn, min(max_turn, diff))
        
        self.rotation = (current_rotation + actual_turn) % 360

    def _apply_movement(self):
        self.x += self.velocity[0]
        self.z += self.velocity[1]

    def __str__(self):
        return (f"Stealth Bomber: Position: ({self.x:.1f}, {self.z:.1f}), "
                f"Mission: {self.mission_state}, Speed: {self.speed:.2f}, "
                f"Target: {self.bomb_target}, Team: {self.team}")
    




class dumbBomb(baseEntity):
    def __init__(self, x, z, y, player_team, rot, damage = 10, size = 1):
        super().__init__(x, z, 1, player_team, "game_models/bomb.txt")
        self.local_vertices *= size
        self.visibility = 0.1
        self.util = True
        self.damage = damage
        self.speed = .3
        self.state = "moving"
        self.in_air = True
        self.color = (255, 255, 0)
        self.creation_time = pygame.time.get_ticks()  
        self.lifetime = 5000 
        self.real_terrain_height = 0
        self.y_vel = 0


        
        self.y = y
        self.rotation = rot
        bullet_entities.append(self)


    def _get_terrain_height(self, terrain_vertices):
        
        self.real_terrain_height = super()._get_terrain_height(terrain_vertices)

        self.y_vel += 0.01

        return self.y + self.y_vel
        
        
    def move(self, known_entities):
        self.rotation = (self.rotation + 180) % 360
        move_x = self.speed * math.sin(math.radians(-self.rotation))
        move_z = self.speed * math.cos(math.radians(self.rotation-180))

        self.rotation = (self.rotation + 180) % 360

        self.x += move_x
        self.z += move_z

        if abs(self.y - self.real_terrain_height) < 0.6:
            self._delete(known_entities)
        pass

    def _delete(self, known_entities):
        for entity in known_entities:
            if entity.team != self.team and entity.health > 0 and not entity.util and not entity.in_air:
                if abs(self.x - entity.x) < 7 and abs(self.z - entity.z) < 7:
                    entity.health -= self.damage*entity.armor



        if self in bullet_entities:
            bomb_explosion(self.x, self.z)
            bullet_entities.remove(self)



class cactus(baseEntity):
    def __init__(self, x, z, health, player_team):
        super().__init__(x, z, health, player_team, f"game_models/cactus{random.randint(1, 3)}.txt")
        self.rotation = random.randint(0, 180)
        self.visibility = 10000
        self.color = (0, 100, 0)
        self.util = True
    
    def _get_terrain_height(self, terrain_vertices):
        return super()._get_terrain_height(terrain_vertices) - 1.5

    def move(self, _, not_Used):
        self.state = "none"


class battleship(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 100, player_team, "game_models/battleship/base.txt")
        self.cannon_vertices, self.cannon_edges = self._initialize_shape("game_models/battleship/cannon.txt")

        self.cannon_vertices[:, 2] += 1
        self.cannon_vertices[:, 1] -= 0.45


        self.local_vertices *= 0.5
        self.range = 200
        self.max_speed = 0.08
        self.current_speed = 0  
        self.acceleration = 0.002  
        self.deceleration = 0.004
        self.attack_speed = 180
        self.speed = self.max_speed
        self.damage = 100
        self.armor = 1
        self.danger = 5
        self.accuracy = 0.9
        self.supply = float('inf')
        self.max_supply = self.supply
        self.turret_rotation = 0
        
        self.cannon_offset = -2.5

        self.rotation = random.randint(0, 360)
        self.state = "idle"
        self.unit_type = "attack"
        self.in_air = False
        self.grass_capeable = False
        self.water_capeable = True

        # Add cannon edge pairs like artillery
        self.cannon_edge_pairs = [(self.cannon_vertices[start_idx], self.cannon_vertices[end_idx]) 
                                for start_idx, end_idx in self.cannon_edges]

    def _get_terrain_height(self, terrain_vertices):
        return super()._get_terrain_height(terrain_vertices) - 1.5



    def draw(self, ctx, line_prog, terrain_vertices, camera_transform, scale):
        # Draw the main battleship body
        self.rotation += 180
        super().draw(ctx, line_prog, terrain_vertices, camera_transform, scale)
        self.rotation -= 180
        
        # Draw the cannon like artillery does
        y = self._get_terrain_height(terrain_vertices)
        
        # Calculate cannon position offset relative to ship body
        body_rotation_rad = math.radians(self.rotation)
        offset_x = self.cannon_offset * math.sin(body_rotation_rad)
        offset_z = self.cannon_offset * math.cos(body_rotation_rad)
        
        # Apply cannon rotation
        cannon_rotation_matrix = self._get_rotation_matrix(self.turret_rotation)
        
        rotated_cannon_vertices = np.dot(self.cannon_vertices, cannon_rotation_matrix.T)
        
        # Translate cannon to correct position
        translated_vertices = rotated_cannon_vertices + np.array([
            self.x + offset_x, 
            y, 
            self.z + offset_z
        ])
        
        # Prepare edge vertices for rendering
        edge_vertices = []
        for start_idx, end_idx in self.cannon_edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])
        
        # Transform and render
        transformed_vertices = camera_transform(np.array(edge_vertices))
        
        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()
            render_with_hover(ctx, transformed_vertices, self.color, scale, line_prog, mouse_pos)


        transformed_vertices = camera_transform(np.array(edge_vertices))
        
        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()
            render_with_hover(ctx, transformed_vertices, self.color, scale, line_prog, mouse_pos)



    def move(self, known_entities, all_entities):
        if (self.state == "moving" or self.state == "attacking") and self.target is not None:
            target_x, target_z = self.target

            angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
            target_rotation = (angle_to_target + 180) % 360
            diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
            self.rotation = (self.rotation + diff * 0.1) % 360

            if self.current_speed < self.max_speed:
                self.current_speed += self.acceleration
                self.current_speed = min(self.current_speed, self.max_speed)

            move_x = self.current_speed * math.sin(math.radians(-self.rotation))
            move_z = self.current_speed * math.cos(math.radians(self.rotation-180))
            self.x += move_x
            self.z += move_z

            if abs(self.x - target_x) < 1.0 and abs(self.z - target_z) < 1.0:
                self.state = "idle"
                self.target = None
                self.target_entity = None
                if self.current_speed > 0:
                    self.current_speed -= self.deceleration
                    self.current_speed = max(self.current_speed, 0)

            self._find_target(known_entities)
            if self.target_entity is not None and self.target_entity not in known_entities:
                self.target_entity = None            
            if self.target_entity is not None:
                self.state = "attacking"
                self.turret_rotation = (math.degrees(math.atan2(self.target_entity.x - self.x, self.target_entity.z - self.z))) % 360
                self.attack_count += 1
                if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                    self.shoot(self.target_entity)
            else: 
                self.state = "moving"
                self.target_entity = None
        
        else:
            if self.target_entity is None:
                self._find_target(known_entities)
            elif self.target_entity is not None and self.target_entity not in known_entities:
                self.target_entity = None
            

            if self.target_entity is not None:
                self.state = "attacking"
                self.turret_rotation = (math.degrees(math.atan2(self.target_entity.x - self.x, self.target_entity.z - self.z))) % 360
                self.attack_count += 1
                if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                    self.shoot(self.target_entity)
            
            if self.current_speed > 0:
                self.current_speed -= self.deceleration
                self.current_speed = max(self.current_speed, 0)

    def _find_target(self, known_entities):
        if not known_entities:
            return
            
        if self.target_entity and (
            self.target_entity not in known_entities or 
            self.target_entity.health <= 0 or
            self.target_entity.team == self.team or self.target_entity.in_air
        ):
            self.target_entity = None
        
        potential_targets = []
        for entity in known_entities:
            if (entity.team != self.team and 
                entity.health > 0 and 
                not entity.util and
                not entity.in_air):
                
                distance = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                
                if distance < self.range:
                    potential_targets.append((entity, entity.danger, distance))

        potential_targets.sort(key=lambda x: (-x[1], x[2]))
        
        if potential_targets:
            new_target = potential_targets[0][0]
            
            if not self.target_entity or new_target.danger > self.target_entity.danger:
                self.target_entity = new_target
                self.attack_count = 0
    
    def shoot(self, target_entity):
        body_rotation_rad = math.radians(self.rotation)
        offset_x = self.cannon_offset * math.sin(body_rotation_rad)
        offset_z = self.cannon_offset * math.cos(body_rotation_rad)

        self.supply -= 1
        artillery_bullet(self.x + offset_x, self.z + offset_z, self.y-.5, self.team, target_entity, self.damage)






class mediumTank(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 200, player_team, "game_models/mediumTank/mediumTank.txt")
        self.tank_vertices, self.tank_edges = self._initialize_shape("game_models/mediumTank/cannon.txt")
        self.tank_vertices[:, 1] -= 0.8 
        self.range = 20
        self.speed = 0.05
        self.damage = 40
        self.armor = 0.5
        self.danger = 6
        self.accuracy = .95
        self.supply = 50
        self.attack_speed = 120
        self.turret_rotation = 0 
        self.rotation += 180
        self.target = (x, z)
        self.state = "idle"
        self.unit_type = "attack"
        self.max_supply = self.supply

        self.tank_edge_pairs = [(self.tank_vertices[start_idx], self.tank_vertices[end_idx]) 
                               for start_idx, end_idx in self.tank_edges]
  
    def move(self, known_entities, all_entities):
        # Always search for targets first
        self._find_target(known_entities)
        
        # Update state based on current situation
        if self.target_entity is not None:
            # Check if target is still in range
            if (abs(self.x - self.target_entity.x) < self.range and 
                abs(self.z - self.target_entity.z) < self.range and 
                self.target_entity in known_entities):
                self.state = "attacking"

        elif self.target is not None:
            self.state = "moving"
        else:
            self.state = "idle"
        
        # Handle turret rotation for any state if we have a target entity
        if self.target_entity is not None and self.target_entity in known_entities:
            # Point turret at target entity regardless of state
            target_x, target_z = self.target_entity.x, self.target_entity.z
            angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
            target_turret_rotation = (angle_to_target + 180) % 360
            
            # Smooth turret rotation
            diff = (target_turret_rotation - self.turret_rotation % 360 + 180) % 360 - 180
            self.turret_rotation = (self.turret_rotation + diff * 0.1) % 360
        
        # Movement logic - now happens in both moving and attacking states if we have a target location
        if self.target is not None and (self.state == "moving" or (self.state == "attacking" and self.target_entity is not None)):
            target_x, target_z = self.target

            
            if abs(self.x - target_x) < 0.5 and abs(self.z - target_z) < 0.5:
                if self.target_entity is None:
                    self.state = "idle"
                    self.target = None
            else:
                angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
                target_rotation = (angle_to_target + 180) % 360
                
                diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
                self.rotation = (self.rotation + diff * 0.1) % 360


                move_x = self.speed * math.sin(math.radians(-self.rotation))
                move_z = self.speed * math.cos(math.radians(self.rotation-180))
                self.x += move_x
                self.z += move_z


        # Handle attack logic if we're in attacking state
        if self.state == "attacking":
            if self.target_entity is None or self.target_entity not in known_entities:
                # Lost the target, reset state
                self.target_entity = None
                self.state = "idle"
                return
            
            # Fire when ready
            self.attack_count += 1
            if self.attack_count % self.attack_speed == 0 and self.supply > 0:
                self.shoot(self.target_entity)
                    
    def _find_target(self, known_entities):
        """Find the highest danger target within range"""
        if not known_entities:
            return
            
        # Clear target if it's no longer valid
        if self.target_entity and (
            self.target_entity not in known_entities or 
            self.target_entity.health <= 0 or
            self.target_entity.team == self.team or self.target_entity.in_air
        ):
            self.target_entity = None
        
        # Look for new targets
        potential_targets = []
        for entity in known_entities:
            if (entity.team != self.team and 
                entity.health > 0 and 
                not entity.util and
                not entity.in_air):
                
                # Calculate distance to target
                distance = math.sqrt((self.x - entity.x)**2 + (self.z - entity.z)**2)
                
                if distance < self.range:
                    potential_targets.append((entity, entity.danger, distance))
            

        # Sort targets by danger (primary) and distance (secondary)
        potential_targets.sort(key=lambda x: (-x[1], x[2]))
        
        if potential_targets:
            # Take the highest priority target
            new_target = potential_targets[0][0]
            
            # If we have a new target or no current target
            if not self.target_entity or new_target.danger > self.target_entity.danger:
                self.target_entity = new_target
                self.attack_count = 0

    def draw(self, ctx, line_prog, terrain_vertices, camera_transform, scale):
        super().draw(ctx, line_prog, terrain_vertices, camera_transform, scale)

        y = self._get_terrain_height(terrain_vertices)
        
        # Get the rotation matrix for the turret
        turret_rotation_matrix = self._get_rotation_matrix(self.turret_rotation)
        
        # Optimized rotation and translation
        rotated_cannon_vertices = np.dot(self.tank_vertices, turret_rotation_matrix.T)
        translated_vertices = rotated_cannon_vertices + np.array([self.x, y, self.z])

        # Extract vertices for edges
        edge_vertices = []
        for start_idx, end_idx in self.tank_edges:
            edge_vertices.append(translated_vertices[start_idx])
            edge_vertices.append(translated_vertices[end_idx])
            
        transformed_vertices = camera_transform(np.array(edge_vertices))
        
        if len(transformed_vertices) > 0:
            mouse_pos = pygame.mouse.get_pos()  
            render_with_hover(ctx, transformed_vertices, self.color, scale, line_prog, mouse_pos)

    def shoot(self, target):
        move_x = 1 * math.sin(math.radians(-self.turret_rotation))
        move_z = 1 * math.cos(math.radians(self.turret_rotation-180))
        self.supply -= 1
        bullet(self.x + move_x, self.z + move_z, self.y-.5, self.team, target, self.accuracy, self.damage)


class atv(baseEntity):
    def __init__(self, x, z, player_team):
        super().__init__(x, z, 75, player_team, "game_models/atv.txt")
        self.visibility = 1
        self.rotation += 180
        self.speed = 0.05
        self.unit_type = "transport"
        self.target = None
        self.state = "idle"
        self.range = 10
        self.units_carried = []
        self.water_capeable = True

        self.danger = 2

    def move(self, known_entities, all_entities):
        
        
        if self.state == "moving" and self.target is not None:
            target_x, target_z = self.target
            
            angle_to_target = math.degrees(math.atan2(target_x - self.x, target_z - self.z))
            target_rotation = (angle_to_target + 180) % 360
            diff = (target_rotation - self.rotation % 360 + 180) % 360 - 180
            self.rotation = (self.rotation + diff * 0.1) % 360
            
            move_x = self.speed * math.sin(math.radians(-self.rotation))
            move_z = self.speed * math.cos(math.radians(self.rotation-180))
            self.x += move_x
            self.z += move_z
            
            if abs(self.x - target_x) < 1.0 and abs(self.z - target_z) < 1.0:
                self.state = "idle"
                self.target = None
                self.target_entity = None

