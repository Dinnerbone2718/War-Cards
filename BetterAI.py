import copy
import math

class AI:
    def __init__(self, capture_locations, ground_vert):
        
        self.capture_locations = copy.copy(capture_locations)

        self.ground_vertices = ground_vert

        self.attack_units = 0
        self.transport_units = 0
        self.bomber_units = 0
        self.artillery_units = 0
        self.intel_units = 0
        self.support_units = 0
        self.defense_units = 0
        self.total_units = 0

        self.optimal_ratio = {
            "attack_units": 0.4,
            "transport_units": 0.1,
            "bomber_units": 0.1,
            "artillery_units": 0.1,
            "intel_units": 0.1,
            "support_units": 0.1,
            "defense_units": 0.1
        }

        self.past_known_units = []

        self.transport_units_states = {

        }

        pass


    def place(self, deck, own_units, money, all_players):
        current_counts = {
            "attack_units": 0,
            "transport_units": 0,
            "bomber_units": 0,
            "artillery_units": 0,
            "intel_units": 0,
            "support_units": 0,
            "defense_units": 0
        }
        
        for unit in own_units:
            unit_type = unit.unit_type
            if unit_type == "attack":
                current_counts["attack_units"] += 1
            elif unit_type == "transport":
                current_counts["transport_units"] += 1
            elif unit_type == "bomber":
                current_counts["bomber_units"] += 1
            elif unit_type == "artillery":
                current_counts["artillery_units"] += 1
            elif unit_type == "intel":
                current_counts["intel_units"] += 1
            elif unit_type == "support":
                current_counts["support_units"] += 1
            elif unit_type == "defense":
                current_counts["defense_units"] += 1
        
        self.total_units = sum(current_counts.values())

        current_ratios = {}
        for unit_type, count in current_counts.items():
            current_ratios[unit_type] = count / self.total_units if self.total_units > 0 else 0
        
        deficits = {}
        for unit_type in self.optimal_ratio:
            deficit = self.optimal_ratio[unit_type] - current_ratios[unit_type]
            if deficit > 0:
                deficits[unit_type] = deficit
        
        if not deficits:
            return money, own_units
        
        sorted_deficits = sorted(deficits.items(), key=lambda x: x[1], reverse=True)
        
        available_cards = deck[:5]
        expensive, confidence = self.is_winning(all_players)


        possible_options = []
        for unit_type_with_suffix, deficit in sorted_deficits:
            target_unit_type = unit_type_with_suffix.replace("_units", "")
            for card in available_cards:
                if card.entity.unit_type == target_unit_type:
                    possible_options.append(card)
                    break

        if not possible_options:
            return money, own_units


        possible_options = possible_options[:2]
        before_sort = possible_options[0]
        possible_options = sorted(possible_options, key=lambda card: card.price)

        target_entity = None
        if expensive and len(possible_options) > 1:
            target_entity = possible_options[1]
        else:
            target_entity = before_sort

        if money >= target_entity.price:
            added_entity = copy.deepcopy(target_entity.entity)
            own_units.append(added_entity)
            added_entity.team = False

            bases_iter = iter(self.capture_locations)
            next(bases_iter)
            second_base = next(bases_iter)
            added_entity.x = second_base.x
            added_entity.z = second_base.z

            money -= target_entity.price

        return money, own_units
    

    def is_winning(self, player_entities):
        owned_bases = 0
        enemy_bases = 0
        
        for base, owner in self.capture_locations.items():
            if owner == "Enemy": 
                owned_bases += 1
            elif owner != "Neutral":  
                enemy_bases += 1
        
        known_enemy_units = len(player_entities)
        own_unit_count = self.total_units

        
        unit_advantage = False
        if known_enemy_units > 0:
            unit_advantage = own_unit_count > known_enemy_units
        else:
            unit_advantage = own_unit_count > 0
        
        territory_advantage = owned_bases > enemy_bases
        
        is_winning = False
        confidence = 0.0
        
        if unit_advantage and territory_advantage:
            is_winning = True
            confidence = 0.9
        elif unit_advantage or territory_advantage:
            if unit_advantage and known_enemy_units > 0:
                unit_ratio = own_unit_count / known_enemy_units
                if unit_ratio >= 1.5: 
                    is_winning = True
                    confidence = 0.7
                else:
                    confidence = 0.5
            
            if territory_advantage:
                territory_ratio = owned_bases / max(enemy_bases, 1)
                if territory_ratio >= 2: 
                    is_winning = True
                    confidence = max(confidence, 0.7)
                else:
                    confidence = max(confidence, 0.5)
        else:
            is_winning = False
            confidence = 0.2
        
        if known_enemy_units == 0:
            confidence *= 0.6 
        
        if own_unit_count == 0:
            confidence *= 0.3 
        

        
        return is_winning, confidence

    def make_move(self, players_spotted, own_units, capture_status):

        self.capture_locations = copy.copy(capture_status)


        to_rem = []
        for unit in self.past_known_units:
            unit[1] += 1
            if unit[1] > 180:
                to_rem.append(unit)
        for unit in to_rem:
            self.past_known_units.remove(unit)

        for spotted_unit in players_spotted:
            found = False
            for known_unit in self.past_known_units:
                if known_unit[0] == spotted_unit:
                    known_unit[1] = 0
                    found = True
                    break
            if not found:
                self.past_known_units.append([spotted_unit, 0])


        sorted_units = sorted(own_units, key=lambda unit: unit.unit_type == "transport")

        total_units = 0
        self.attack_units = 0
        self.transport_units = 0
        self.bomber_units = 0
        self.artillery_units = 0
        self.intel_units = 0
        self.support_units = 0
        self.defense_units = 0


        for unit in sorted_units:
            total_units += 1

            if unit.unit_type == "attack":
                self.move_attack_unit(players_spotted, unit)
                self.attack_units += 1
            if unit.unit_type == "support":
                self.move_support_unit(players_spotted, unit, own_units)
                self.support_units+=1
            if unit.unit_type == "intel":
                self.move_intel_unit(players_spotted, unit)
                self.intel_units+=1
            if unit.unit_type == "bomber":
                self.move_bomber_unit(players_spotted, unit)
                self.bomber_units+=1
            if unit.unit_type == "transport":
                self.move_transport_unit(players_spotted, unit, own_units)
                self.transport_units+=1
            if unit.unit_type == "artillery":
                #WILL GET REDONE TRUST 🙏🙏🙏
                self.move_artillery_unit(unit, players_spotted)
                self.artillery_units += 1

        self.total_units = total_units



    def _find_closest_safe_base(self, unit):
        closest_safe_location = None
        closest_dist_to_safe_location = float('inf')

        for base in self.capture_locations:
            dist = math.sqrt((base.x - unit.x)**2 + (base.z - unit.z)**2)
            if dist < closest_dist_to_safe_location and self.capture_locations[base] == "Enemy":
                closest_safe_location = base
                closest_dist_to_safe_location = dist

        return closest_safe_location




    def _path_to_unit(players_spotted, start_unit, end_unit, safety_distance=5.0, path_samples=10):


        
        if not players_spotted:
            return True
        
        dx = end_unit.x - start_unit.x
        dz = end_unit.z - start_unit.z
        path_length = math.sqrt(dx**2 + dz**2)
        
        if path_length == 0:
            for player in players_spotted:
                dist_to_player = math.sqrt((player.x - start_unit.x)**2 + (player.z - start_unit.z)**2)
                if dist_to_player < safety_distance:
                    return False
            return True
        
        for i in range(path_samples + 1):
            t = i / path_samples

            
            current_x = start_unit.x + t * dx
            current_z = start_unit.z + t * dz
            
            for player in players_spotted:
                dist_to_player = math.sqrt((player.x - current_x)**2 + (player.z - current_z)**2)
                
                if dist_to_player < safety_distance:
                    return False
        
        return True





    def _find_best_position(self, own_units, players_spotted):

        
        enemy_positions = [(unit.x, unit.z) for unit in players_spotted]
        
        friendly_positions = [(unit.x, unit.z) for unit in own_units]
        
        strategic_positions = []
        for base in self.capture_locations:
            if self.capture_locations[base] != "Enemy":
                strategic_positions.append((base.x, base.z))
        
        best_position = None
        best_score = -float('inf')
        
        for strategic_pos in strategic_positions:
            for angle in range(0, 360, 30):  
                for radius in [15, 25, 35]:  
                    
                    rad = math.radians(angle)
                    pos_x = strategic_pos[0] + radius * math.cos(rad)
                    pos_z = strategic_pos[1] + radius * math.sin(rad)
                    
                    position = (pos_x, pos_z)
                    score = self._evaluate_position(position, enemy_positions, friendly_positions, strategic_positions)
                    
                    if score > best_score:
                        best_score = score
                        best_position = position
        
        if best_position is None:
            best_position = self._find_safe_fallback_position(enemy_positions, friendly_positions)
        
        return best_position

    def _evaluate_position(self, position, enemy_positions, friendly_positions, strategic_positions):

        score = 0
        pos_x, pos_z = position
        
        min_strategic_dist = float('inf')
        for strategic_pos in strategic_positions:
            dist = math.sqrt((strategic_pos[0] - pos_x)**2 + (strategic_pos[1] - pos_z)**2)
            min_strategic_dist = min(min_strategic_dist, dist)
        
        if min_strategic_dist < float('inf'):
            if 15 <= min_strategic_dist <= 35:
                score += 50 - abs(min_strategic_dist - 25)  
            elif min_strategic_dist < 15:
                score += 20 
            else:
                score += max(0, 50 - (min_strategic_dist - 35) * 0.5)  
        
        min_enemy_dist = float('inf')
        for enemy_pos in enemy_positions:
            dist = math.sqrt((enemy_pos[0] - pos_x)**2 + (enemy_pos[1] - pos_z)**2)
            min_enemy_dist = min(min_enemy_dist, dist)
        
        if min_enemy_dist < float('inf'):
            if min_enemy_dist < 10:
                score -= 30  
            elif 10 <= min_enemy_dist <= 30:
                score += 20  
            elif 30 < min_enemy_dist <= 60:
                score += 10 
            else:
                score -= 10 
        
        for friendly_pos in friendly_positions:
            dist = math.sqrt((friendly_pos[0] - pos_x)**2 + (friendly_pos[1] - pos_z)**2)
            if dist < 15:
                score -= 15 
            elif dist < 25:
                score -= 5  
        
        nearby_strategic_count = 0
        for strategic_pos in strategic_positions:
            dist = math.sqrt((strategic_pos[0] - pos_x)**2 + (strategic_pos[1] - pos_z)**2)
            if dist <= 40:
                nearby_strategic_count += 1
        
        if nearby_strategic_count > 1:
            score += nearby_strategic_count * 10
        
        return score

    def _find_safe_fallback_position(self, enemy_positions, friendly_positions):

        if friendly_positions:
            center_x = sum(pos[0] for pos in friendly_positions) / len(friendly_positions)
            center_z = sum(pos[1] for pos in friendly_positions) / len(friendly_positions)
        else:
            center_x, center_z = 0, 0  
        
        best_position = (center_x, center_z)
        best_safety_score = -float('inf')
        
        for dx in range(-50, 51, 10):
            for dz in range(-50, 51, 10):
                pos_x = center_x + dx
                pos_z = center_z + dz
                
                min_enemy_dist = float('inf')
                for enemy_pos in enemy_positions:
                    dist = math.sqrt((enemy_pos[0] - pos_x)**2 + (enemy_pos[1] - pos_z)**2)
                    min_enemy_dist = min(min_enemy_dist, dist)
                
                safety_score = min_enemy_dist
                
                avg_friendly_dist = 0
                if friendly_positions:
                    total_dist = sum(math.sqrt((pos[0] - pos_x)**2 + (pos[1] - pos_z)**2) 
                                for pos in friendly_positions)
                    avg_friendly_dist = total_dist / len(friendly_positions)
                    
                    if 20 <= avg_friendly_dist <= 40:
                        safety_score += 10
                
                if safety_score > best_safety_score:
                    best_safety_score = safety_score
                    best_position = (pos_x, pos_z)
        
        return best_position
    
    def move_attack_unit(self, players_spotted, unit):


        closest_unit = None
        closest_dist = float('inf')
        for player_unit in players_spotted:
            dist = math.sqrt((player_unit.x - unit.x)**2 + (player_unit.z - unit.z)**2)
            
            if dist < closest_dist and ((unit.can_target_air and player_unit.in_air) or player_unit.in_air == False):
                closest_unit = player_unit
                closest_dist = dist
        

        closest_capture_location = None
        closest_dist_to_capture_location = float('inf')

        for base in self.capture_locations:

            dist = math.sqrt((base.x - unit.x)**2 + (base.z - unit.z)**2)
            
            if dist < closest_dist_to_capture_location and self.capture_locations[base] != "Enemy":
                closest_capture_location = base
                closest_dist_to_capture_location = dist

        engagement_range = 50

        if closest_unit != None and closest_dist <= engagement_range:
            unit.target = (closest_unit.x, closest_unit.z)
        elif closest_capture_location != None:
            unit.target = (closest_capture_location.x, closest_capture_location.z)
        elif closest_unit != None:
            unit.target = (closest_unit.x, closest_unit.z)


        #Retreat Code
        if unit.health/unit.max_health < .5 or unit.supply/unit.max_supply < .25:
            closest_safe_location = self._find_closest_safe_base(unit)

            if closest_safe_location != None:
                unit.target = (closest_safe_location.x, closest_safe_location.z)

    def move_support_unit(self, players_spotted, unit, own_units):


        unit_need_ammo = None
        ammo_refill_ratio = float('inf')

        for possible_unit in own_units:
            if possible_unit.in_air == False and AI._path_to_unit(players_spotted, unit, possible_unit) and possible_unit != self:
                if possible_unit.supply/possible_unit.max_supply < ammo_refill_ratio:
                    unit_need_ammo = possible_unit
                    ammo_refill_ratio = possible_unit.supply/possible_unit.max_supply

        
        if unit_need_ammo != None:
            dist = math.sqrt((unit_need_ammo.x - unit.x)**2 + (unit_need_ammo.z - unit.z)**2)
            if dist > 7:
                unit.target = (unit_need_ammo.x, unit_need_ammo.z)

        else:
            close_safe_base = self._find_closest_safe_base(unit)
            if close_safe_base != None:
                unit.target = (close_safe_base.x, close_safe_base.z)

    def move_intel_unit(self, players_spotted, unit):
        expiring_units = []
        for known_unit in self.past_known_units:
            if known_unit[1] > 60: 
                expiring_units.append(known_unit)
        
        if not expiring_units:
            if self.past_known_units:
                sorted_units = sorted(self.past_known_units, key=lambda x: x[1], reverse=True)
                expiring_units = sorted_units[:3]  
        
        best_target = None
        best_priority = -1
        
        for known_unit_data in expiring_units:
            known_unit_pos = known_unit_data[0]  
            age = known_unit_data[1]
            
            safe_to_investigate = True
            for spotted_unit in players_spotted:
                dist_to_threat = math.sqrt((spotted_unit.x - known_unit_pos.x)**2 + 
                                        (spotted_unit.z - known_unit_pos.z)**2)
                
                if (spotted_unit.can_target_air and 
                    dist_to_threat < 15): 
                    safe_to_investigate = False
                    break
            
            if safe_to_investigate:
                dist_to_intel = math.sqrt((known_unit_pos.x - unit.x)**2 + 
                                        (known_unit_pos.z - unit.z)**2)
                
                priority = age - (dist_to_intel * 0.1) 
                
                if priority > best_priority:
                    best_priority = priority
                    best_target = (known_unit_pos.x, known_unit_pos.z)
        
        if best_target:
            unit.target = best_target
        else:

            safe_patrol_location = None
            for base in self.capture_locations:
                safe_area = True
                for spotted_unit in players_spotted:
                    dist_to_base = math.sqrt((spotted_unit.x - base.x)**2 + 
                                        (spotted_unit.z - base.z)**2)
                    if spotted_unit.can_target_air and dist_to_base < 12:
                        safe_area = False
                        break
                
                if safe_area:
                    safe_patrol_location = base
                    break
            
            if safe_patrol_location:
                unit.target = (safe_patrol_location.x, safe_patrol_location.z)

    def move_bomber_unit(self, players_spotted, own_unit):
        dangerous_unit = None
        for unit in players_spotted:
            if unit.in_air:
                continue
            if dangerous_unit == None:
                dangerous_unit = unit
            elif unit.danger > dangerous_unit.danger:
                dangerous_unit = unit
        
        if dangerous_unit and own_unit.target == None:
            own_unit.target = (dangerous_unit.x, dangerous_unit.z)
            

        return

    def move_transport_unit(self, players_spotted, unit, own_units):
        if unit not in self.transport_units_states.keys():
            self.transport_units_states[unit] = ("idle", None)

        state = self.transport_units_states[unit]

        if len(unit.units_carried) == 0 and state[0] == "idle":
            unit_needs_movement = None
            unit_movement_score = 0
            
            for own_unit in own_units:
                if (own_unit != unit and 
                    own_unit.in_air == False and 
                    own_unit.health / own_unit.max_health < 0.25 and
                    AI._path_to_unit(players_spotted, unit, own_unit, 5)):
                    
                    injury_score = 1 - (own_unit.health / own_unit.max_health)
                    if injury_score > unit_movement_score:
                        unit_movement_score = injury_score
                        unit_needs_movement = own_unit

            if unit_needs_movement is not None:
                self.transport_units_states[unit] = ("move_into_safety", unit_needs_movement)
                return

            best_combat_unit = None
            
            for own_unit in own_units:

                if own_unit == unit:
                    continue
                    
                if own_unit.health / own_unit.max_health <= 0.95:
                    continue
                    
                if own_unit.in_air:
                    continue
                    
                if not AI._path_to_unit(players_spotted, unit, own_unit, 40, 20):
                    continue
                    
                if own_unit.has_been_moved <= 600:
                    continue
                
                if best_combat_unit is None or own_unit.danger > best_combat_unit.danger:
                    best_combat_unit = own_unit

            if best_combat_unit is not None:
                self.transport_units_states[unit] = ("move_into_war", best_combat_unit)

        elif state[0] == "move_into_war" or state[0] == "move_into_safety":

            unit_needs_movement = self.transport_units_states[unit][1]
            

            if unit_needs_movement not in own_units:
                self.transport_units_states[unit] = ("idle", None)
                return
                
            unit.target = (unit_needs_movement.x, unit_needs_movement.z)

            dist_to_unit = math.sqrt((unit_needs_movement.x - unit.x)**2 + (unit_needs_movement.z - unit.z)**2)

            if dist_to_unit < 20:
                unit_needs_movement.target = (unit.x, unit.z)

                if dist_to_unit < 2:
                    unit.target = None

                    if unit.in_air == False:
                        unit.pickup([], own_units)
                        if state[0] == "move_into_war":
                            self.transport_units_states[unit] = ("transport_into_war", None)
                        elif state[0] == "move_into_safety":
                            self.transport_units_states[unit] = ("transport_into_safety", None)

                    pass


            if not AI._path_to_unit(players_spotted, unit, unit_needs_movement, 20) or unit_needs_movement.in_air:
                self.transport_units_states[unit] = ("idle", None)
                unit.target = (unit.x, unit.z)
                return
            
        elif len(unit.units_carried) != 0 and state[0] != "idle":
            
            if state[0] == "transport_into_war" and state[1] == None:
                self.transport_units_states[unit] = ("transport_into_war", self._find_best_position(own_units, players_spotted))
                return
            elif state[0] == "transport_into_war":
                unit.target = state[1]

            
            if state[0] == "transport_into_safety" and state[1] == None:
                closest_owned_base = None
                closest_dist_to_owned_location = float('inf')

                for base in self.capture_locations:

                    dist = math.sqrt((base.x - unit.x)**2 + (base.z - unit.z)**2)
                    
                    if dist < closest_dist_to_owned_location and self.capture_locations[base] != "Enemy":
                        closest_owned_base = base
                        closest_dist_to_owned_location = dist

                self.transport_units_states[unit] = ("transport_into_safety", (closest_owned_base.x, closest_owned_base.z))

                return
            
            elif state[0] == "transport_into_safety":
                unit.target = state[1]


            if unit.target != None and math.sqrt((unit.target[0] - unit.x)**2 + (unit.target[1] - unit.z)**2) < 5:
                unit.target = None
                self.transport_units_states[unit] = ("idle", None)


        elif len(unit.units_carried) != 0 and state[0] == "idle":
            if hasattr(unit, 'y_off_ground'):
                if unit.y_off_ground != 0:
                    return
            
            for t_unit in unit.units_carried:
                t_unit.has_been_moved = 0

            unit.deploy([], own_units, self.ground_vertices)

    def move_artillery_unit(self, unit, players_spotted):
        closest_unit = None
        closest_dist = float('inf')
        for player_unit in players_spotted:
            dist = math.sqrt((player_unit.x - unit.x)**2 + (player_unit.z - unit.z)**2)
            if dist < closest_dist and ((unit.can_target_air and player_unit.in_air) or not player_unit.in_air):
                closest_unit = player_unit
                closest_dist = dist

        closest_capture_location = None
        closest_dist_to_capture_location = float('inf')
        for base in self.capture_locations:
            dist = math.sqrt((base.x - unit.x)**2 + (base.z - unit.z)**2)
            if dist < closest_dist_to_capture_location and self.capture_locations[base] != "Enemy":
                closest_capture_location = base
                closest_dist_to_capture_location = dist

        min_safe_distance = 10 
        if closest_unit is not None and closest_dist < min_safe_distance:
            dx = unit.x - closest_unit.x
            dz = unit.z - closest_unit.z
            length = math.sqrt(dx**2 + dz**2)
            if length == 0:
                length = 1  
            back_x = closest_unit.x + dx / length * min_safe_distance
            back_z = closest_unit.z + dz / length * min_safe_distance
            unit.target = (back_x, back_z)
        elif closest_unit is None and closest_capture_location is not None:
            unit.target = (closest_capture_location.x, closest_capture_location.z)
        elif closest_unit is not None:
            unit.target = (closest_unit.x, closest_unit.z)

        if unit.health / unit.max_health < 0.5 or unit.supply / unit.max_supply < 0.25:
            closest_safe_location = self._find_closest_safe_base(unit)
            if closest_safe_location is not None:
                unit.target = (closest_safe_location.x, closest_safe_location.z)
