import pygame
import sys
import random
import math
import noise

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TILE_SIZE = 16
CAVE_WIDTH = SCREEN_WIDTH // TILE_SIZE
CAVE_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 200)
GREEN = (0, 200, 0)
CRYSTAL_BLUE = (100, 200, 255)
GLITCH_PINK = (255, 100, 200)
WALL_COLOR = (80, 60, 40)
GLITCH_GREEN = (0, 255, 100)
CAVE_WALL = (60, 40, 30)
CAVE_FLOOR = (20, 15, 10)
CAVE_ACCENT = (100, 80, 60)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
DOOR_COLOR = (150, 100, 50)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.speed = 4
        self.color = GREEN
        self.glitch_timer = 0
        self.health = 3
        self.invulnerable_timer = 0
        self.keys = 0
        
    def update(self, keys, walls):
        old_x, old_y = self.x, self.y
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
            
        # Check wall collisions
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for wall in walls:
            if player_rect.colliderect(wall):
                self.x, self.y = old_x, old_y
                break
                
        # Keep player on screen
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))
        
        # Update timers
        if self.glitch_timer > 0:
            self.glitch_timer -= 1
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
    
    def draw(self, screen):
        color = self.color
        if self.glitch_timer > 0:
            color = GLITCH_GREEN if random.randint(0, 3) == 0 else self.color
        elif self.invulnerable_timer > 0 and self.invulnerable_timer % 10 < 5:
            color = WHITE  # Flashing when invulnerable
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        
    def activate_glitch(self):
        self.glitch_timer = 60  # 1 second at 60 FPS
        
    def take_damage(self):
        if self.invulnerable_timer <= 0:
            self.health -= 1
            self.invulnerable_timer = 120  # 2 seconds of invulnerability
            return True
        return False

class Crystal:
    def __init__(self, x, y, is_glitch=False):
        self.x = x
        self.y = y
        self.size = 16
        self.glow = 0
        self.collected = False
        self.is_glitch = is_glitch
        
    def update(self):
        self.glow = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 50
        
    def draw(self, screen):
        if not self.collected:
            if self.is_glitch:
                # Glitch crystal with random colors
                colors = [GLITCH_PINK, GLITCH_GREEN, CRYSTAL_BLUE]
                color = random.choice(colors)
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
            else:
                glow_color = (100 + self.glow, 150 + self.glow, 255)
                pygame.draw.circle(screen, glow_color, (int(self.x), int(self.y)), self.size)
                pygame.draw.circle(screen, CRYSTAL_BLUE, (int(self.x), int(self.y)), self.size - 4)

class Enemy:
    def __init__(self, x, y, enemy_type="patrol"):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.speed = 1
        self.color = RED
        self.type = enemy_type
        self.direction = random.choice([-1, 1])
        self.move_timer = 0
        
    def update(self, walls, player):
        if self.type == "patrol":
            self.move_timer += 1
            if self.move_timer > 120:  # Change direction every 2 seconds
                self.direction *= -1
                self.move_timer = 0
                
            old_x = self.x
            self.x += self.speed * self.direction
            
            # Check wall collisions
            enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            for wall in walls:
                if enemy_rect.colliderect(wall):
                    self.x = old_x
                    self.direction *= -1
                    break
                    
        elif self.type == "chaser":
            # Simple AI to chase player
            if abs(player.x - self.x) < 150 and abs(player.y - self.y) < 150:
                if player.x > self.x:
                    self.x += self.speed * 0.7
                elif player.x < self.x:
                    self.x -= self.speed * 0.7
                if player.y > self.y:
                    self.y += self.speed * 0.7
                elif player.y < self.y:
                    self.y -= self.speed * 0.7
                    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Draw simple "eyes"
        pygame.draw.circle(screen, WHITE, (int(self.x + 5), int(self.y + 5)), 2)
        pygame.draw.circle(screen, WHITE, (int(self.x + 15), int(self.y + 5)), 2)

class Key:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 12
        self.collected = False
        self.glow = 0
        
    def update(self):
        self.glow = (math.sin(pygame.time.get_ticks() * 0.02) + 1) * 30
        
    def draw(self, screen):
        if not self.collected:
            glow_color = (255, 255 - self.glow, 0)
            pygame.draw.circle(screen, glow_color, (int(self.x), int(self.y)), self.size)
            pygame.draw.rect(screen, YELLOW, (self.x - 3, self.y - 8, 6, 16))

class Door:
    def __init__(self, x, y, width, height, keys_required=1):
        self.rect = pygame.Rect(x, y, width, height)
        self.keys_required = keys_required
        self.locked = True
        
    def draw(self, screen):
        if self.locked:
            pygame.draw.rect(screen, DOOR_COLOR, self.rect)
            # Draw lock symbol
            pygame.draw.circle(screen, YELLOW, self.rect.center, 8)
            pygame.draw.circle(screen, DOOR_COLOR, self.rect.center, 5)

class CaveGenerator:
    @staticmethod
    def generate_cellular_automata(width, height, initial_density=0.45, iterations=5):
        # Create initial random cave
        cave = [[random.random() < initial_density for _ in range(width)] for _ in range(height)]
        
        # Apply cellular automata rules
        for _ in range(iterations):
            new_cave = [[False for _ in range(width)] for _ in range(height)]
            for y in range(height):
                for x in range(width):
                    wall_count = CaveGenerator.count_walls(cave, x, y, width, height)
                    new_cave[y][x] = wall_count >= 4
            cave = new_cave
        
        return cave
    
    @staticmethod
    def count_walls(cave, x, y, width, height):
        count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    count += 1  # Treat boundaries as walls
                elif cave[ny][nx]:
                    count += 1
        return count
    
    @staticmethod
    def generate_perlin_cave(width, height, scale=0.1, threshold=0.3, seed=None):
        if seed:
            random.seed(seed)
        
        cave = [[False for _ in range(width)] for _ in range(height)]
        offset_x = random.randint(0, 1000)
        offset_y = random.randint(0, 1000)
        
        for y in range(height):
            for x in range(width):
                # Create noise value
                noise_val = 0
                amplitude = 1
                frequency = scale
                
                # Layer multiple octaves for more interesting caves
                for _ in range(3):
                    noise_val += amplitude * (math.sin((x + offset_x) * frequency) * math.cos((y + offset_y) * frequency))
                    amplitude *= 0.5
                    frequency *= 2
                
                # Normalize and apply threshold
                noise_val = (noise_val + 1) / 2
                cave[y][x] = noise_val > threshold
        
        return cave
    
    @staticmethod
    def smooth_cave(cave, width, height):
        # Remove isolated walls and fill small holes
        new_cave = [[cave[y][x] for x in range(width)] for y in range(height)]
        
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                wall_count = CaveGenerator.count_walls(cave, x, y, width, height)
                if cave[y][x] and wall_count <= 2:  # Remove isolated walls
                    new_cave[y][x] = False
                elif not cave[y][x] and wall_count >= 6:  # Fill small holes
                    new_cave[y][x] = True
        
        return new_cave
    
    @staticmethod
    def ensure_connectivity(cave, width, height):
        # Ensure there's a path through the cave
        # Find largest open area and connect smaller areas to it
        visited = [[False for _ in range(width)] for _ in range(height)]
        regions = []
        
        for y in range(height):
            for x in range(width):
                if not cave[y][x] and not visited[y][x]:
                    region = CaveGenerator.flood_fill(cave, visited, x, y, width, height)
                    if len(region) > 10:  # Only keep significant regions
                        regions.append(region)
        
        if len(regions) > 1:
            # Connect regions by carving tunnels
            main_region = max(regions, key=len)
            for region in regions:
                if region != main_region:
                    CaveGenerator.connect_regions(cave, main_region, region, width, height)
        
        return cave
    
    @staticmethod
    def flood_fill(cave, visited, start_x, start_y, width, height):
        region = []
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            if x < 0 or x >= width or y < 0 or y >= height or visited[y][x] or cave[y][x]:
                continue
            
            visited[y][x] = True
            region.append((x, y))
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                stack.append((x + dx, y + dy))
        
        return region
    
    @staticmethod
    def connect_regions(cave, region1, region2, width, height):
        # Find closest points between regions and carve a tunnel
        min_dist = float('inf')
        best_points = None
        
        for x1, y1 in region1[:20]:  # Sample subset for performance
            for x2, y2 in region2[:20]:
                dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    best_points = ((x1, y1), (x2, y2))
        
        if best_points:
            CaveGenerator.carve_tunnel(cave, best_points[0], best_points[1], width, height)
    
    @staticmethod
    def carve_tunnel(cave, start, end, width, height):
        x1, y1 = start
        x2, y2 = end
        
        # Simple line drawing algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            # Carve tunnel (make it 2 tiles wide)
            for dx_offset in [-1, 0, 1]:
                for dy_offset in [-1, 0, 1]:
                    nx, ny = x + dx_offset, y + dy_offset
                    if 0 <= nx < width and 0 <= ny < height:
                        cave[ny][nx] = False
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

class Room:
    def __init__(self, room_id):
        self.id = room_id
        self.cave_map = []
        self.walls = []
        self.crystals = []
        self.enemies = []
        self.keys = []
        self.doors = []
        self.generate_room()
        
    def generate_room(self):
        # Generate cave using different algorithms based on room type
        if self.id % 3 == 0:
            # Cellular automata caves
            self.cave_map = CaveGenerator.generate_cellular_automata(
                CAVE_WIDTH, CAVE_HEIGHT, 
                initial_density=0.45 + (self.id * 0.05), 
                iterations=4 + (self.id % 3)
            )
        elif self.id % 3 == 1:
            # Perlin noise caves
            self.cave_map = CaveGenerator.generate_perlin_cave(
                CAVE_WIDTH, CAVE_HEIGHT,
                scale=0.08 + (self.id * 0.02),
                threshold=0.35 + (self.id * 0.05),
                seed=self.id * 42
            )
        else:
            # Hybrid approach
            cave1 = CaveGenerator.generate_cellular_automata(CAVE_WIDTH, CAVE_HEIGHT, 0.4, 3)
            cave2 = CaveGenerator.generate_perlin_cave(CAVE_WIDTH, CAVE_HEIGHT, 0.1, 0.4, self.id * 17)
            # Combine both caves
            self.cave_map = [[cave1[y][x] or cave2[y][x] for x in range(CAVE_WIDTH)] for y in range(CAVE_HEIGHT)]
        
        # Post-process the cave
        self.cave_map = CaveGenerator.smooth_cave(self.cave_map, CAVE_WIDTH, CAVE_HEIGHT)
        self.cave_map = CaveGenerator.ensure_connectivity(self.cave_map, CAVE_WIDTH, CAVE_HEIGHT)
        
        # Convert cave map to wall rectangles
        self.walls = []
        for y in range(CAVE_HEIGHT):
            for x in range(CAVE_WIDTH):
                if self.cave_map[y][x]:
                    wall_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    self.walls.append(wall_rect)
        
        # Ensure borders are always walls
        for x in range(CAVE_WIDTH):
            self.walls.append(pygame.Rect(x * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE))
            self.walls.append(pygame.Rect(x * TILE_SIZE, (CAVE_HEIGHT - 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        for y in range(CAVE_HEIGHT):
            self.walls.append(pygame.Rect(0, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            self.walls.append(pygame.Rect((CAVE_WIDTH - 1) * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        
        # Place game objects in open areas
        self.place_objects()
            
    def place_objects(self):
        # Find all open spaces
        open_spaces = []
        for y in range(2, CAVE_HEIGHT - 2):
            for x in range(2, CAVE_WIDTH - 2):
                if not self.cave_map[y][x]:
                    # Check if there's enough space around this position
                    clear = True
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if self.cave_map[y + dy][x + dx]:
                                clear = False
                                break
                        if not clear:
                            break
                    if clear:
                        open_spaces.append((x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2))
        
        if not open_spaces:
            return
        
        # Place crystals
        crystal_count = min(random.randint(4, 8), len(open_spaces) // 3)
        crystal_positions = random.sample(open_spaces, crystal_count)
        for x, y in crystal_positions:
            is_glitch = random.randint(0, 4) == 0
            self.crystals.append(Crystal(x, y, is_glitch))
            open_spaces.remove((x, y))
        
        # Place enemies based on room difficulty
        enemy_count = min(1 + (self.id // 2), len(open_spaces) // 4)
        if enemy_count > 0 and open_spaces:
            enemy_positions = random.sample(open_spaces, min(enemy_count, len(open_spaces)))
            for i, (x, y) in enumerate(enemy_positions):
                enemy_type = "chaser" if i % 3 == 0 else "patrol"
                self.enemies.append(Enemy(x, y, enemy_type))
                open_spaces.remove((x, y))
        
        # Place keys and doors for certain rooms
        if self.id > 0 and len(open_spaces) >= 2:
            # Place a key
            key_pos = random.choice(open_spaces)
            self.keys.append(Key(key_pos[0], key_pos[1]))
            open_spaces.remove(key_pos)
            
            # Place a door near a wall
            door_placed = False
            attempts = 0
            while not door_placed and attempts < 20:
                x = random.randint(2, CAVE_WIDTH - 3) * TILE_SIZE
                y = random.randint(2, CAVE_HEIGHT - 3) * TILE_SIZE
                
                # Check if this position is near a wall but accessible
                door_rect = pygame.Rect(x, y, TILE_SIZE * 2, TILE_SIZE)
                collision = any(wall.colliderect(door_rect) for wall in self.walls)
                
                if not collision:
                    self.doors.append(Door(x, y, TILE_SIZE * 2, TILE_SIZE))
                    door_placed = True
                attempts += 1
                
    def get_all_walls(self):
        # Return walls + locked doors as obstacles
        all_walls = self.walls[:]
        for door in self.doors:
            if door.locked:
                all_walls.append(door.rect)
        return all_walls
                
    def draw_walls(self, screen):
        # Draw cave walls with more visual variety
        for y in range(CAVE_HEIGHT):
            for x in range(CAVE_WIDTH):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                if self.cave_map[y][x]:
                    # Wall tile - vary color based on position for texture
                    color_variation = (x + y) % 3
                    if color_variation == 0:
                        color = CAVE_WALL
                    elif color_variation == 1:
                        color = tuple(max(0, c - 20) for c in CAVE_WALL)
                    else:
                        color = CAVE_ACCENT
                    pygame.draw.rect(screen, color, rect)
                    
                    # Add some texture lines
                    if random.randint(0, 10) == 0:
                        pygame.draw.line(screen, tuple(min(255, c + 30) for c in color), 
                                       (rect.left, rect.top), (rect.right, rect.bottom), 1)
                else:
                    # Floor tile
                    pygame.draw.rect(screen, CAVE_FLOOR, rect)
                    
                    # Add occasional floor details
                    if random.randint(0, 20) == 0:
                        detail_color = tuple(min(255, c + 10) for c in CAVE_FLOOR)
                        pygame.draw.circle(screen, detail_color, rect.center, 2)
            
    def draw_objects(self, screen):
        # Draw doors
        for door in self.doors:
            door.draw(screen)
        # Draw keys
        for key in self.keys:
            key.draw(screen)
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(screen)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Crystal Caverns - Glitch Adventure")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game objects
        self.player = Player(100, 100)
        self.current_room_id = 0
        self.rooms = {}
        self.score = 0
        self.glitch_effects = []
        self.game_over = False
        
        # Generate more rooms with procedural caves
        room_count = 5 + random.randint(0, 3)  # 5-8 rooms
        for i in range(room_count):
            self.rooms[i] = Room(i)
            
        self.current_room = self.rooms[self.current_room_id]
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.game_over:
                    # Room transition - find a safe spawn point
                    self.current_room_id = (self.current_room_id + 1) % len(self.rooms)
                    self.current_room = self.rooms[self.current_room_id]
                    self.find_safe_spawn_point()
                elif event.key == pygame.K_r and self.game_over:
                    # Restart game
                    self.__init__()
    
    def update(self):
        if self.game_over:
            return
            
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.current_room.get_all_walls())
        
        # Update room objects
        for crystal in self.current_room.crystals:
            crystal.update()
        for key in self.current_room.keys:
            key.update()
        for enemy in self.current_room.enemies:
            enemy.update(self.current_room.walls, self.player)
            
        # Check crystal collection
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for crystal in self.current_room.crystals:
            if not crystal.collected:
                crystal_rect = pygame.Rect(crystal.x - crystal.size, crystal.y - crystal.size, 
                                         crystal.size * 2, crystal.size * 2)
                if player_rect.colliderect(crystal_rect):
                    crystal.collected = True
                    self.score += 1
                    if crystal.is_glitch:
                        self.player.activate_glitch()
                        self.add_glitch_effect()
                        
        # Check key collection
        for key in self.current_room.keys:
            if not key.collected:
                key_rect = pygame.Rect(key.x - key.size, key.y - key.size, key.size * 2, key.size * 2)
                if player_rect.colliderect(key_rect):
                    key.collected = True
                    self.player.keys += 1
                    
        # Check door unlocking
        for door in self.current_room.doors:
            if door.locked and self.player.keys >= door.keys_required:
                door.locked = False
                self.player.keys -= door.keys_required
                
        # Check enemy collisions
        for enemy in self.current_room.enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
            if player_rect.colliderect(enemy_rect):
                if self.player.take_damage():
                    if self.player.health <= 0:
                        self.game_over = True
                        
    def find_safe_spawn_point(self):
        # Find a safe place to spawn the player in the new room
        attempts = 0
        while attempts < 50:
            x = random.randint(2, CAVE_WIDTH - 3) * TILE_SIZE
            y = random.randint(2, CAVE_HEIGHT - 3) * TILE_SIZE
            
            # Check if this position is clear
            player_rect = pygame.Rect(x, y, self.player.width, self.player.height)
            collision = any(wall.colliderect(player_rect) for wall in self.current_room.walls)
            
            if not collision:
                self.player.x, self.player.y = x, y
                return
            attempts += 1
        
        # Fallback: place at a calculated safe position
        self.player.x, self.player.y = TILE_SIZE * 3, TILE_SIZE * 3
                        
    def add_glitch_effect(self):
        # Add screen glitch effect
        effect = {
            'timer': 30,
            'offset_x': random.randint(-10, 10),
            'offset_y': random.randint(-10, 10)
        }
        self.glitch_effects.append(effect)
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Apply glitch effects
        screen_offset_x, screen_offset_y = 0, 0
        for effect in self.glitch_effects[:]:
            effect['timer'] -= 1
            if effect['timer'] <= 0:
                self.glitch_effects.remove(effect)
            else:
                screen_offset_x += effect['offset_x'] // 3
                screen_offset_y += effect['offset_y'] // 3
        
        # Create temporary surface for glitch effects
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        temp_surface.fill(BLACK)
        
        # Draw room walls
        self.current_room.draw_walls(temp_surface)
        
        # Draw crystals in current room
        for crystal in self.current_room.crystals:
            crystal.draw(temp_surface)
            
        # Draw room objects
        self.current_room.draw_objects(temp_surface)
            
        # Draw player
        self.player.draw(temp_surface)
        
        # Apply screen offset for glitch effect
        self.screen.blit(temp_surface, (screen_offset_x, screen_offset_y))
        
        # Draw UI (not affected by glitch)
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        if self.game_over:
            game_over_text = font.render("GAME OVER - Press R to Restart", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(game_over_text, text_rect)
        else:
            score_text = font.render(f"Crystals: {self.score}", True, WHITE)
            room_text = font.render(f"Room: {self.current_room_id + 1}", True, WHITE)
            health_text = font.render(f"Health: {self.player.health}", True, WHITE)
            keys_text = font.render(f"Keys: {self.player.keys}", True, WHITE)
            help_text = small_font.render("SPACE: Next Room | WASD: Move", True, WHITE)
            
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(room_text, (10, 50))
            self.screen.blit(health_text, (10, 90))
            self.screen.blit(keys_text, (10, 130))
            self.screen.blit(help_text, (10, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()