import pygame
import sys
import random
from config import *
from entities import Player
from room import Room
from audio import audio_manager

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Crystal Caverns - Glitch Adventure")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Load background image
        try:
            self.background = pygame.image.load("bg.png")
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            print("Background image loaded successfully")
        except:
            print("Could not load bg.png, using default background")
            self.background = None
        
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
                    self.try_advance_room()
                elif event.key == pygame.K_r and self.game_over:
                    self.__init__()
    
    def update(self):
        if self.game_over:
            return
            
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.current_room.get_all_walls())
        
        # If inventory is open, pause game world updates
        if self.player.inventory_open:
            return
        
        # Update room objects
        for crystal in self.current_room.crystals:
            crystal.update()
        for key in self.current_room.keys:
            key.update()
        for enemy in self.current_room.enemies:
            enemy.update(self.current_room.walls, self.player)
        for boss in self.current_room.bosses:
            boss.update(self.current_room.walls, self.player)
        for rock in self.current_room.falling_rocks:
            rock.update(self.current_room.walls, self.player)
        for platform in self.current_room.moving_platforms:
            platform.update()
            
        # Check collisions
        self.check_crystal_collection()
        self.check_key_collection()
        self.check_door_unlocking()
        self.check_door_interaction()
        self.check_enemy_collisions()
        self.check_falling_rock_collisions()
        self.check_combat()
        self.check_boss_combat()
        self.check_projectile_collisions()
                        
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
                    audio_manager.play_sound("crystal")
                        
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
                print(f"Door unlocked! Keys remaining: {self.player.keys}")
                
    def check_door_interaction(self):
        """Check if player is near an unlocked door"""
        for door in self.current_room.doors:
            if not door.locked:
                # Check if player is close to the door
                door_center_x = door.rect.centerx
                door_center_y = door.rect.centery
                distance = ((self.player.x + self.player.width//2 - door_center_x)**2 + 
                           (self.player.y + self.player.height//2 - door_center_y)**2)**0.5
                
                if distance < 50:  # Within 50 pixels of door
                    door.can_use = True
                else:
                    door.can_use = False
                    
    def try_advance_room(self):
        """Try to advance to next room - requires being near unlocked door"""
        can_advance = False
        
        # Check if player is near any unlocked door
        for door in self.current_room.doors:
            if not door.locked and hasattr(door, 'can_use') and door.can_use:
                can_advance = True
                break
                
        if can_advance:
            if self.current_room_id < len(self.rooms) - 1:
                self.current_room_id += 1
                self.current_room = self.rooms[self.current_room_id]
                self.find_safe_spawn_point()
                print(f"Advanced to Room {self.current_room_id + 1}!")
            else:
                print("You've reached the final room!")
        else:
            # Check if there are any unlocked doors at all
            unlocked_doors = [door for door in self.current_room.doors if not door.locked]
            if unlocked_doors:
                print("Move closer to an unlocked door to advance!")
            else:
                print("Find a key to unlock the door first!")
                
    def check_enemy_collisions(self):
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for enemy in self.current_room.enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
            if player_rect.colliderect(enemy_rect):
                if self.player.take_damage():
                    audio_manager.play_sound("damage")
                    if self.player.health <= 0:
                        self.game_over = True
                        
    def check_falling_rock_collisions(self):
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for rock in self.current_room.falling_rocks:
            if rock.active and player_rect.colliderect(rock.get_rect()):
                if self.player.take_damage():
                    audio_manager.play_sound("damage")
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
                        audio_manager.play_sound("beat")  # Enemy death sound
                        self.drop_loot(enemy.x, enemy.y, "enemy")
                        self.current_room.enemies.remove(enemy)
                        self.score += 5  # Bonus points for killing enemies
                        
    def check_boss_combat(self):
        """Check for player attacks hitting bosses"""
        attack_rect = self.player.get_attack_rect()
        if attack_rect:
            for boss in self.current_room.bosses[:]:
                boss_rect = pygame.Rect(boss.x, boss.y, boss.width, boss.height)
                if attack_rect.colliderect(boss_rect):
                    weapon_stats = self.player.get_weapon_stats()
                    print(f"Hit boss! Damage: {weapon_stats['damage']}, Boss health: {boss.health}")
                    if boss.take_damage(weapon_stats["damage"]):
                        print("Boss defeated!")
                        audio_manager.play_sound("glitch")  # Special boss death sound
                        self.drop_loot(boss.x, boss.y, "boss")
                        self.current_room.bosses.remove(boss)
                        self.score += 50  # Big bonus for boss kill
                        
    def check_projectile_collisions(self):
        """Check boss projectiles hitting player"""
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for boss in self.current_room.bosses:
            for projectile in boss.projectiles[:]:
                if player_rect.colliderect(projectile.get_rect()):
                    if self.player.take_damage():
                        audio_manager.play_sound("damage")
                        boss.projectiles.remove(projectile)
                        if self.player.health <= 0:
                            self.game_over = True
                        
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
        
    def drop_loot(self, x, y, enemy_type):
        """Drop loot when enemy dies"""
        if enemy_type == "boss":
            # Boss always drops rare loot
            if random.randint(0, 1) == 0:
                weapon = self.generate_weapon("rare")
                self.player.add_item(weapon)
                print(f"Boss dropped: {weapon['name']}!")
            else:
                armor = self.generate_armor("rare")
                self.player.add_item(armor)
                print(f"Boss dropped: {armor['name']}!")
        else:
            # Regular enemies have chance to drop items
            if random.randint(0, 4) == 0:  # 20% chance
                loot_type = random.choice(["weapon", "armor", "crystal"])
                if loot_type == "weapon":
                    weapon = self.generate_weapon("common")
                    self.player.add_item(weapon)
                    print(f"Found: {weapon['name']}!")
                elif loot_type == "armor":
                    armor = self.generate_armor("common")
                    self.player.add_item(armor)
                    print(f"Found: {armor['name']}!")
                else:
                    crystal = {'type': 'crystal', 'subtype': 'glitch', 'count': 1, 'name': 'Glitch Crystal'}
                    self.player.add_item(crystal)
                    print("Found: Glitch Crystal!")
                    
    def generate_weapon(self, rarity):
        """Generate random weapon based on rarity"""
        if rarity == "rare":
            weapons = [
                {'type': 'weapon', 'name': 'Crystal Sword', 'damage': 3, 'range': 45, 'speed': 20},
                {'type': 'weapon', 'name': 'Void Blade', 'damage': 4, 'range': 35, 'speed': 25},
                {'type': 'weapon', 'name': 'Glitch Staff', 'damage': 2, 'range': 60, 'speed': 15}
            ]
        else:  # common
            weapons = [
                {'type': 'weapon', 'name': 'Iron Sword', 'damage': 2, 'range': 35, 'speed': 20},
                {'type': 'weapon', 'name': 'Steel Knife', 'damage': 1, 'range': 25, 'speed': 12},
                {'type': 'weapon', 'name': 'Wooden Staff', 'damage': 1, 'range': 50, 'speed': 18}
            ]
        return random.choice(weapons)
        
    def generate_armor(self, rarity):
        """Generate random armor based on rarity"""
        if rarity == "rare":
            armors = [
                {'type': 'armor', 'name': 'Crystal Plate', 'defense': 3, 'health_bonus': 2},
                {'type': 'armor', 'name': 'Void Mail', 'defense': 2, 'speed_bonus': 1},
                {'type': 'armor', 'name': 'Glitch Robe', 'defense': 1, 'energy_bonus': 50}
            ]
        else:  # common
            armors = [
                {'type': 'armor', 'name': 'Leather Armor', 'defense': 1, 'health_bonus': 1},
                {'type': 'armor', 'name': 'Chain Mail', 'defense': 2, 'health_bonus': 0},
                {'type': 'armor', 'name': 'Cloth Robe', 'defense': 1, 'speed_bonus': 0}
            ]
        return random.choice(armors)
    
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
        
        # Draw background image or fill with black
        if self.background:
            temp_surface.blit(self.background, (0, 0))
        else:
            temp_surface.fill(BLACK)
        
        # Draw room walls on top of background
        self.current_room.draw_walls(temp_surface)
        
        # Draw crystals
        for crystal in self.current_room.crystals:
            crystal.draw(temp_surface)
            
        # Draw room objects
        self.current_room.draw_objects(temp_surface)
        
        # Draw bosses
        for boss in self.current_room.bosses:
            boss.draw(temp_surface)
            
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
        
        # Draw door interaction indicators
        if not self.game_over and not self.player.inventory_open:
            for door in self.current_room.doors:
                if not door.locked and hasattr(door, 'can_use') and door.can_use:
                    # Draw "Press R" indicator near door
                    indicator_text = small_font.render("Press R to Enter", True, GREEN)
                    text_rect = indicator_text.get_rect(center=(door.rect.centerx, door.rect.centery - 30))
                    self.screen.blit(indicator_text, text_rect)
        
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
            if self.player.inventory_open:
                help_text = small_font.render(f"INVENTORY OPEN - Game Paused", True, GLITCH_PINK)
            else:
                # Check door status for help text
                near_door = any(hasattr(door, 'can_use') and door.can_use for door in self.current_room.doors if not door.locked)
                if near_door:
                    help_text = small_font.render(f"R: Enter Door | AD: Move | W/SPACE: Jump | Q: Phase | E: Teleport | X: Attack | I: Inventory", True, GREEN)
                else:
                    unlocked_doors = any(not door.locked for door in self.current_room.doors)
                    if unlocked_doors:
                        help_text = small_font.render(f"Move near unlocked door, then R: Enter | Keys: {self.player.keys}", True, YELLOW)
                    else:
                        help_text = small_font.render(f"Find key to unlock door | Keys: {self.player.keys} | Need: {self.current_room.doors[0].keys_required if self.current_room.doors else 0}", True, RED)
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