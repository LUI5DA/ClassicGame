import pygame
import sys
import random
from config import *
from entities import Player
from room import Room

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Crystal Caverns - Glitch Adventure")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game objects
        self.player = Player(0, 0)
        self.current_room_id = 0
        self.rooms = {}
        self.score = 0
        self.glitch_effects = []
        self.game_over = False
        
        # Generate rooms
        room_count = 5 + random.randint(0, 3)
        for i in range(room_count):
            self.rooms[i] = Room(i)
            
        self.current_room = self.rooms[self.current_room_id]
        self.find_safe_spawn_point()
        self.player.glitch_energy = 100  # Start with full energy
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and not self.game_over:
                    self.current_room_id = (self.current_room_id + 1) % len(self.rooms)
                    self.current_room = self.rooms[self.current_room_id]
                    self.find_safe_spawn_point()
                elif event.key == pygame.K_r and self.game_over:
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
        for rock in self.current_room.falling_rocks:
            rock.update(self.current_room.walls, self.player)
        for platform in self.current_room.moving_platforms:
            platform.update()
            
        # Check collisions
        self.check_crystal_collection()
        self.check_key_collection()
        self.check_door_unlocking()
        self.check_enemy_collisions()
        self.check_falling_rock_collisions()
        self.check_combat()
                        
    def check_crystal_collection(self):
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
                        
    def check_key_collection(self):
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for key in self.current_room.keys:
            if not key.collected:
                key_rect = pygame.Rect(key.x - key.size, key.y - key.size, key.size * 2, key.size * 2)
                if player_rect.colliderect(key_rect):
                    key.collected = True
                    self.player.keys += 1
                    
    def check_door_unlocking(self):
        for door in self.current_room.doors:
            if door.locked and self.player.keys >= door.keys_required:
                door.locked = False
                self.player.keys -= door.keys_required
                
    def check_enemy_collisions(self):
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for enemy in self.current_room.enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
            if player_rect.colliderect(enemy_rect):
                if self.player.take_damage():
                    if self.player.health <= 0:
                        self.game_over = True
                        
    def check_falling_rock_collisions(self):
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for rock in self.current_room.falling_rocks:
            if rock.active and player_rect.colliderect(rock.get_rect()):
                if self.player.take_damage():
                    if self.player.health <= 0:
                        self.game_over = True
                        
    def check_combat(self):
        """Check for player attacks hitting enemies"""
        attack_rect = self.player.get_attack_rect()
        if attack_rect:
            for enemy in self.current_room.enemies[:]:
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                if attack_rect.colliderect(enemy_rect):
                    weapon_stats = self.player.get_weapon_stats()
                    print(f"Hit enemy! Damage: {weapon_stats['damage']}, Enemy health: {enemy.health}")
                    if enemy.take_damage(weapon_stats["damage"]):
                        print("Enemy killed!")
                        self.current_room.enemies.remove(enemy)
                        self.score += 5  # Bonus points for killing enemies
                        
    def find_safe_spawn_point(self):
        open_spaces = []
        for y in range(3, CAVE_HEIGHT - 3):
            for x in range(3, CAVE_WIDTH - 3):
                if not self.current_room.cave_map[y][x]:
                    clear = True
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if self.current_room.cave_map[y + dy][x + dx]:
                                clear = False
                                break
                        if not clear:
                            break
                    if clear:
                        world_x = x * TILE_SIZE + TILE_SIZE // 2 - self.player.width // 2
                        world_y = y * TILE_SIZE + TILE_SIZE // 2 - self.player.height // 2
                        open_spaces.append((world_x, world_y))
        
        if open_spaces:
            spawn_x, spawn_y = random.choice(open_spaces)
            self.player.x, self.player.y = spawn_x, spawn_y
        else:
            for y in range(3, 6):
                for x in range(3, 6):
                    self.current_room.cave_map[y][x] = False
            self.current_room.rebuild_walls()
            self.player.x = 3 * TILE_SIZE + TILE_SIZE // 2
            self.player.y = 3 * TILE_SIZE + TILE_SIZE // 2
                        
    def add_glitch_effect(self):
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
        
        # Draw room
        self.current_room.draw_walls(temp_surface)
        
        # Draw crystals
        for crystal in self.current_room.crystals:
            crystal.draw(temp_surface)
            
        # Draw room objects
        self.current_room.draw_objects(temp_surface)
            
        # Draw player
        self.player.draw(temp_surface)
        
        # Apply screen offset for glitch effect
        self.screen.blit(temp_surface, (screen_offset_x, screen_offset_y))
        
        # Draw inventory overlay (not affected by glitch effects)
        self.player.draw_inventory(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
        
    def draw_ui(self):
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
            cave_type = ["Cellular", "Perlin", "Maze", "Cavern", "Mixed"][self.current_room_id % 5]
            glitch_energy = int(self.player.glitch_energy)
            help_text = small_font.render(f"R: Next Room | AD: Move | W/SPACE: Jump | Q: Phase | E: Teleport | X: Attack", True, WHITE)
            glitch_text = small_font.render(f"Glitch Energy: {glitch_energy}/100 | Cave: {cave_type}", True, GLITCH_PINK)
            
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(room_text, (10, 50))
            self.screen.blit(health_text, (10, 90))
            self.screen.blit(keys_text, (10, 130))
            self.screen.blit(help_text, (10, SCREEN_HEIGHT - 50))
            self.screen.blit(glitch_text, (10, SCREEN_HEIGHT - 30))
    
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