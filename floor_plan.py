"""Floor Plan Renderer
Realistic Floor Plan Rendering for Smart Home
"""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    # Create dummy pygame module for type hints
    class DummyPygame:
        class Surface:
            pass
    pygame = DummyPygame()

import math
from typing import Tuple, List, TYPE_CHECKING
from config import *
from models import Room, Wire, NetworkNode

if TYPE_CHECKING:
    from network import IoTNetwork, PowerGrid, WaterNetwork

# ============================================================================
# FLOOR PLAN RENDERER
# ============================================================================

class FloorPlanRenderer:
    """Renders realistic floor plan with rooms, doors, and infrastructure"""
    
    def __init__(self, screen: pygame.Surface):
        if not PYGAME_AVAILABLE:
            raise ImportError("FloorPlanRenderer requires pygame")
        self.screen = screen
        self.font_small = pygame.font.Font(None, 16)
        self.font_medium = pygame.font.Font(None, 20)
        self.font_large = pygame.font.Font(None, 24)
        
        # Wall thickness
        self.wall_thickness = 4
        
    def draw_room(self, room: Room, highlight: bool = False):
        """Draw a single room with walls and label"""
        rect = room.get_rect()
        
        # Fill room with subtle gradient effect
        room_color = LIGHT_GRAY
        if highlight:
            room_color = LIGHT_BLUE
        
        # Draw floor
        pygame.draw.rect(self.screen, room_color, rect)
        
        # Add subtle floor texture (tiles pattern for bathrooms/kitchen)
        if "Bathroom" in room.name or room.name == "Kitchen" or room.name == "Laundry Room":
            tile_size = 20
            for i in range(room.x, room.x + room.width, tile_size):
                for j in range(room.y, room.y + room.height, tile_size):
                    if (i // tile_size + j // tile_size) % 2:
                        tile_rect = pygame.Rect(i, j, tile_size, tile_size)
                        pygame.draw.rect(self.screen, (240, 240, 240), tile_rect)
                        pygame.draw.rect(self.screen, (200, 200, 200), tile_rect, 1)
        
        # Draw walls (thicker, with shadow effect)
        shadow_rect = rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pygame.draw.rect(self.screen, DARK_GRAY, shadow_rect, self.wall_thickness)
        pygame.draw.rect(self.screen, BLACK, rect, self.wall_thickness)
        
        # Draw room label with background
        label = self.font_small.render(room.name, True, BLACK)
        label_rect = label.get_rect(center=(room.x + room.width // 2, room.y + 18))
        # Background for label
        bg_rect = label_rect.copy()
        bg_rect.inflate_ip(10, 4)
        pygame.draw.rect(self.screen, WHITE, bg_rect)
        pygame.draw.rect(self.screen, BLACK, bg_rect, 1)
        self.screen.blit(label, label_rect)
        
        # Draw room stats (temperature, light, etc.) if room is large enough
        if room.width > 120 and room.height > 100:
            stats_y = room.y + 45
            
            # Temperature with color coding
            temp_color = BLACK
            if room.temperature > 28:
                temp_color = RED
            elif room.temperature < 18:
                temp_color = BLUE
            
            temp_text = f"🌡 {room.temperature:.1f}°C"
            temp_surf = self.font_small.render(temp_text, True, temp_color)
            self.screen.blit(temp_surf, (room.x + 10, stats_y))
            
            # Light level
            light_text = f"💡 {room.light_level:.0f}"
            light_surf = self.font_small.render(light_text, True, DARK_GRAY)
            self.screen.blit(light_surf, (room.x + 10, stats_y + 18))
            
            # Motion with animation
            if room.motion_detected:
                motion_surf = self.font_medium.render("👤", True, RED)
                self.screen.blit(motion_surf, (room.x + 10, stats_y + 36))
    
    def draw_door(self, room1: Room, room2: Room):
        """Draw a door between two rooms"""
        # Find shared wall
        r1 = room1.get_rect()
        r2 = room2.get_rect()
        
        # Determine if rooms share a wall and where
        door_pos = None
        door_size = 30
        
        # Check right wall of room1 with left wall of room2
        if r1.right == r2.left:
            # Vertical door on shared vertical wall
            mid_y = max(r1.top, r2.top) + abs(r1.centery - r2.centery) // 2
            door_pos = (r1.right, mid_y - door_size // 2, 
                       self.wall_thickness, door_size)
        
        # Check bottom wall of room1 with top wall of room2
        elif r1.bottom == r2.top:
            # Horizontal door on shared horizontal wall
            mid_x = max(r1.left, r2.left) + abs(r1.centerx - r2.centerx) // 2
            door_pos = (mid_x - door_size // 2, r1.bottom, 
                       door_size, self.wall_thickness)
        
        # Check left wall of room1 with right wall of room2
        elif r1.left == r2.right:
            mid_y = max(r1.top, r2.top) + abs(r1.centery - r2.centery) // 2
            door_pos = (r2.right, mid_y - door_size // 2, 
                       self.wall_thickness, door_size)
        
        # Check top wall of room1 with bottom wall of room2
        elif r1.top == r2.bottom:
            mid_x = max(r1.left, r2.left) + abs(r1.centerx - r2.centerx) // 2
            door_pos = (mid_x - door_size // 2, r2.bottom, 
                       door_size, self.wall_thickness)
        
        # Draw door (white gap in wall)
        if door_pos:
            pygame.draw.rect(self.screen, WHITE, door_pos)
            pygame.draw.rect(self.screen, BROWN, door_pos, 1)
    
    def draw_all_rooms(self, rooms: List[Room]):
        """Draw all rooms"""
        for room in rooms:
            self.draw_room(room)
    
    def draw_all_doors(self, rooms: List[Room], connections: List[Tuple[str, str]]):
        """Draw all doors based on connections"""
        room_dict = {room.name: room for room in rooms}
        
        for room1_name, room2_name in connections:
            if room1_name in room_dict and room2_name in room_dict:
                self.draw_door(room_dict[room1_name], room_dict[room2_name])

# ============================================================================
# INFRASTRUCTURE RENDERER
# ============================================================================

class InfrastructureRenderer:
    """Renders electrical, data, and water infrastructure"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_small = pygame.font.Font(None, 16)
        self.font_tiny = pygame.font.Font(None, 14)
        
    def draw_sensor_icon(self, position: Tuple[int, int], sensor_type: str, 
                        value: float = 0, active: bool = True):
        """Draw a clear, descriptive sensor icon"""
        x, y = position
        
        # Icon backgrounds
        bg_color = WHITE if active else LIGHT_GRAY
        border_color = BLACK if active else GRAY
        
        # Draw icon background circle
        pygame.draw.circle(self.screen, bg_color, (x, y), 12)
        pygame.draw.circle(self.screen, border_color, (x, y), 12, 2)
        
        # Sensor-specific icons and colors
        if sensor_type == "temperature":
            # Thermometer icon
            color = RED if value > 25 else BLUE if value < 18 else BLACK
            pygame.draw.rect(self.screen, color, (x-2, y-6, 4, 8))
            pygame.draw.circle(self.screen, color, (x, y+4), 3)
            label = f"{value:.0f}°"
            
        elif sensor_type == "light":
            # Sun/light bulb icon
            color = BRIGHT_YELLOW if value > 50 else DARK_GRAY
            pygame.draw.circle(self.screen, color, (x, y), 4)
            # Rays
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                x2 = x + int(7 * math.cos(rad))
                y2 = y + int(7 * math.sin(rad))
                pygame.draw.line(self.screen, color, (x, y), (x2, y2), 2)
            label = f"{value:.0f}"
            
        elif sensor_type == "motion":
            # Person icon
            color = RED if value > 0 else DARK_GRAY
            # Head
            pygame.draw.circle(self.screen, color, (x, y-3), 3)
            # Body
            pygame.draw.line(self.screen, color, (x, y), (x, y+6), 2)
            # Arms
            pygame.draw.line(self.screen, color, (x-4, y+2), (x+4, y+2), 2)
            label = "✓" if value > 0 else "✗"
            
        elif sensor_type == "humidity":
            # Water drop icon
            color = BLUE
            points = [(x, y+4), (x-3, y), (x-2, y-3), (x+2, y-3), (x+3, y)]
            pygame.draw.polygon(self.screen, color, points)
            label = f"{value:.0f}%"
            
        elif sensor_type == "power":
            # Lightning bolt
            color = BRIGHT_YELLOW
            points = [(x, y-6), (x-2, y), (x+1, y), (x-1, y+6)]
            pygame.draw.polygon(self.screen, color, points)
            label = f"{value:.0f}W"
            
        elif sensor_type == "co2":
            # CO2 molecules icon
            color = GREEN if value < 800 else ORANGE if value < 1200 else RED
            pygame.draw.circle(self.screen, color, (x-3, y), 2)
            pygame.draw.circle(self.screen, color, (x+3, y), 2)
            pygame.draw.circle(self.screen, color, (x, y-3), 2)
            pygame.draw.circle(self.screen, color, (x, y+3), 2)
            label = f"{value:.0f}"
        else:
            color = BLACK
            label = "?"
        
        # Draw value label below icon
        label_surf = self.font_tiny.render(label, True, color)
        label_rect = label_surf.get_rect(center=(x, y + 20))
        # Background for label
        bg_rect = label_rect.copy()
        bg_rect.inflate_ip(4, 2)
        pygame.draw.rect(self.screen, WHITE, bg_rect)
        pygame.draw.rect(self.screen, BLACK, bg_rect, 1)
        self.screen.blit(label_surf, label_rect)
        
    def draw_wire(self, wire: Wire, animated: bool = False, animation_offset: float = 0):
        """Draw a wire (power, data, or water)"""
        color = {
            "power": NETWORK_POWER,
            "data": NETWORK_DATA,
            "water": NETWORK_WATER
        }.get(wire.wire_type, GRAY)
        
        # Dim color if not active
        if not wire.active:
            color = tuple(c // 3 for c in color)
        
        # Draw wire
        thickness = 3 if wire.active else 2
        pygame.draw.line(self.screen, color, wire.start, wire.end, thickness)
        
        # Draw animated flow if active
        if animated and wire.active:
            self._draw_wire_flow(wire, color, animation_offset)
    
    def draw_wall_following_wire(self, points: List[Tuple[int, int]], wire_type: str,
                                 active: bool = True, animated: bool = False, 
                                 animation_offset: float = 0):
        """Draw a wire that follows a path of points along walls"""
        color = {
            "power": NETWORK_POWER,
            "data": NETWORK_DATA,
            "water": NETWORK_WATER
        }.get(wire_type, GRAY)
        
        # Dim color if not active
        if not active:
            color = tuple(c // 3 for c in color)
        
        thickness = 3 if active else 2
        
        # Draw each segment
        for i in range(len(points) - 1):
            pygame.draw.line(self.screen, color, points[i], points[i + 1], thickness)
        
        # Draw junction points
        for point in points:
            pygame.draw.circle(self.screen, color, point, thickness + 1)
        
        # Draw animated flow if active
        if animated and active and len(points) > 1:
            self._draw_path_flow(points, color, animation_offset)
    
    def _draw_path_flow(self, points: List[Tuple[int, int]], 
                       color: Tuple[int, int, int], offset: float):
        """Draw animated flow along a path"""
        # Calculate total path length
        total_length = 0
        segment_lengths = []
        for i in range(len(points) - 1):
            dx = points[i+1][0] - points[i][0]
            dy = points[i+1][1] - points[i][1]
            length = math.sqrt(dx*dx + dy*dy)
            segment_lengths.append(length)
            total_length += length
        
        if total_length == 0:
            return
        
        # Draw flowing dots
        num_dots = max(3, int(total_length / 40))
        for i in range(num_dots):
            # Position along path with animation
            t = (i / num_dots + offset) % 1.0
            target_dist = t * total_length
            
            # Find which segment this dot is on
            current_dist = 0
            for seg_idx, seg_len in enumerate(segment_lengths):
                if current_dist + seg_len >= target_dist:
                    # Dot is on this segment
                    seg_t = (target_dist - current_dist) / seg_len
                    p1 = points[seg_idx]
                    p2 = points[seg_idx + 1]
                    x = int(p1[0] + (p2[0] - p1[0]) * seg_t)
                    y = int(p1[1] + (p2[1] - p1[1]) * seg_t)
                    pygame.draw.circle(self.screen, color, (x, y), 4)
                    break
                current_dist += seg_len
    
    def _draw_wire_flow(self, wire: Wire, color: Tuple[int, int, int], 
                       offset: float):
        """Draw animated flow along wire"""
        # Calculate direction
        dx = wire.end[0] - wire.start[0]
        dy = wire.end[1] - wire.start[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Draw flowing dots
        num_dots = int(length / 30)
        for i in range(num_dots):
            # Position along wire with animation
            t = (i / num_dots + offset) % 1.0
            if wire.flow_direction < 0:
                t = 1.0 - t
            
            x = wire.start[0] + dx * length * t
            y = wire.start[1] + dy * length * t
            
            # Draw dot
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 4)
    
    def draw_power_infrastructure(self, power_grid, animated: bool = False,
                                 animation_offset: float = 0):
        """Draw electrical wiring and panel"""
        # Draw main electrical panel
        panel_rect = pygame.Rect(power_grid.main_panel_position[0] - 15,
                                 power_grid.main_panel_position[1] - 20,
                                 30, 40)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect)
        pygame.draw.rect(self.screen, NETWORK_POWER, panel_rect, 3)
        
        # Panel label
        label = self.font_small.render("⚡", True, BRIGHT_YELLOW)
        self.screen.blit(label, (panel_rect.centerx - 8, panel_rect.centery - 8))
        
        # Draw power lines
        for wire in power_grid.power_lines:
            self.draw_wire(wire, animated, animation_offset)
            
            # Show load on wire if active
            if wire.active and wire.current_load > 100:
                mid = wire.get_midpoint()
                load_text = f"{wire.current_load:.0f}W"
                load_surf = self.font_small.render(load_text, True, ORANGE)
                self.screen.blit(load_surf, (mid[0] - 20, mid[1] - 10))
    
    def draw_data_infrastructure(self, network, animated: bool = False,
                                animation_offset: float = 0):
        """Draw data network wiring and hub"""
        if not network.hub_node:
            return
        
        # Draw network hub
        hub_pos = network.hub_node.position
        hub_rect = pygame.Rect(hub_pos[0] - 15, hub_pos[1] - 15, 30, 30)
        pygame.draw.rect(self.screen, DARK_BLUE, hub_rect)
        pygame.draw.rect(self.screen, NETWORK_DATA, hub_rect, 3)
        
        # Hub label
        label = self.font_small.render("HUB", True, WHITE)
        self.screen.blit(label, (hub_rect.centerx - 15, hub_rect.centery - 8))
        
        # Draw data lines
        for wire in network.wires:
            if wire.wire_type == "data":
                self.draw_wire(wire, animated, animation_offset)
        
        # Draw active transmissions
        for transmission in network.active_transmissions:
            start = transmission["start_pos"]
            end = transmission["end_pos"]
            progress = transmission["progress"]
            
            # Calculate current position
            x = start[0] + (end[0] - start[0]) * progress
            y = start[1] + (end[1] - start[1]) * progress
            
            # Draw data packet
            pygame.draw.circle(self.screen, CYAN, (int(x), int(y)), 6)
            pygame.draw.circle(self.screen, WHITE, (int(x), int(y)), 6, 1)
    
    def draw_water_infrastructure(self, water_network, 
                                 water_level_percent: float, animated: bool = False,
                                 animation_offset: float = 0):
        """Draw water tank and piping"""
        # Draw water tank
        tank_pos = water_network.tank_position
        tank_width = 60
        tank_height = 80
        tank_rect = pygame.Rect(tank_pos[0] - tank_width // 2,
                                tank_pos[1] - tank_height // 2,
                                tank_width, tank_height)
        
        # Tank outline
        pygame.draw.rect(self.screen, DARK_BLUE, tank_rect, 3)
        
        # Water level
        water_height = int(tank_height * water_level_percent / 100)
        water_rect = pygame.Rect(tank_rect.left, 
                                 tank_rect.bottom - water_height,
                                 tank_width, water_height)
        pygame.draw.rect(self.screen, LIGHT_BLUE, water_rect)
        pygame.draw.rect(self.screen, BLUE, water_rect, 2)
        
        # Tank label
        label = self.font_small.render(f"{water_level_percent:.0f}%", True, BLACK)
        self.screen.blit(label, (tank_rect.centerx - 15, tank_rect.centery - 8))
        
        # Draw pipes
        for pipe in water_network.pipes:
            self.draw_wire(pipe, animated, animation_offset)
    
    def draw_actuator_icon(self, position: Tuple[int, int], actuator_type: str, 
                          state: bool):
        """Draw actuator icon at position"""
        # Light
        if "Light" in actuator_type:
            color = BRIGHT_YELLOW if state else GRAY
            pygame.draw.circle(self.screen, color, position, 8)
            
            # Rays if ON
            if state:
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    end_x = position[0] + int(math.cos(rad) * 15)
                    end_y = position[1] + int(math.sin(rad) * 15)
                    pygame.draw.line(self.screen, YELLOW, position, 
                                   (end_x, end_y), 2)
        
        # Fan
        elif "Fan" in actuator_type:
            color = BLUE if state else GRAY
            pygame.draw.circle(self.screen, color, position, 8)
            pygame.draw.circle(self.screen, BLACK, position, 8, 2)
            
            # Blades if ON
            if state:
                for angle in range(0, 360, 90):
                    rad = math.radians(angle)
                    end_x = position[0] + int(math.cos(rad) * 10)
                    end_y = position[1] + int(math.sin(rad) * 10)
                    pygame.draw.line(self.screen, DARK_BLUE, position,
                                   (end_x, end_y), 3)
        
        # Heater
        elif "Heater" in actuator_type or "AC" in actuator_type:
            color = RED if state else GRAY
            pygame.draw.rect(self.screen, color, 
                           (position[0] - 8, position[1] - 6, 16, 12))
            pygame.draw.rect(self.screen, BLACK,
                           (position[0] - 8, position[1] - 6, 16, 12), 2)

# ============================================================================
# OUTDOOR INFRASTRUCTURE RENDERER
# ============================================================================

class OutdoorRenderer:
    """Renders outdoor infrastructure (solar, wind, etc.)"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_small = pygame.font.Font(None, 16)
        self.font_medium = pygame.font.Font(None, 20)
    
    def draw_solar_panels(self, position: Tuple[int, int], power: float, 
                         max_power: float):
        """Draw solar panel array"""
        width = 200
        height = 100
        x, y = position
        
        # Draw solar panel array
        for i in range(4):
            for j in range(2):
                panel_x = x + i * 50
                panel_y = y + j * 50
                panel_rect = pygame.Rect(panel_x, panel_y, 45, 45)
                
                # Color based on power generation
                intensity = int((power / max_power) * 255) if max_power > 0 else 0
                color = (intensity // 2, intensity // 2, 50 + intensity // 4)
                
                pygame.draw.rect(self.screen, color, panel_rect)
                pygame.draw.rect(self.screen, BLACK, panel_rect, 2)
        
        # Label
        label = self.font_medium.render(f"☀️ Solar: {power:.0f}W", True, BLACK)
        self.screen.blit(label, (x, y - 25))
    
    def draw_wind_turbine(self, position: Tuple[int, int], power: float,
                         max_power: float, animation_angle: float = 0):
        """Draw wind turbine"""
        x, y = position
        
        # Draw tower
        pygame.draw.line(self.screen, DARK_GRAY, (x, y), (x, y + 60), 5)
        
        # Draw nacelle (turbine house)
        nacelle_rect = pygame.Rect(x - 15, y - 10, 30, 20)
        pygame.draw.rect(self.screen, GRAY, nacelle_rect)
        pygame.draw.rect(self.screen, BLACK, nacelle_rect, 2)
        
        # Draw rotating blades
        blade_length = 35
        rotation_speed = (power / max_power) * 10 if max_power > 0 else 0
        
        for i in range(3):
            angle = animation_angle + i * 120
            rad = math.radians(angle)
            
            # Blade endpoint
            blade_x = x + int(math.cos(rad) * blade_length)
            blade_y = y + int(math.sin(rad) * blade_length)
            
            # Draw blade
            pygame.draw.line(self.screen, WHITE, (x, y), (blade_x, blade_y), 4)
            pygame.draw.line(self.screen, BLACK, (x, y), (blade_x, blade_y), 1)
        
        # Center hub
        pygame.draw.circle(self.screen, GRAY, (x, y), 8)
        pygame.draw.circle(self.screen, BLACK, (x, y), 8, 2)
        
        # Label
        label = self.font_medium.render(f"🌬️ Wind: {power:.0f}W", True, BLACK)
        self.screen.blit(label, (x - 60, y + 70))
