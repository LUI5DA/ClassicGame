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
        self.glitch_energy = 0
        self.max_glitch_energy = 100
        self.phase_timer = 0
        self.teleport_cooldown = 0
        
    def update(self, keys, walls):
        # Handle input
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
        else:
            self.vel_x *= FRICTION
            
        # Glitch abilities
        if keys[pygame.K_q] and not hasattr(self, '_q_pressed'):
            self.glitch_phase()
            self._q_pressed = True
        elif not keys[pygame.K_q]:
            self._q_pressed = False
            
        if keys[pygame.K_e] and not hasattr(self, '_e_pressed'):
            # Teleport in movement direction
            teleport_distance = 80
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.glitch_teleport(self.x - teleport_distance, self.y, walls)
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.glitch_teleport(self.x + teleport_distance, self.y, walls)
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                self.glitch_teleport(self.x, self.y - teleport_distance, walls)
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.glitch_teleport(self.x, self.y + teleport_distance, walls)
            else:
                # Default teleport forward
                self.glitch_teleport(self.x + teleport_distance, self.y, walls)
            self._e_pressed = True
        elif not keys[pygame.K_e]:
            self._e_pressed = False
            
        # Jumping (ground jump or double jump)
        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.can_jump:
            if self.on_ground or self.jump_count < self.max_jumps:
                self.vel_y = JUMP_STRENGTH
                self.jump_count += 1
                self.on_ground = False
                self.can_jump = False
                
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
            
        # Regenerate glitch energy slowly
        if self.glitch_energy < self.max_glitch_energy:
            self.glitch_energy += 0.2
    
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
        else:
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        
        # Draw jump indicator
        if self.jump_count > 0 and not self.on_ground:
            for i in range(self.jump_count):
                pygame.draw.circle(screen, YELLOW, (int(self.x + 5 + i * 8), int(self.y - 5)), 3)
                
        # Draw glitch energy bar
        if self.glitch_energy > 0:
            bar_width = 30
            bar_height = 4
            bar_x = self.x - 3
            bar_y = self.y - 10
            
            # Background
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Energy
            energy_width = int((self.glitch_energy / self.max_glitch_energy) * bar_width)
            pygame.draw.rect(screen, GLITCH_PINK, (bar_x, bar_y, energy_width, bar_height))
        
    def activate_glitch(self):
        self.glitch_timer = 60
        self.glitch_energy = min(self.max_glitch_energy, self.glitch_energy + 30)
        # Glitch jump boost
        if not self.on_ground:
            self.vel_y = JUMP_STRENGTH * 0.7
            self.jump_count = 0  # Reset jumps
            
    def glitch_teleport(self, target_x, target_y, walls):
        """Teleport to target position if enough energy"""
        if self.glitch_energy >= 40 and self.teleport_cooldown <= 0:
            # Check if target position is valid (not in wall)
            target_rect = pygame.Rect(target_x, target_y, self.width, self.height)
            collision = any(wall.colliderect(target_rect) for wall in walls)
            
            if not collision:
                self.x = target_x
                self.y = target_y
                self.glitch_energy -= 40
                self.teleport_cooldown = 60
                self.glitch_timer = 30
                return True
        return False
        
    def glitch_phase(self):
        """Phase through walls for short time"""
        if self.glitch_energy >= 25 and self.phase_timer <= 0:
            self.phase_timer = 90  # 1.5 seconds
            self.glitch_energy -= 25
            self.glitch_timer = 30
            return True
        return False
        
    def take_damage(self):
        if self.invulnerable_timer <= 0:
            self.health -= 1
            self.invulnerable_timer = 120
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
                    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
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