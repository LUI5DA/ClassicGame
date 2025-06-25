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
        
        # Enhanced inventory system
        self.inventory_slots = [None] * 12  # 12 item slots
        self.equipment = {
            'weapon': {'type': 'knife', 'name': 'Iron Knife', 'damage': 1, 'speed': 15},
            'armor': None,
            'amulet': None,
            'ring': None
        }
        self.inventory_open = False
        self.crafting_mode = False
        self.selected_slot = 0
        
        # Add starting crystals to inventory
        self.add_item({'type': 'crystal', 'subtype': 'phase', 'count': 2, 'name': 'Phase Crystal'})
        self.add_item({'type': 'crystal', 'subtype': 'teleport', 'count': 2, 'name': 'Teleport Crystal'})
        
        # Combat system
        # Remove old weapon system - now handled by equipment
        self.attack_timer = 0
        self.attack_range = 35
        self.attack_damage = 1
        self.facing_direction = 1  # 1 = right, -1 = left
        
        # Power-up timers
        self.power_timer = 0
        self.shield_timer = 0
        
    def update(self, keys, walls):
        # Inventory toggle (always available)
        if keys[pygame.K_i]:
            if not hasattr(self, '_i_pressed') or not self._i_pressed:
                self.inventory_open = not self.inventory_open
                self.crafting_mode = False  # Reset crafting mode
                self._i_pressed = True
        else:
            self._i_pressed = False
            
        # If inventory is open, only handle inventory controls
        if self.inventory_open:
            self.handle_inventory_input(keys)
            return  # Skip all other player actions
            
        # Handle normal gameplay input
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
        else:
            self.vel_x *= FRICTION
            
        # Crystal-based abilities
        if keys[pygame.K_q]:
            if not hasattr(self, '_q_pressed') or not self._q_pressed:
                if self.count_crystals('phase') > 0:
                    self.use_phase_crystal()
                    print(f"Phase crystal used! {self.count_crystals('phase')} remaining")
                else:
                    print("No phase crystals! Collect glitch crystals first.")
                self._q_pressed = True
        else:
            self._q_pressed = False
            
        if keys[pygame.K_e]:
            if not hasattr(self, '_e_pressed') or not self._e_pressed:
                if self.count_crystals('teleport') > 0:
                    self.use_teleport_crystal()
                    print(f"Teleport crystal used! {self.count_crystals('teleport')} remaining")
                else:
                    print("No teleport crystals! Collect glitch crystals first.")
                self._e_pressed = True
        else:
            self._e_pressed = False
            
        # Inventory toggle
        if keys[pygame.K_i]:
            if not hasattr(self, '_i_pressed') or not self._i_pressed:
                self.inventory_open = not self.inventory_open
                self.crafting_mode = False  # Reset crafting mode
                self._i_pressed = True
        else:
            self._i_pressed = False
            
        # Crafting mode toggle (C key when inventory open)
        if self.inventory_open and keys[pygame.K_c]:
            if not hasattr(self, '_c_pressed') or not self._c_pressed:
                self.crafting_mode = not self.crafting_mode
                self._c_pressed = True
        else:
            self._c_pressed = False
            
        # Inventory navigation (when inventory open)
        if self.inventory_open:
            if keys[pygame.K_LEFT]:
                if not hasattr(self, '_left_pressed') or not self._left_pressed:
                    self.selected_slot = (self.selected_slot - 1) % 12
                    self._left_pressed = True
            else:
                self._left_pressed = False
                
            if keys[pygame.K_RIGHT]:
                if not hasattr(self, '_right_pressed') or not self._right_pressed:
                    self.selected_slot = (self.selected_slot + 1) % 12
                    self._right_pressed = True
            else:
                self._right_pressed = False
                
            if keys[pygame.K_UP]:
                if not hasattr(self, '_up_pressed') or not self._up_pressed:
                    self.selected_slot = (self.selected_slot - 4) % 12
                    self._up_pressed = True
            else:
                self._up_pressed = False
                
            if keys[pygame.K_DOWN]:
                if not hasattr(self, '_down_pressed') or not self._down_pressed:
                    self.selected_slot = (self.selected_slot + 4) % 12
                    self._down_pressed = True
            else:
                self._down_pressed = False
                
            # Use/equip selected item
            if keys[pygame.K_RETURN]:
                if not hasattr(self, '_enter_pressed') or not self._enter_pressed:
                    self.use_selected_item()
                    self._enter_pressed = True
            else:
                self._enter_pressed = False
            
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
        if self.power_timer > 0:
            self.power_timer -= 1
        if self.shield_timer > 0:
            self.shield_timer -= 1
            
    def handle_inventory_input(self, keys):
        """Handle input when inventory is open"""
        # Crafting mode toggle
        if keys[pygame.K_c]:
            if not hasattr(self, '_c_pressed') or not self._c_pressed:
                self.crafting_mode = not self.crafting_mode
                self._c_pressed = True
        else:
            self._c_pressed = False
            
        # Inventory navigation
        if keys[pygame.K_LEFT]:
            if not hasattr(self, '_left_pressed') or not self._left_pressed:
                self.selected_slot = (self.selected_slot - 1) % 12
                self._left_pressed = True
        else:
            self._left_pressed = False
            
        if keys[pygame.K_RIGHT]:
            if not hasattr(self, '_right_pressed') or not self._right_pressed:
                self.selected_slot = (self.selected_slot + 1) % 12
                self._right_pressed = True
        else:
            self._right_pressed = False
            
        if keys[pygame.K_UP]:
            if not hasattr(self, '_up_pressed') or not self._up_pressed:
                self.selected_slot = (self.selected_slot - 4) % 12
                self._up_pressed = True
        else:
            self._up_pressed = False
            
        if keys[pygame.K_DOWN]:
            if not hasattr(self, '_down_pressed') or not self._down_pressed:
                self.selected_slot = (self.selected_slot + 4) % 12
                self._down_pressed = True
        else:
            self._down_pressed = False
            
        # Use/equip selected item
        if keys[pygame.K_RETURN]:
            if not hasattr(self, '_enter_pressed') or not self._enter_pressed:
                self.use_selected_item()
                self._enter_pressed = True
        else:
            self._enter_pressed = False
            
        # Crafting in inventory
        if self.crafting_mode:
            if keys[pygame.K_1]:
                if not hasattr(self, '_craft1_pressed') or not self._craft1_pressed:
                    self.craft_power_crystal()
                    self._craft1_pressed = True
            else:
                self._craft1_pressed = False
                
            if keys[pygame.K_2]:
                if not hasattr(self, '_craft2_pressed') or not self._craft2_pressed:
                    self.craft_shield_crystal()
                    self._craft2_pressed = True
            else:
                self._craft2_pressed = False
            
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
            
        # Draw attack effect when attacking
        if self.attack_timer > 15:  # Only during attack frames
            attack_color = RED
            attack_rect = self.get_attack_rect()
            if attack_rect:
                # Draw attack effect rectangle
                pygame.draw.rect(screen, attack_color, attack_rect, 2)
                
                # Draw direction indicator based on attack direction
                if hasattr(self, 'attack_direction'):
                    dx, dy = self.attack_direction
                    center_x = self.x + self.width/2
                    center_y = self.y + self.height/2
                    
                    # Normalize for drawing
                    length = max(0.1, (dx**2 + dy**2)**0.5)
                    ndx = dx / length * 20  # Scale for arrow
                    ndy = dy / length * 20
                    
                    # Draw arrow in attack direction
                    end_x = center_x + ndx
                    end_y = center_y + ndy
                    pygame.draw.line(screen, attack_color, (center_x, center_y), (end_x, end_y), 2)
                    
                    # Arrow head
                    head_size = 8
                    pygame.draw.circle(screen, attack_color, (int(end_x), int(end_y)), head_size//2)
            
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
        teleport_count = self.count_crystals('teleport')
        phase_count = self.count_crystals('phase')
        if teleport_count > 0 or phase_count > 0:
            # Teleport crystals (pink dots)
            if teleport_count > 0:
                for i in range(min(teleport_count, 5)):
                    pygame.draw.circle(screen, GLITCH_PINK, (int(self.x + 5 + i * 8), int(self.y - 8)), 3)
            
            # Phase crystals (blue dots)
            if phase_count > 0:
                for i in range(min(phase_count, 5)):
                    pygame.draw.circle(screen, BLUE, (int(self.x + 5 + i * 8), int(self.y - 18)), 3)
                    
        # Power-up indicators
        if self.power_timer > 0:
            # Power crystal effect - red glow
            pygame.draw.circle(screen, RED, (int(self.x + self.width + 15), int(self.y + 5)), 6)
            pygame.draw.circle(screen, YELLOW, (int(self.x + self.width + 15), int(self.y + 5)), 3)
            
        if self.shield_timer > 0:
            # Shield crystal effect - blue glow
            pygame.draw.circle(screen, BLUE, (int(self.x + self.width + 15), int(self.y + 15)), 6)
            pygame.draw.circle(screen, WHITE, (int(self.x + self.width + 15), int(self.y + 15)), 3)
        
    def activate_glitch(self):
        self.glitch_timer = 60
        # Add glitch crystal to inventory
        glitch_crystal = {'type': 'crystal', 'subtype': 'glitch', 'count': 1, 'name': 'Glitch Crystal'}
        self.add_item(glitch_crystal)
        
        # Convert to usable crystals randomly
        if random.randint(0, 1) == 0:
            teleport_crystal = {'type': 'crystal', 'subtype': 'teleport', 'count': 1, 'name': 'Teleport Crystal'}
            self.add_item(teleport_crystal)
            print("Gained teleport crystal!")
        else:
            phase_crystal = {'type': 'crystal', 'subtype': 'phase', 'count': 1, 'name': 'Phase Crystal'}
            self.add_item(phase_crystal)
            print("Gained phase crystal!")
            
        # Glitch jump boost
        if not self.on_ground:
            self.vel_y = JUMP_STRENGTH * 0.7
            self.jump_count = 0  # Reset jumps
            
    def use_teleport_crystal(self):
        """Use teleport crystal from inventory"""
        if self.consume_crystal('teleport') and self.teleport_cooldown <= 0:
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
            
    def use_teleport_crystal_directed(self, dx, dy):
        """Use teleport crystal in a specific direction (for mouse control)"""
        if self.consume_crystal('teleport') and self.teleport_cooldown <= 0:
            from audio import audio_manager
            audio_manager.play_sound("teleport")
            
            # Calculate target position
            target_x = self.x + dx
            target_y = self.y + dy
            
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
        if self.consume_crystal('phase'):
            from audio import audio_manager
            audio_manager.play_sound("phase")
            self.phase_timer = 120  # 2 seconds
            self.glitch_timer = 30
            
    def craft_power_crystal(self):
        """Craft power crystal: 2 glitch + 1 teleport = 1 power"""
        if self.count_crystals('glitch') >= 2 and self.count_crystals('teleport') >= 1:
            for _ in range(2):
                self.consume_crystal('glitch')
            self.consume_crystal('teleport')
            power_crystal = {'type': 'crystal', 'subtype': 'power', 'count': 1, 'name': 'Power Crystal'}
            self.add_item(power_crystal)
            print("Crafted Power Crystal! (Double damage for 10 seconds)")
            from audio import audio_manager
            audio_manager.play_sound("crystal")
        else:
            print("Need: 2 Glitch + 1 Teleport crystals")
            
    def craft_shield_crystal(self):
        """Craft shield crystal: 2 glitch + 1 phase = 1 shield"""
        if self.count_crystals('glitch') >= 2 and self.count_crystals('phase') >= 1:
            for _ in range(2):
                self.consume_crystal('glitch')
            self.consume_crystal('phase')
            shield_crystal = {'type': 'crystal', 'subtype': 'shield', 'count': 1, 'name': 'Shield Crystal'}
            self.add_item(shield_crystal)
            print("Crafted Shield Crystal! (Invulnerability for 5 seconds)")
            from audio import audio_manager
            audio_manager.play_sound("crystal")
        else:
            print("Need: 2 Glitch + 1 Phase crystals")
            
    def use_power_crystal(self):
        """Use power crystal for double damage"""
        if self.consume_crystal('power'):
            self.power_timer = 600  # 10 seconds
            print("Power Crystal activated! Double damage for 10 seconds!")
            from audio import audio_manager
            audio_manager.play_sound("glitch")
            
    def use_shield_crystal(self):
        """Use shield crystal for invulnerability"""
        if self.consume_crystal('shield'):
            self.shield_timer = 300  # 5 seconds
            print("Shield Crystal activated! Invulnerable for 5 seconds!")
            from audio import audio_manager
            audio_manager.play_sound("glitch")
            
    def count_crystals(self, crystal_type):
        """Count crystals of specified type"""
        count = 0
        for slot in self.inventory_slots:
            if slot and slot['type'] == 'crystal' and slot['subtype'] == crystal_type:
                count += slot['count']
        return count
            
    def draw_inventory(self, screen):
        """Draw enhanced inventory overlay"""
        if not self.inventory_open:
            return
            
        # Larger inventory window
        inv_width, inv_height = 500, 400
        inv_x = SCREEN_WIDTH // 2 - inv_width // 2
        inv_y = SCREEN_HEIGHT // 2 - inv_height // 2
        
        # Semi-transparent background
        overlay = pygame.Surface((inv_width, inv_height))
        overlay.set_alpha(220)
        overlay.fill((15, 15, 30))
        screen.blit(overlay, (inv_x, inv_y))
        
        # Border
        pygame.draw.rect(screen, GLITCH_PINK, (inv_x, inv_y, inv_width, inv_height), 3)
        
        # Title
        font = pygame.font.Font(None, 32)
        title = font.render("INVENTORY", True, WHITE)
        screen.blit(title, (inv_x + 20, inv_y + 10))
        
        small_font = pygame.font.Font(None, 18)
        
        # Equipment slots (left side)
        eq_x, eq_y = inv_x + 20, inv_y + 50
        eq_font = pygame.font.Font(None, 20)
        
        # Equipment title
        eq_title = eq_font.render("EQUIPMENT", True, YELLOW)
        screen.blit(eq_title, (eq_x, eq_y))
        
        # Draw equipment slots
        slot_size = 40
        equipment_slots = [
            ('weapon', 'WEAPON', RED),
            ('armor', 'ARMOR', BLUE),
            ('amulet', 'AMULET', GLITCH_PINK),
            ('ring', 'RING', YELLOW)
        ]
        
        for i, (slot_type, label, color) in enumerate(equipment_slots):
            slot_x = eq_x
            slot_y = eq_y + 30 + i * 50
            
            # Slot background
            pygame.draw.rect(screen, (40, 40, 40), (slot_x, slot_y, slot_size, slot_size))
            pygame.draw.rect(screen, color, (slot_x, slot_y, slot_size, slot_size), 2)
            
            # Equipment item
            item = self.equipment[slot_type]
            if item:
                # Draw item (simplified as colored square)
                pygame.draw.rect(screen, color, (slot_x + 5, slot_y + 5, slot_size - 10, slot_size - 10))
                # Item name
                name_text = small_font.render(item['name'][:8], True, WHITE)
                screen.blit(name_text, (slot_x + slot_size + 5, slot_y + 5))
            else:
                # Empty slot label
                label_text = small_font.render(label, True, (100, 100, 100))
                screen.blit(label_text, (slot_x + slot_size + 5, slot_y + 15))
        
        # Inventory grid (right side)
        grid_x = inv_x + 250
        grid_y = inv_y + 50
        
        # Inventory title
        inv_title = eq_font.render("ITEMS (12 slots)", True, WHITE)
        screen.blit(inv_title, (grid_x, grid_y))
        
        # Draw inventory grid (3x4)
        slot_size = 45
        for i in range(12):
            row = i // 4
            col = i % 4
            slot_x = grid_x + col * (slot_size + 5)
            slot_y = grid_y + 30 + row * (slot_size + 5)
            
            # Slot background
            if i == self.selected_slot:
                pygame.draw.rect(screen, GLITCH_PINK, (slot_x - 2, slot_y - 2, slot_size + 4, slot_size + 4), 3)
            
            pygame.draw.rect(screen, (30, 30, 30), (slot_x, slot_y, slot_size, slot_size))
            pygame.draw.rect(screen, (80, 80, 80), (slot_x, slot_y, slot_size, slot_size), 1)
            
            # Item in slot
            item = self.inventory_slots[i]
            if item:
                if item['type'] == 'crystal':
                    colors = {
                        'glitch': GLITCH_GREEN,
                        'teleport': GLITCH_PINK,
                        'phase': BLUE,
                        'power': YELLOW,
                        'shield': WHITE
                    }
                    color = colors.get(item['subtype'], WHITE)
                    pygame.draw.circle(screen, color, (slot_x + slot_size//2, slot_y + slot_size//2), 15)
                    
                    # Count
                    if item['count'] > 1:
                        count_text = small_font.render(str(item['count']), True, WHITE)
                        screen.blit(count_text, (slot_x + slot_size - 15, slot_y + slot_size - 15))
                        
                elif item['type'] in ['weapon', 'armor']:
                    color = RED if item['type'] == 'weapon' else BLUE
                    pygame.draw.rect(screen, color, (slot_x + 5, slot_y + 5, slot_size - 10, slot_size - 10))
        
        # Instructions
        inst_y = inv_y + inv_height - 80
        instructions = [
            "Arrow Keys: Navigate | Enter: Use/Equip",
            "C: Crafting Mode | I: Close"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_text = small_font.render(instruction, True, WHITE)
            screen.blit(inst_text, (inv_x + 20, inst_y + i * 20))
            
        # Selected item info
        if self.inventory_slots[self.selected_slot]:
            item = self.inventory_slots[self.selected_slot]
            info_text = small_font.render(f"Selected: {item['name']}", True, YELLOW)
            screen.blit(info_text, (inv_x + 20, inst_y + 40))
            
        # Crafting recipes (if in crafting mode)
        if self.crafting_mode:
            craft_y = inv_y + 250
            craft_title = eq_font.render("CRAFTING RECIPES:", True, GLITCH_PINK)
            screen.blit(craft_title, (inv_x + 20, craft_y))
            
            recipe1 = small_font.render("1. Power Crystal: 2 Glitch + 1 Teleport", True, YELLOW)
            screen.blit(recipe1, (inv_x + 20, craft_y + 25))
            
            recipe2 = small_font.render("2. Shield Crystal: 2 Glitch + 1 Phase", True, WHITE)
            screen.blit(recipe2, (inv_x + 20, craft_y + 45))
        
    def take_damage(self):
        if self.shield_timer > 0:
            print("Shield blocked damage!")
            return False  # Shield blocks damage
        if self.invulnerable_timer <= 0:
            self.health -= 1
            self.invulnerable_timer = 120
            return True
        return False
        
    def attack(self, direction_x=None, direction_y=None):
        """Perform melee attack, optionally in a specific direction"""
        if self.attack_timer <= 0:
            self.attack_timer = 20  # Attack cooldown
            
            # Store attack direction if provided
            if direction_x is not None and direction_y is not None:
                self.attack_direction = (direction_x, direction_y)
            else:
                # Default to horizontal direction based on facing
                self.attack_direction = (self.facing_direction, 0)
                
            weapon_name = self.equipment['weapon']['name'] if self.equipment['weapon'] else 'Fists'
            print(f"Player attacks with {weapon_name}!")
            from audio import audio_manager
            audio_manager.play_sound("attack")
            return True
        return False
        
    def get_attack_rect(self):
        """Get attack hitbox rectangle based on attack direction"""
        if self.attack_timer > 15:  # Only during attack frames
            # Get attack direction (stored during attack)
            if hasattr(self, 'attack_direction'):
                dx, dy = self.attack_direction
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                
                # Determine if attack is more horizontal or vertical
                if abs(dx) > abs(dy):  # More horizontal
                    if dx > 0:  # Right
                        return pygame.Rect(self.x + self.width, self.y, self.attack_range, self.height)
                    else:  # Left
                        return pygame.Rect(self.x - self.attack_range, self.y, self.attack_range, self.height)
                else:  # More vertical
                    if dy > 0:  # Down
                        return pygame.Rect(self.x, self.y + self.height, self.width, self.attack_range)
                    else:  # Up
                        return pygame.Rect(self.x, self.y - self.attack_range, self.width, self.attack_range)
            else:
                # Fallback to horizontal direction
                if self.facing_direction == 1:  # Facing right
                    return pygame.Rect(self.x + self.width, self.y, self.attack_range, self.height)
                else:  # Facing left
                    return pygame.Rect(self.x - self.attack_range, self.y, self.attack_range, self.height)
        return None
        
    def get_weapon_stats(self):
        """Get current weapon stats"""
        weapon = self.equipment['weapon']
        if not weapon:
            weapon = {'damage': 1, 'range': 25, 'speed': 15}  # Default fists
            
        stats = {
            'damage': weapon.get('damage', 1),
            'range': weapon.get('range', 25),
            'speed': weapon.get('speed', 15)
        }
        
        # Double damage if power crystal is active
        if self.power_timer > 0:
            stats['damage'] *= 2
        return stats
        
    def add_item(self, item):
        """Add item to inventory"""
        # Try to stack crystals
        if item['type'] == 'crystal':
            for slot in self.inventory_slots:
                if slot and slot['type'] == 'crystal' and slot['subtype'] == item['subtype']:
                    slot['count'] += item['count']
                    return True
                    
        # Find empty slot
        for i, slot in enumerate(self.inventory_slots):
            if slot is None:
                self.inventory_slots[i] = item
                return True
        return False  # Inventory full
        
    def consume_crystal(self, crystal_type):
        """Consume one crystal of specified type"""
        for slot in self.inventory_slots:
            if slot and slot['type'] == 'crystal' and slot['subtype'] == crystal_type:
                slot['count'] -= 1
                if slot['count'] <= 0:
                    idx = self.inventory_slots.index(slot)
                    self.inventory_slots[idx] = None
                return True
        return False
        
    def use_selected_item(self):
        """Use or equip the selected inventory item"""
        item = self.inventory_slots[self.selected_slot]
        if not item:
            return
            
        if item['type'] == 'crystal':
            if item['subtype'] == 'teleport':
                self.use_teleport_crystal()
            elif item['subtype'] == 'phase':
                self.use_phase_crystal()
            elif item['subtype'] == 'power':
                self.use_power_crystal()
            elif item['subtype'] == 'shield':
                self.use_shield_crystal()
        elif item['type'] == 'weapon':
            self.equip_weapon(item)
        elif item['type'] == 'armor':
            self.equip_armor(item)
            
    def equip_weapon(self, weapon):
        """Equip a weapon"""
        old_weapon = self.equipment['weapon']
        self.equipment['weapon'] = weapon
        self.inventory_slots[self.selected_slot] = old_weapon
        print(f"Equipped {weapon['name']}!")
        
    def equip_armor(self, armor):
        """Equip armor"""
        old_armor = self.equipment['armor']
        self.equipment['armor'] = armor
        self.inventory_slots[self.selected_slot] = old_armor
        print(f"Equipped {armor['name']}!")

class Crystal:
    # Class variables for shared images
    crystal_image = None
    glitch_crystal_image = None
    
    def __init__(self, x, y, is_glitch=False):
        self.x = x
        self.y = y
        self.size = 16
        self.glow = 0
        self.collected = False
        self.is_glitch = is_glitch
        
        # Load images if not already loaded
        if Crystal.crystal_image is None:
            try:
                Crystal.crystal_image = pygame.image.load("crystal.png")
                Crystal.crystal_image = pygame.transform.scale(Crystal.crystal_image, (80, 80))
                print("Crystal image loaded")
            except:
                print("Could not load crystal.png")
                Crystal.crystal_image = False
                
        if Crystal.glitch_crystal_image is None:
            try:
                Crystal.glitch_crystal_image = pygame.image.load("gllitch_crystal.png")
                Crystal.glitch_crystal_image = pygame.transform.scale(Crystal.glitch_crystal_image, (80, 80))
                print("Glitch crystal image loaded")
            except:
                print("Could not load gllitch_crystal.png")
                Crystal.glitch_crystal_image = False
        
    def update(self):
        self.glow = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 50
        
    def draw(self, screen):
        if not self.collected:
            if self.is_glitch and Crystal.glitch_crystal_image:
                # Draw glitch crystal image
                rect = Crystal.glitch_crystal_image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(Crystal.glitch_crystal_image, rect)
            elif not self.is_glitch and Crystal.crystal_image:
                # Draw normal crystal image
                rect = Crystal.crystal_image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(Crystal.crystal_image, rect)
            else:
                # Fallback to colored circles if images failed to load
                if self.is_glitch:
                    colors = [GLITCH_PINK, GLITCH_GREEN, CRYSTAL_BLUE]
                    color = random.choice(colors)
                    pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
                else:
                    glow_color = (100 + self.glow, 150 + self.glow, 255)
                    pygame.draw.circle(screen, glow_color, (int(self.x), int(self.y)), self.size)
                    pygame.draw.circle(screen, CRYSTAL_BLUE, (int(self.x), int(self.y)), self.size - 4)

class Enemy:
    # Class variable for shared image
    enemy_image = None
    
    def __init__(self, x, y, enemy_type="patrol"):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        # Faster enemies for higher difficulty
        self.speed = 1.5 if enemy_type == "chaser" else 1
        self.color = RED
        self.type = enemy_type
        self.direction = random.choice([-1, 1])
        self.move_timer = 0
        self.health = 2
        self.max_health = 2
        self.damage_timer = 0
        
        # Load enemy image if not already loaded
        if Enemy.enemy_image is None:
            try:
                Enemy.enemy_image = pygame.image.load("beatle.png")
                Enemy.enemy_image = pygame.transform.scale(Enemy.enemy_image, (120, 120))
                print("Enemy image loaded")
            except:
                print("Could not load beatle.png")
                Enemy.enemy_image = False
        
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
        if Enemy.enemy_image:
            # Draw enemy image
            image = Enemy.enemy_image
            if self.damage_timer > 0:
                # Create white flash effect
                flash_image = image.copy()
                flash_image.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
                image = flash_image
            
            rect = image.get_rect(center=(int(self.x + self.width//2), int(self.y + self.height//2)))
            screen.blit(image, rect)
        else:
            # Fallback to colored rectangle if image failed to load
            color = WHITE if self.damage_timer > 0 else self.color
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
            pygame.draw.circle(screen, WHITE, (int(self.x + 5), int(self.y + 5)), 2)
            pygame.draw.circle(screen, WHITE, (int(self.x + 15), int(self.y + 5)), 2)
        
        # Always show health bar above enemy
        bar_width = 30
        bar_height = 4
        bar_x = self.x - 5
        bar_y = self.y - 15  # Moved up slightly for image
        
        # Background (dark gray)
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        # Health (green to red based on health)
        health_width = int((self.health / self.max_health) * bar_width)
        if self.health > 1:
            health_color = GREEN
        else:
            health_color = RED
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Health text
        font = pygame.font.Font(None, 16)
        health_text = font.render(f"{self.health}/{self.max_health}", True, WHITE)
        screen.blit(health_text, (bar_x, bar_y - 15))
        
    def take_damage(self, damage):
        """Take damage and return True if enemy dies"""
        self.health -= damage
        self.damage_timer = 10
        return self.health <= 0
        
class GlitchEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "glitch")
        self.color = GLITCH_PINK
        self.health = 3
        self.max_health = 3
        self.speed = 2
        self.teleport_timer = 0
        
    def update(self, walls, player):
        if self.teleport_timer > 0:
            self.teleport_timer -= 1
            
        distance = ((player.x - self.x)**2 + (player.y - self.y)**2)**0.5
        
        if distance < 150 and self.teleport_timer <= 0:
            # Simple teleport near player
            self.x = player.x + random.randint(-80, 80)
            self.y = player.y + random.randint(-80, 80)
            self.teleport_timer = 120
            from audio import audio_manager
            audio_manager.play_sound("glitch")
            print("Glitch enemy teleported!")
        else:
            # Normal chase behavior
            if player.x > self.x:
                self.x += self.speed
            elif player.x < self.x:
                self.x -= self.speed
            if player.y > self.y:
                self.y += self.speed
            elif player.y < self.y:
                self.y -= self.speed
                
        if self.damage_timer > 0:
            self.damage_timer -= 1
            
    def draw(self, screen):
        color = GLITCH_PINK if random.randint(0, 3) == 0 else self.color
        if self.damage_timer > 0:
            color = WHITE
            
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        pygame.draw.circle(screen, RED, (int(self.x + 5), int(self.y + 5)), 2)
        pygame.draw.circle(screen, RED, (int(self.x + 15), int(self.y + 5)), 2)
        
        # Pink health bar
        bar_width = 30
        bar_height = 4
        bar_x = self.x - 5
        bar_y = self.y - 15
        
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(screen, GLITCH_PINK, (bar_x, bar_y, health_width, bar_height))

class Boss(Enemy):
    def __init__(self, x, y, boss_type="guardian"):
        super().__init__(x, y, boss_type)
        self.width = 40
        self.height = 40
        self.health = 8
        self.max_health = 8
        self.speed = 0.5
        self.color = (150, 0, 150)  # Purple
        self.attack_timer = 0
        self.special_timer = 0
        self.phase = 1
        self.projectiles = []
        
    def update(self, walls, player):
        # Boss AI phases
        if self.health > 6:  # Phase 1: Slow chase
            self.chase_player(player)
        elif self.health > 3:  # Phase 2: Projectile attacks
            self.projectile_attack(player)
        else:  # Phase 3: Aggressive rush
            self.aggressive_attack(player)
            
        # Update projectiles
        for projectile in self.projectiles[:]:
            projectile.update()
            if projectile.x < 0 or projectile.x > SCREEN_WIDTH or projectile.y < 0 or projectile.y > SCREEN_HEIGHT:
                self.projectiles.remove(projectile)
                
        # Update timers
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.special_timer > 0:
            self.special_timer -= 1
        if self.damage_timer > 0:
            self.damage_timer -= 1
            
    def chase_player(self, player):
        if abs(player.x - self.x) < 200 and abs(player.y - self.y) < 200:
            if player.x > self.x:
                self.x += self.speed
            elif player.x < self.x:
                self.x -= self.speed
            if player.y > self.y:
                self.y += self.speed
            elif player.y < self.y:
                self.y -= self.speed
                
    def projectile_attack(self, player):
        if self.attack_timer <= 0:
            # Shoot projectile at player
            dx = player.x - self.x
            dy = player.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                proj_speed = 3
                proj_dx = (dx / distance) * proj_speed
                proj_dy = (dy / distance) * proj_speed
                self.projectiles.append(Projectile(self.x + self.width//2, self.y + self.height//2, proj_dx, proj_dy))
                self.attack_timer = 60
                
    def aggressive_attack(self, player):
        # Fast chase in final phase
        if abs(player.x - self.x) < 300 and abs(player.y - self.y) < 300:
            chase_speed = self.speed * 2
            if player.x > self.x:
                self.x += chase_speed
            elif player.x < self.x:
                self.x -= chase_speed
            if player.y > self.y:
                self.y += chase_speed
            elif player.y < self.y:
                self.y -= chase_speed
                
    def draw(self, screen):
        # Flash when damaged
        color = WHITE if self.damage_timer > 0 else self.color
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        
        # Boss eyes
        pygame.draw.circle(screen, RED, (int(self.x + 10), int(self.y + 10)), 4)
        pygame.draw.circle(screen, RED, (int(self.x + 30), int(self.y + 10)), 4)
        
        # Health bar (always visible for boss)
        bar_width = 60
        bar_height = 6
        bar_x = self.x - 10
        bar_y = self.y - 15
        
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        health_width = int((self.health / self.max_health) * bar_width)
        if self.health > 4:
            health_color = GREEN
        elif self.health > 2:
            health_color = YELLOW
        else:
            health_color = RED
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(screen)
            
class Projectile:
    def __init__(self, x, y, vel_x, vel_y):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.size = 6
        
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        
    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.size - 2)
        
    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)

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
        self.can_use = False
        
    def draw(self, screen):
        if self.locked:
            pygame.draw.rect(screen, DOOR_COLOR, self.rect)
            pygame.draw.circle(screen, YELLOW, self.rect.center, 8)
            pygame.draw.circle(screen, DOOR_COLOR, self.rect.center, 5)
        else:
            # Unlocked door - different color
            color = GREEN if hasattr(self, 'can_use') and self.can_use else BLUE
            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.circle(screen, WHITE, self.rect.center, 8)
            if hasattr(self, 'can_use') and self.can_use:
                # Glowing effect when player can use
                pygame.draw.rect(screen, WHITE, self.rect, 3)

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