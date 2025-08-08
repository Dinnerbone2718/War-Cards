import pygame
from pygame.locals import *
import render
import os
from game import Game
from menu import Menu
from deck_creation import Deck_Creation_Menu
from sandbox_settings import Sandbox_Menu
from join_menu import Connection_Menu
from settings import Settings
from terminal import Terminal
from campaign import Campaign_Menu
from shop import Shop
import card_global
import global_vals
import json

#print("PID:", os.getpid())






class GameStates:
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    OPTIONS = "options"
    DECK_BUILD = "deck_build"
    SANDBOX_MENU = "sandbox_menu"
    TERMINAL = "terminal"
    CAMPAIGN = "campaign"
    SHOP = "shop"
    MULTIPLAYER_MENU = "multiplayer_menu"

class MainApp:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefix = f"{script_dir}/"
        self.WIDTH, self.HEIGHT = global_vals.SCREEN_SIZE
        self.screen, self.ctx, self.line_prog = render.initialize_context(self.WIDTH, self.HEIGHT)
        pygame.display.set_caption("3D Terrain Renderer")
    
        self.current_state = GameStates.MENU
        self.running = True
        self.clock = pygame.time.Clock()
         
        self.frame_count = 0
        self.last_time = pygame.time.get_ticks()
        self.fps_display_time = 0
        
        self.initialize_game_objects()

        

        with open(f"{self.prefix}owned_cards.json", "r") as f:
            owned_cards = json.load(f)
        
        
        card_global.owned_cards = owned_cards

        print("Owned Cards:", card_global.owned_cards)


        

        self.needs_resize = False


    def initialize_game_objects(self):
        self.game = Game(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)
        self.menu = Menu(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)
        self.deck_build = Deck_Creation_Menu(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)
        self.sandbox_menu = Sandbox_Menu(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)
        self.settings_menu = Settings(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)
        self.terminal = Terminal(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)
        self.campaign = Campaign_Menu(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)
        self.shop = Shop(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)
        self.connection_menu = Connection_Menu(self.ctx, self.line_prog, self.WIDTH, self.HEIGHT)

    def handle_resize(self):
        self.WIDTH, self.HEIGHT = global_vals.SCREEN_SIZE

        pygame.quit()

        print("RESTART")

        render.clear_text_cache()
        
        pygame.init()
        
        self.screen, self.ctx, self.line_prog = render.initialize_context(self.WIDTH, self.HEIGHT)
        
        self.initialize_game_objects()
        
        pygame.display.set_caption("3D Terrain Renderer")

    def handle_events(self):
        self.events = []
        for event in pygame.event.get():
            self.events.append(event)
            if event.type == pygame.QUIT: 
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                print(f"Pygame resize event: {event.w}x{event.h}")

    def check_for_resize(self):
        if self.WIDTH != global_vals.SCREEN_SIZE[0] or self.HEIGHT != global_vals.SCREEN_SIZE[1]:
            self.needs_resize = True

    def update_fps_display(self):
        current_time = pygame.time.get_ticks()
        self.frame_count += 1
        
        if current_time - self.last_time > self.fps_display_time:
            fps = self.frame_count * 1000 / (current_time - self.last_time)
            pygame.display.set_caption(f"3D Terrain Renderer - FPS: {fps:.1f}")
            self.frame_count = 0
            self.last_time = current_time
    
    def run(self):
        while self.running:
            self.handle_events()
            
            self.check_for_resize()
            if self.needs_resize:
                self.handle_resize()
                self.needs_resize = False
                continue
            
            self.update_fps_display()
            
            self.ctx.clear(0, 0, 0)
            
            if self.current_state == GameStates.PLAYING:  
                self.game.render(GameStates, self, self.events)
                self.game.update()
            elif self.current_state == GameStates.MENU:
                self.render_menu()
            elif self.current_state == GameStates.PAUSED:
                self.render_pause_screen()
            elif self.current_state == GameStates.GAME_OVER:
                self.render_game_over()
            elif self.current_state == GameStates.DECK_BUILD:
                self.render_deck_create()
            elif self.current_state == GameStates.SANDBOX_MENU:
                self.sandbox_menu.render_menu(GameStates, self, self.events)
            elif self.current_state == GameStates.OPTIONS:
                self.settings_menu.render_menu(GameStates, self, self.events)
            elif self.current_state == GameStates.TERMINAL:
                self.terminal.render_menu(GameStates, self, self.events)
            elif self.current_state == GameStates.CAMPAIGN:
                self.campaign.draw(GameStates, self, self.events)
            elif self.current_state == GameStates.SHOP:
                self.shop.draw(GameStates, self)
            elif self.current_state == GameStates.MULTIPLAYER_MENU:
                self.connection_menu.render(GameStates, self, self.events)


            pygame.display.flip()
            self.clock.tick(60)

        self.cleanup()
    
    def render_menu(self):
        self.menu.render_menu(GameStates, self)
    
    def render_deck_create(self):
        self.deck_build.draw(GameStates, self)

    def render_pause_screen(self):
        pass
    
    def render_game_over(self):
        pass
    
    def cleanup(self):

        with open(f"{self.prefix}owned_cards.json", "w") as f:
            json.dump(card_global.owned_cards, f, indent=4)

        pygame.quit()


if __name__ == "__main__":
    import cProfile
    app = MainApp()
    #cProfile.run('app.run()', sort='tottime')
    app.run()