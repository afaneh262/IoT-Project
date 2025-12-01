"""
IoT Network and Data Communication System
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from models import NetworkNode, DataPacket, Wire, Room
from config import NETWORK_HUB_LOCATION, DATA_PACKET_SIZE, NETWORK_LATENCY

# ============================================================================
# IoT NETWORK
# ============================================================================

class IoTNetwork:
    """Manages IoT network topology and data transmission"""
    
    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.wires: List[Wire] = []
        self.hub_node: NetworkNode = None
        
        # Network statistics
        self.total_packets_sent = 0
        self.total_packets_received = 0
        self.total_data_transmitted = 0  # bytes
        self.packet_loss_count = 0
        self.average_latency = NETWORK_LATENCY
        
        # Active transmissions (for visualization)
        self.active_transmissions: List[Dict] = []
        
    def add_node(self, node: NetworkNode):
        """Add a node to the network"""
        self.nodes[node.node_id] = node
        
        if node.node_type == "hub":
            self.hub_node = node
    
    def add_wire(self, wire: Wire):
        """Add a wire to the network"""
        self.wires.append(wire)
    
    def connect_nodes(self, node1_id: str, node2_id: str):
        """Create a connection between two nodes"""
        if node1_id in self.nodes and node2_id in self.nodes:
            node1 = self.nodes[node1_id]
            node2 = self.nodes[node2_id]
            
            if node2_id not in node1.connected_to:
                node1.connected_to.append(node2_id)
            
            if node1_id not in node2.connected_to:
                node2.connected_to.append(node1_id)
            
            # Create data wire for visualization
            wire = Wire(node1.position, node2.position, "data")
            self.add_wire(wire)
    
    def auto_connect_to_hub(self):
        """Automatically connect all sensors and actuators to the hub"""
        if not self.hub_node:
            return
        
        for node_id, node in self.nodes.items():
            if node.node_type in ["sensor", "actuator"] and node != self.hub_node:
                self.connect_nodes(node_id, self.hub_node.node_id)
    
    def send_packet(self, packet: DataPacket) -> bool:
        """
        Send a packet through the network
        Returns True if successful, False if failed
        """
        # Check if source and destination exist
        if packet.source not in self.nodes or packet.destination not in self.nodes:
            return False
        
        # Simulate packet loss (1% failure rate)
        if random.random() < 0.01:
            self.packet_loss_count += 1
            return False
        
        # Add to active transmissions for visualization
        source_node = self.nodes[packet.source]
        dest_node = self.nodes[packet.destination]
        
        transmission = {
            "packet": packet,
            "start_pos": source_node.position,
            "end_pos": dest_node.position,
            "progress": 0.0,  # 0 to 1
            "start_time": datetime.now()
        }
        self.active_transmissions.append(transmission)
        
        # Update statistics
        self.total_packets_sent += 1
        self.total_data_transmitted += DATA_PACKET_SIZE
        
        # Update node statistics
        source_node.last_transmission = datetime.now()
        
        return True
    
    def update_transmissions(self, delta_time: float):
        """
        Update active transmissions (for animation)
        delta_time in seconds
        """
        completed = []
        
        for i, transmission in enumerate(self.active_transmissions):
            # Update progress based on network speed
            # Assume transmission takes ~0.1 seconds for visualization
            transmission["progress"] += delta_time / 0.1
            
            if transmission["progress"] >= 1.0:
                # Transmission complete
                self.total_packets_received += 1
                completed.append(i)
        
        # Remove completed transmissions
        for i in reversed(completed):
            self.active_transmissions.pop(i)
    
    def get_network_load(self) -> float:
        """Calculate current network load (0-100%)"""
        # Based on active transmissions
        max_concurrent = 50  # Assume max 50 concurrent transmissions
        load = (len(self.active_transmissions) / max_concurrent) * 100
        return min(100, load)
    
    def get_node_by_room(self, room_name: str, node_type: str = None) -> List[NetworkNode]:
        """Get all nodes in a specific room"""
        nodes = []
        for node in self.nodes.values():
            if node.room and node.room.name == room_name:
                if node_type is None or node.node_type == node_type:
                    nodes.append(node)
        return nodes
    
    def get_statistics(self) -> dict:
        """Get network statistics"""
        packet_loss_rate = 0
        if self.total_packets_sent > 0:
            packet_loss_rate = (self.packet_loss_count / self.total_packets_sent) * 100
        
        return {
            "total_packets_sent": self.total_packets_sent,
            "total_packets_received": self.total_packets_received,
            "packet_loss_count": self.packet_loss_count,
            "packet_loss_rate": packet_loss_rate,
            "total_data_transmitted": self.total_data_transmitted,
            "active_transmissions": len(self.active_transmissions),
            "network_load": self.get_network_load(),
            "average_latency": self.average_latency
        }

# ============================================================================
# POWER GRID
# ============================================================================

class PowerGrid:
    """Manages power distribution wiring and load balancing"""
    
    def __init__(self, technical_room: Room):
        self.technical_room = technical_room
        self.main_panel_position = technical_room.get_center()
        
        # Power lines
        self.power_lines: List[Wire] = []
        self.circuits: Dict[str, List[str]] = {}  # circuit_name -> [room_names]
        
        # Load tracking
        self.total_load = 0.0  # Watts
        self.circuit_loads: Dict[str, float] = {}
        
    def add_circuit(self, circuit_name: str, rooms: List[str]):
        """Add a power circuit"""
        self.circuits[circuit_name] = rooms
        self.circuit_loads[circuit_name] = 0.0
    
    def add_power_line(self, start: Tuple[int, int], end: Tuple[int, int], 
                       load: float = 0):
        """Add a power line for visualization"""
        wire = Wire(start, end, "power")
        wire.current_load = load
        wire.active = load > 0
        self.power_lines.append(wire)
    
    def update_loads(self, room_loads: Dict[str, float]):
        """Update power loads for all circuits"""
        self.total_load = sum(room_loads.values())
        
        # Reset circuit loads
        for circuit in self.circuit_loads:
            self.circuit_loads[circuit] = 0.0
        
        # Calculate circuit loads
        for circuit_name, rooms in self.circuits.items():
            for room in rooms:
                if room in room_loads:
                    self.circuit_loads[circuit_name] += room_loads[room]
        
        # Update wire states
        for wire in self.power_lines:
            wire.active = self.total_load > 0
            wire.current_load = self.total_load / len(self.power_lines) if self.power_lines else 0
    
    def get_circuit_status(self, circuit_name: str) -> dict:
        """Get status of a specific circuit"""
        if circuit_name not in self.circuits:
            return {}
        
        load = self.circuit_loads.get(circuit_name, 0)
        max_capacity = 3000  # 3kW per circuit (typical)
        utilization = (load / max_capacity) * 100
        
        return {
            "load": load,
            "capacity": max_capacity,
            "utilization": utilization,
            "status": "overload" if utilization > 100 else "normal",
            "rooms": self.circuits[circuit_name]
        }

# ============================================================================
# WATER NETWORK
# ============================================================================

class WaterNetwork:
    """Manages water distribution piping"""
    
    def __init__(self, tank_position: Tuple[int, int]):
        self.tank_position = tank_position
        self.pipes: List[Wire] = []
        self.flow_rate = 0.0  # L/min
        
    def add_pipe(self, start: Tuple[int, int], end: Tuple[int, int]):
        """Add a water pipe for visualization"""
        wire = Wire(start, end, "water")
        self.pipes.append(wire)
    
    def update_flow(self, flow_rate: float):
        """Update water flow through pipes"""
        self.flow_rate = flow_rate
        
        for pipe in self.pipes:
            pipe.active = flow_rate > 0
            pipe.flow_direction = 1 if flow_rate > 0 else 0
