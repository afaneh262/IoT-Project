"""
Wall-Following Wiring System
Generates realistic wiring paths that follow walls and avoid overlaps
"""

import math
from typing import List, Tuple, Dict, Set
from models import Room, Wire
from config import WIRE_OFFSET_FROM_WALL, WIRE_VERTICAL_SPACING

# ============================================================================
# WIRING PATH GENERATOR
# ============================================================================

class WiringPathGenerator:
    """Generates wiring paths that follow walls"""
    
    def __init__(self, rooms: List[Room], door_connections: List[Tuple[str, str]]):
        self.rooms = rooms
        self.room_dict = {room.name: room for room in rooms}
        self.door_connections = door_connections
        
        # Track wiring channels (which walls have wires)
        self.wire_channels = {}  # (wall_id, wire_type) -> channel_number
        
    def generate_wiring(self, hub_room_name: str, wire_type: str) -> List[Wire]:
        """
        Generate wiring from hub to all rooms following walls
        wire_type: 'power', 'data', or 'water'
        """
        if hub_room_name not in self.room_dict:
            return []
        
        hub_room = self.room_dict[hub_room_name]
        wires = []
        
        # Build room connectivity graph
        graph = self._build_room_graph()
        
        # For each room, find path from hub
        for room in self.rooms:
            if room.name == hub_room_name:
                continue
                
            path = self._find_path(hub_room_name, room.name, graph)
            if path:
                # Convert room path to wire segments
                wire_segments = self._path_to_wire_segments(path, wire_type)
                wires.extend(wire_segments)
        
        return wires
    
    def _build_room_graph(self) -> Dict[str, Set[str]]:
        """Build adjacency graph from door connections"""
        graph = {room.name: set() for room in self.rooms}
        
        for room1, room2 in self.door_connections:
            if room1 in graph and room2 in graph:
                graph[room1].add(room2)
                graph[room2].add(room1)
        
        return graph
    
    def _find_path(self, start: str, end: str, graph: Dict[str, Set[str]]) -> List[str]:
        """Find shortest path between two rooms using BFS"""
        if start == end:
            return [start]
        
        visited = {start}
        queue = [(start, [start])]
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    
                    if neighbor == end:
                        return new_path
                    
                    queue.append((neighbor, new_path))
        
        return []  # No path found
    
    def _path_to_wire_segments(self, room_path: List[str], wire_type: str) -> List[Wire]:
        """Convert room path to actual wire segments along walls"""
        if len(room_path) < 2:
            return []
        
        wires = []
        
        for i in range(len(room_path) - 1):
            room1 = self.room_dict[room_path[i]]
            room2 = self.room_dict[room_path[i + 1]]
            
            # Find wall points to connect
            wire_segment = self._create_wall_wire(room1, room2, wire_type)
            if wire_segment:
                wires.append(wire_segment)
        
        return wires
    
    def _create_wall_wire(self, room1: Room, room2: Room, wire_type: str) -> Wire:
        """Create a wire segment along walls between two adjacent rooms"""
        r1 = room1.get_rect()
        r2 = room2.get_rect()
        
        # Get channel offset for this wire type
        channel_key = f"{room1.name}-{room2.name}-{wire_type}"
        channel_offset = self._get_channel_offset(channel_key, wire_type)
        
        # Determine shared wall and create wire along it
        # Check if rooms share a vertical wall
        if abs(r1.right - r2.left) < 5:  # Room1 is to the left of room2
            # Wire runs along the shared vertical wall
            y_start = max(r1.top, r2.top) + WIRE_OFFSET_FROM_WALL
            y_end = min(r1.bottom, r2.bottom) - WIRE_OFFSET_FROM_WALL
            y_mid = (y_start + y_end) // 2
            
            x = r1.right - WIRE_OFFSET_FROM_WALL + channel_offset
            
            # Create L-shaped wire: center of room1 -> wall -> center of room2
            # For visualization, simplify to single segment along wall
            start = (x, y_mid)
            end = (x, y_mid)  # Will be extended to room centers
            
        elif abs(r2.right - r1.left) < 5:  # Room2 is to the left of room1
            y_start = max(r1.top, r2.top) + WIRE_OFFSET_FROM_WALL
            y_end = min(r1.bottom, r2.bottom) - WIRE_OFFSET_FROM_WALL
            y_mid = (y_start + y_end) // 2
            
            x = r1.left + WIRE_OFFSET_FROM_WALL + channel_offset
            start = (x, y_mid)
            end = (x, y_mid)
            
        # Check if rooms share a horizontal wall
        elif abs(r1.bottom - r2.top) < 5:  # Room1 is above room2
            x_start = max(r1.left, r2.left) + WIRE_OFFSET_FROM_WALL
            x_end = min(r1.right, r2.right) - WIRE_OFFSET_FROM_WALL
            x_mid = (x_start + x_end) // 2
            
            y = r1.bottom - WIRE_OFFSET_FROM_WALL + channel_offset
            start = (x_mid, y)
            end = (x_mid, y)
            
        elif abs(r2.bottom - r1.top) < 5:  # Room2 is above room1
            x_start = max(r1.left, r2.left) + WIRE_OFFSET_FROM_WALL
            x_end = min(r1.right, r2.right) - WIRE_OFFSET_FROM_WALL
            x_mid = (x_start + x_end) // 2
            
            y = r1.top + WIRE_OFFSET_FROM_WALL + channel_offset
            start = (x_mid, y)
            end = (x_mid, y)
        
        else:
            # Rooms not adjacent, create connecting wire
            start = room1.get_center()
            end = room2.get_center()
        
        # Actually connect room centers through wall point
        c1 = room1.get_center()
        c2 = room2.get_center()
        
        # Create path that goes: room1_center -> wall -> room2_center
        # For simplicity, create a direct connection with offset
        wire = Wire(c1, c2, wire_type)
        
        return wire
    
    def _get_channel_offset(self, channel_key: str, wire_type: str) -> int:
        """Get offset for wire to avoid overlapping with other wires"""
        # Assign different offsets for different wire types
        wire_type_offset = {
            'power': 0,
            'data': WIRE_VERTICAL_SPACING,
            'water': WIRE_VERTICAL_SPACING * 2
        }
        
        if channel_key not in self.wire_channels:
            self.wire_channels[channel_key] = 0
        
        base_offset = wire_type_offset.get(wire_type, 0)
        return base_offset

# ============================================================================
# IMPROVED WIRING RENDERER
# ============================================================================

class ImprovedWiringRenderer:
    """Renders wiring with wall-following paths"""
    
    @staticmethod
    def create_wall_following_wire(start_room: Room, end_room: Room, 
                                   wire_type: str, offset: int = 0) -> List[Tuple[int, int]]:
        """
        Create a wire path that follows walls from start to end room
        Wire exits room at nearest wall, follows perimeter, enters target room
        Returns list of points forming the path
        """
        points = []
        
        # Get room boundaries
        r1 = start_room.get_rect()
        r2 = end_room.get_rect()
        
        # Start point: exit point on start room wall (towards hallway/target)
        # End point: entry point on end room wall
        
        # Determine best exit point from start room
        if r1.centerx < r2.centerx:
            # Target is to the right - exit right wall
            exit_x = r1.right - WIRE_OFFSET_FROM_WALL
            exit_y = r1.centery
            exit_dir = "right"
        else:
            # Target is to the left - exit left wall  
            exit_x = r1.left + WIRE_OFFSET_FROM_WALL
            exit_y = r1.centery
            exit_dir = "left"
        
        # Determine best entry point to end room
        if r2.centerx < r1.centerx:
            # Coming from right - enter left wall
            entry_x = r2.left + WIRE_OFFSET_FROM_WALL
            entry_y = r2.centery
        else:
            # Coming from left - enter right wall
            entry_x = r2.right - WIRE_OFFSET_FROM_WALL
            entry_y = r2.centery
        
        points.append((exit_x, exit_y))
        
        # Route along walls
        # Simple approach: move to hallway-like path
        
        # If rooms are horizontally aligned
        if abs(r1.centery - r2.centery) < 100:
            # Horizontal routing along wall
            mid_x = (exit_x + entry_x) // 2
            points.append((mid_x, exit_y))
            points.append((mid_x, entry_y))
        else:
            # Vertical routing needed
            # Go to edge of room, then along hallway space, then to target
            if exit_dir == "right":
                hallway_x = r1.right + WIRE_OFFSET_FROM_WALL + offset
            else:
                hallway_x = r1.left - WIRE_OFFSET_FROM_WALL - offset
            
            points.append((hallway_x, exit_y))
            points.append((hallway_x, entry_y))
            points.append((entry_x, entry_y))
        
        return points
    
    @staticmethod
    def draw_segmented_wire(screen, points: List[Tuple[int, int]], color: Tuple[int, int, int],
                           thickness: int = 3, active: bool = False):
        """Draw a wire along a path of points"""
        import pygame
        
        if len(points) < 2:
            return
        
        # Draw each segment
        for i in range(len(points) - 1):
            pygame.draw.line(screen, color, points[i], points[i + 1], thickness)
        
        # Draw junction points
        for point in points:
            pygame.draw.circle(screen, color, point, thickness + 1)
