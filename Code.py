import pygame
import random

# Initialisiere pygame
pygame.init()

# Spieleinstellungen
WIDTH, HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Tower Defense")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Tower Klasse
class Tower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.range = 300
        self.damage = 10
        self.shots = []
        self.shoot_interval = 30
        self.shoot_timer = self.shoot_interval
        self.shots_per_shoot = 1
        self.hp = 100

    def draw(self, win):
        pygame.draw.circle(win, BLACK, (self.x, self.y), 20)
        pygame.draw.circle(win, RED, (self.x, self.y), self.range, 1)
        for shot in self.shots:
            shot.draw(win)

    def attack(self, monsters):
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            targets = [monster for monster in monsters if self.in_range(monster)]
            for i in range(min(self.shots_per_shoot, len(targets))):
                self.shoot(targets[i])
            self.shoot_timer = self.shoot_interval

    def in_range(self, monster):
        return ((self.x - monster.x)**2 + (self.y - monster.y)**2)**0.5 <= self.range

    def shoot(self, target):
        self.shots.append(Shot(self.x, self.y, target))

    def update_shots(self, monsters, coins, coin_value):
        for shot in self.shots[:]:
            shot.move()
            for monster in monsters[:]:
                if shot.hit(monster):
                    monsters.remove(monster)
                    coins += coin_value
                    if shot in self.shots:
                        self.shots.remove(shot)
                    break
            else:
                # Entferne den Schuss, wenn er das Ziel verfehlt hat und außerhalb des Bildschirms ist
                if not shot.is_in_bounds():
                    self.shots.remove(shot)
        return coins

# Shot Klasse
class Shot:
    def __init__(self, x, y, target):
        self.x = x
        self.y = y
        self.target = target
        self.speed = 10

    def draw(self, win):
        pygame.draw.circle(win, BLACK, (self.x, self.y), 5)

    def move(self):
        direction_x = self.target.x - self.x
        direction_y = self.target.y - self.y
        length = (direction_x**2 + direction_y**2)**0.5
        direction_x /= length
        direction_y /= length
        self.x += direction_x * self.speed
        self.y += direction_y * self.speed

    def hit(self, monster):
        if ((self.x - monster.x)**2 + (self.y - monster.y)**2)**0.5 <= 5:
            return True
        return False

    def is_in_bounds(self):
        return 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT

# Monster Klasse
class Monster:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.hp = 100
        self.speed = speed

    def draw(self, win):
        pygame.draw.circle(win, RED, (self.x, self.y), 10)

    def move(self, target_x, target_y):
        direction_x = target_x - self.x
        direction_y = target_y - self.y
        length = (direction_x**2 + direction_y**2)**0.5
        direction_x /= length
        direction_y /= length
        self.x += direction_x * self.speed
        self.y += direction_y * self.speed

# Menü Klasse
class Menu:
    def __init__(self, tower):
        self.width = 300
        self.is_open = True
        self.bg_color = BLUE
        self.upgrade_costs = {'faster_shoot': 50, 'more_shots': 50, 'greater_range': 50}
        self.upgrade_increment = 1.2
        self.coins = 0
        self.tower = tower

    def draw(self, win):
        if self.is_open:
            pygame.draw.rect(win, self.bg_color, (WIDTH - self.width, 0, self.width, HEIGHT))
            font = pygame.font.SysFont(None, 36)
            text = font.render('Upgrade Tower', True, WHITE)
            win.blit(text, (WIDTH - self.width + 20, 50))
            coin_text = font.render(f'Coins: {self.coins}', True, WHITE)
            win.blit(coin_text, (WIDTH - self.width + 20, 100))

            # Zeichne Upgrade Schaltflächen
            upgrades = [
                ('+ Speed ({})'.format(self.upgrade_costs['faster_shoot']), 'faster_shoot', self.upgrade_costs['faster_shoot'], 150),
                ('+ Projectiles ({})'.format(self.upgrade_costs['more_shots']), 'more_shots', self.upgrade_costs['more_shots'], 200),
                ('+ Range ({})'.format(self.upgrade_costs['greater_range']), 'greater_range', self.upgrade_costs['greater_range'], 250)
            ]
            for text, key, cost, y in upgrades:
                upgrade_text = font.render(text, True, WHITE)
                pygame.draw.rect(win, GREEN if self.coins >= cost else RED, (WIDTH - self.width + 20, y, 260, 40))
                win.blit(upgrade_text, (WIDTH - self.width + 25, y + 10))

    def toggle(self):
        self.is_open = not self.is_open

    def add_coins(self, amount):
        self.coins += amount

    def handle_upgrade(self, pos):
        if self.is_open and WIDTH - self.width < pos[0] < WIDTH:
            if 150 < pos[1] < 190 and self.coins >= self.upgrade_costs['faster_shoot']:
                self.tower.shoot_interval = max(1, int(self.tower.shoot_interval * 0.8))
                self.coins -= self.upgrade_costs['faster_shoot']
                self.upgrade_costs['faster_shoot'] = int(self.upgrade_costs['faster_shoot'] * self.upgrade_increment)
            elif 200 < pos[1] < 240 and self.coins >= self.upgrade_costs['more_shots']:
                self.tower.shots_per_shoot += 1
                self.coins -= self.upgrade_costs['more_shots']
                self.upgrade_costs['more_shots'] = int(self.upgrade_costs['more_shots'] * self.upgrade_increment)
            elif 250 < pos[1] < 290 and self.coins >= self.upgrade_costs['greater_range']:
                self.tower.range = int(self.tower.range * 1.02)
                self.coins -= self.upgrade_costs['greater_range']
                self.upgrade_costs['greater_range'] = int(self.upgrade_costs['greater_range'] * self.upgrade_increment)

# Hauptspielfunktion
def main():
    def restart_game():
        nonlocal tower, monsters, menu, spawn_timer, spawn_interval, run, game_over, difficulty_timer, level, coin_value
        tower = Tower(WIDTH // 2, HEIGHT // 2)
        monsters = []
        menu = Menu(tower)
        spawn_timer = 0
        spawn_interval = 60
        difficulty_timer = 0
        run = True
        game_over = False
        level = 1
        coin_value = 1

    run = True
    game_over = False
    clock = pygame.time.Clock()

    tower = Tower(WIDTH // 2, HEIGHT // 2)
    monsters = []
    menu = Menu(tower)

    spawn_timer = 0
    spawn_interval = 60  # Spawne alle 60 Frames ein Monster
    difficulty_timer = 0
    difficulty_interval = 1000  # Erhöhe alle 1000 Frames die Schwierigkeit
    level = 1
    coin_value = 1

    while run:
        clock.tick(60)
        WIN.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                if event.key == pygame.K_m:
                    menu.toggle()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    restart_game()
                else:
                    menu.handle_upgrade(event.pos)

        if game_over:
            font = pygame.font.SysFont(None, 72)
            game_over_text = font.render('Game Over', True, RED)
            WIN.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - game_over_text.get_height() // 2))
            restart_text = font.render('Erneut spielen', True, RED)
            restart_rect = pygame.Rect(WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50, restart_text.get_width(), restart_text.get_height())
            pygame.draw.rect(WIN, BLACK, restart_rect, 2)
            WIN.blit(restart_text, (restart_rect.x, restart_rect.y))
            pygame.display.update()
            continue

        # Schwierigkeit erhöhen
        difficulty_timer += 1
        if difficulty_timer >= difficulty_interval:
            spawn_interval = max(10, spawn_interval - 5)
            for monster in monsters:
                monster.speed += 0.2
            coin_value = int(coin_value * 1.3)
            level += 1
            difficulty_timer = 0

        # Monster spawnen
        if spawn_timer <= 0:
            side = random.choice(['left', 'right', 'top', 'bottom'])
            if side == 'left':
                x, y = 0, random.randint(0, HEIGHT)
            elif side == 'right':
                x, y = WIDTH, random.randint(0, HEIGHT)
            elif side == 'top':
                x, y = random.randint(0, WIDTH), 0
            else:  # bottom
                x, y = random.randint(0, WIDTH), HEIGHT
            monsters.append(Monster(x, y, 2 + difficulty_timer // difficulty_interval * 0.2))
            spawn_timer = spawn_interval
        else:
            spawn_timer -= 1

        tower.attack(monsters)
        menu.coins = tower.update_shots(monsters, menu.coins, coin_value)

        tower.draw(WIN)
        for monster in monsters[:]:
            if monster.hp > 0:
                monster.move(tower.x, tower.y)
                monster.draw(WIN)
                if ((tower.x - monster.x)**2 + (tower.y - monster.y)**2)**0.5 <= 20:
                    tower.hp -= 1
                    monsters.remove(monster)
                    if tower.hp <= 0:
                        game_over = True
                        break

        # Tower HP anzeigen
        font = pygame.font.SysFont(None, 36)
        hp_text = font.render(f'HP: {tower.hp}', True, RED)
        WIN.blit(hp_text, (20, 20))

        # Level anzeigen
        level_text = font.render(f'Level: {level}', True, BLACK)
        WIN.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 20))

        menu.draw(WIN)
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
