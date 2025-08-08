import time
import threading
import queue
from network import NetworkClient
import render
import pygame
import game
import json
import ast
import time



#IMPORTANT : READ DEDICATED SERVER CODE




# ===========================
# NETWORK HANDLER
# ===========================

class NetworkHandler:
    
    def __init__(self, timeout=5.0):
        self.client = NetworkClient(timeout=timeout)
        self.connected = False
        self.server_ip = ""
        self.server_port = 5000
        self.connection_status = "DISCONNECTED"
        self.connection_log = []
        self.max_log_entries = 15
        self.in_game = False
        
        self.on_log_update = None
        self.on_status_change = None
        self.team = None
        
        self.add_log_entry("SYSTEM", "Client terminal initialized")
    
    def set_callbacks(self, on_log_update=None, on_status_change=None):
        self.on_log_update = on_log_update
        self.on_status_change = on_status_change
    
    def add_log_entry(self, source, message):
        entry = {
            'timestamp': time.strftime('%H:%M:%S'),
            'source': source,
            'message': message
        }
        self.connection_log.append(entry)
        if len(self.connection_log) > self.max_log_entries:
            self.connection_log.pop(0)
        
        if self.on_log_update:
            self.on_log_update(self.connection_log)
    
    def update_status(self, status):
        self.connection_status = status
        if self.on_status_change:
            self.on_status_change(status, self.connected, self.server_ip, self.server_port)
    
    def connect_to_server(self, ip, port):
        if self.connected:
            return False
        
        try:
            self.server_ip = ip
            self.server_port = int(port)
            
            test_message = "§CONNECTION_TEST§"
            response = self.client.send_message(self.server_ip, self.server_port, test_message.encode("utf-8"))
            
            if response:
                self.connected = True
                self.update_status("CONNECTED")
                self.add_log_entry("CLIENT", f"Connected to {self.server_ip}:{self.server_port}")
                self.add_log_entry("SERVER", response.decode("utf-8"))
                return True
            else:
                self.add_log_entry("CLIENT", "Connection failed - no response")
                self.update_status("CONNECTION FAILED")
                return False
                
        except Exception as e:
            self.add_log_entry("CLIENT", f"Connection error: {str(e)}")
            self.update_status("CONNECTION FAILED")
            return False
    
    def disconnect_from_server(self):
        if self.connected:
            self.connected = False
            self.update_status("DISCONNECTED")
            self.add_log_entry("CLIENT", "Disconnected from server")
            return True
        return False
    
    def send_message(self, message):
        if not self.connected or not message.strip():
            return False
        
        try:
            message = message.strip()
            message = f"§MESSAGE§{message}"
            self.add_log_entry("CLIENT", f"Sending")
            
            response = self.client.send_message(self.server_ip, self.server_port, message.encode("utf-8"))
            
            if response:
                self.add_log_entry("SERVER", response.decode("utf-8"))
                return True
            else:
                self.add_log_entry("CLIENT", "No response from server")
                return False
                
        except Exception as e:
            self.add_log_entry("CLIENT", f"Send error: {str(e)}")
            self.connected = False
            self.update_status("CONNECTION LOST")
            return False
    
    def ping_server(self, message = None):
        if not self.connected:
            return False
            
        try:
            if message != None:
                response = self.client.send_message(self.server_ip, self.server_port, f"§DATA§{message}".encode("utf-8"))
                if response:
                    return response.decode("utf-8")
                else:
                    self.add_log_entry("SERVER", "Ping failed - no response")
                    return False        


            else:
                response = self.client.send_message(self.server_ip, self.server_port, "§PING§".encode("utf-8"))
                if response:
                    if not (self.connection_log and self.connection_log[-1]['message'] == response.decode("utf-8")) and response.decode("utf-8") != "§EMPTYRESPONSE§":
                        if response.decode("utf-8") == "§STARTING_GAME§":
                            self.in_game = True
                        else:
                            self.add_log_entry("PERSON", response.decode("utf-8"))
                            if "blue" in response.decode("utf-8"):
                                self.team = "BLUE"
                            elif "red" in response.decode("utf-8"):
                                self.team = "RED"
                            elif "spectator" in response.decode("utf-8"):
                                self.team = "SPECTATOR"
                    return True
                else:
                    self.add_log_entry("SERVER", "Ping failed - no response")
                    return False
        except Exception as e:
            self.add_log_entry("SERVER", f"Ping error: {str(e)}")
            self.connected = False
            self.update_status("CONNECTION LOST")
            return False
    
    def clear_log(self):
        self.connection_log.clear()
        self.add_log_entry("SYSTEM", "Log cleared")
    
    def get_connection_info(self):
        return {
            'connected': self.connected,
            'status': self.connection_status,
            'server_ip': self.server_ip,
            'server_port': self.server_port,
            'log': self.connection_log
        }


# ===========================
# ONLINE GAME MANAGER
# ===========================

class OnlineGameManager:
    
    def __init__(self, ctx, line_prog, width, height, network_handler):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height
        self.network = network_handler
        
        self.data_to_send = None

        self.game = game.Game(
            ctx=ctx,
            line_prog=line_prog,
            width=width,
            height=height,
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
        
        self.game_active = False
    
    def start_game(self):
        self.game_active = True
        self.network.add_log_entry("SYSTEM", "Starting online game...")
    
    def stop_game(self):
        self.game_active = False
        self.network.in_game = False
        self.network.add_log_entry("SYSTEM", "Returned to connection menu")
    
    def update_game_state(self):
        if self.game_active and self.network.connected:
            self.data_to_send = self.game.online_update_client()
    
    def render_game(self, gamestates, main, events):
        if self.game_active:
            self.game.render(gamestates, main, events)
            self.update_game_state()
    
    def handle_game_input(self, events):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_0]:
            self.stop_game()
            return True
        return False


# ===========================
# UI COMPONENTS
# ===========================

class InputField:
    
    def __init__(self, rect, max_length, allowed_chars=None, default_text=""):
        self.rect = rect
        self.max_length = max_length
        self.allowed_chars = allowed_chars
        self.text = default_text
        self.cursor_pos = len(default_text)
        self.is_editing = False
    
    def handle_input(self, event):
        if not self.is_editing:
            return
        
        if event.key == pygame.K_BACKSPACE and self.cursor_pos > 0:
            self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
            self.cursor_pos -= 1
        elif event.key == pygame.K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif event.key == pygame.K_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        elif event.key == pygame.K_HOME:
            self.cursor_pos = 0
        elif event.key == pygame.K_END:
            self.cursor_pos = len(self.text)
        elif len(event.unicode) == 1 and len(self.text) < self.max_length:
            if self.allowed_chars is None or event.unicode in self.allowed_chars:
                if (self.allowed_chars is None and event.unicode.isprintable()) or \
                   (self.allowed_chars and event.unicode in self.allowed_chars):
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
    
    def draw(self, ctx, line_prog, label, label_pos, counter):
        render.draw_text(ctx, label, label_pos, (0, 255, 0), font_size=25, font_path="font/Tektur-Black.ttf")
        
        field_color = (255, 255, 0) if self.is_editing else (0, 255, 0)
        render.draw_rect(ctx, self.rect, (0, 30, 0), line_prog, True)
        render.draw_rect(ctx, self.rect, field_color, line_prog, False)
        
        display_text = self.text
        if self.is_editing and counter % 60 < 30:
            display_text = display_text[:self.cursor_pos] + "|" + display_text[self.cursor_pos:]
        
        render.draw_text(ctx, display_text, (self.rect[0] + 5, self.rect[1] + 5), field_color, font_size=20, font_path="font/Tektur-Black.ttf")


class Button:
    
    def __init__(self, rect, text, color, enabled_callback=None):
        self.rect = rect
        self.text = text
        self.color = color
        self.enabled_callback = enabled_callback
    
    def is_enabled(self):
        return self.enabled_callback() if self.enabled_callback else True
    
    def is_clicked(self, mouse_pos):
        return (mouse_pos[0] > self.rect[0] and mouse_pos[0] < self.rect[0] + self.rect[2] and
                mouse_pos[1] > self.rect[1] and mouse_pos[1] < self.rect[1] + self.rect[3])
    
    def draw(self, ctx, line_prog):
        enabled = self.is_enabled()
        button_color = self.color if enabled else (100, 100, 100)
        render.draw_rect(ctx, self.rect, (0, 0, 0), line_prog, True)
        render.draw_rect(ctx, self.rect, button_color, line_prog, False)
        render.draw_text(ctx, self.text, (self.rect[0] + 20, self.rect[1] + 10), button_color, font_size=25, font_path="font/Tektur-Black.ttf")


# ===========================
# MAIN CONNECTION MENU
# ===========================

class ConnectionMenu:
    
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height
        self.counter = 0
        self.mouse_pos = (0, 0)
        self.mouse_release = False
        
        self.network = NetworkHandler()
        self.network.set_callbacks(
            on_log_update=self._on_log_update,
            on_status_change=self._on_status_change
        )
        
        self.game_manager = OnlineGameManager(ctx, line_prog, width, height, self.network)
        self.response_data = None

        self.connection_status = "DISCONNECTED"
        self.connected = False
        self.server_info = {"ip": "", "port": 5000}
        self.connection_log = []
        
        self.ip_field = InputField((200, 150, 300, 30), 15, '0123456789.', "192.168.1.6")
        self.port_field = InputField((200, 200, 150, 30), 5, '0123456789', "5000")
        self.message_field = InputField((200, 400, 400, 30), 100, None, "")
        
        self.connect_btn = Button((30, 300, 200, 50), "   CONNECT", (0, 255, 0), lambda: not self.connected)
        self.disconnect_btn = Button((250, 300, 200, 50), "DISCONNECT", (255, 100, 0), lambda: self.connected)
        self.send_btn = Button((30, 450, 200, 50), "SEND MSG", (0, 255, 255), lambda: self.connected)
        self.clear_log_btn = Button((250, 450, 200, 50), "CLEAR LOG", (255, 255, 0), lambda: True)
        
        self.buttons = [self.connect_btn, self.disconnect_btn, self.send_btn, self.clear_log_btn]
        self.input_fields = [self.ip_field, self.port_field, self.message_field]
    

        self.last_ping_time = 0
        self.ping_interval = .5


    def _on_log_update(self, log):
        self.connection_log = log
    
    def _on_status_change(self, status, connected, server_ip, server_port):
        self.connection_status = status
        self.connected = connected
        self.server_info = {"ip": server_ip, "port": server_port}
    
    def handle_text_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                for field in self.input_fields:
                    field.is_editing = False
                return
            elif event.key == pygame.K_TAB:
                self._cycle_field_focus()
                return
            
            for field in self.input_fields:
                if field.is_editing:
                    field.handle_input(event)
                    break
    
    def _cycle_field_focus(self):
        current_editing = None
        for i, field in enumerate(self.input_fields):
            if field.is_editing:
                current_editing = i
                field.is_editing = False
                break
        
        if current_editing is None:
            self.ip_field.is_editing = True
        elif current_editing == 0:  
            self.port_field.is_editing = True
        elif current_editing == 1:
            if self.connected:
                self.message_field.is_editing = True
        elif current_editing == 2: 
            self.ip_field.is_editing = True
    
    def handle_mouse_input(self):
        if pygame.mouse.get_pressed()[0] and self.mouse_release:
            self.mouse_release = False
            
            if self.connect_btn.is_clicked(self.mouse_pos) and self.connect_btn.is_enabled():
                self.network.connect_to_server(self.ip_field.text, self.port_field.text)
            elif self.disconnect_btn.is_clicked(self.mouse_pos) and self.disconnect_btn.is_enabled():
                self.network.disconnect_from_server()
            elif self.send_btn.is_clicked(self.mouse_pos) and self.send_btn.is_enabled():
                if self.network.send_message(self.message_field.text):
                    self.message_field.text = ""
                    self.message_field.cursor_pos = 0
            elif self.clear_log_btn.is_clicked(self.mouse_pos):
                self.network.clear_log()
            
            for field in self.input_fields:
                field.is_editing = False
            
            if self.ip_field.is_clicked(self.mouse_pos):
                self.ip_field.is_editing = True
            elif self.port_field.is_clicked(self.mouse_pos):
                self.port_field.is_editing = True
            elif self.message_field.is_clicked(self.mouse_pos) and self.connected:
                self.message_field.is_editing = True
    
    def draw_background_elements(self):

        for i in range(0, self.HEIGHT, 8):
            if (self.counter + i) % 120 < 50:
                render.draw_rect(self.ctx, (0, i, self.WIDTH, 1), (0, 50, 0), self.line_prog, True)
        
        border_color = (0, 180, 0)
        border_thickness = 3
        render.draw_rect(self.ctx, (0, 0, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, self.HEIGHT - border_thickness, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.WIDTH - border_thickness, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)
        
        header_y = 20
        render.draw_text(self.ctx, "CLIENT CONNECTION TERMINAL v1.0", (20, header_y), (0, 255, 0), font_size=35, font_path="font/Tektur-Black.ttf")
        render.draw_text(self.ctx, f"TIME: {time.strftime('%H:%M:%S')}", (self.WIDTH - 250, header_y), (0, 255, 0), font_size=25, font_path="font/Tektur-Black.ttf")
        
        separator_y = header_y + 50
        for i in range(0, self.WIDTH - 40, 20):
            render.draw_text(self.ctx, "-", (20 + i, separator_y), (0, 150, 0), font_size=25, font_path="font/Tektur-Black.ttf")
    
    def draw_connection_status(self):
        status_y = 100
        render.draw_text(self.ctx, "STATUS:", (30, status_y), (0, 255, 0), font_size=30, font_path="font/Tektur-Black.ttf")
        status_color = (0, 255, 0) if self.connected else (255, 100, 0)
        render.draw_text(self.ctx, self.connection_status, (180, status_y), status_color, font_size=30, font_path="font/Tektur-Black.ttf")
        
        if self.connected:
            target_text = f"TARGET: {self.server_info['ip']}:{self.server_info['port']}"
            render.draw_text(self.ctx, target_text, (400, status_y), (0, 255, 0), font_size=25, font_path="font/Tektur-Black.ttf")
    
    def draw_connection_log(self):
        log_start_y = 520
        log_height = self.HEIGHT - 570
        
        render.draw_text(self.ctx, "CONNECTION LOG:", (30, log_start_y), (0, 255, 0), font_size=25, font_path="font/Tektur-Black.ttf")
        
        log_rect = (20, log_start_y + 30, self.WIDTH - 40, log_height)
        render.draw_rect(self.ctx, log_rect, (0, 30, 0), self.line_prog, True)
        render.draw_rect(self.ctx, log_rect, (0, 150, 0), self.line_prog, False)
        
        y_offset = log_start_y + 50
        line_height = 20
        
        visible_entries = min(len(self.connection_log), (log_height - 40) // line_height)
        start_index = max(0, len(self.connection_log) - visible_entries)
        
        for i in range(start_index, len(self.connection_log)):
            entry = self.connection_log[i]
            display_y = y_offset + (i - start_index) * line_height
            
            if display_y < log_start_y + log_height:
                render.draw_text(self.ctx, entry['timestamp'], (30, display_y), (0, 200, 0), font_size=15, font_path="font/Tektur-Black.ttf")
                
                source_colors = {'CLIENT': (100, 100, 255), 'SERVER': (255, 100, 100), 'PERSON': (100, 255, 100)}
                source_color = source_colors.get(entry['source'], (200, 200, 200))
                
                render.draw_text(self.ctx, f"[{entry['source']}]", (120, display_y), source_color, font_size=15, font_path="font/Tektur-Black.ttf")
                render.draw_text(self.ctx, entry['message'], (200, display_y), (255, 255, 100), font_size=15, font_path="font/Tektur-Black.ttf")
    
    def render_menu(self):
        self.draw_background_elements()
        self.draw_connection_status()
        
        self.ip_field.draw(self.ctx, self.line_prog, "SERVER IP:", (30, 160), self.counter)
        self.port_field.draw(self.ctx, self.line_prog, "PORT:", (30, 210), self.counter)
        if self.connected:
            self.message_field.draw(self.ctx, self.line_prog, "MESSAGE:", (30, 410), self.counter)
        
        for button in self.buttons:
            if button == self.send_btn and not self.connected:
                continue
            button.draw(self.ctx, self.line_prog)
        
        self.draw_connection_log()
    
    def render(self, gamestates, main, events=None):
        self.counter += 1
        self.mouse_pos = pygame.mouse.get_pos()
        
        if not pygame.mouse.get_pressed()[0]:
            self.mouse_release = True
        
        if events:
            for event in events:
                self.handle_text_input(event)
        
        self.handle_mouse_input()
        
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        
        current_time = time.time()
        if current_time - self.last_ping_time >= self.ping_interval:
            self.last_ping_time = current_time
            
            def ping_in_background():
                try:
                    response = self.network.ping_server(self.game_manager.data_to_send)
                    self.game_manager.game.quene_units = []
                    if isinstance(response, str):
                        self.game_manager.game.decompile_data_client(ast.literal_eval(response))
                except Exception as e:
                    print(f"Ping error: {e}")
            
            threading.Thread(target=ping_in_background, daemon=True).start()
        
        if self.network.in_game:
            if not self.game_manager.game_active:
                self.game_manager.start_game()
            
            if events and self.game_manager.handle_game_input(events):
                return 
            
            self.game_manager.render_game(gamestates, main, events)
        else:
            self.render_menu()








def is_clicked(self, mouse_pos):
    return (mouse_pos[0] > self.rect[0] and mouse_pos[0] < self.rect[0] + self.rect[2] and
            mouse_pos[1] > self.rect[1] and mouse_pos[1] < self.rect[1] + self.rect[3])

InputField.is_clicked = is_clicked


# ===========================
# MAIN ENTRY POINT
# ===========================

# Update the main class name for compatibility
Connection_Menu = ConnectionMenu

if __name__ == "__main__":
    import pygame
    import render
    
    pygame.init()
    WIDTH, HEIGHT = 1280, 720
    screen, ctx, line_prog = render.initialize_context(WIDTH, HEIGHT)
    
    client_screen = ConnectionMenu(ctx, line_prog, WIDTH, HEIGHT)
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            events.append(event)
        
        client_screen.render(None, None, events)
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()