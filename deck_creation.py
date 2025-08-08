import entity as e
import render
import pygame
import card_global
import re
import json
import os

class Deck_Creation_Menu:
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefix = f"{script_dir}/"

        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_release = False
        self.card_y_scroll_right = 0
        self.card_y_scroll_left = 0
        
        self.back_button_rect = (50, self.HEIGHT - 100, 150, 50)
        self.save_deck_button_rect = (self.WIDTH - 500, self.HEIGHT - 100, 150, 50)
        self.load_deck_button_rect = (self.WIDTH - 250, self.HEIGHT - 100, 150, 50)

        self.saved_decks_box_rect = (self.WIDTH - 750, self.HEIGHT - 100, 150, 50)
        self.saved_decks_dropdown_open = False
        
        self.counter = 0
        self.saved_deck_index = 0
        self.saved_decks = {}

        with open(f"{self.prefix}save_data.json", "r") as f:
            data = json.load(f)

        self.selected_deck_name = data["last_saved_deck"]

        if os.path.exists(f"{self.prefix}deck_saves"):
            for deck in os.listdir(f"{self.prefix}deck_saves"):
                if deck.endswith(".deck"):
                    deck_name = deck[:-5]                        
                    with open(f"{self.prefix}deck_saves/{deck}", "r") as f:
                        deck_data = "e"
                        self.saved_decks[deck_name] = deck_data

        self.load_deck()
        


    def draw_card_amount(self, amount, x, y):
        render.draw_text(self.ctx, str(amount), (x, y), (0, 255, 0), font_size=20)
    
    def draw_back_button(self):
        render.draw_rect(self.ctx, self.back_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.back_button_rect, (0, 255, 0), self.line_prog, False)
        render.draw_text(self.ctx, "Back", (self.back_button_rect[0] + 50, self.back_button_rect[1] + 15), (0, 255, 0), font_size=30)
    
    def is_back_button_clicked(self):
        return (self.mouse_pos[0] > self.back_button_rect[0] and 
                self.mouse_pos[0] < self.back_button_rect[0] + self.back_button_rect[2] and
                self.mouse_pos[1] > self.back_button_rect[1] and 
                self.mouse_pos[1] < self.back_button_rect[1] + self.back_button_rect[3])
    
    def draw_save_deck_button(self):
        render.draw_rect(self.ctx, self.save_deck_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.save_deck_button_rect, (0, 255, 0), self.line_prog, False)
        render.draw_text(self.ctx, "Save Deck", (self.save_deck_button_rect[0] + 30, self.save_deck_button_rect[1] + 15), (0, 255, 0), font_size=30)
    
    def is_save_deck_button_clicked(self):
        return (self.mouse_pos[0] > self.save_deck_button_rect[0] and 
                self.mouse_pos[0] < self.save_deck_button_rect[0] + self.save_deck_button_rect[2] and
                self.mouse_pos[1] > self.save_deck_button_rect[1] and 
                self.mouse_pos[1] < self.save_deck_button_rect[1] + self.save_deck_button_rect[3])

    def draw_load_deck_button(self):
        render.draw_rect(self.ctx, self.load_deck_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.load_deck_button_rect, (0, 255, 0), self.line_prog, False)
        render.draw_text(self.ctx, "Load Deck", (self.load_deck_button_rect[0] + 30, self.load_deck_button_rect[1] + 15), (0, 255, 0), font_size=30)
    
    def is_load_deck_button_clicked(self):
        return (self.mouse_pos[0] > self.load_deck_button_rect[0] and 
                self.mouse_pos[0] < self.load_deck_button_rect[0] + self.load_deck_button_rect[2] and
                self.mouse_pos[1] > self.load_deck_button_rect[1] and 
                self.mouse_pos[1] < self.load_deck_button_rect[1] + self.load_deck_button_rect[3])

    def draw_saved_decks_dropdown(self):
        render.draw_rect(self.ctx, self.saved_decks_box_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.saved_decks_box_rect, (0, 255, 0), self.line_prog, False)
        
        text_x = self.saved_decks_box_rect[0] + 10
        text_y = self.saved_decks_box_rect[1] + 10
        render.draw_text(self.ctx, self.selected_deck_name, (text_x, text_y), (0, 255, 0), font_size=20)
        


        if self.saved_decks_dropdown_open and self.saved_decks:
            dropdown_height = min(len(self.saved_decks) * 35, 200) 
            dropdown_rect = (
                self.saved_decks_box_rect[0],
                self.saved_decks_box_rect[1] - dropdown_height,
                self.saved_decks_box_rect[2],
                dropdown_height
            )
            
            render.draw_rect(self.ctx, dropdown_rect, (0, 0, 0), self.line_prog, True)
            render.draw_rect(self.ctx, dropdown_rect, (0, 255, 0), self.line_prog, False)
            
            for i, deck_name in enumerate(self.saved_decks.keys()):
                option_rect = (
                    dropdown_rect[0],
                    dropdown_rect[1] + i * 35,
                    dropdown_rect[2],
                    35
                )
                
                if (self.mouse_pos[0] > option_rect[0] and 
                    self.mouse_pos[0] < option_rect[0] + option_rect[2] and
                    self.mouse_pos[1] > option_rect[1] and 
                    self.mouse_pos[1] < option_rect[1] + option_rect[3]):
                    render.draw_rect(self.ctx, option_rect, (0, 50, 0), self.line_prog, True)
                
                render.draw_text(self.ctx, deck_name, 
                               (option_rect[0] + 10, option_rect[1] + 8), 
                               (0, 255, 0), font_size=18)

    def is_saved_decks_box_clicked(self):
        return (self.mouse_pos[0] > self.saved_decks_box_rect[0] and 
                self.mouse_pos[0] < self.saved_decks_box_rect[0] + self.saved_decks_box_rect[2] and
                self.mouse_pos[1] > self.saved_decks_box_rect[1] and 
                self.mouse_pos[1] < self.saved_decks_box_rect[1] + self.saved_decks_box_rect[3])
    

    def get_clicked_deck_option(self):
        if not self.saved_decks_dropdown_open or not self.saved_decks:
            return None
        
        dropdown_height = min(len(self.saved_decks) * 35, 200)
        dropdown_rect = (
            self.saved_decks_box_rect[0],
            self.saved_decks_box_rect[1] - dropdown_height,
            self.saved_decks_box_rect[2],
            dropdown_height
        )
        
        if (self.mouse_pos[0] > dropdown_rect[0] and 
            self.mouse_pos[0] < dropdown_rect[0] + dropdown_rect[2] and
            self.mouse_pos[1] > dropdown_rect[1] and 
            self.mouse_pos[1] < dropdown_rect[1] + dropdown_rect[3]):
            
            relative_y = self.mouse_pos[1] - dropdown_rect[1]
            option_index = relative_y // 35
            
            if 0 <= option_index < len(self.saved_decks):
                return list(self.saved_decks.keys())[option_index]
        
        return None



    def draw(self, gamestates, main):
        self.counter += 1

        self.mouse_pos = pygame.mouse.get_pos()
        render.draw_rect(self.ctx, (0, 0, self.WIDTH/2, self.HEIGHT), (0, 255, 0), self.line_prog)
        render.draw_rect(self.ctx, (self.WIDTH/2 + 1, 0, self.WIDTH/2 - 2, self.HEIGHT), (255, 0, 0), self.line_prog)
       
        for i in range(self.counter % 60 - 60, self.HEIGHT, 8):
            render.draw_rect(self.ctx, (0, i, self.WIDTH, 1), (0, 50, 0), self.line_prog, True)

        if self.card_y_scroll_left > 0:
            self.card_y_scroll_left = 0
        elif self.card_y_scroll_left < -((len(card_global.owned_cards) // 2) * (280 + 20)):
            self.card_y_scroll_left = -((len(card_global.owned_cards) // 2) * (280 + 20))
        
        if self.card_y_scroll_right > 0:
            self.card_y_scroll_right = 0 
        elif self.card_y_scroll_right < -((len(card_global.cards_in_deck) // 2) * (280 + 20)):
            self.card_y_scroll_right = -((len(card_global.cards_in_deck) // 2) * (280 + 20))
       
        if pygame.mouse.get_pressed()[0] == False:
            self.mouse_release = True
        
        if pygame.mouse.get_pressed()[0] and self.mouse_release:
            if self.is_back_button_clicked():
                print("Back button clicked")
                main.current_state = gamestates.MENU
                self.mouse_release = False
            elif self.is_saved_decks_box_clicked():
                self.saved_decks_dropdown_open = not self.saved_decks_dropdown_open
                self.mouse_release = False
            elif self.saved_decks_dropdown_open:
                clicked_deck = self.get_clicked_deck_option()
                if clicked_deck:
                    self.saved_decks_dropdown_open = False
                    self.mouse_release = False
                    self.selected_deck_name = clicked_deck
                else:
                    self.saved_decks_dropdown_open = False
                    self.mouse_release = False

        keys = pygame.key.get_pressed()
        if pygame.mouse.get_pos()[0] > self.WIDTH/2:
            if keys[pygame.K_UP]:
                self.card_y_scroll_right += 10
            elif keys[pygame.K_DOWN]:
                self.card_y_scroll_right -= 10
        else:
            if keys[pygame.K_UP]:
                self.card_y_scroll_left += 10
            elif keys[pygame.K_DOWN]:
                self.card_y_scroll_left -= 10

        index = 0
        for card_id in card_global.owned_cards.keys():
            if card_global.owned_cards[card_id] > 0:
                card = card_global.card_instances[card_id] 
                card_x = 85 + (index % 2) * (card.card_width + 20)
                card_y = 10 + (index // 2) * (card.card_height + 20)
                if card_y + self.card_y_scroll_left > -280 and card_y + self.card_y_scroll_left < self.HEIGHT + 200:
                    card.draw(self.ctx, self.line_prog, card_x, card_y + self.card_y_scroll_left)
                    self.draw_card_amount(card_global.owned_cards[card_id], card_x + 200, card_y + 10 + self.card_y_scroll_left)
                
                if (self.mouse_pos[0] > card_x and self.mouse_pos[0] < card_x + card.card_width and 
                    self.mouse_pos[1] > card_y + self.card_y_scroll_left and 
                    self.mouse_pos[1] < card_y + self.card_y_scroll_left + card.card_height
                    and self.HEIGHT/4 * 3 > self.mouse_pos[1]):
                    if pygame.mouse.get_pressed()[0] and self.mouse_release:
                        self.mouse_release = False
                        card_global.owned_cards[card_id] -= 1
                        card_global.cards_in_deck[card_id] += 1
                index += 1

        index = 0
        for card_id in card_global.cards_in_deck.keys():
            if card_global.cards_in_deck[card_id] > 0:
                card = card_global.card_instances[card_id]  
                card_x = self.WIDTH/2 + 85 + (index % 2) * (card.card_width + 20)
                card_y = 10 + (index // 2) * (card.card_height + 20)
                if card_y + self.card_y_scroll_right > -280 and card_y + self.card_y_scroll_right < self.HEIGHT + 200:
                    card.draw(self.ctx, self.line_prog, card_x, card_y + self.card_y_scroll_right)
                    self.draw_card_amount(card_global.cards_in_deck[card_id], card_x + 200, card_y + 10 + self.card_y_scroll_right)
                
                if (self.mouse_pos[0] > card_x and self.mouse_pos[0] < card_x + card.card_width and 
                    self.mouse_pos[1] > card_y + self.card_y_scroll_right and 
                    self.mouse_pos[1] < card_y + self.card_y_scroll_right + card.card_height
                    and self.HEIGHT/4 * 3 > self.mouse_pos[1]):
                    if pygame.mouse.get_pressed()[0] and self.mouse_release:
                        self.mouse_release = False
                        card_global.cards_in_deck[card_id] -= 1
                        card_global.owned_cards[card_id] += 1
                index += 1

        cards_in_deck_total = sum(card_global.cards_in_deck.values())

        #render.draw_text(self.ctx, f"{cards_in_deck_total}/20", (self.WIDTH - 90, 10), (0, 255, 0), font_size=50)

        render.draw_rect(self.ctx, (0, self.HEIGHT - 180, self.WIDTH, 180), (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, (0, self.HEIGHT - 180, self.WIDTH, 180), (0, 255, 0), self.line_prog, False)
        
        self.draw_back_button()
        self.draw_save_deck_button()
        self.draw_load_deck_button()
        self.draw_saved_decks_dropdown()


        if self.is_save_deck_button_clicked() and pygame.mouse.get_pressed()[0] and self.mouse_release:
            self.save_deck()

        if self.is_load_deck_button_clicked() and pygame.mouse.get_pressed()[0] and self.mouse_release:
            self.load_deck()


        if pygame.mouse.get_pressed()[0]:
            self.mouse_release = False



    def save_deck(self):
        deck_name = self.selected_deck_name

        deck_data = card_global.cards_in_deck

        with open(f"{self.prefix}deck_saves/{deck_name}.deck", "w") as f:
            json.dump(deck_data, f)

        with open(f"{self.prefix}save_data.json", "r") as f:
            data = json.load(f)
        
        data["last_saved_deck"] = deck_name

        with open(f"{self.prefix}save_data.json", "w") as f:
            json.dump(data, f)
        
        print(f"Deck '{deck_name}' saved successfully.")

    def load_deck(self):

        for card_id in card_global.cards_in_deck:
            card_global.owned_cards[card_id] += card_global.cards_in_deck[card_id]
            card_global.cards_in_deck[card_id] = 0

        deck_name = self.selected_deck_name

        with open(f"{self.prefix}deck_saves/{deck_name}.deck", "r") as f:
            data = json.load(f)

        for card_id in data:
            amount = data[card_id]
            card_global.cards_in_deck[card_id] = amount
            card_global.owned_cards[card_id] -= amount


            


if __name__ == "__main__":
    pygame.init()
    WIDTH, HEIGHT = 1280, 720
    screen, ctx, line_prog = render.initialize_context(WIDTH, HEIGHT)
    deck_menu = Deck_Creation_Menu(ctx, line_prog, WIDTH, HEIGHT)

    Clock = pygame.time.Clock()

    running = True
    while running:
        ctx.clear(0, 0, 0)
        Clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        deck_menu.draw(None, None)
        pygame.display.flip()

    pygame.quit()