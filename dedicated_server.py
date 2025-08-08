import render
import pygame
import time
import threading
import queue
from network import NetworkServer
import json
import game
import ast


#Promis you nothing bad here, Was gonna add multiplayer and hopefully if your reading this you want to add it to. This all works good and if you want multiplayer
# - Use the game code. In there theres a function for the server processing and basically captures needed to be broadcasted and the red team too. Idk
# - Id be really shocked if anyone is reading this



class NetworkMonitor:
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height
        
        self.counter = 0
        self.external_ip = "Waiting to start..."
        self.connection_log = []
        self.data_log = []
        self.max_log_entries = 20
        
        self.message_history = []
        self.max_message_history = 10
        
        self.teams = {
            'red': {'players': [], 'max_players': 1, 'color': (255, 100, 100)},
            'blue': {'players': [], 'max_players': 1, 'color': (100, 100, 255)},
            'spectator': {'players': [], 'max_players': float('inf'), 'color': (200, 200, 200)}
        }
        
        self.unique_connections = set()
        self.connected_clients = {}
        self.selected_ip = None  

        self.server = None
        self.server_running = False
        self.game_running = False
        self.message_queue = queue.Queue()
        
        self.start_server_button_rect = (20, self.HEIGHT - 100, 150, 40)
        self.stop_server_button_rect = (180, self.HEIGHT - 100, 150, 40)
        self.start_game_button_rect = (20, self.HEIGHT - 50, 150, 40)

        self.red_team_button_rect = (350, self.HEIGHT - 100, 100, 40)
        self.blue_team_button_rect = (460, self.HEIGHT - 100, 100, 40)
        self.spec_team_button_rect = (570, self.HEIGHT - 100, 120, 40)
        self.clear_teams_button_rect = (700, self.HEIGHT - 100, 120, 40)
        self.reset_button_rect = (830, self.HEIGHT - 100, 120, 40)

        self.mouse_pos = (0, 0)
        self.mouse_release = False
        
        self.log_scroll = 0

        self.ping_override = None
        
        self.client_last_seen = {}
        self.activity_timeout = 5.0

        self.in_game = False
        self.game = game.Game(ctx, line_prog, width, height, board_size= 100, seed=24, starting_money=0, money_multiplier=1, fog_of_war=False, num_cities=2, win_condition="CAPTURE", biome="grass", game_og="sandbox", ai_deck=None, online=True, role="client")
        self.data_to_send = None

    def get_player_team(self, ip):
        for team_name, team_data in self.teams.items():
            if ip in team_data['players']:
                return team_name
        return None
    
    def assign_to_team(self, ip, team_name):
        if ip not in self.unique_connections:
            return False, "IP not connected"
        
        current_team = self.get_player_team(ip)
        if current_team:
            self.teams[current_team]['players'].remove(ip)
        
        team = self.teams[team_name]
        if len(team['players']) >= team['max_players']:
            return False, f"Team {team_name} is full"
        
        team['players'].append(ip)
        
        log_entry = {
            'timestamp': time.strftime('%H:%M:%S'),
            'client': 'SYSTEM',
            'data': f'IP {ip} assigned to {team_name} team'
        }
        self.data_log.append(log_entry)
        if len(self.data_log) > self.max_log_entries:
            self.data_log.pop(0)
        
        return True, f"Assigned to {team_name} team"
    
    def clear_all_teams(self):
        for team_data in self.teams.values():
            team_data['players'].clear()
        
        log_entry = {
            'timestamp': time.strftime('%H:%M:%S'),
            'client': 'SYSTEM',
            'data': 'All team assignments cleared'
        }
        self.data_log.append(log_entry)
        if len(self.data_log) > self.max_log_entries:
            self.data_log.pop(0)
        
        self.selected_ip = None
        
    def draw_terminal_border(self):
        border_color = (0, 180, 0)
        border_thickness = 3
        
        render.draw_rect(self.ctx, (0, 0, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, self.HEIGHT - border_thickness, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.WIDTH - border_thickness, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)

    def draw_terminal_header(self):
        header_y = 20
        render.draw_text(self.ctx, "NETWORK MONITORING TERMINAL v1.1 - TEAM EDITION", (20, header_y), (0, 255, 0), font_size=32, font_path="font/Tektur-Black.ttf")
        
        separator_y = header_y + 50
        for i in range(0, self.WIDTH - 40, 20):
            render.draw_text(self.ctx, "-", (20 + i, separator_y), (0, 150, 0), font_size=25, font_path="font/Tektur-Black.ttf")
    
    def draw_network_status(self):
        status_y = 100
        
        render.draw_text(self.ctx, "EXTERNAL IP:", (30, status_y), (0, 255, 0), font_size=30, font_path="font/Tektur-Black.ttf")
        ip_color = (0, 255, 0) if self.external_ip != "Waiting to start..." else (255, 255, 0)
        render.draw_text(self.ctx, self.external_ip, (250, status_y), ip_color, font_size=30, font_path="font/Tektur-Black.ttf")
        
        status_y += 40
        render.draw_text(self.ctx, "SERVER STATUS:", (30, status_y), (0, 255, 0), font_size=30, font_path="font/Tektur-Black.ttf")
        server_status = "ONLINE" if self.server_running else "OFFLINE"
        status_color = (0, 255, 0) if self.server_running else (255, 100, 0)
        render.draw_text(self.ctx, server_status, (300, status_y), status_color, font_size=30, font_path="font/Tektur-Black.ttf")
        
        status_y += 40
        render.draw_text(self.ctx, "PORT: 5000", (30, status_y), (0, 255, 0), font_size=25, font_path="font/Tektur-Black.ttf")
        
        render.draw_text(self.ctx, f"Total Connects: {len(self.unique_connections)}", (200, status_y), (0, 255, 0), font_size=25, font_path="font/Tektur-Black.ttf")
    
    def draw_team_status(self):
        team_start_y = 210
        
        render.draw_text(self.ctx, "TEAM STATUS:", (30, team_start_y), (0, 255, 0), font_size=25, font_path="font/Tektur-Black.ttf")
        
        y_offset = team_start_y + 35
        
        for team_name, team_data in self.teams.items():
            team_color = team_data['color']
            player_count = len(team_data['players'])
            max_players = team_data['max_players'] if team_data['max_players'] != float('inf') else '∞'
            
            team_text = f"{team_name.upper()}: {player_count}/{max_players}"
            render.draw_text(self.ctx, team_text, (30, y_offset), team_color, font_size=20, font_path="font/Tektur-Black.ttf")
            
            if team_data['players']:
                player_list = ", ".join(team_data['players'][:3])
                if len(team_data['players']) > 3:
                    player_list += f" (+{len(team_data['players']) - 3} more)"
                render.draw_text(self.ctx, f"  Players: {player_list}", (200, y_offset), (150, 150, 150), font_size=16, font_path="font/Tektur-Black.ttf")
            
            y_offset += 25
        
        unassigned = [ip for ip in self.unique_connections if not self.get_player_team(ip)]
        if unassigned:
            render.draw_text(self.ctx, f"UNASSIGNED: {len(unassigned)}", (30, y_offset), (255, 255, 0), font_size=20, font_path="font/Tektur-Black.ttf")
            unassigned_list = ", ".join(unassigned[:3])
            if len(unassigned) > 3:
                unassigned_list += f" (+{len(unassigned) - 3} more)"
            render.draw_text(self.ctx, f"  IPs: {unassigned_list}", (200, y_offset), (200, 200, 0), font_size=16, font_path="font/Tektur-Black.ttf")
            y_offset += 25
        
        if self.selected_ip:
            render.draw_text(self.ctx, f"SELECTED IP: {self.selected_ip}", (30, y_offset), (255, 255, 255), font_size=18, font_path="font/Tektur-Black.ttf")
    
    def draw_data_log(self):
        log_start_y = 350
        log_height = self.HEIGHT - 500
                
        log_rect = (20, log_start_y + 30, self.WIDTH - 40, log_height)
        render.draw_rect(self.ctx, log_rect, (0, 30, 0), self.line_prog, True)
        render.draw_rect(self.ctx, log_rect, (0, 150, 0), self.line_prog, False)
        
        y_offset = log_start_y + 50
        line_height = 25
        
        visible_entries = min(len(self.data_log), (log_height - 40) // line_height)
        start_index = max(0, len(self.data_log) - visible_entries + self.log_scroll)
        end_index = min(len(self.data_log), start_index + visible_entries)
        
        for i in range(start_index, end_index):
            entry = self.data_log[i]
            display_y = y_offset + (i - start_index) * line_height
            
            if display_y < log_start_y + log_height:
                render.draw_text(self.ctx, entry['timestamp'], (30, display_y), (0, 200, 0), font_size=18, font_path="font/Tektur-Black.ttf")
                
                client_ip = entry['client'].split(':')[0] if ':' in entry['client'] else entry['client']
                team = self.get_player_team(client_ip)
                if team and team in self.teams:
                    client_color = self.teams[team]['color']
                else:
                    client_color = (255, 255, 0)
                
                client_info = f"FROM: {client_ip}"
                render.draw_text(self.ctx, client_info, (150, display_y), client_color, font_size=18, font_path="font/Tektur-Black.ttf")
                data_text = f"DATA: {entry['data']}"
                render.draw_text(self.ctx, data_text, (350, display_y), (255, 255, 100), font_size=18, font_path="font/Tektur-Black.ttf")
    
    def draw_buttons(self):
        start_color = (0, 255, 0) if not self.server_running else (100, 100, 100)
        render.draw_rect(self.ctx, self.start_server_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.start_server_button_rect, start_color, self.line_prog, False)
        render.draw_text(self.ctx, "Start", (self.start_server_button_rect[0] + 50, self.start_server_button_rect[1] + 10), start_color, font_size=20, font_path="font/Tektur-Black.ttf")
        
        stop_color = (255, 100, 0) if self.server_running else (100, 100, 100)
        render.draw_rect(self.ctx, self.stop_server_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.stop_server_button_rect, stop_color, self.line_prog, False)
        render.draw_text(self.ctx, "Stop", (self.stop_server_button_rect[0] + 55, self.stop_server_button_rect[1] + 10), stop_color, font_size=20, font_path="font/Tektur-Black.ttf")

        if self.server_running:
            start_color = (0, 255, 0) if not self.game_running else (100, 100, 100)
            render.draw_rect(self.ctx, self.start_game_button_rect, (0, 0, 0), self.line_prog, True)
            render.draw_rect(self.ctx, self.start_game_button_rect, start_color, self.line_prog, False)
            render.draw_text(self.ctx, "Start Game", (self.start_game_button_rect[0] + 20, self.start_game_button_rect[1] + 10), start_color, font_size=20, font_path="font/Tektur-Black.ttf")
            
        reset_color = (255, 0, 255)
        render.draw_rect(self.ctx, self.reset_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.reset_button_rect, reset_color, self.line_prog, False)
        render.draw_text(self.ctx, "RESET", (self.reset_button_rect[0] + 30, self.reset_button_rect[1] + 10), reset_color, font_size=18, font_path="font/Tektur-Black.ttf")

        team_button_active = self.selected_ip is not None
        
        red_color = (255, 100, 100) if team_button_active else (100, 50, 50)
        render.draw_rect(self.ctx, self.red_team_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.red_team_button_rect, red_color, self.line_prog, False)
        render.draw_text(self.ctx, "Red", (self.red_team_button_rect[0] + 35, self.red_team_button_rect[1] + 10), red_color, font_size=18, font_path="font/Tektur-Black.ttf")
        
        blue_color = (100, 100, 255) if team_button_active else (50, 50, 100)
        render.draw_rect(self.ctx, self.blue_team_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.blue_team_button_rect, blue_color, self.line_prog, False)
        render.draw_text(self.ctx, "Blue", (self.blue_team_button_rect[0] + 30, self.blue_team_button_rect[1] + 10), blue_color, font_size=18, font_path="font/Tektur-Black.ttf")
        
        spec_color = (200, 200, 200) if team_button_active else (100, 100, 100)
        render.draw_rect(self.ctx, self.spec_team_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.spec_team_button_rect, spec_color, self.line_prog, False)
        render.draw_text(self.ctx, "Spec", (self.spec_team_button_rect[0] + 35, self.spec_team_button_rect[1] + 10), spec_color, font_size=18, font_path="font/Tektur-Black.ttf")
        
        clear_color = (255, 255, 0)
        render.draw_rect(self.ctx, self.clear_teams_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.clear_teams_button_rect, clear_color, self.line_prog, False)
        render.draw_text(self.ctx, "Clear", (self.clear_teams_button_rect[0] + 35, self.clear_teams_button_rect[1] + 10), clear_color, font_size=18, font_path="font/Tektur-Black.ttf")
        
        render.draw_text(self.ctx, "Click IP in log to select, then assign to team", (20, self.HEIGHT - 140), (150, 150, 150), font_size=16, font_path="font/Tektur-Black.ttf")
    
    def is_button_clicked(self, button_rect):
        return (self.mouse_pos[0] > button_rect[0] and 
                self.mouse_pos[0] < button_rect[0] + button_rect[2] and
                self.mouse_pos[1] > button_rect[1] and 
                self.mouse_pos[1] < button_rect[1] + button_rect[3])
    
    def is_ip_clicked_in_log(self):
        log_start_y = 350 + 50
        log_height = self.HEIGHT - 500
        line_height = 25
        
        if (self.mouse_pos[0] >= 150 and self.mouse_pos[0] <= 300 and
            self.mouse_pos[1] >= log_start_y and self.mouse_pos[1] <= log_start_y + log_height):
            
            line_index = (self.mouse_pos[1] - log_start_y) // line_height
            
            visible_entries = min(len(self.data_log), (log_height - 40) // line_height)
            start_index = max(0, len(self.data_log) - visible_entries + self.log_scroll)
            actual_index = start_index + line_index
            
            if 0 <= actual_index < len(self.data_log):
                entry = self.data_log[actual_index]
                client_info = entry['client']
                if ':' in client_info:
                    ip = client_info.split(':')[0]
                    if ip in self.unique_connections:
                        return ip
        return None
    
    def parse_client_message(self, raw_message):
        try:
            decoded_message = raw_message.decode('utf-8', errors='ignore')
            
            if decoded_message.startswith("§CONNECTION_TEST§"):
                return "CONNECTION_TEST", decoded_message[17:]
            elif decoded_message.startswith("§MESSAGE§"):
                return "MESSAGE", decoded_message[9:]
            elif decoded_message.startswith("§PING§"):
                return "PING", ""
            elif decoded_message.startswith("§DATA§"):
                return "DATA", decoded_message[6:]
            else:
                return "LEGACY", decoded_message
                
        except Exception as e:
            return "ERROR", f"Failed to parse message: {str(e)}"
    
    def generate_response(self, message_type, message_content, addr):
        try:
            ip = addr[0]
            team = self.get_player_team(ip)
            
            self.client_last_seen[ip] = time.time()

            if message_type == "CONNECTION_TEST":
                team_info = f" - Assigned to {team} team" if team else " - No team assigned"
                return f"Connection established successfully{team_info}".encode('utf-8')
                
            elif message_type == "PING":
                if self.ping_override == None:
                    if self.message_history:
                        return self.message_history[-1].encode('utf-8')
                    else:
                        team_status = f"You are on {team} team" if team else "You are unassigned"
                        return team_status.encode('utf-8')
                else:
                    return self.ping_override.encode('utf-8')
                    
            elif message_type == "MESSAGE":
                if message_content and message_content.strip():
                    self.message_history.append(message_content.strip())
                    if len(self.message_history) > self.max_message_history:
                        self.message_history.pop(0)
                team_info = f" (from {team} team)" if team else " (unassigned)"
                return f"Message received{team_info}".encode('utf-8')
            
            elif message_type == "DATA":
                if message_content and message_content.strip():
                    self.message_history.append(message_content.strip())
                    if len(self.message_history) > self.max_message_history:
                        self.message_history.pop(0)

                    self.game.decompile_data_server(ast.literal_eval(message_content))
                if self.data_to_send:
                    return self.data_to_send.encode('utf-8')
                else:
                    return  f"None".encode('utf-8')
                                
                    
            else:
                print(message_content)
                return f"Error: {message_content}".encode('utf-8')
                
        except Exception as e:
            return f"Server error: {str(e)}".encode('utf-8')
    
    def network_connection_handler(self, conn, addr):
        try:

            self.unique_connections.add(addr[0])
            
            connection_info = {
                'timestamp': time.strftime('%H:%M:%S'),
                'client': f"{addr[0]}:{addr[1]}",
                'type': 'CONNECTION'
            }
            self.connection_log.append(connection_info)
            
            data = conn.recv(1024)
            if data:
                message_type, message_content = self.parse_client_message(data)
                
                log_data = f"[{message_type}] {message_content}" if message_content else f"[{message_type}]"
                data_info = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'client': f"{addr[0]}:{addr[1]}",
                    'data': log_data[:100]
                }
                self.data_log.append(data_info)
                if len(self.data_log) > self.max_log_entries:
                    self.data_log.pop(0)
                
                response = self.generate_response(message_type, message_content, addr)
                conn.sendall(response)
            
        except Exception as e:
            error_info = {
                'timestamp': time.strftime('%H:%M:%S'),
                'client': f"{addr[0]}:{addr[1]}",
                'data': f"ERROR: {str(e)}"
            }
            self.data_log.append(error_info)
        finally:
            conn.close()
    
    def start_server(self):
        if not self.server_running:
            try:
                self.server = NetworkServer(port=5000)
                self.server.set_connection_handler(self.network_connection_handler)
                self.external_ip = self.server.open_port()
                self.server.start()
                self.server_running = True
                start_info = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'client': 'SYSTEM',
                    'data': 'Server started successfully'
                }
                self.data_log.append(start_info)
                
                self.message_history.clear()
                
            except Exception as e:
                error_info = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'client': 'SYSTEM',
                    'data': f'Server start failed: {str(e)}'
                }
                self.data_log.append(error_info)
    
    def stop_server(self):
        if self.server_running and self.server:
            try:
                self.server.shutdown()
                self.server_running = False
                self.unique_connections.clear()
                self.message_history.clear()
                for team_data in self.teams.values():
                    team_data['players'].clear()
                self.selected_ip = None
                
                stop_info = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'client': 'SYSTEM',
                    'data': 'Server stopped - all teams cleared'
                }
                self.data_log.append(stop_info)
            except Exception as e:
                error_info = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'client': 'SYSTEM',
                    'data': f'Server stop error: {str(e)}'
                }
                self.data_log.append(error_info)
    
    def start_game(self):
        if not self.server_running:
            log_entry = {
                'timestamp': time.strftime('%H:%M:%S'),
                'client': 'SYSTEM',
                'data': 'Cannot start game: Server not running'
            }
            self.data_log.append(log_entry)
            return
        
        if self.game_running:
            log_entry = {
                'timestamp': time.strftime('%H:%M:%S'),
                'client': 'SYSTEM',
                'data': 'Game already started'
            }
            self.data_log.append(log_entry)
            return
        
        total_players = sum(len(team['players']) for team in self.teams.values())
        if total_players == 0:
            log_entry = {
                'timestamp': time.strftime('%H:%M:%S'),
                'client': 'SYSTEM',
                'data': 'Cannot start game: No players assigned to teams'
            }
            self.data_log.append(log_entry)
            return
        
        self.ping_override = "§STARTING_GAME§"
        
        self.game_running = True
        
        log_entry = {
            'timestamp': time.strftime('%H:%M:%S'),
            'client': 'SYSTEM',
            'data' : 'Starting Game'
        }
        self.data_log.append(log_entry)
        
        self.message_history.append("Starting Game")
        if len(self.message_history) > self.max_message_history:
            self.message_history.pop(0)

    def cleanup_inactive_clients(self):

        current_time = time.time()
        inactive_ips = []
        
        for ip, last_seen in self.client_last_seen.items():
            if current_time - last_seen > self.activity_timeout:
                inactive_ips.append(ip)
        
        for ip in inactive_ips:
            if ip in self.unique_connections:
                self.unique_connections.remove(ip)
                
                current_team = self.get_player_team(ip)
                if current_team:
                    self.teams[current_team]['players'].remove(ip)
                
                if self.selected_ip == ip:
                    self.selected_ip = None
                
                del self.client_last_seen[ip]
                
                log_entry = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'client': 'SYSTEM',
                    'data': f'IP {ip} removed due to inactivity (5s timeout)'
                }
                self.data_log.append(log_entry)
                if len(self.data_log) > self.max_log_entries:
                    self.data_log.pop(0)

    def reset_all(self):
        try:
            if self.server_running:
                self.stop_server()
            
            self.counter = 0
            self.external_ip = "Waiting to start..."
            self.connection_log.clear()
            self.data_log.clear()
            self.message_history.clear()
            
            for team_data in self.teams.values():
                team_data['players'].clear()
            
            self.unique_connections.clear()
            self.connected_clients.clear()
            self.selected_ip = None
            self.client_last_seen.clear()
            
            self.server = None
            self.server_running = False
            self.game_running = False
            
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                except:
                    break
            
            self.log_scroll = 0
            
            self.ping_override = None
            
            self.in_game = False
            self.data_to_send = None
            
            self.game = game.Game(
                self.ctx, 
                self.line_prog, 
                self.WIDTH, 
                self.HEIGHT, 
                board_size=100, 
                seed=24, 
                starting_money=0, 
                money_multiplier=1, 
                fog_of_war=False, 
                num_cities=2, 
                win_condition="CAPTURE", 
                biome="grass", 
                game_og="sandbox", 
                ai_deck=None, 
                online=True, 
                role="client"
            )
            
            reset_log_entry = {
                'timestamp': time.strftime('%H:%M:%S'),
                'client': 'SYSTEM',
                'data': 'COMPLETE SYSTEM RESET - All values restored to default'
            }
            self.data_log.append(reset_log_entry)
            
        except Exception as e:
            error_log_entry = {
                'timestamp': time.strftime('%H:%M:%S'),
                'client': 'SYSTEM',
                'data': f'Reset error: {str(e)}'
            }
            self.data_log.append(error_log_entry)

    def handle_input(self, keys, gamestates, main):
        if keys[pygame.K_UP]:
            self.log_scroll = min(self.log_scroll + 1, 0)
        elif keys[pygame.K_DOWN]:
            max_scroll = max(0, len(self.data_log) - 10)
            self.log_scroll = max(self.log_scroll - 1, -max_scroll)
        
        if pygame.mouse.get_pressed()[0] and self.mouse_release:
            self.mouse_release = False
            
            if self.is_button_clicked(self.start_server_button_rect):
                self.start_server()
            elif self.is_button_clicked(self.stop_server_button_rect):
                self.stop_server()
            
            if self.is_button_clicked(self.start_game_button_rect):
                self.start_game()

            elif self.is_button_clicked(self.red_team_button_rect) and self.selected_ip:
                success, message = self.assign_to_team(self.selected_ip, 'red')
                if not success:
                    log_entry = {
                        'timestamp': time.strftime('%H:%M:%S'),
                        'client': 'SYSTEM',
                        'data': f'Failed to assign {self.selected_ip} to red team: {message}'
                    }
                    self.data_log.append(log_entry)
            
            elif self.is_button_clicked(self.blue_team_button_rect) and self.selected_ip:
                success, message = self.assign_to_team(self.selected_ip, 'blue')
                if not success:
                    log_entry = {
                        'timestamp': time.strftime('%H:%M:%S'),
                        'client': 'SYSTEM',
                        'data': f'Failed to assign {self.selected_ip} to blue team: {message}'
                    }
                    self.data_log.append(log_entry)
            
            elif self.is_button_clicked(self.spec_team_button_rect) and self.selected_ip:
                self.assign_to_team(self.selected_ip, 'spectator')
            
            elif self.is_button_clicked(self.clear_teams_button_rect):
                self.clear_all_teams()
            elif self.is_button_clicked(self.reset_button_rect):
                self.reset_all()
                
            else:
                clicked_ip = self.is_ip_clicked_in_log()
                if clicked_ip:
                    self.selected_ip = clicked_ip
    
    def render(self, gamestates, main):
        self.counter += 1
        self.mouse_pos = pygame.mouse.get_pos()
        if not pygame.mouse.get_pressed()[0]:
            self.mouse_release = True
        
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        
        for i in range(0, self.HEIGHT, 8):
            if (self.counter + i) % 120 < 50:
                render.draw_rect(self.ctx, (0, i, self.WIDTH, 1), (0, 50, 0), self.line_prog, True)
        
        self.draw_terminal_border()
        self.draw_terminal_header()
        self.draw_network_status()
        self.draw_team_status()
        self.draw_data_log()
        self.draw_buttons()

        self.cleanup_inactive_clients()

        self.data_to_send = self.game.online_update_server()

        keys = pygame.key.get_pressed()
        self.handle_input(keys, gamestates, main)

if __name__ == "__main__":
    import pygame
    import render
    
    pygame.init()
    WIDTH, HEIGHT = 1000, 720
    screen, ctx, line_prog = render.initialize_context(WIDTH, HEIGHT)
    
    network_monitor = NetworkMonitor(ctx, line_prog, WIDTH, HEIGHT)
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        network_monitor.render(None, None)
        pygame.display.flip()
        clock.tick(60)
    
    network_monitor.stop_server()
    pygame.quit()