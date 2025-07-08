import random
import math
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

class CaveParameters:
    def __init__(self, 
                 cave_type="mixed",
                 density=0.45,
                 iterations=5,
                 smoothing_passes=2,
                 tunnel_width=5,
                 room_size_preference=0.5,
                 vertical_bias=0.0,
                 horizontal_bias=0.0,
                 noise_scale=0.5,
                 noise_octaves=3,
                 connectivity_strength=1.0):
        
        self.cave_type = cave_type  # "cellular", "perlin", "maze", "cavern", "mixed"
        self.density = density  # 0.0-1.0: Wall density for cellular automata
        self.iterations = iterations  # Cellular automata iterations
        self.smoothing_passes = smoothing_passes  # Post-processing smoothing
        self.tunnel_width = tunnel_width  # Width of connecting tunnels
        self.room_size_preference = room_size_preference  # 0.0=small rooms, 1.0=large rooms
        self.vertical_bias = vertical_bias  # -1.0=horizontal, 1.0=vertical caves
        self.horizontal_bias = horizontal_bias  # -1.0=vertical, 1.0=horizontal caves
        self.noise_scale = noise_scale  # Perlin noise frequency
        self.noise_octaves = noise_octaves  # Noise complexity layers
        self.connectivity_strength = connectivity_strength  # How aggressively to connect regions

class CaveGenerator:
    @staticmethod
    def generate_cave(width, height, params):
        """Main cave generation function using parameters"""
        if params.cave_type == "cellular":
            return CaveGenerator.generate_cellular_automata(width, height, params)
        elif params.cave_type == "perlin":
            return CaveGenerator.generate_perlin_cave(width, height, params)
        elif params.cave_type == "maze":
            return CaveGenerator.generate_maze_cave(width, height, params)
        elif params.cave_type == "cavern":
            return CaveGenerator.generate_cavern(width, height, params)
        else:  # mixed
            return CaveGenerator.generate_mixed_cave(width, height, params)
    
    @staticmethod
    def generate_cellular_automata(width, height, params):
        cave = [[False for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                base_density = params.density
                
                # Apply vertical bias
                if params.vertical_bias != 0:
                    center_distance = abs(x - width // 2) / (width // 2)
                    base_density += params.vertical_bias * center_distance * 0.3
                    
                # Apply horizontal bias
                if params.horizontal_bias != 0:
                    center_distance = abs(y - height // 2) / (height // 2)
                    base_density += params.horizontal_bias * center_distance * 0.3
                    
                cave[y][x] = random.random() < base_density
        
        # Cellular automata iterations
        for iteration in range(params.iterations):
            new_cave = [[False for _ in range(width)] for _ in range(height)]
            for y in range(height):
                for x in range(width):
                    wall_count = CaveGenerator.count_walls(cave, x, y, width, height)
                    threshold = 4 + int((1 - params.room_size_preference) * 2)
                    new_cave[y][x] = wall_count >= threshold
            cave = new_cave
        
        return cave
    
    @staticmethod
    def generate_perlin_cave(width, height, params):
        cave = [[False for _ in range(width)] for _ in range(height)]
        offset_x = random.randint(0, 1000)
        offset_y = random.randint(0, 1000)
        
        for y in range(height):
            for x in range(width):
                noise_val = 0
                amplitude = 1
                frequency = params.noise_scale
                
                for _ in range(params.noise_octaves):
                    x_freq = frequency * (1 + params.horizontal_bias * 0.5)
                    y_freq = frequency * (1 + params.vertical_bias * 0.5)
                    
                    noise_val += amplitude * (math.sin((x + offset_x) * x_freq) * math.cos((y + offset_y) * y_freq))
                    amplitude *= 0.5
                    frequency *= 2
                
                threshold = 0.3 + (params.room_size_preference - 0.5) * 0.4
                noise_val = (noise_val + 1) / 2
                cave[y][x] = noise_val > threshold
        
        return cave
    
    @staticmethod
    def generate_maze_cave(width, height, params):
        """Generate maze-like cave structures"""
        cave = [[True for _ in range(width)] for _ in range(height)]
        
        path_width = max(1, int(params.tunnel_width))
        start_x, start_y = width // 2, height // 2
        stack = [(start_x, start_y)]
        visited = set()
        
        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
                
            visited.add((x, y))
            
            # Carve out area
            for dy in range(-path_width, path_width + 1):
                for dx in range(-path_width, path_width + 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        cave[ny][nx] = False
            
            # Add neighbors with bias
            directions = [(0, 4), (0, -4), (4, 0), (-4, 0)]
            
            if params.horizontal_bias > 0:
                directions = [(4, 0), (-4, 0), (0, 4), (0, -4)]
            elif params.vertical_bias > 0:
                directions = [(0, 4), (0, -4), (4, 0), (-4, 0)]
                
            random.shuffle(directions)
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 < nx < width - 1 and 0 < ny < height - 1 and 
                    (nx, ny) not in visited and random.random() < 0.7):
                    stack.append((nx, ny))
        
        return cave
    
    @staticmethod
    def generate_cavern(width, height, params):
        """Generate large open caverns"""
        cave = [[True for _ in range(width)] for _ in range(height)]
        
        num_caverns = max(2, int(4 * params.room_size_preference))
        
        for _ in range(num_caverns):
            cx = random.randint(width // 4, 3 * width // 4)
            cy = random.randint(height // 4, 3 * height // 4)
            
            base_radius = int(20 + params.room_size_preference * 30)
            
            for y in range(max(0, cy - base_radius), min(height, cy + base_radius)):
                for x in range(max(0, cx - base_radius), min(width, cx + base_radius)):
                    dx, dy = x - cx, y - cy
                    
                    x_scale = 1 + params.horizontal_bias * 0.5
                    y_scale = 1 + params.vertical_bias * 0.5
                    
                    distance = math.sqrt((dx / x_scale) ** 2 + (dy / y_scale) ** 2)
                    
                    if distance < base_radius * (0.7 + random.random() * 0.3):
                        cave[y][x] = False
        
        return cave
    
    @staticmethod
    def generate_mixed_cave(width, height, params):
        """Combine multiple generation techniques"""
        cave1 = CaveGenerator.generate_cellular_automata(width, height, params)
        
        perlin_params = CaveParameters(
            noise_scale=params.noise_scale * 1.5,
            room_size_preference=1 - params.room_size_preference
        )
        cave2 = CaveGenerator.generate_perlin_cave(width, height, perlin_params)
        
        combined = [[False for _ in range(width)] for _ in range(height)]
        for y in range(height):
            for x in range(width):
                if params.room_size_preference > 0.5:
                    combined[y][x] = cave1[y][x] and cave2[y][x]
                else:
                    combined[y][x] = cave1[y][x] or cave2[y][x]
        
        return combined
    
    @staticmethod
    def count_walls(cave, x, y, width, height):
        count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    count += 1
                elif cave[ny][nx]:
                    count += 1
        return count
    
    @staticmethod
    def smooth_cave(cave, width, height, params):
        new_cave = [[cave[y][x] for x in range(width)] for y in range(height)]
        
        for _ in range(params.smoothing_passes):
            temp_cave = [[new_cave[y][x] for x in range(width)] for y in range(height)]
            
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    wall_count = CaveGenerator.count_walls(new_cave, x, y, width, height)
                    
                    if params.room_size_preference > 0.5:
                        if new_cave[y][x] and wall_count <= 3:
                            temp_cave[y][x] = False
                        elif not new_cave[y][x] and wall_count >= 5:
                            temp_cave[y][x] = True
                    else:
                        if new_cave[y][x] and wall_count <= 2:
                            temp_cave[y][x] = False
                        elif not new_cave[y][x] and wall_count >= 6:
                            temp_cave[y][x] = True
            
            new_cave = temp_cave
        
        return new_cave
    
    @staticmethod
    def ensure_connectivity(cave, width, height, params):
        visited = [[False for _ in range(width)] for _ in range(height)]
        regions = []
        
        for y in range(height):
            for x in range(width):
                if not cave[y][x] and not visited[y][x]:
                    region = CaveGenerator.flood_fill(cave, visited, x, y, width, height)
                    min_region_size = int(10 * params.room_size_preference + 5)
                    if len(region) > min_region_size:
                        regions.append(region)
        
        if len(regions) > 1:
            main_region = max(regions, key=len)
            connections_made = 0
            max_connections = int(len(regions) * params.connectivity_strength)
            
            for region in regions:
                if region != main_region and connections_made < max_connections:
                    CaveGenerator.connect_regions(cave, main_region, region, width, height, params)
                    connections_made += 1
        
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
    def connect_regions(cave, region1, region2, width, height, params):
        min_dist = float('inf')
        best_points = None
        
        sample_size = min(20, len(region1), len(region2))
        for x1, y1 in region1[:sample_size]:
            for x2, y2 in region2[:sample_size]:
                dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    best_points = ((x1, y1), (x2, y2))
        
        if best_points:
            CaveGenerator.carve_tunnel(cave, best_points[0], best_points[1], width, height, params)
    
    @staticmethod
    def carve_tunnel(cave, start, end, width, height, params):
        x1, y1 = start
        x2, y2 = end
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        tunnel_width = max(1, int(params.tunnel_width))
        
        x, y = x1, y1
        while True:
            for dx_offset in range(-tunnel_width, tunnel_width + 1):
                for dy_offset in range(-tunnel_width, tunnel_width + 1):
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