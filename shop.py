import entity as e
import render
import pygame
from card_global import owned_cards, card_instances
import json
import random
import card_global
import global_vals

class Shop:
    def __init__(self, ctx, line_prog, width, height):
        self.ctx = ctx
        self.line_prog = line_prog
        self.WIDTH = width
        self.HEIGHT = height
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_release = False
        self.card_x_scroll = 0
        self.counter = 0
        self.load_money()
        self.back_button_rect = (50, self.HEIGHT - 100, 150, 50)
        self.refresh_shop_button_rect = (self.WIDTH - 300, self.HEIGHT - 100, 200, 50)
        self.shop_inventory = {}
        self.shop_prices = {}
        self.generate_shop_inventory()
        self.purchase_message = ""
        self.purchase_message_timer = 0

    def load_money(self):
        try:
            with open("save_data.json", "r") as f:
                data = json.load(f)
                global_vals.money = data.get("money", 1000)
        except FileNotFoundError:
            global_vals.money = 1000
            self.save_money()

    def save_money(self):
        try:
            with open("save_data.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        data["money"] = global_vals.money
        with open("save_data.json", "w") as f:
            json.dump(data, f)

    def generate_shop_inventory(self):
        self.shop_inventory.clear()
        self.shop_prices.clear()
        if not card_instances:
            return
        all_card_ids = list(card_instances.keys())
        num_cards = random.randint(6, 10)
        selected_cards = random.sample(all_card_ids, min(num_cards, len(all_card_ids)))
        for card_id in selected_cards:
            quantity = random.randint(1, 5)
            self.shop_inventory[card_id] = quantity
            card = card_instances[card_id].entity
            base_price = card.danger * 20
            self.shop_prices[card_id] = base_price

    def draw_money_display(self):
        money_text = f"Credits: {global_vals.money}"
        render.draw_text(self.ctx, money_text, (self.WIDTH - 250, 20), (255, 255, 0), font_size=30)

    def draw_back_button(self):
        render.draw_rect(self.ctx, self.back_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.back_button_rect, (0, 255, 0), self.line_prog, False)
        render.draw_text(self.ctx, "Back", (self.back_button_rect[0] + 50, self.back_button_rect[1] + 15), (0, 255, 0), font_size=30)

    def is_back_button_clicked(self):
        return (self.mouse_pos[0] > self.back_button_rect[0] and 
                self.mouse_pos[0] < self.back_button_rect[0] + self.back_button_rect[2] and
                self.mouse_pos[1] > self.back_button_rect[1] and 
                self.mouse_pos[1] < self.back_button_rect[1] + self.back_button_rect[3])

    def draw_refresh_shop_button(self):
        render.draw_rect(self.ctx, self.refresh_shop_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, self.refresh_shop_button_rect, (0, 255, 0), self.line_prog, False)
        render.draw_text(self.ctx, "Refresh Shop", (self.refresh_shop_button_rect[0] + 30, self.refresh_shop_button_rect[1] + 15), (0, 255, 0), font_size=25)

    def is_refresh_shop_button_clicked(self):
        return (self.mouse_pos[0] > self.refresh_shop_button_rect[0] and 
                self.mouse_pos[0] < self.refresh_shop_button_rect[0] + self.refresh_shop_button_rect[2] and
                self.mouse_pos[1] > self.refresh_shop_button_rect[1] and 
                self.mouse_pos[1] < self.refresh_shop_button_rect[1] + self.refresh_shop_button_rect[3])

    def draw_shop_card(self, card_id, x, y):
        if card_id not in card_instances:
            return None
        card = card_instances[card_id]
        price = self.shop_prices[card_id]
        quantity = self.shop_inventory[card_id]
        card_x = x + self.card_x_scroll
        price_color = (0, 255, 0) if global_vals.money >= price else (255, 0, 0)
        render.draw_text(self.ctx, f"Price: {price}", (card_x, y - 50), price_color, font_size=20)
        stock_color = (255, 255, 255) if quantity > 0 else (150, 150, 150)
        render.draw_text(self.ctx, f"Stock: {quantity}", (card_x, y - 25), stock_color, font_size=18)
        card.draw(self.ctx, self.line_prog, card_x, y)
        buy_button_rect = (card_x + 10, y + card.card_height + 10, 80, 30)
        button_color = (0, 150, 0) if global_vals.money >= price and quantity > 0 else (100, 100, 100)
        render.draw_rect(self.ctx, buy_button_rect, (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, buy_button_rect, button_color, self.line_prog, False)
        button_text = "        BUY" if quantity > 0 else "  SOLD OUT"
        text_color = (255, 255, 255) if quantity > 0 else (150, 150, 150)
        render.draw_text(self.ctx, button_text, (buy_button_rect[0], buy_button_rect[1] + 8), text_color, font_size=18)
        return buy_button_rect

    def attempt_purchase(self, card_id):
        if card_id not in self.shop_inventory or card_id not in self.shop_prices:
            return
        price = self.shop_prices[card_id]
        quantity = self.shop_inventory[card_id]
        if quantity <= 0:
            self.purchase_message = "Item sold out!"
            self.purchase_message_timer = 180
            return
        if global_vals.money < price:
            self.purchase_message = "Not enough credits!"
            self.purchase_message_timer = 180
            return
        global_vals.money -= price
        self.shop_inventory[card_id] -= 1
        if card_id in owned_cards:
            owned_cards[card_id] += 1
        else:
            owned_cards[card_id] = 1
        self.purchase_message = f"Purchased!"
        self.purchase_message_timer = 180
        self.save_money()
        card_global.owned_cards[card_id] += 1

    def draw_purchase_message(self):
        if self.purchase_message_timer > 0:
            message_color = (0, 255, 0) if "Purchased" in self.purchase_message else (255, 0, 0)
            render.draw_text(self.ctx, self.purchase_message, (self.WIDTH // 2 - 100, 100), message_color, font_size=25)
            self.purchase_message_timer -= 1

    def draw_shop_header(self):
        render.draw_text(self.ctx, "TACTICAL SUPPLY DEPOT", (50, 20), (0, 255, 0), font_size=40)
        render.draw_text(self.ctx, "Use LEFT/RIGHT arrow keys to scroll", (50, 70), (0, 200, 0), font_size=20)

    def get_card_width(self):
        if not card_instances:
            return 200
        return list(card_instances.values())[0].card_width

    def calculate_scroll_bounds(self):
        if not self.shop_inventory:
            return 0, 0
        card_width = self.get_card_width()
        card_spacing = 40
        total_cards = len(self.shop_inventory)
        total_width = total_cards * (card_width + card_spacing)
        if total_width <= self.WIDTH:
            return 0, 0
        max_scroll = 0
        min_scroll = -(total_width - self.WIDTH + 100)
        return min_scroll, max_scroll

    def draw(self, gamestates, main):
        self.counter += 1
        self.mouse_pos = pygame.mouse.get_pos()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        for i in range(self.counter % 60 - 60, self.HEIGHT, 8):
            render.draw_rect(self.ctx, (0, i, self.WIDTH, 1), (0, 50, 0), self.line_prog, True)
        min_scroll, max_scroll = self.calculate_scroll_bounds()
        self.card_x_scroll = max(min_scroll, min(max_scroll, self.card_x_scroll))
        if pygame.mouse.get_pressed()[0] == False:
            self.mouse_release = True
        if pygame.mouse.get_pressed()[0] and self.mouse_release:
            if self.is_back_button_clicked():
                main.current_state = gamestates.MENU
                self.mouse_release = False
            elif self.is_refresh_shop_button_clicked():
                refresh_cost = 50
                if global_vals.money >= refresh_cost:
                    global_vals.money -= refresh_cost
                    self.generate_shop_inventory()
                    self.save_money()
                    self.purchase_message = f"Shop refreshed! (-{refresh_cost} credits)"
                    self.purchase_message_timer = 180
                else:
                    self.purchase_message = "Not enough credits to refresh!"
                    self.purchase_message_timer = 180
                self.mouse_release = False
            else:
                self.check_card_purchases()
        min_scroll, max_scroll = self.calculate_scroll_bounds()
        if min_scroll < max_scroll:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.card_x_scroll += 15
            elif keys[pygame.K_RIGHT]:
                self.card_x_scroll -= 15
        self.draw_shop_header()
        self.draw_money_display()
        self.draw_purchase_message()
        self.draw_shop_cards()
        render.draw_rect(self.ctx, (0, self.HEIGHT - 180, self.WIDTH, 180), (0, 0, 0), self.line_prog, True)
        render.draw_rect(self.ctx, (0, self.HEIGHT - 180, self.WIDTH, 180), (0, 255, 0), self.line_prog, False)
        self.draw_back_button()
        self.draw_refresh_shop_button()
        render.draw_text(self.ctx, "Refresh Cost: 50 Credits", (self.WIDTH - 300, self.HEIGHT - 130), (255, 255, 0), font_size=18)
        if pygame.mouse.get_pressed()[0]:
            self.mouse_release = False

    def check_card_purchases(self):
        if not self.shop_inventory:
            return
        card_width = self.get_card_width()
        card_spacing = 40
        index = 0
        for card_id in self.shop_inventory.keys():
            if self.shop_inventory[card_id] >= 0:
                card_x = 50 + index * (card_width + card_spacing)
                card_y = 180
                buy_button_rect = self.draw_shop_card(card_id, card_x, card_y)
                if buy_button_rect:
                    if (self.mouse_pos[0] > buy_button_rect[0] and 
                        self.mouse_pos[0] < buy_button_rect[0] + buy_button_rect[2] and
                        self.mouse_pos[1] > buy_button_rect[1] and 
                        self.mouse_pos[1] < buy_button_rect[1] + buy_button_rect[3]):
                        self.attempt_purchase(card_id)
                        self.mouse_release = False
                        break
                index += 1

    def draw_shop_cards(self):
        if not self.shop_inventory:
            render.draw_text(self.ctx, "No cards available in shop", 
                           (self.WIDTH // 2 - 150, self.HEIGHT // 2), 
                           (255, 255, 255), font_size=30)
            return
        card_width = self.get_card_width()
        card_spacing = 40
        index = 0
        for card_id in self.shop_inventory.keys():
            if self.shop_inventory[card_id] >= 0:
                card_x = 50 + index * (card_width + card_spacing)
                card_y = 180
                self.draw_shop_card(card_id, card_x, card_y)
                index += 1

if __name__ == "__main__":
    pygame.init()
    WIDTH, HEIGHT = 1920, 1080
    screen, ctx, line_prog = render.initialize_context(WIDTH, HEIGHT)
    shop = Shop(ctx, line_prog, WIDTH, HEIGHT)
    Clock = pygame.time.Clock()
    running = True
    while running:
        ctx.clear(0, 0, 0)
        Clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        shop.draw(None, None)
        pygame.display.flip()
    pygame.quit()
