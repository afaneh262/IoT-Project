"""
Data Models for Smart Home IoT Simulation
"""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from datetime import datetime
from typing import List, Tuple, Optional
from config import DeviceStatus

# ============================================================================
# ROOM MODEL
# ============================================================================

class Room:
    """Represents a physical room in the house"""
    
    def __init__(self, name: str, x: int, y: int, width: int, height: int):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Environmental properties
        self.temperature = 22.0  # Celsius
        self.humidity = 50.0  # Percentage
        self.light_level = 50  # 0-100
        self.motion_detected = False
        self.occupancy = 0  # Number of people
        
        # Equipment
        self.sensors = []
        self.actuators = []
        
    def get_center(self) -> Tuple[int, int]:
        """Returns the center point of the room"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def get_rect(self):
        """Returns pygame rect for the room (only if pygame is available)"""
        if PYGAME_AVAILABLE:
            return pygame.Rect(self.x, self.y, self.width, self.height)
        else:
            # Return a simple tuple representation
            return (self.x, self.y, self.width, self.height)
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside the room"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def __repr__(self):
        return f"Room({self.name}, {self.width}x{self.height})"

# ============================================================================
# DATA PACKET MODEL
# ============================================================================

class DataPacket:
    """Represents a data packet transmitted over the IoT network"""
    
    def __init__(self, source: str, destination: str, data_type: str, 
                 payload: any, timestamp: datetime):
        self.source = source
        self.destination = destination
        self.data_type = data_type  # "sensor_reading", "control_command", "status"
        self.payload = payload
        self.timestamp = timestamp
        self.packet_id = id(self)
        
    def __repr__(self):
        return f"Packet({self.source} -> {self.destination}: {self.data_type})"

# ============================================================================
# NETWORK NODE MODEL
# ============================================================================

class NetworkNode:
    """Represents a node in the IoT network (sensor, actuator, or hub)"""
    
    def __init__(self, node_id: str, node_type: str, room: Room, 
                 position: Tuple[int, int]):
        self.node_id = node_id
        self.node_type = node_type  # "sensor", "actuator", "hub", "router"
        self.room = room
        self.position = position
        self.status = DeviceStatus.ONLINE
        self.connected_to = []  # List of node_ids
        self.packet_queue = []  # Outgoing packets
        self.last_transmission = None
        
    def send_packet(self, packet: DataPacket):
        """Add packet to transmission queue"""
        self.packet_queue.append(packet)
        
    def __repr__(self):
        return f"Node({self.node_id}, {self.node_type})"

# ============================================================================
# WIRING MODEL
# ============================================================================

class Wire:
    """Represents a physical wire (power or data) between two points"""
    
    def __init__(self, start: Tuple[int, int], end: Tuple[int, int], 
                 wire_type: str):
        self.start = start
        self.end = end
        self.wire_type = wire_type  # "power", "data", "water"
        self.active = False  # Is current/data flowing?
        self.flow_direction = 1  # 1 = forward, -1 = backward
        self.current_load = 0.0  # For power lines (watts)
        
    def get_midpoint(self) -> Tuple[int, int]:
        """Returns the midpoint of the wire"""
        return ((self.start[0] + self.end[0]) // 2,
                (self.start[1] + self.end[1]) // 2)
    
    def __repr__(self):
        return f"Wire({self.wire_type}: {self.start} -> {self.end})"

# ============================================================================
# SYSTEM STATUS MODEL
# ============================================================================

class SystemStatus:
    """Tracks overall system status and statistics"""
    
    def __init__(self):
        self.total_sensors = 0
        self.active_sensors = 0
        self.total_actuators = 0
        self.active_actuators = 0
        self.network_packets_sent = 0
        self.network_packets_received = 0
        self.total_power_generated = 0.0
        self.total_power_consumed = 0.0
        self.battery_cycles = 0
        self.alerts = []
        
    def add_alert(self, message: str, severity: str):
        """Add a system alert"""
        self.alerts.append({
            "message": message,
            "severity": severity,  # "info", "warning", "error"
            "timestamp": datetime.now()
        })
        
        # Keep only last 10 alerts
        if len(self.alerts) > 10:
            self.alerts.pop(0)
    
    def get_recent_alerts(self, count: int = 5) -> List[dict]:
        """Get most recent alerts"""
        return self.alerts[-count:]
