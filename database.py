"""
MongoDB Database Module for Smart Home IoT Data Storage
Handles all database connections and data persistence operations
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
from threading import Lock

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Manages MongoDB connection and data storage operations"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            connection_string: MongoDB connection URI. If None, uses environment variable or default
        """
        self.connection_string = connection_string or os.getenv(
            'MONGO_URI',
            'mongodb://admin:smartHomeAdmin2024@localhost:27017/smart_home_iot?authSource=admin'
        )
        
        self.client = None
        self.db = None
        self.connected = False
        self.lock = Lock()
        
        # Collection references
        self.sensor_readings = None
        self.actuator_states = None
        self.energy_data = None
        self.water_data = None
        self.events = None
        self.system_stats = None
        
        # Batch storage for performance
        self.batch_size = 100
        self.sensor_batch = []
        self.actuator_batch = []
        self.event_batch = []
        
        # Connect to database
        self.connect()
    
    def connect(self) -> bool:
        """
        Establish connection to MongoDB
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client.smart_home_iot
            
            # Get collection references
            self.sensor_readings = self.db.sensor_readings
            self.actuator_states = self.db.actuator_states
            self.energy_data = self.db.energy_data
            self.water_data = self.db.water_data
            self.events = self.db.events
            self.system_stats = self.db.system_stats
            
            self.connected = True
            print("✓ Connected to MongoDB successfully")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            print("  Running in offline mode - data will not be persisted")
            self.connected = False
            return False
        except Exception as e:
            print(f"✗ Unexpected error connecting to MongoDB: {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.connected
    
    def disconnect(self):
        """Close database connection"""
        if self.client:
            # Flush any remaining batches
            self.flush_batches()
            self.client.close()
            self.connected = False
            print("✓ Disconnected from MongoDB")
    
    # ========================================================================
    # SENSOR DATA STORAGE
    # ========================================================================
    
    def store_sensor_reading(self, sensor_id: str, sensor_type: str, room: str,
                           value: float, unit: str, simulation_time: datetime,
                           transmission_format: str = None, serialized_data: str = None,
                           encrypted: bool = False, security_level: str = 'low'):
        """
        Store a sensor reading
        
        Args:
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor
            room: Room location
            value: Sensor reading value
            unit: Unit of measurement
            simulation_time: Simulated time in application
            transmission_format: Format used for transmission (json, xml, mixed)
            serialized_data: Serialized data string (optional, for debugging)
            encrypted: Whether data is encrypted
            security_level: Security level (low, medium, high)
        """
        if not self.connected:
            return
        
        reading = {
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'room': room,
            'value': value,
            'unit': unit,
            'timestamp': datetime.now(),
            'simulation_time': simulation_time,
            'encrypted': encrypted,
            'security_level': security_level
        }
        
        # Add transmission format metadata if provided
        if transmission_format:
            reading['transmission_format'] = transmission_format
        if serialized_data:
            reading['serialized_data'] = serialized_data
        
        with self.lock:
            self.sensor_batch.append(reading)
            
            if len(self.sensor_batch) >= self.batch_size:
                self._flush_sensor_batch()
    
    def _flush_sensor_batch(self):
        """Flush sensor readings batch to database"""
        if self.sensor_batch and self.connected:
            try:
                self.sensor_readings.insert_many(self.sensor_batch)
                self.sensor_batch.clear()
            except Exception as e:
                print(f"Error storing sensor batch: {e}")
    
    def get_sensor_readings(self, sensor_id: Optional[str] = None,
                          room: Optional[str] = None,
                          sensor_type: Optional[str] = None,
                          limit: int = 100) -> List[Dict]:
        """
        Retrieve sensor readings with optional filters
        
        Args:
            sensor_id: Filter by sensor ID
            room: Filter by room
            sensor_type: Filter by sensor type
            limit: Maximum number of records to return
            
        Returns:
            List of sensor reading documents
        """
        if not self.connected:
            return []
        
        query = {}
        if sensor_id:
            query['sensor_id'] = sensor_id
        if room:
            query['room'] = room
        if sensor_type:
            query['sensor_type'] = sensor_type
        
        try:
            return list(self.sensor_readings.find(query)
                       .sort('timestamp', DESCENDING)
                       .limit(limit))
        except Exception as e:
            print(f"Error retrieving sensor readings: {e}")
            return []
    
    # ========================================================================
    # ACTUATOR STATE STORAGE
    # ========================================================================
    
    def store_actuator_state(self, actuator_id: str, actuator_type: str, room: str,
                           state: bool, power_consumption: float, simulation_time: datetime,
                           transmission_format: str = None, serialized_data: str = None):
        """
        Store actuator state change
        
        Args:
            actuator_id: Unique actuator identifier
            actuator_type: Type of actuator
            room: Room location
            state: On/Off state
            power_consumption: Current power consumption
            simulation_time: Simulated time in application
            transmission_format: Format used for transmission (json, xml, mixed)
            serialized_data: Serialized data string (optional, for debugging)
        """
        if not self.connected:
            return
        
        state_doc = {
            'actuator_id': actuator_id,
            'actuator_type': actuator_type,
            'room': room,
            'state': state,
            'power_consumption': power_consumption,
            'timestamp': datetime.now(),
            'simulation_time': simulation_time
        }
        
        # Add transmission format metadata if provided
        if transmission_format:
            state_doc['transmission_format'] = transmission_format
        if serialized_data:
            state_doc['serialized_data'] = serialized_data
        
        with self.lock:
            self.actuator_batch.append(state_doc)
            
            if len(self.actuator_batch) >= self.batch_size:
                self._flush_actuator_batch()
    
    def _flush_actuator_batch(self):
        """Flush actuator states batch to database"""
        if self.actuator_batch and self.connected:
            try:
                self.actuator_states.insert_many(self.actuator_batch)
                self.actuator_batch.clear()
            except Exception as e:
                print(f"Error storing actuator batch: {e}")
    
    def get_actuator_states(self, actuator_id: Optional[str] = None,
                          room: Optional[str] = None,
                          limit: int = 100) -> List[Dict]:
        """Retrieve actuator state history"""
        if not self.connected:
            return []
        
        query = {}
        if actuator_id:
            query['actuator_id'] = actuator_id
        if room:
            query['room'] = room
        
        try:
            return list(self.actuator_states.find(query)
                       .sort('timestamp', DESCENDING)
                       .limit(limit))
        except Exception as e:
            print(f"Error retrieving actuator states: {e}")
            return []
    
    # ========================================================================
    # ENERGY DATA STORAGE
    # ========================================================================
    
    def store_energy_data(self, solar_generation: float, wind_generation: float,
                        total_generation: float, total_consumption: float,
                        battery_level: float, battery_percentage: float,
                        grid_import: float, grid_export: float,
                        simulation_time: datetime):
        """Store energy system data"""
        if not self.connected:
            return
        
        energy_doc = {
            'timestamp': datetime.now(),
            'simulation_time': simulation_time,
            'solar_generation': solar_generation,
            'wind_generation': wind_generation,
            'total_generation': total_generation,
            'total_consumption': total_consumption,
            'battery_level': battery_level,
            'battery_percentage': battery_percentage,
            'grid_import': grid_import,
            'grid_export': grid_export
        }
        
        try:
            self.energy_data.insert_one(energy_doc)
        except Exception as e:
            print(f"Error storing energy data: {e}")
    
    def get_energy_data(self, limit: int = 100) -> List[Dict]:
        """Retrieve energy data history"""
        if not self.connected:
            return []
        
        try:
            return list(self.energy_data.find()
                       .sort('timestamp', DESCENDING)
                       .limit(limit))
        except Exception as e:
            print(f"Error retrieving energy data: {e}")
            return []
    
    # ========================================================================
    # WATER DATA STORAGE
    # ========================================================================
    
    def store_water_data(self, rainwater_level: float, rainwater_percentage: float,
                       consumption: float, rainfall: float, simulation_time: datetime):
        """Store water system data"""
        if not self.connected:
            return
        
        water_doc = {
            'timestamp': datetime.now(),
            'simulation_time': simulation_time,
            'rainwater_level': rainwater_level,
            'rainwater_percentage': rainwater_percentage,
            'consumption': consumption,
            'rainfall': rainfall
        }
        
        try:
            self.water_data.insert_one(water_doc)
        except Exception as e:
            print(f"Error storing water data: {e}")
    
    def get_water_data(self, limit: int = 100) -> List[Dict]:
        """Retrieve water data history"""
        if not self.connected:
            return []
        
        try:
            return list(self.water_data.find()
                       .sort('timestamp', DESCENDING)
                       .limit(limit))
        except Exception as e:
            print(f"Error retrieving water data: {e}")
            return []
    
    # ========================================================================
    # EVENT STORAGE
    # ========================================================================
    
    def store_event(self, event_type: str, message: str, severity: str,
                   room: Optional[str] = None, simulation_time: Optional[datetime] = None):
        """
        Store system event
        
        Args:
            event_type: Type of event (sensor, actuator, control, etc.)
            message: Event message
            severity: Severity level (info, warning, critical)
            room: Associated room (optional)
            simulation_time: Simulated time (optional)
        """
        if not self.connected:
            return
        
        event_doc = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'message': message,
            'severity': severity
        }
        
        if room:
            event_doc['room'] = room
        if simulation_time:
            event_doc['simulation_time'] = simulation_time
        
        with self.lock:
            self.event_batch.append(event_doc)
            
            if len(self.event_batch) >= self.batch_size:
                self._flush_event_batch()
    
    def _flush_event_batch(self):
        """Flush events batch to database"""
        if self.event_batch and self.connected:
            try:
                self.events.insert_many(self.event_batch)
                self.event_batch.clear()
            except Exception as e:
                print(f"Error storing event batch: {e}")
    
    def get_events(self, event_type: Optional[str] = None,
                  severity: Optional[str] = None,
                  limit: int = 100) -> List[Dict]:
        """Retrieve events with optional filters"""
        if not self.connected:
            return []
        
        query = {}
        if event_type:
            query['event_type'] = event_type
        if severity:
            query['severity'] = severity
        
        try:
            return list(self.events.find(query)
                       .sort('timestamp', DESCENDING)
                       .limit(limit))
        except Exception as e:
            print(f"Error retrieving events: {e}")
            return []
    
    # ========================================================================
    # SYSTEM STATISTICS STORAGE
    # ========================================================================
    
    def store_system_stats(self, cycle_count: int, num_people: int,
                         active_sensors: int, active_actuators: int,
                         network_packets: int, simulation_time: datetime):
        """Store system statistics snapshot"""
        if not self.connected:
            return
        
        stats_doc = {
            'timestamp': datetime.now(),
            'simulation_time': simulation_time,
            'cycle_count': cycle_count,
            'num_people': num_people,
            'active_sensors': active_sensors,
            'active_actuators': active_actuators,
            'network_packets': network_packets
        }
        
        try:
            self.system_stats.insert_one(stats_doc)
        except Exception as e:
            print(f"Error storing system stats: {e}")
    
    def get_system_stats(self, limit: int = 100) -> List[Dict]:
        """Retrieve system statistics history"""
        if not self.connected:
            return []
        
        try:
            return list(self.system_stats.find()
                       .sort('timestamp', DESCENDING)
                       .limit(limit))
        except Exception as e:
            print(f"Error retrieving system stats: {e}")
            return []
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    def flush_batches(self):
        """Flush all pending batches to database"""
        with self.lock:
            self._flush_sensor_batch()
            self._flush_actuator_batch()
            self._flush_event_batch()
    
    # ========================================================================
    # ANALYTICS QUERIES
    # ========================================================================
    
    def get_average_sensor_reading(self, sensor_type: str, room: Optional[str] = None,
                                  hours: int = 24) -> Optional[float]:
        """Get average sensor reading for specified period"""
        if not self.connected:
            return None
        
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        pipeline = [
            {'$match': {
                'sensor_type': sensor_type,
                'timestamp': {'$gte': cutoff_time}
            }},
            {'$group': {
                '_id': None,
                'avg_value': {'$avg': '$value'}
            }}
        ]
        
        if room:
            pipeline[0]['$match']['room'] = room
        
        try:
            result = list(self.sensor_readings.aggregate(pipeline))
            return result[0]['avg_value'] if result else None
        except Exception as e:
            print(f"Error calculating average: {e}")
            return None
    
    def get_total_energy_consumed(self, hours: int = 24) -> Optional[float]:
        """Get total energy consumed in specified period (kWh)"""
        if not self.connected:
            return None
        
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff_time}}},
            {'$group': {
                '_id': None,
                'total': {'$sum': '$total_consumption'}
            }}
        ]
        
        try:
            result = list(self.energy_data.aggregate(pipeline))
            # Convert W to kWh (assuming readings are per minute)
            return (result[0]['total'] / 1000 / 60) if result else None
        except Exception as e:
            print(f"Error calculating energy: {e}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.connected:
            return {'connected': False}
        
        try:
            stats = {
                'connected': True,
                'sensor_readings': self.sensor_readings.count_documents({}),
                'actuator_states': self.actuator_states.count_documents({}),
                'energy_data': self.energy_data.count_documents({}),
                'water_data': self.water_data.count_documents({}),
                'events': self.events.count_documents({}),
                'system_stats': self.system_stats.count_documents({}),
                'database_size': self.db.command('dbStats')['dataSize']
            }
            return stats
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {'connected': True, 'error': str(e)}
