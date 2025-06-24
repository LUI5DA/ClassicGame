import pygame
import random
from config import *
from entities import Crystal, Enemy, Key, Door, FallingRock, MovingPlatform
from cave_generator import CaveGenerator, CaveParameters

class Room:
    def __init__(self, room_id):
        self.id = room_id
        self.cave_map = []
        self.walls = []
        self.crystals = []
        self.enemies = []
        self.keys = []
        self.doors = []
        self.falling_rocks = []
        self.moving_platforms = []
        self.generate_room()
        
    def generate_room(self):
        # Create different cave parameters based on room ID
        params = self.get_cave_parameters()
        
        # Generate cave using parameters
        self.cave_map = CaveGenerator.generate_cave(CAVE_WIDTH, CAVE_HEIGHT, params)
        
        # Post-process the cave
        self.cave_map = CaveGenerator.smooth_cave(self.cave_map, CAVE_WIDTH, CAVE_HEIGHT, params)
        self.cave_map = CaveGenerator.ensure_connectivity(self.cave_map, CAVE_WIDTH, CAVE_HEIGHT, params)
        
        # Convert cave map to wall rectangles
        self.rebuild_walls()
        
        # Place game objects in open areas
        self.place_objects()
        
    def get_cave_parameters(self):
        """Generate cave parameters based on room ID for variety"""
        room_type = self.id % 5
        
        if room_type == 0:  # Cellular caves - organic, bubble-like
            return CaveParameters(
                cave_type="cellular",
                density=0.45 + (self.id * 0.03),
                iterations=4 + (self.id % 3),
                room_size_preference=0.6,
                smoothing_passes=2
            )
        elif room_type == 1:  # Perlin caves - flowing, natural
            return CaveParameters(
                cave_type="perlin",
                noise_scale=0.08 + (self.id * 0.02),
                noise_octaves=3,
                room_size_preference=0.7,
                vertical_bias=0.3 if self.id % 2 == 0 else -0.3
            )
        elif room_type == 2:  # Maze caves - structured paths
            return CaveParameters(
                cave_type="maze",
                tunnel_width=2 + (self.id % 3),
                horizontal_bias=0.5 if self.id % 2 == 0 else 0,
                vertical_bias=0.5 if self.id % 2 == 1 else 0,
                connectivity_strength=0.8
            )
        elif room_type == 3:  # Cavern - large open spaces
            return CaveParameters(
                cave_type="cavern",
                room_size_preference=0.8 + (self.id * 0.05),
                tunnel_width=4,
                smoothing_passes=3,
                connectivity_strength=1.2
            )
        else:  # Mixed - combination of techniques
            return CaveParameters(
                cave_type="mixed",
                density=0.4 + (self.id * 0.02),
                noise_scale=0.1,
                room_size_preference=0.5 + (self.id % 3) * 0.15,
                horizontal_bias=(self.id % 3 - 1) * 0.4,
                vertical_bias=(self.id % 2) * 0.3,
                smoothing_passes=2,
                connectivity_strength=1.0
            )
        
    def rebuild_walls(self):
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
    
    def place_objects(self):
        # Find all open spaces
        open_spaces = []
        for y in range(2, CAVE_HEIGHT - 2):
            for x in range(2, CAVE_WIDTH - 2):
                if not self.cave_map[y][x]:
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
        
        # Place enemies
        enemy_count = min(1 + (self.id // 2), len(open_spaces) // 4)
        if enemy_count > 0 and open_spaces:
            enemy_positions = random.sample(open_spaces, min(enemy_count, len(open_spaces)))
            for i, (x, y) in enumerate(enemy_positions):
                enemy_type = "chaser" if i % 3 == 0 else "patrol"
                self.enemies.append(Enemy(x, y, enemy_type))
                open_spaces.remove((x, y))
        
        # Place keys and doors
        if self.id > 0 and len(open_spaces) >= 2:
            key_pos = random.choice(open_spaces)
            self.keys.append(Key(key_pos[0], key_pos[1]))
            open_spaces.remove(key_pos)
            
            door_placed = False
            attempts = 0
            while not door_placed and attempts < 20:
                x = random.randint(2, CAVE_WIDTH - 3) * TILE_SIZE
                y = random.randint(2, CAVE_HEIGHT - 3) * TILE_SIZE
                
                door_rect = pygame.Rect(x, y, TILE_SIZE * 2, TILE_SIZE)
                collision = any(wall.colliderect(door_rect) for wall in self.walls)
                
                if not collision:
                    self.doors.append(Door(x, y, TILE_SIZE * 2, TILE_SIZE))
                    door_placed = True
                attempts += 1
                
        # Place falling rocks and moving platforms
        if self.id > 1:
            for _ in range(random.randint(1, 3)):
                if open_spaces:
                    pos = random.choice(open_spaces)
                    rock_y = pos[1] - random.randint(100, 200)
                    if rock_y > 0:
                        self.falling_rocks.append(FallingRock(pos[0], rock_y))
                        
            for _ in range(random.randint(0, 2)):
                x = random.randint(TILE_SIZE * 3, SCREEN_WIDTH - TILE_SIZE * 6)
                y = random.randint(TILE_SIZE * 5, SCREEN_HEIGHT - TILE_SIZE * 5)
                
                platform_rect = pygame.Rect(x, y, TILE_SIZE * 4, TILE_SIZE)
                collision = any(wall.colliderect(platform_rect) for wall in self.walls)
                
                if not collision:
                    self.moving_platforms.append(MovingPlatform(x, y, TILE_SIZE * 4))
                
    def get_all_walls(self):
        all_walls = self.walls[:]
        for door in self.doors:
            if door.locked:
                all_walls.append(door.rect)
        for platform in self.moving_platforms:
            all_walls.append(platform.get_rect())
        return all_walls
                
    def draw_walls(self, screen):
        for y in range(CAVE_HEIGHT):
            for x in range(CAVE_WIDTH):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                if self.cave_map[y][x]:
                    color_variation = (x + y) % 3
                    if color_variation == 0:
                        color = CAVE_WALL
                    elif color_variation == 1:
                        color = tuple(max(0, c - 20) for c in CAVE_WALL)
                    else:
                        color = CAVE_ACCENT
                    pygame.draw.rect(screen, color, rect)
                    
                    if random.randint(0, 10) == 0:
                        pygame.draw.line(screen, tuple(min(255, c + 30) for c in color), 
                                       (rect.left, rect.top), (rect.right, rect.bottom), 1)
                else:
                    pygame.draw.rect(screen, CAVE_FLOOR, rect)
                    
                    if random.randint(0, 20) == 0:
                        detail_color = tuple(min(255, c + 10) for c in CAVE_FLOOR)
                        pygame.draw.circle(screen, detail_color, rect.center, 2)
            
    def draw_objects(self, screen):
        for door in self.doors:
            door.draw(screen)
        for key in self.keys:
            key.draw(screen)
        for enemy in self.enemies:
            enemy.draw(screen)
        for rock in self.falling_rocks:
            rock.draw(screen)
        for platform in self.moving_platforms:
            platform.draw(screen)