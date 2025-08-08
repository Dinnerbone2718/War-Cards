import global_vals
import render
import pygame
import json
import random
import os

class Terminal:
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height

        self.game = 0
        
        self.birb_game = flappy_bird()
        self.puzzle_lock = puzzle_lock()
        self.snake_game = snake_game()

        self.tick = 0
        
        self.terminal_lines = []
        self.current_line = ""
        self.cursor_pos = 0
        self.cursor_blink_timer = 0
        self.cursor_visible = True
        
        self.font_size = 16
        self.line_height = 20
        self.text_start_x = 20
        self.text_start_y = 30
        self.max_lines = (height - 150) // self.line_height
        
        self.char_width = 10 

        self.leave = False
        
        self.terminal_lines.append("STONEWALL TERMINAL v1.0 READY")
        self.terminal_lines.append("Type commands and press ENTER...")
        self.terminal_lines.append("")


    def print_console(self, text):
        self.terminal_lines.append(text)
        self.current_line = ""
        self.cursor_pos = 0
        if len(self.terminal_lines) > self.max_lines:
            self.terminal_lines = self.terminal_lines[-self.max_lines:]

    def handle_text_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.terminal_lines.append(f"> {self.current_line}")
                    if self.current_line.strip():
                        response = self.process_command(self.current_line.strip())
                        if response:
                            self.terminal_lines.append(response)
                    self.current_line = ""
                    self.cursor_pos = 0
                    if len(self.terminal_lines) > self.max_lines:
                        self.terminal_lines = self.terminal_lines[-self.max_lines:]
                elif event.key == pygame.K_BACKSPACE:
                    if self.cursor_pos > 0:
                        self.current_line = self.current_line[:self.cursor_pos-1] + self.current_line[self.cursor_pos:]
                        self.cursor_pos -= 1
                elif event.key == pygame.K_DELETE:
                    if self.cursor_pos < len(self.current_line):
                        self.current_line = self.current_line[:self.cursor_pos] + self.current_line[self.cursor_pos+1:]
                elif event.key == pygame.K_LEFT:
                    if self.cursor_pos > 0:
                        self.cursor_pos -= 1
                elif event.key == pygame.K_RIGHT:
                    if self.cursor_pos < len(self.current_line):
                        self.cursor_pos += 1
                elif event.key == pygame.K_HOME:
                    self.cursor_pos = 0
                elif event.key == pygame.K_END:
                    self.cursor_pos = len(self.current_line)
            elif event.type == pygame.TEXTINPUT:
                self.current_line = self.current_line[:self.cursor_pos] + event.text + self.current_line[self.cursor_pos:]
                self.cursor_pos += len(event.text)

    def process_command(self, command):
        command = command.lower()
        if command == "help":
            return "Available commands: help, clear, user, status, time, echo [text], quit, secret"
        elif command == "clear":
            self.terminal_lines = []
            return None
        elif command == "quit":
            self.leave = True
            return "quitting"
        elif command == "status":
            return "SYSTEM STATUS: ALL SYSTEMS OPERATIONAL"
        elif command == "user":
            return(os.getlogin())
        elif command == "time":
            import time
            return f"SYSTEM TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        elif command.startswith("echo "):
            return command[5:]
        elif command.startswith("print "):
            self.print_console(command[6:])
        elif command == "sam":
            temp = [
                "",
                "                 ########",
                "       ##                              ##",
                "       #       #               #        #",
                "       #                                    #",
                "       #                                    #",
                "       #                                    #",
                "       #   #                       #    #",
                "       #       #######        #",
                "       #                                    #",
                "       ##      #          #        ##",
                "           #           ##          #",
                "               #                   #",
                "                ########",
                "                         ##",
                "                         ##",


            ]
            for x in temp:
                self.print_console(x)


        elif command == "smile":
            temp = [
                " ~  ~ ",
                "",
                "~    ~",
                " ~~~~"


            ]
            for x in temp:
                self.print_console(x)

        elif command == "secret":
            return "Available commands: sam, smile, birb, puzzle, snake"  

        elif command == "birb":
            self.game = 1
            return "Starting"
        
        elif command == "puzzle":
            self.game = 2
            return "Starting"
        
        elif command == "snake":  
            self.game = 3
            return "Starting Snake Game"
        
        elif command == "":
            return None
        else:
            return f"Unknown command: {command}"

    def draw_terminal_border(self):
        border_color = (0, 180, 0)
        border_thickness = 3
        render.draw_rect(self.ctx, (0, 0, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, self.HEIGHT - border_thickness, self.WIDTH, border_thickness), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (0, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)
        render.draw_rect(self.ctx, (self.WIDTH - border_thickness, 0, border_thickness, self.HEIGHT), border_color, self.line_prog, True)

    def draw_text_with_tilde_rectangles(self, text, pos, color):
        if '~' not in text and '-' not in text:
            render.draw_text(self.ctx, text, pos, color, 
                           font_size=self.font_size, font_path="font\Tektur-Black.ttf")
        else:
            text_with_spaces = text.replace('~', ' ').replace('-', ' ')
            render.draw_text(self.ctx, text_with_spaces, pos, color, 
                           font_size=self.font_size, font_path="font\Tektur-Black.ttf")
            
            x, y = pos
            for i, char in enumerate(text):
                char_x = x + i * self.char_width
                if char == '~':
                    render.draw_rect(self.ctx, (char_x, y, self.char_width, self.font_size), color, self.line_prog, True)
                elif char == '-':
                    render.draw_rect(self.ctx, (char_x, y, self.char_width, self.font_size), color, self.line_prog, False)

    def draw_terminal_text(self):
        for i, line in enumerate(self.terminal_lines):
            y_pos = self.text_start_y + i * self.line_height
            if y_pos < self.HEIGHT - 120:
                color = (0, 255, 0) if line.startswith(">") else (0, 200, 0)
                self.draw_text_with_tilde_rectangles(line, (self.text_start_x, y_pos), color)
        
        current_y = self.text_start_y + len(self.terminal_lines) * self.line_height
        if current_y < self.HEIGHT - 120:
            current_display = f"> {self.current_line}"
            self.draw_text_with_tilde_rectangles(current_display, (self.text_start_x, current_y), (0, 255, 0))
            
            if self.cursor_visible:
                cursor_x = self.text_start_x + (self.cursor_pos + 2) * self.char_width
                cursor_y = current_y
                render.draw_rect(self.ctx, (cursor_x, cursor_y+2, 2, self.font_size), (0, 255, 0), self.line_prog, True)

    def update_cursor_blink(self):
        self.cursor_blink_timer += 1
        if self.cursor_blink_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_blink_timer = 0

    def render_menu(self, gamestates, main, events=None):
        self.tick += 1
        if self.game == 0:
            if events:
                self.handle_text_input(events)
            self.update_cursor_blink()
        elif self.game == 1:
            self.birb_game.draw(self)
        elif self.game == 2:
            self.puzzle_lock.draw(self)
        elif self.game == 3:
            self.snake_game.draw(self)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        self.draw_terminal_border()
        self.draw_terminal_text()

        if self.leave:
            self.leave = False
            main.current_state = gamestates.MENU



class flappy_bird:
    def __init__(self):
        self.bird_y = 10
        self.y_vel = 0
        self.space_up = False
        self.pipes = []
        self.pipe_timer = 0
        self.score = 0
        self.game_over = False
        self.tick = 0
        
    def add_pipe(self):
        gap_size = 4
        gap_start = random.randint(3, 16 - gap_size)
        pipe = {
            'x': 40,  
            'gap_start': gap_start,
            'gap_end': gap_start + gap_size,
            'scored': False
        }
        self.pipes.append(pipe)
    
    def update_pipes(self):
        for pipe in self.pipes:
            pipe['x'] -= 1
        
        self.pipes = [pipe for pipe in self.pipes if pipe['x'] > -5]
        
        self.pipe_timer += 1
        if self.pipe_timer >= 20: 
            self.add_pipe()
            self.pipe_timer = 0
    
    def check_collision(self):
        bird_row = 20 - int(self.bird_y)
        
        for pipe in self.pipes:
            if pipe['x'] <= 10 <= pipe['x'] + 3:
                if bird_row < pipe['gap_start'] or bird_row > pipe['gap_end']:
                    self.game_over = True
                    self.tick = 0
                    return True
        
        if self.bird_y <= 0 or self.bird_y >= 19:
            self.game_over = True
            self.tick = 0
            return True
            
        return False
    
    def update_score(self):
        bird_x = 10
        for pipe in self.pipes:
            if not pipe['scored'] and pipe['x'] + 3 < bird_x:
                pipe['scored'] = True
                self.score += 1
    
    def draw(self, Terminal):
        keys = pygame.key.get_pressed()
        self.tick += 1
        if self.game_over and self.tick < 240:
            Terminal.process_command("clear")
            Terminal.process_command("print GAME OVER!")
            Terminal.process_command(f"print Score: {self.score}")
            Terminal.process_command(f"print press r to restart")
            Terminal.process_command(f"print Qutting in: {240 - self.tick}")

            if keys[pygame.K_r] and self.game_over:
                self.__init__()

            return
        elif self.game_over:
            self.__init__()
            Terminal.process_command("clear")
            Terminal.game = 0
            return

            
        self.bird_y += self.y_vel
        self.y_vel -= .025
        
        if keys[pygame.K_SPACE] == False:
            self.space_up = True
        elif keys[pygame.K_SPACE] and self.space_up == True:
            self.space_up = False
            self.y_vel = .3
        

        
        if self.tick %3 ==0:
            self.update_pipes()

        self.check_collision()
        self.update_score()
        
        Terminal.process_command("clear")
        
        for y in range(20):
            line = ""
            for x in range(40):
                char = " "
                
                if x == 10 and y == 20 - int(self.bird_y):
                    char = "~"
                
                for pipe in self.pipes:
                    if pipe['x'] <= x <= pipe['x'] + 2:
                        if y < pipe['gap_start'] or y > pipe['gap_end']:
                            char = "~"
                
                line += char
            
            Terminal.process_command(f"print {line}")
        
        Terminal.process_command(f"print Score: {self.score}")
        
        Terminal.process_command("print SPACE to flap, R to restart")
    

class puzzle_lock:
    def __init__(self):
        self.x_pos = 20 
        self.y_pos = 10 
        self.game_over = False
        self.tick = 0
        self.move_delay = 0
        self.field_width = 40
        self.field_height = 20
        
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if self.move_delay > 0:
            self.move_delay -= 1
            return
            
        moved = False
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if self.x_pos > 1:
                self.x_pos -= 1
                moved = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if self.x_pos < self.field_width - 2: 
                self.x_pos += 1
                moved = True
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            if self.y_pos > 1: 
                self.y_pos -= 1
                moved = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if self.y_pos < self.field_height - 2:  
                self.y_pos += 1
                moved = True
                
        if moved:
            self.move_delay = 8  
    
    def draw_x_shape(self, field):

        positions = [
            (self.x_pos - 1, self.y_pos - 1),  
            (self.x_pos + 1, self.y_pos - 1),  
            (self.x_pos, self.y_pos),         
            (self.x_pos - 1, self.y_pos + 1),  
            (self.x_pos + 1, self.y_pos + 1), 
        ]
        
        for x, y in positions:
            if 0 <= x < self.field_width and 0 <= y < self.field_height:
                field[y][x] = "~"
    
    def draw(self, Terminal):
        keys = pygame.key.get_pressed()
        self.tick += 1
        
        if keys[pygame.K_ESCAPE] or keys[pygame.K_q]:
            Terminal.process_command("clear")
            Terminal.game = 0
            return
            
        self.handle_input()
        
        Terminal.process_command("clear")
        
        field = [[" " for _ in range(self.field_width)] for _ in range(self.field_height)]
        
        self.draw_x_shape(field)
        
        Terminal.process_command("print " + "~" * (self.field_width + 2))
        
        for y in range(self.field_height):
            line = "~" + "".join(field[y]) + "~"
            Terminal.process_command(f"print {line}")
        
        Terminal.process_command("print " + "~" * (self.field_width + 2))
        
        Terminal.process_command("print ")
        Terminal.process_command(f"print Go Check Out Puzzle Lock")
        Terminal.process_command("print Use ARROW KEYS or WASD to move")
        Terminal.process_command("print Press Q or ESC to quit")

class snake_game:
    def __init__(self):
        self.field_width = 40
        self.field_height = 20
        self.snake = [(20, 10), (19, 10), (18, 10)]  
        self.direction = (1, 0)  
        self.next_direction = (1, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        self.tick = 0
        self.move_delay = 0
        self.speed = 8  
        
    def spawn_food(self):
        while True:
            food_x = random.randint(0, self.field_width - 1)
            food_y = random.randint(0, self.field_height - 1)
            if (food_x, food_y) not in self.snake:
                return (food_x, food_y)
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.direction != (0, 1):
            self.next_direction = (0, -1)
        elif (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.direction != (-1, 0):
            self.next_direction = (1, 0)
    
    def update_snake(self):
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        if (new_head[0] < 0 or new_head[0] >= self.field_width or 
            new_head[1] < 0 or new_head[1] >= self.field_height):
            self.game_over = True
            return
        
        if new_head in self.snake:
            self.game_over = True
            return
        
        self.snake.insert(0, new_head)
        
        if new_head == self.food:
            self.score += 1
            self.food = self.spawn_food()
            if self.score % 5 == 0 and self.speed > 3:
                self.speed -= 1
        else:
            self.snake.pop() 
    
    def draw(self, Terminal):
        keys = pygame.key.get_pressed()
        self.tick += 1
        
        if keys[pygame.K_r] and self.game_over:
            self.__init__()
            return
            
        if keys[pygame.K_q] or keys[pygame.K_ESCAPE]:
            Terminal.process_command("clear")
            Terminal.game = 0
            return
        
        if self.game_over:
            Terminal.process_command("clear")
            Terminal.process_command("print GAME OVER!")
            Terminal.process_command(f"print Final Score: {self.score}")
            Terminal.process_command("print Press R to restart")
            Terminal.process_command("print Press Q to quit")
            return
        
        self.handle_input()
        
        self.move_delay += 1
        if self.move_delay >= self.speed:
            self.update_snake()
            self.move_delay = 0
        
        Terminal.process_command("clear")
        
        field = [[" " for _ in range(self.field_width)] for _ in range(self.field_height)]
        
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                field[y][x] = "-" 
            else:
                field[y][x] = "~"  
        
        food_x, food_y = self.food
        field[food_y][food_x] = "~"
        
        Terminal.process_command("print " + "~" * (self.field_width + 2))
        
        for y in range(self.field_height):
            line = "~" + "".join(field[y]) + "~"
            Terminal.process_command(f"print {line}")
        
        Terminal.process_command("print " + "~" * (self.field_width + 2))

        Terminal.process_command("print ")
        Terminal.process_command(f"print Score: {self.score}")
        Terminal.process_command(f"print Length: {len(self.snake)}")
        Terminal.process_command("print WASD or Arrow Keys to move")
        Terminal.process_command("print Q to quit")

if __name__ == "__main__":
    pygame.init()
    WIDTH, HEIGHT = 1280, 720
    screen, ctx, line_prog = render.initialize_context(WIDTH, HEIGHT)
    term = Terminal(ctx, line_prog, WIDTH, HEIGHT)

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

        term.render_menu(None, None, events)
        pygame.display.flip()

    pygame.quit()
