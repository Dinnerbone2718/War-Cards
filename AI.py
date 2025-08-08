import entity as e
import time

class AI:
    def __init__(self, player_base, enemy_base, cities):
        self.possible_states = ["Defensive", "Offensive", "Investigate"]
        self.convoys = {
            "Tank Covoy": [[("attack", False, 3), ("attack", False, 3), ("attack", False, 3), ("support", False, 2)], ("Aggresive")],
            "Foot Convoy": [[("attack", False, 2), ("attack", False, 2), ("attack", False, 2), ("attack", False, 2)], ("Aggresive")],
            "Support": [[("attack", False, 3), ("support", False, 2), ("support", False, 2), ("support", False, 2)], ("Aggresive")],
        }
        
        self.remembered_positions = []
        
        self.current_convoys = []
        self.previous_team_units = []

        self.convoy_update_counter = 0

        self.target_cords = None

        self.furtherst_known_player_object = None
        
        self.max_convoy_dispersion = 3.0
        self.regrouping = False          

        self.player_base = player_base
        self.enemy_base = enemy_base
        self.cities = cities

        self.base_capture = {self.player_base : "Player",
                             self.enemy_base : "Enemy"}
        
        for city in self.cities:
            self.base_capture[city] = "None"

    def update_intel(self, known_player_objects):
        self.furtherst_known_player_object = None

        current_time = time.time()
        
        for obj in known_player_objects:
            found = False
            for i, (remembered_obj, _) in enumerate(self.remembered_positions):
                if obj == remembered_obj:
                    self.remembered_positions[i] = (obj, current_time)
                    found = True
                    break
            
            if not found:
                self.remembered_positions.append((obj, current_time))
        
        self.remembered_positions = [(obj, timestamp) for obj, timestamp in self.remembered_positions 
                                    if current_time - timestamp <= 2.0]
        
        sorted_objects = []
        for obj in known_player_objects:
            if self.furtherst_known_player_object is None or obj.z > self.furtherst_known_player_object.z:
                self.furtherst_known_player_object = obj

            for i, (remembered_obj, _) in enumerate(self.remembered_positions):
                if obj == remembered_obj:
                    sorted_objects.append((obj, i))
                    break
        
        sorted_objects.sort(key=lambda x: x[1])
        sorted_known_objects = [item[0] for item in sorted_objects]

    def check_for_disbanded_convoys(self, team_cords):
        current_unit_ids = {id(unit) for unit in team_cords}
        convoys_to_remove = []
        
        for i, convoy in enumerate(self.current_convoys):
            convoy_units = convoy[0]
            convoy_type = convoy[1]
            
            for unit in convoy_units[:]:
                if id(unit) not in current_unit_ids:
                    convoys_to_remove.append(i)
                    for remaining_unit in convoy_units:
                        if id(remaining_unit) in current_unit_ids:
                            remaining_unit.in_convoy = False
                    break
        
        for i in sorted(convoys_to_remove, reverse=True):
            del self.current_convoys[i]
            
        self.previous_team_units = team_cords[:]

    def create_convoys(self, team_cords):
        for convoy_name in self.convoys.keys():
            available_units = self.get_available_units(team_cords)
            needed_indexes = list(range(len(self.convoys[convoy_name][0])))
            temp = []
            
            for i, units_needed in enumerate(self.convoys[convoy_name][0]):
                for unit in available_units[:]:
                    if unit.unit_type == units_needed[0] and unit.in_air == units_needed[1] and unit.danger >= units_needed[2] and (self.furtherst_known_player_object is None or unit.z - self.furtherst_known_player_object.z >= 15):
                        available_units.remove(unit)
                        if i in needed_indexes:
                            needed_indexes.remove(i)
                            temp.append(unit)
                        break

            if len(needed_indexes) == 0:
                convoy_behavior = self.convoys[convoy_name][1]
                self.current_convoys.append([temp, convoy_name, convoy_behavior])
                for unit in temp:
                    unit.in_convoy = True

    def get_available_units(self, team_cords):
        availible_units = []
        for unit in team_cords:
            if unit.in_convoy == False:
                availible_units.append(unit)
        return availible_units
    
    def make_move(self, known_player_objects, team_cords, base_capture):
        self.check_for_disbanded_convoys(team_cords)
        
        self.update_intel(known_player_objects)
        if self.convoy_update_counter >= 100:
            self.create_convoys(team_cords)
            self.convoy_update_counter = 0

        self.convoy_update_counter += 1

        individual_units = self.get_available_units(team_cords)
        
        all_unit_groups = []

        self.base_capture = base_capture

        for convoy in self.current_convoys:
            convoy_units = convoy[0]
            convoy_name = convoy[1]
            convoy_behavior = convoy[2]  
            
            all_unit_groups.append({
                "type": "convoy",
                "convoy_type": convoy_name,
                "convoy_behavior": convoy_behavior,
                "units": convoy_units,
                "unit_count": len(convoy_units)
            })
        
        for unit in individual_units:
            all_unit_groups.append({
                "type": "individual",
                "unit": unit,
                "unit_type": unit.unit_type
            })

        for group in all_unit_groups:
            if group["type"] == "convoy":
                self._handle_convoy_movement(group, known_player_objects)
            elif group["type"] == "individual":
                self._handle_individual_movement(group["unit"], known_player_objects, team_cords)

    def _handle_convoy_movement(self, convoy_group, known_player_objects):
        convoy_name = convoy_group["convoy_type"]
        convoy_behavior = convoy_group["convoy_behavior"]  
        convoy_units = convoy_group["units"]
        
        if convoy_behavior == "Aggresive": 
            if self._should_regroup(convoy_units):
                self._regroup_convoy(convoy_units)
            else:
                target = self._find_target(known_player_objects, convoy_units)
                self._move_convoy_to_target(convoy_units, target, distance_factor=1.0)

    def _should_regroup(self, convoy_units):
        if len(convoy_units) <= 1:
            return False
            
        convoy_center_x = sum(unit.x for unit in convoy_units) / len(convoy_units)
        convoy_center_y = sum(unit.y for unit in convoy_units) / len(convoy_units)
        convoy_center_z = sum(unit.z for unit in convoy_units) / len(convoy_units)
        
        for unit in convoy_units:
            distance = ((unit.x - convoy_center_x) ** 2 + 
                        (unit.y - convoy_center_y) ** 2 + 
                        (unit.z - convoy_center_z) ** 2) ** 0.5
            
            if distance > self.max_convoy_dispersion:
                return True
                
        return False

    def _regroup_convoy(self, convoy_units):
        convoy_center_x = sum(unit.x for unit in convoy_units) / len(convoy_units)
        convoy_center_z = sum(unit.z for unit in convoy_units) / len(convoy_units)
        
        closest_unit = None
        min_distance = float('inf')
        
        for unit in convoy_units:
            distance = ((unit.x - convoy_center_x) ** 2 + 
                       (unit.z - convoy_center_z) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_unit = unit
        
        if closest_unit:
            rally_point_x = closest_unit.x
            rally_point_z = closest_unit.z
            
            formation_width = 5.0
            formation_depth = 8.0
            
            for i, unit in enumerate(convoy_units):
                row = i // 2  
                col = i % 2
                
                target_x = rally_point_x + (col - 0.5) * formation_width
                target_z = rally_point_z - row * formation_depth
                
                unit.target = (target_x, target_z)

    def _handle_individual_movement(self, unit, known_player_objects, team):
        if unit.unit_type == "attack":
            target = self._find_target(known_player_objects, [unit])
            self._move_convoy_to_target([unit], target, distance_factor=1.0)
            pass
        if unit.unit_type == "intel":
            self._move_intel_unit(unit, known_player_objects)
            pass

        if unit.unit_type == "support":
            self._move_support_unit(unit, team)
            pass
        if unit.unit_type == "artillery":
            self._move_artillery_unit(unit, known_player_objects)
            pass

        if unit.unit_type == "bomber":
            target = self._find_target(known_player_objects, [unit])
            if target:
                unit.target = (target.x, target.z)

    def _move_artillery_unit(self, artillery_unit, known_player_objects):

        target = self._find_target(known_player_objects, [artillery_unit])
        
        if not target:
            self.move_to_capture([artillery_unit])
            return
        
        min_artillery_distance = 20
        
        current_distance = ((target.x - artillery_unit.x) ** 2 + 
                        (target.z - artillery_unit.z) ** 2) ** 0.5
        
        direction_x = target.x - artillery_unit.x
        direction_z = target.z - artillery_unit.z
        
        magnitude = (direction_x**2 + direction_z**2)**0.5
        if magnitude > 0:
            direction_x /= magnitude
            direction_z /= magnitude
        
        if current_distance > min_artillery_distance:
            target_distance = min_artillery_distance * 0.9  
            target_x = target.x - direction_x * target_distance
            target_z = target.z - direction_z * target_distance
            
            artillery_unit.target = (target_x, target_z)
            
        elif current_distance < min_artillery_distance:
            retreat_distance = min_artillery_distance * 1.2  
            target_x = target.x - direction_x * retreat_distance
            target_z = target.z - direction_z * retreat_distance
            
            artillery_unit.target = (target_x, target_z)
            
        else:
            strafe_x = -direction_z
            strafe_z = direction_x
            
            strafe_distance = 3.0
            target_x = artillery_unit.x + strafe_x * strafe_distance
            target_z = artillery_unit.z + strafe_z * strafe_distance
            
            new_distance = ((target_x - target.x) ** 2 + (target_z - target.z) ** 2) ** 0.5
            
            if abs(new_distance - min_artillery_distance) > 2.0:
                corrected_direction_x = target.x - target_x
                corrected_direction_z = target.z - target_z
                
                corrected_magnitude = (corrected_direction_x**2 + corrected_direction_z**2)**0.5
                if corrected_magnitude > 0:
                    corrected_direction_x /= corrected_magnitude
                    corrected_direction_z /= corrected_magnitude
                
                target_x = target.x - corrected_direction_x * min_artillery_distance
                target_z = target.z - corrected_direction_z * min_artillery_distance
            
            artillery_unit.target = (target_x, target_z)

    def _move_support_unit(self, support_unit, all_team_units):
        best_target = None
        lowest_ammo_ratio = 1.0  
        closest_distance = float('inf')
        
        for ally in all_team_units:
            if ally == support_unit:
                continue

            ammo_ratio = ally.supply / ally.supply
            distance = ((ally.x - support_unit.x) ** 2 + (ally.z - support_unit.z) ** 2) ** 0.5
            
            if ammo_ratio < lowest_ammo_ratio:
                lowest_ammo_ratio = ammo_ratio
                best_target = ally
                closest_distance = distance
            elif ammo_ratio == lowest_ammo_ratio and distance < closest_distance:
                best_target = ally
                closest_distance = distance

        if best_target:
            healing_range = 8.0
            current_distance = ((best_target.x - support_unit.x) ** 2 + 
                            (best_target.z - support_unit.z) ** 2) ** 0.5
            
            if current_distance > healing_range:
                direction_x = best_target.x - support_unit.x
                direction_z = best_target.z - support_unit.z
                
                magnitude = (direction_x**2 + direction_z**2)**0.5
                if magnitude > 0:
                    direction_x /= magnitude
                    direction_z /= magnitude
                
                target_distance = healing_range * 0.8  
                target_x = best_target.x - direction_x * target_distance
                target_z = best_target.z - direction_z * target_distance
                
                support_unit.target = (target_x, target_z)
            else:
                support_unit.target = (best_target.x, best_target.z)

    def _find_target(self, known_player_objects, convoy_units):
        if not known_player_objects:
            return None
        
        best_target = None
        lowest_health = float('inf')
        closest_distance = float('inf')
        
        convoy_couter_air = True

        for unit in convoy_units:
            if unit.can_target_air == False:
                convoy_couter_air = False
                break

        convoy_center_x = sum(unit.x for unit in convoy_units) / len(convoy_units)
        convoy_center_y = sum(unit.y for unit in convoy_units) / len(convoy_units)
        convoy_center_z = sum(unit.z for unit in convoy_units) / len(convoy_units)
        
        for target in known_player_objects:
            distance = ((target.x - convoy_center_x) ** 2 + 
                        (target.y - convoy_center_y) ** 2 + 
                        (target.z - convoy_center_z) ** 2) ** 0.5
            
            target_health = getattr(target, 'health', None)
            
            if convoy_couter_air == True or (convoy_couter_air == False and target.in_air == False):
                if target_health is not None:
                    if target_health < lowest_health:
                        lowest_health = target_health
                        best_target = target
                        closest_distance = distance
                    elif target_health == lowest_health and distance < closest_distance:
                        best_target = target
                        closest_distance = distance
                        
                elif best_target is None or distance < closest_distance:
                    best_target = target
                    closest_distance = distance
        
        return best_target
    
    def move_to_capture(self, convoy_units):
        closest_location = None
        closest_distance = float('inf')

        all_locations = [self.player_base, self.enemy_base] + self.cities

        for location in all_locations:
            convoy_center_x = sum(unit.x for unit in convoy_units) / len(convoy_units)
            convoy_center_z = sum(unit.z for unit in convoy_units) / len(convoy_units)
            
            distance = ((location.x - convoy_center_x) ** 2 + 
                        (location.z - convoy_center_z) ** 2) ** 0.5
            
            if distance < closest_distance and self.base_capture[location] != "Enemy":
                closest_distance = distance
                closest_location = location

        if closest_location:
            convoy_center_x = sum(unit.x for unit in convoy_units) / len(convoy_units)
            convoy_center_z = sum(unit.z for unit in convoy_units) / len(convoy_units)
            
            dir_x = closest_location.x - convoy_center_x
            dir_z = closest_location.z - convoy_center_z
            
            magnitude = (dir_x**2 + dir_z**2)**0.5
            if magnitude > 0:
                dir_x /= magnitude
                dir_z /= magnitude
            
            formation_width = 5.0  
            formation_depth = 8.0 
            
            for i, unit in enumerate(convoy_units):
                row = i // 2  
                col = i % 2  
                
                offset_x = (col - 0.5) * formation_width
                offset_z = -row * formation_depth  
                
                rotated_offset_x = offset_x * dir_z + offset_z * dir_x
                rotated_offset_z = -offset_x * dir_x + offset_z * dir_z
                
                target_x = closest_location.x + rotated_offset_x
                target_z = closest_location.z + rotated_offset_z
                
                unit.target = (target_x, target_z)

    def _move_convoy_to_target(self, convoy_units, target, distance_factor=1.0):
        if not target and len(convoy_units) != 1 and self._should_regroup(convoy_units):
            self._regroup_convoy(convoy_units)
            return
        
        if not target:
            self.move_to_capture(convoy_units)
            return

        convoy_center_x = sum(unit.x for unit in convoy_units) / len(convoy_units)
        convoy_center_y = sum(unit.y for unit in convoy_units) / len(convoy_units)
        convoy_center_z = sum(unit.z for unit in convoy_units) / len(convoy_units)
        
        dir_x = target.x - convoy_center_x
        dir_z = target.z - convoy_center_z
        
        magnitude = (dir_x**2 + dir_z**2)**0.5
        if magnitude > 0:
            dir_x /= magnitude
            dir_z /= magnitude
        
        formation_width = 5.0  
        formation_depth = 8.0 
        
        for i, unit in enumerate(convoy_units):
            row = i // 2
            col = i % 2
            
            offset_x = (col - 0.5) * formation_width
            offset_z = -row * formation_depth  
            
            rotated_offset_x = offset_x * dir_z + offset_z * dir_x
            rotated_offset_z = -offset_x * dir_x + offset_z * dir_z
            
            target_x = target.x + rotated_offset_x
            target_z = target.z + rotated_offset_z
            
            unit.target = (target_x, target_z)

    def _move_intel_unit(self, intel_unit, known_player_objects):
        if not known_player_objects:
            if self.remembered_positions:
                most_recent = max(self.remembered_positions, key=lambda x: x[1])
                remembered_obj, timestamp = most_recent
                intel_unit.target = (remembered_obj.x, remembered_obj.z)
            return
        
        optimal_distance = 15.0
        min_safe_distance = 10.0
        
        best_observation_point_x = 0
        best_observation_point_z = 0
        total_weight = 0
        
        for enemy in known_player_objects:
            distance = ((enemy.x - intel_unit.x) ** 2 + (enemy.z - intel_unit.z) ** 2) ** 0.5
            
            if distance < min_safe_distance:
                direction_x = intel_unit.x - enemy.x
                direction_z = intel_unit.z - enemy.z
                
                magnitude = (direction_x**2 + direction_z**2)**0.5
                if magnitude > 0:
                    direction_x /= magnitude
                    direction_z /= magnitude
                    
                escape_distance = min_safe_distance * 1.5
                intel_unit.target = (intel_unit.x + direction_x * escape_distance,
                                    intel_unit.z + direction_z * escape_distance)
                return
            
            weight = 1.0 / max(distance, 1.0)
            total_weight += weight
            
            best_observation_point_x += enemy.x * weight
            best_observation_point_z += enemy.z * weight
        
        if total_weight > 0:
            best_observation_point_x /= total_weight
            best_observation_point_z /= total_weight
            
            direction_x = best_observation_point_x - intel_unit.x
            direction_z = best_observation_point_z - intel_unit.z
            
            current_distance = ((direction_x)**2 + (direction_z)**2)**0.5
            
            if current_distance > 0:
                direction_x /= current_distance
                direction_z /= current_distance
                
                if current_distance < optimal_distance:
                    target_x = best_observation_point_x - direction_x * optimal_distance
                    target_z = best_observation_point_z - direction_z * optimal_distance
                elif current_distance > optimal_distance * 1.5:
                    target_x = best_observation_point_x - direction_x * optimal_distance
                    target_z = best_observation_point_z - direction_z * optimal_distance
                else:
                    strafe_x = -direction_z
                    strafe_z = direction_x
                    
                    target_x = intel_unit.x + strafe_x * 5.0
                    target_z = intel_unit.z + strafe_z * 5.0
                    
                    current_distance = ((target_x - best_observation_point_x)**2 + 
                                    (target_z - best_observation_point_z)**2)**0.5
                    
                    if abs(current_distance - optimal_distance) > 5.0:
                        direction_to_center_x = best_observation_point_x - target_x
                        direction_to_center_z = best_observation_point_z - target_z
                        
                        magnitude = (direction_to_center_x**2 + direction_to_center_z**2)**0.5
                        if magnitude > 0:
                            direction_to_center_x /= magnitude
                            direction_to_center_z /= magnitude
                        
                        target_x = best_observation_point_x - direction_to_center_x * optimal_distance
                        target_z = best_observation_point_z - direction_to_center_z * optimal_distance
            else:
                target_x = intel_unit.x + 10.0
                target_z = intel_unit.z + 10.0
            
            intel_unit.target = (target_x, target_z)
