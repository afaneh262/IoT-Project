"""
IoT Sensors for Smart Home Simulation
"""

import random
import math
from datetime import datetime
from typing import Optional
from models import Room, DataPacket
from config import Season, SENSOR_ACCURACY

# ============================================================================
# BASE SENSOR CLASS
# ============================================================================

class Sensor:
    """Base class for all IoT sensors"""
    
    def __init__(self, sensor_id: str, room: Room, sensor_type: str):
        self.sensor_id = sensor_id
        self.room = room
        self.sensor_type = sensor_type
        self.value = 0.0
        self.last_reading = None
        self.last_update = None
        self.accuracy = SENSOR_ACCURACY
        self.power_consumption = 0.5  # Watts
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Read sensor value - to be overridden by subclasses"""
        raise NotImplementedError
    
    def add_noise(self, value: float, noise_percent: float = 2.0) -> float:
        """Add realistic sensor noise"""
        noise = random.uniform(-noise_percent, noise_percent) / 100
        return value * (1 + noise)
    
    def create_data_packet(self, destination: str) -> DataPacket:
        """Create a data packet with sensor reading"""
        return DataPacket(
            source=self.sensor_id,
            destination=destination,
            data_type="sensor_reading",
            payload={
                "sensor_type": self.sensor_type,
                "value": self.value,
                "room": self.room.name,
                "unit": self.get_unit()
            },
            timestamp=datetime.now()
        )
    
    def get_unit(self) -> str:
        """Get measurement unit"""
        return ""
    
    def __repr__(self):
        return f"{self.sensor_type}({self.sensor_id}, {self.room.name})"

# ============================================================================
# TEMPERATURE SENSOR
# ============================================================================

class TemperatureSensor(Sensor):
    """Measures ambient temperature"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "Temperature")
        self.value = 22.0
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Generate realistic temperature based on conditions"""
        # Base temperature by season
        base_temp = {
            Season.WINTER: 12,
            Season.SPRING: 18,
            Season.SUMMER: 26,
            Season.AUTUMN: 20
        }[season]
        
        # Outdoor temperature variation by time of day
        if 6 <= time_hour <= 18:
            # Warmer during day, peak at noon
            hour_offset = (time_hour - 12) / 12  # -1 to 0 to +1
            time_modifier = 8 * (1 - abs(hour_offset))  # Peak at noon
        else:
            # Cooler at night
            time_modifier = -4
        
        # Indoor insulation reduces outdoor effect
        insulation_factor = 0.4
        
        # People generate heat (100W per person)
        people_heat = num_people * 0.8 if self.room.occupancy > 0 else 0
        
        # Kitchen and laundry are warmer due to appliances
        appliance_heat = 0
        if self.room.name == "Kitchen":
            appliance_heat = random.uniform(0, 3)
        elif self.room.name == "Laundry Room":
            appliance_heat = random.uniform(0, 2)
        
        # Calculate final temperature
        outdoor_temp = base_temp + time_modifier
        indoor_temp = (22 + (outdoor_temp - 22) * insulation_factor + 
                      people_heat + appliance_heat)
        
        # Add sensor noise
        self.value = self.add_noise(indoor_temp, 1.5)
        self.room.temperature = self.value
        self.last_update = datetime.now()
        
        return self.value
    
    def get_unit(self) -> str:
        return "°C"

# ============================================================================
# LIGHT SENSOR
# ============================================================================

class LightSensor(Sensor):
    """Measures ambient light level"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "Light")
        self.value = 50
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Generate realistic light level"""
        # Natural daylight hours
        if 6 <= time_hour <= 18:
            # Peak at noon
            hour_offset = abs(time_hour - 12) / 6  # 0 at noon, 1 at 6am/6pm
            base_light = 90 * (1 - hour_offset)
        else:
            base_light = 5  # Minimal ambient light at night
        
        # Season affects daylight intensity
        season_modifier = {
            Season.WINTER: 0.6,
            Season.SPRING: 0.85,
            Season.SUMMER: 1.0,
            Season.AUTUMN: 0.75
        }[season]
        
        # Interior rooms get less natural light
        interior_rooms = ["Hallway", "Bathroom 2", "Bathroom 3", "Bathroom 4",
                         "Master Bathroom", "Guest Bathroom", "Laundry Room", 
                         "Storage", "Technical Room"]
        
        if self.room.name in interior_rooms:
            window_factor = 0.2  # Much less natural light
        else:
            window_factor = 0.7  # Windows allow more light
        
        # Calculate light level
        natural_light = base_light * season_modifier * window_factor
        
        # Add randomness
        self.value = max(0, min(100, self.add_noise(natural_light, 5)))
        self.room.light_level = self.value
        self.last_update = datetime.now()
        
        return self.value
    
    def get_unit(self) -> str:
        return "lux"

# ============================================================================
# MOTION SENSOR
# ============================================================================

class MotionSensor(Sensor):
    """Detects motion/presence in a room"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "Motion")
        self.value = 0
        self.detection_timeout = 5  # minutes
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Detect motion based on time and occupancy"""
        # High activity hours
        if 7 <= time_hour <= 23:
            base_probability = 0.25
        else:
            base_probability = 0.05  # Low activity at night
        
        # More people = more likely motion
        occupancy_factor = 1 + (num_people * 0.15)
        
        # Certain rooms have different patterns
        if self.room.name in ["Kitchen", "Living Room", "Dining Room"]:
            # High traffic areas
            room_modifier = 1.5
        elif self.room.name in ["Storage", "Technical Room", "Garage"]:
            # Low traffic areas
            room_modifier = 0.3
        elif "Bedroom" in self.room.name:
            # Active during morning/evening
            if 7 <= time_hour <= 9 or 20 <= time_hour <= 23:
                room_modifier = 1.2
            else:
                room_modifier = 0.4
        else:
            room_modifier = 1.0
        
        # Calculate motion probability
        motion_prob = base_probability * occupancy_factor * room_modifier
        motion_prob = min(0.8, motion_prob)  # Cap at 80%
        
        # Detect motion
        self.value = 1 if random.random() < motion_prob else 0
        self.room.motion_detected = bool(self.value)
        
        # Update occupancy estimate
        if self.value == 1:
            self.room.occupancy = random.randint(1, min(3, num_people))
        else:
            self.room.occupancy = 0
        
        self.last_update = datetime.now()
        return self.value
    
    def get_unit(self) -> str:
        return ""

# ============================================================================
# HUMIDITY SENSOR
# ============================================================================

class HumiditySensor(Sensor):
    """Measures relative humidity"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "Humidity")
        self.value = 50.0
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Generate realistic humidity level"""
        # Base humidity by season
        base_humidity = {
            Season.WINTER: 35,
            Season.SPRING: 55,
            Season.SUMMER: 65,
            Season.AUTUMN: 50
        }[season]
        
        # Bathrooms and laundry are more humid
        if "Bathroom" in self.room.name or self.room.name == "Laundry Room":
            humidity_boost = random.uniform(10, 25)
        else:
            humidity_boost = 0
        
        # People add moisture
        people_moisture = self.room.occupancy * 2
        
        # Calculate humidity
        humidity = base_humidity + humidity_boost + people_moisture
        self.value = max(20, min(90, self.add_noise(humidity, 3)))
        self.room.humidity = self.value
        self.last_update = datetime.now()
        
        return self.value
    
    def get_unit(self) -> str:
        return "%"

# ============================================================================
# POWER METER SENSOR
# ============================================================================

class PowerMeterSensor(Sensor):
    """Measures power consumption in a room"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "Power")
        self.value = 0.0
        self.cumulative_consumption = 0.0
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Calculate power consumption from actuators"""
        # Sum power from all actuators in the room
        total_power = sum(act.get_consumption() for act in self.room.actuators)
        
        # Add base load (always-on devices)
        base_load = 5  # Watts (outlets, chargers, etc.)
        
        self.value = total_power + base_load
        self.cumulative_consumption += self.value / 60  # Wh (assuming minute cycles)
        self.last_update = datetime.now()
        
        return self.value
    
    def get_unit(self) -> str:
        return "W"

# ============================================================================
# CO2 SENSOR
# ============================================================================

class CO2Sensor(Sensor):
    """Measures CO2 concentration (air quality indicator)"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "CO2")
        self.value = 400.0  # ppm
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Calculate CO2 level based on occupancy and ventilation"""
        # Outdoor CO2 level
        base_co2 = 420  # ppm
        
        # People generate CO2
        if self.room.occupancy > 0:
            co2_per_person = 200  # ppm per person
            accumulated_co2 = self.room.occupancy * co2_per_person
        else:
            # CO2 dissipates when room is empty
            accumulated_co2 = max(0, self.value - base_co2 - 50)
        
        # Ventilation reduces CO2
        ventilation_factor = 0.8  # 20% reduction due to air exchange
        
        self.value = base_co2 + (accumulated_co2 * ventilation_factor)
        self.value = max(400, min(2000, self.add_noise(self.value, 5)))
        self.last_update = datetime.now()
        
        return self.value
    
    def get_unit(self) -> str:
        return "ppm"

# ============================================================================
# VIBRATION SENSOR
# ============================================================================

class VibrationSensor(Sensor):
    """Detects vibrations and mechanical disturbances"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "Vibration")
        self.value = 0.0  # Vibration intensity (0-100)
        self.threshold = 30.0  # Alert threshold
        self.baseline = 5.0  # Normal background vibration
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Measure vibration levels"""
        # Base vibration from HVAC, appliances
        base_vibration = self.baseline
        
        # Occupancy increases vibration (movement, doors, etc.)
        if self.room.occupancy > 0:
            occupancy_vibration = self.room.occupancy * random.uniform(5, 15)
        else:
            occupancy_vibration = 0
        
        # Random events (door slams, appliances)
        if random.random() < 0.1:  # 10% chance of event
            event_vibration = random.uniform(20, 50)
        else:
            event_vibration = 0
        
        # Weather effects (wind on windows)
        if season == Season.WINTER:
            weather_vibration = random.uniform(0, 10)
        else:
            weather_vibration = random.uniform(0, 5)
        
        self.value = base_vibration + occupancy_vibration + event_vibration + weather_vibration
        self.value = max(0, min(100, self.add_noise(self.value, 3)))
        self.last_update = datetime.now()
        
        return self.value
    
    def get_unit(self) -> str:
        return "intensity"
    
    def is_abnormal(self) -> bool:
        """Check if vibration exceeds threshold"""
        return self.value > self.threshold

# ============================================================================
# CAMERA / OBJECT DETECTION SENSOR
# ============================================================================

class CameraSensor(Sensor):
    """Vision-based sensor with object detection capabilities"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "Camera")
        self.detected_objects = []
        self.detection_confidence = 0.0
        self.distance_to_object = 0.0
        self.power_consumption = 3.0  # Cameras use more power
        
        # Common household objects
        self.object_library = [
            "person", "chair", "table", "sofa", "bed", "door", "window",
            "plant", "lamp", "tv", "computer", "phone", "book", "cup",
            "bottle", "clock", "picture", "curtain", "rug", "cabinet"
        ]
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Perform object detection and distance measurement"""
        self.detected_objects = []
        
        # Detect people based on occupancy
        if self.room.occupancy > 0:
            for i in range(self.room.occupancy):
                distance = random.uniform(1.0, 5.0)  # meters
                confidence = random.uniform(0.85, 0.99)
                self.detected_objects.append({
                    'object': 'person',
                    'distance': round(distance, 2),
                    'confidence': round(confidence, 2)
                })
        
        # Detect static objects in room
        num_static_objects = random.randint(2, 5)
        for _ in range(num_static_objects):
            obj = random.choice(self.object_library)
            distance = random.uniform(0.5, 8.0)
            confidence = random.uniform(0.70, 0.95)
            self.detected_objects.append({
                'object': obj,
                'distance': round(distance, 2),
                'confidence': round(confidence, 2)
            })
        
        # Set primary detection (closest object)
        if self.detected_objects:
            closest = min(self.detected_objects, key=lambda x: x['distance'])
            self.distance_to_object = closest['distance']
            self.detection_confidence = closest['confidence']
            self.value = len(self.detected_objects)  # Number of detected objects
        else:
            self.distance_to_object = 0.0
            self.detection_confidence = 0.0
            self.value = 0
        
        self.last_update = datetime.now()
        return self.value
    
    def get_unit(self) -> str:
        return "objects"
    
    def get_detection_data(self) -> dict:
        """Get detailed detection information for SOAP/XML transmission"""
        return {
            'total_objects': int(self.value),
            'objects': self.detected_objects,
            'primary_distance': self.distance_to_object,
            'primary_confidence': self.detection_confidence,
            'timestamp': self.last_update.isoformat() if self.last_update else None
        }

# ============================================================================
# SOIL MOISTURE SENSOR
# ============================================================================

class SoilMoistureSensor(Sensor):
    """Measures soil moisture for irrigation control"""
    
    def __init__(self, sensor_id: str, room: Room):
        super().__init__(sensor_id, room, "SoilMoisture")
        self.value = 50.0  # Percentage (0-100%)
        self.optimal_range = (40, 60)  # Optimal moisture range
        self.evaporation_rate = 0.5  # % per hour
        
    def read(self, time_hour: int, season: Season, num_people: int) -> float:
        """Calculate soil moisture level"""
        # Natural evaporation
        evaporation = self.evaporation_rate
        
        # Temperature affects evaporation
        if season == Season.SUMMER:
            evaporation *= 1.5
        elif season == Season.WINTER:
            evaporation *= 0.5
        
        # Time of day affects evaporation (higher during day)
        if 10 <= time_hour <= 16:
            evaporation *= 1.3
        
        # Decrease moisture
        self.value -= evaporation
        
        # Ensure bounds
        self.value = max(0, min(100, self.add_noise(self.value, 2)))
        self.last_update = datetime.now()
        
        return self.value
    
    def get_unit(self) -> str:
        return "%"
    
    def needs_irrigation(self) -> bool:
        """Check if irrigation is needed"""
        return self.value < self.optimal_range[0]
    
    def add_water(self, amount: float):
        """Simulate irrigation (called by irrigation actuator)"""
        self.value = min(100, self.value + amount)
