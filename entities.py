import pygame
import random
import math
from config import *

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.speed = 5
        self.color = GREEN
        self.glitch_timer = 0
        self.health = 3
        self.invulnerable_timer = 0
        self.keys = 0
        
        # Physics properties
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.can_jump = True
        self.wall_jump_timer = 0
        self.against_wall = False
        self.jump_count = 0
        self.max_jumps = 2  # Double jump
        self.phase_timer = 0
        self.teleport_cooldown = 0
        
        # Inventory system - crystal-based abilities
        self.inventory = {
            'glitch_crystals': 0,
            'phase_crystals': 2,  # Start with 2 for testing
            'teleport_crystals': 2  # Start with 2 for testing
        }
        self.inventory_open = False
        
        # Combat system
        self.weapon = "knife"  # knife, sword, stick
        self.attack_timer = 0
        self.attack_range = 35
        self.attack_damage = 1
        self.facing_direction = 1  # 1 = right, -1 = left
        
    def update(self, keys, walls):
        # Handle input
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
        else:
            self.vel_x *= FRICTION
            
        # Crystal-based abilities
        if keys[pygame.K_q]:
            if not hasattr(self, '_q_pressed') or not self._q_pressed:
                if self.inventory['phase_crystals'] > 0:
                    self.use_phase_crystal()
                    print(f"Phase crystal used! {self.inventory['phase_crystals']} remaining")
                else:
                    print("No phase crystals! Collect glitch crystals first.")
                self._q_pressed = True
        else:
            self._q_pressed = False
            
        if keys[pygame.K_e]:
            if not hasattr(self, '_e_pressed') or not self._e_pressed:
                if self.inventory['teleport_crystals'] > 0:
                    self.use_teleport_crystal()
                    print(f"Teleport crystal used! {self.inventory['teleport_crystals']} remaining")
                else:
                    print("No teleport crystals! Collect glitch crystals first.")
                self._e_pressed = True
        else:
            self._e_pressed = False
            
        # Inventory toggle
        if keys[pygame.K_i]:
            if not hasattr(self, '_i_pressed') or not self._i_pressed:
                self.inventory_open = not self.inventory_open
                self._i_pressed = True
        else:
            self._i_pressed = False
            
        # Combat - X key to attack
        if keys[pygame.K_x]:
            if not hasattr(self, '_x_pressed') or not self._x_pressed:
                self.attack()
                self._x_pressed = True
        else:
            self._x_pressed = False
            
        # Jumping (ground jump or double jump)
        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.can_jump:
            if self.on_ground or self.jump_count < self.max_jumps:
                self.vel_y = JUMP_STRENGTH
                self.jump_count += 1
                self.on_ground = False
                self.can_jump = False
                from audio import audio_manager
                audio_manager.play_sound("jump")
                
                # Wall jump
                if self.against_wall and not self.on_ground:
                    self.vel_x = -self.vel_x * 1.5  # Push away from wall
                    self.wall_jump_timer = 10
        
        # Reset jump when key released
        if not (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]):
            self.can_jump = True
            
        # Apply gravity
        if not self.on_ground:
            self.vel_y += GRAVITY
            self.vel_y = min(self.vel_y, MAX_FALL_SPEED)
        
        # Move horizontally
        old_x = self.x
        self.x += self.vel_x
        
        # Check horizontal collisions (skip if phasing)
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.against_wall = False
        
        if self.phase_timer <= 0:  # Normal collision
            for wall in walls:
                if player_rect.colliderect(wall):
                    self.x = old_x
                    self.against_wall = True
                    
                    # Wall sliding (slower fall when against wall)
                    if not self.on_ground and self.vel_y > 0:
                        self.vel_y *= 0.7
                        self.jump_count = 1  # Reset double jump when wall sliding
                        
                    self.vel_x = 0
                    break
                
        # Move vertically
        old_y = self.y
        self.y += self.vel_y
        
        # Check vertical collisions (skip if phasing)
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = False
        
        if self.phase_timer <= 0:  # Normal collision
            for wall in walls:
                if player_rect.colliderect(wall):
                    if self.vel_y > 0:  # Falling down
                        self.y = wall.top - self.height
                        self.on_ground = True
                        self.jump_count = 0  # Reset jumps when landing
                    else:  # Moving up
                        self.y = wall.bottom
                    self.vel_y = 0
                    break
                
        # Keep player on screen
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        if self.y > SCREEN_HEIGHT:
            self.take_damage()  # Fall damage
            self.y = SCREEN_HEIGHT - self.height
            self.vel_y = 0
            self.on_ground = True
        
        # Update timers
        if self.glitch_timer > 0:
            self.glitch_timer -= 1
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        if self.wall_jump_timer > 0:
            self.wall_jump_timer -= 1
        if self.phase_timer > 0:
            self.phase_timer -= 1
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1
            
        # Update facing direction based on movement
        if self.vel_x > 0:
            self.facing_direction = 1
        elif self.vel_x < 0:
            self.facing_direction = -1
    
    def draw(self, screen):
        color = self.color
        alpha = 255
        
        if self.phase_timer > 0:
            color = GLITCH_PINK
            alpha = 128  # Semi-transparent when phasing
        elif self.glitch_timer > 0:
            color = GLITCH_GREEN if random.randint(0, 3) == 0 else self.color
        elif self.invulnerable_timer > 0 and self.invulnerable_timer % 10 < 5:
            color = WHITE
        elif self.against_wall and not self.on_ground:
            color = BLUE  # Visual feedback for wall sliding
        
        # Draw player with transparency if phasing
        if alpha < 255:
            temp_surface = pygame.Surface((self.width, self.height))
            temp_surface.set_alpha(alpha)
            temp_surface.fill(color)
            screen.blit(temp_surface, (self.x, self.y))
            # Add phase effect border
            pygame.draw.rect(screen, GLITCH_PINK, (self.x - 2, self.y - 2, self.width + 4, self.height + 4), 2)
        else:
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
            
        # Phase timer indicator
        if self.phase_timer > 0:
            timer_width = 40
            timer_height = 3
            timer_x = self.x - 8
            timer_y = self.y - 18
            
            # Background
            pygame.draw.rect(screen, (30, 30, 30), (timer_x, timer_y, timer_width, timer_height))
            # Timer bar
            remaining = int((self.phase_timer / 120) * timer_width)
            pygame.draw.rect(screen, GLITCH_PINK, (timer_x, timer_y, remaining, timer_height))
        
        # Draw jump indicator
        if self.jump_count > 0 and not self.on_ground:
            for i in range(self.jump_count):
                pygame.draw.circle(screen, YELLOW, (int(self.x + 5 + i * 8), int(self.y - 5)), 3)
                
        # Draw crystal count indicators
        if self.inventory['teleport_crystals'] > 0 or self.inventory['phase_crystals'] > 0:
            # Teleport crystals (pink dots)
            if self.inventory['teleport_crystals'] > 0:
                for i in range(min(self.inventory['teleport_crystals'], 5)):
                    pygame.draw.circle(screen, GLITCH_PINK, (int(self.x + 5 + i * 8), int(self.y - 8)), 3)
            
            # Phase crystals (blue dots)
            if self.inventory['phase_crystals'] > 0:
                for i in range(min(self.inventory['phase_crystals'], 5)):
                    pygame.draw.circle(screen, BLUE, (int(self.x + 5 + i * 8), int(self.y - 18)), 3)
        
    def activate_glitch(self):
        self.glitch_timer = 60
        # Add crystals to inventory
        self.inventory['glitch_crystals'] += 1
        # Convert to usable crystals randomly
        if random.randint(0, 1) == 0:
            self.inventory['teleport_crystals'] += 1
            print("Gained teleport crystal!")
        else:
            self.inventory['phase_crystals'] += 1
            print("Gained phase crystal!")
        # Glitch jump boost
        if not self.on_ground:
            self.vel_y = JUMP_STRENGTH * 0.7
            self.jump_count = 0  # Reset jumps
            
    def use_teleport_crystal(self):
        """Use teleport crystal from inventory"""
        if self.inventory['teleport_crystals'] > 0 and self.teleport_cooldown <= 0:
            self.inventory['teleport_crystals'] -= 1
            from audio import audio_manager
            audio_manager.play_sound("teleport")
            teleport_distance = 80
            
            # Determine direction based on velocity or default to right
            if abs(self.vel_x) > 1:  # Moving horizontally
                if self.vel_x > 0:  # Moving right
                    target_x = self.x + teleport_distance
                    target_y = self.y
                else:  # Moving left
                    target_x = self.x - teleport_distance
                    target_y = self.y
            elif abs(self.vel_y) > 1:  # Moving vertically
                if self.vel_y > 0:  # Moving down
                    target_x = self.x
                    target_y = self.y + teleport_distance
                else:  # Moving up
                    target_x = self.x
                    target_y = self.y - teleport_distance
            else:  # Not moving, teleport right
                target_x = self.x + teleport_distance
                target_y = self.y
            
            # Keep within bounds
            target_x = max(self.width, min(SCREEN_WIDTH - self.width, target_x))
            target_y = max(self.height, min(SCREEN_HEIGHT - self.height, target_y))
            
            # Teleport to target position
            self.x = target_x
            self.y = target_y
            self.teleport_cooldown = 30
            self.glitch_timer = 45
                    
    def use_phase_crystal(self):
        """Use phase crystal from inventory"""
        if self.inventory['phase_crystals'] > 0:
            self.inventory['phase_crystals'] -= 1
            from audio import audio_manager
            audio_manager.play_sound("phase")
            self.phase_timer = 120  # 2 seconds
            self.glitch_timer = 30
            
    def draw_inventory(self, screen):
        """Draw inventory overlay"""
        if not self.inventory_open:
            return
            
        # Semi-transparent background
        overlay = pygame.Surface((300, 200))
        overlay.set_alpha(200)
        overlay.fill((20, 20, 40))
        screen.blit(overlay, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100))
        
        # Border
        pygame.draw.rect(screen, GLITCH_PINK, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100, 300, 200), 3)
        
        # Title
        font = pygame.font.Font(None, 36)
        title = font.render("INVENTORY", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 85))
        
        # Items
        small_font = pygame.font.Font(None, 24)
        y_offset = SCREEN_HEIGHT // 2 - 50
        
        # Glitch crystals
        glitch_text = small_font.render(f"Glitch Crystals Collected: {self.inventory['glitch_crystals']}", True, GLITCH_GREEN)
        screen.blit(glitch_text, (SCREEN_WIDTH // 2 - 130, y_offset))
        
        # Teleport crystals
        teleport_text = small_font.render(f"Teleport Crystals (E): {self.inventory['teleport_crystals']}", True, GLITCH_PINK)
        screen.blit(teleport_text, (SCREEN_WIDTH // 2 - 130, y_offset + 25))
        
        # Phase crystals
        phase_text = small_font.render(f"Phase Crystals (Q): {self.inventory['phase_crystals']}", True, BLUE)
        screen.blit(phase_text, (SCREEN_WIDTH // 2 - 130, y_offset + 50))
        
        # Instructions
        help_text = small_font.render("Abilities now require crystals!", True, WHITE)
        screen.blit(help_text, (SCREEN_WIDTH // 2 - 100, y_offset + 85))
        
        close_text = small_font.render("Press I to close", True, WHITE)
        screen.blit(close_text, (SCREEN_WIDTH // 2 - 60, y_offset + 105))
        
    def take_damage(self):
        if self.invulnerable_timer <= 0:
            self.health -= 1
            self.invulnerable_timer = 120
            return True
        return False
        
    def attack(self):
        """Perform melee attack"""
        if self.attack_timer <= 0:
            self.attack_timer = 20  # Attack cooldown
            return True
        return False
        
    def get_attack_rect(self):
        """Get attack hitbox rectangle"""
        if self.attack_timer > 15:  # Only during attack frames
            if self.facing_direction == 1:  # Facing right
                return pygame.Rect(self.x + self.width, self.y, self.attack_range, self.height)
            else:  # Facing left
                return pygame.Rect(self.x - self.attack_range, self.y, self.attack_range, self.height)
        return None
        
    def get_weapon_stats(self):
        """Get current weapon stats"""
        weapons = {
            "knife": {"damage": 1, "range": 25, "speed": 15},
            "sword": {"damage": 2, "range": 40, "speed": 25},
            "stick": {"damage": 1, "range": 35, "speed": 20}
        }
        return weapons.get(self.weapon, weapons["knife"])

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
        self.health = 2
        self.max_health = 2
        self.damage_timer = 0
        
    def update(self, walls, player):
        if self.type == "patrol":
            self.move_timer += 1
            if self.move_timer > 120:
                self.direction *= -1
                self.move_timer = 0
                
            old_x = self.x
            self.x += self.speed * self.direction
            
            enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            for wall in walls:
                if enemy_rect.colliderect(wall):
                    self.x = old_x
                    self.direction *= -1
                    break
                    
        elif self.type == "chaser":
            if abs(player.x - self.x) < 150 and abs(player.y - self.y) < 150:
                if player.x > self.x:
                    self.x += self.speed * 0.7
                elif player.x < self.x:
                    self.x -= self.speed * 0.7
                if player.y > self.y:
                    self.y += self.speed * 0.7
                elif player.y < self.y:
                    self.y -= self.speed * 0.7
                    
        # Update damage timer
        if self.damage_timer > 0:
            self.damage_timer -= 1
                    
    def draw(self, screen):
        # Flash red when damaged
        color = WHITE if self.damage_timer > 0 else self.color
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        pygame.draw.circle(screen, WHITE, (int(self.x + 5), int(self.y + 5)), 2)
        pygame.draw.circle(screen, WHITE, (int(self.x + 15), int(self.y + 5)), 2)
        
        # Health bar
        if self.health < self.max_health:
            bar_width = self.width
            bar_height = 3
            bar_x = self.x
            bar_y = self.y - 8
            
            # Background
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Health
            health_width = int((self.health / self.max_health) * bar_width)
            pygame.draw.rect(screen, RED, (bar_x, bar_y, health_width, bar_height))
            
    def take_damage(self, damage):
        """Take damage and return True if enemy dies"""
        self.health -= damage
        self.damage_timer = 10
        return self.health <= 0

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
            pygame.draw.circle(screen, YELLOW, self.rect.center, 8)
            pygame.draw.circle(screen, DOOR_COLOR, self.rect.center, 5)

class FallingRock:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.vel_y = 0
        self.active = False
        self.trigger_distance = 100
        
    def update(self, walls, player):
        if not self.active and abs(player.x - self.x) < self.trigger_distance:
            self.active = True
            
        if self.active:
            self.vel_y += GRAVITY * 0.5
            self.vel_y = min(self.vel_y, MAX_FALL_SPEED)
            
            old_y = self.y
            self.y += self.vel_y
            
            rock_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            for wall in walls:
                if rock_rect.colliderect(wall):
                    self.y = old_y
                    self.vel_y = 0
                    break
                    
    def draw(self, screen):
        color = (100, 80, 60) if not self.active else (120, 100, 80)
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        pygame.draw.circle(screen, (80, 60, 40), (int(self.x + 5), int(self.y + 5)), 3)
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class MovingPlatform:
    def __init__(self, x, y, width, move_range=100):
        self.start_x = x
        self.x = x
        self.y = y
        self.width = width
        self.height = 16
        self.move_range = move_range
        self.speed = 1
        self.direction = 1
        
    def update(self):
        self.x += self.speed * self.direction
        
        if self.x >= self.start_x + self.move_range or self.x <= self.start_x:
            self.direction *= -1
            
    def draw(self, screen):
        pygame.draw.rect(screen, CAVE_ACCENT, (self.x, self.y, self.width, self.height))
        for i in range(0, self.width, 8):
            pygame.draw.line(screen, tuple(min(255, c + 20) for c in CAVE_ACCENT), 
                           (self.x + i, self.y), (self.x + i, self.y + self.height), 1)
            
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)