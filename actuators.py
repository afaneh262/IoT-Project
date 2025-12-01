"""
IoT Actuators for Smart Home Simulation
"""

from datetime import datetime
from models import Room, DataPacket
from config import POWER_CONSUMPTION

# ============================================================================
# BASE ACTUATOR CLASS
# ============================================================================

class Actuator:
    """Base class for all IoT actuators"""
    
    def __init__(self, actuator_id: str, room: Room, actuator_type: str):
        self.actuator_id = actuator_id
        self.room = room
        self.actuator_type = actuator_type
        self.state = False  # OFF by default
        self.power_consumption = 0  # Watts when ON
        self.last_state_change = None
        self.total_on_time = 0  # seconds
        self.activation_count = 0
        
    def turn_on(self):
        """Turn actuator ON"""
        if not self.state:
            self.state = True
            self.last_state_change = datetime.now()
            self.activation_count += 1
            
    def turn_off(self):
        """Turn actuator OFF"""
        if self.state:
            self.state = False
            if self.last_state_change:
                duration = (datetime.now() - self.last_state_change).total_seconds()
                self.total_on_time += duration
            self.last_state_change = datetime.now()
            
    def get_consumption(self) -> float:
        """Get current power consumption"""
        return self.power_consumption if self.state else 0
    
    def create_status_packet(self, destination: str) -> DataPacket:
        """Create a status packet"""
        return DataPacket(
            source=self.actuator_id,
            destination=destination,
            data_type="status",
            payload={
                "actuator_type": self.actuator_type,
                "state": "ON" if self.state else "OFF",
                "room": self.room.name,
                "power": self.get_consumption()
            },
            timestamp=datetime.now()
        )
    
    def __repr__(self):
        state_str = "ON" if self.state else "OFF"
        return f"{self.actuator_type}({self.actuator_id}, {self.room.name}, {state_str})"

# ============================================================================
# LIGHT ACTUATOR
# ============================================================================

class LightActuator(Actuator):
    """Controls lighting in a room"""
    
    def __init__(self, actuator_id: str, room: Room, light_type: str = "LED"):
        super().__init__(actuator_id, room, f"{light_type} Light")
        self.light_type = light_type
        self.brightness = 100  # Percentage
        
        # Set power consumption based on light type
        if light_type == "LED":
            self.power_consumption = POWER_CONSUMPTION["LED_Light"]
        else:
            self.power_consumption = POWER_CONSUMPTION["CFL_Light"]
    
    def set_brightness(self, brightness: int):
        """Set light brightness (0-100%)"""
        self.brightness = max(0, min(100, brightness))
        # Dimming reduces power consumption
        self.power_consumption = (POWER_CONSUMPTION[f"{self.light_type}_Light"] * 
                                 self.brightness / 100)
    
    def get_consumption(self) -> float:
        """Get current power consumption based on brightness"""
        if self.state:
            return self.power_consumption * self.brightness / 100
        return 0

# ============================================================================
# FAN ACTUATOR
# ============================================================================

class FanActuator(Actuator):
    """Controls fan or ventilation"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Fan")
        self.speed = 1  # 1 = low, 2 = medium, 3 = high
        self.power_consumption = POWER_CONSUMPTION["Fan"]
    
    def set_speed(self, speed: int):
        """Set fan speed (1-3)"""
        self.speed = max(1, min(3, speed))
        # Higher speed = more power
        base_power = POWER_CONSUMPTION["Fan"]
        self.power_consumption = base_power * (0.5 + 0.25 * self.speed)
    
    def get_consumption(self) -> float:
        """Get current power consumption based on speed"""
        if self.state:
            return self.power_consumption
        return 0

# ============================================================================
# AC UNIT ACTUATOR
# ============================================================================

class ACActuator(Actuator):
    """Controls air conditioning unit"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "AC Unit")
        self.target_temperature = 24  # Celsius
        self.mode = "cool"  # "cool" or "heat"
        self.power_consumption = POWER_CONSUMPTION["AC_Unit"]
    
    def set_target_temperature(self, temp: float):
        """Set target temperature"""
        self.target_temperature = max(16, min(30, temp))
    
    def set_mode(self, mode: str):
        """Set AC mode (cool/heat)"""
        if mode in ["cool", "heat"]:
            self.mode = mode
    
    def get_consumption(self) -> float:
        """AC consumes variable power based on load"""
        if self.state:
            # Simulate variable consumption (60-100% of max)
            temp_diff = abs(self.room.temperature - self.target_temperature)
            load_factor = min(1.0, 0.6 + (temp_diff / 10) * 0.4)
            return self.power_consumption * load_factor
        return 0

# ============================================================================
# HEATER ACTUATOR
# ============================================================================

class HeaterActuator(Actuator):
    """Controls heating element"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Heater")
        self.target_temperature = 22  # Celsius
        self.power_consumption = POWER_CONSUMPTION["Heater"]
    
    def set_target_temperature(self, temp: float):
        """Set target temperature"""
        self.target_temperature = max(16, min(30, temp))
    
    def get_consumption(self) -> float:
        """Heater consumption varies with temperature difference"""
        if self.state:
            temp_diff = self.target_temperature - self.room.temperature
            load_factor = min(1.0, max(0.5, temp_diff / 5))
            return self.power_consumption * load_factor
        return 0

# ============================================================================
# SMART OUTLET ACTUATOR
# ============================================================================

class SmartOutletActuator(Actuator):
    """Controls a smart power outlet"""
    
    def __init__(self, actuator_id: str, room: Room, device_name: str = "Device"):
        super().__init__(actuator_id, room, f"Outlet ({device_name})")
        self.device_name = device_name
        self.power_consumption = 100  # Default device consumption
    
    def set_device_power(self, watts: float):
        """Set the power consumption of connected device"""
        self.power_consumption = max(0, watts)

# ============================================================================
# WINDOW BLIND ACTUATOR
# ============================================================================

class WindowBlindActuator(Actuator):
    """Controls motorized window blinds"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Window Blind")
        self.position = 0  # 0 = fully closed, 100 = fully open
        self.power_consumption = 10  # Low power motor
    
    def set_position(self, position: int):
        """Set blind position (0-100%)"""
        self.position = max(0, min(100, position))
        # Motor only consumes power when moving
        self.state = False  # Motor stops after position is set
    
    def get_consumption(self) -> float:
        """Only consumes power when actively moving"""
        return self.power_consumption if self.state else 0

# ============================================================================
# WATER PUMP ACTUATOR
# ============================================================================

class WaterPumpActuator(Actuator):
    """Controls water pump for distribution"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Water Pump")
        self.flow_rate = 0  # Liters per minute
        self.power_consumption = POWER_CONSUMPTION["Pump"]
    
    def set_flow_rate(self, rate: float):
        """Set pump flow rate"""
        self.flow_rate = max(0, min(50, rate))  # Max 50 L/min
        # Power consumption scales with flow rate
        self.power_consumption = (POWER_CONSUMPTION["Pump"] * 
                                 (0.3 + 0.7 * self.flow_rate / 50))

# ============================================================================
# ALARM ACTUATOR
# ============================================================================

class AlarmActuator(Actuator):
    """Controls alarm/notification system"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Alarm")
        self.alarm_type = "security"  # "security", "fire", "water"
        self.power_consumption = 5
        self.triggered = False
    
    def trigger(self, alarm_type: str = "security"):
        """Trigger alarm"""
        self.alarm_type = alarm_type
        self.triggered = True
        self.turn_on()
    
    def reset(self):
        """Reset alarm"""
        self.triggered = False
        self.turn_off()

# ============================================================================
# DOOR LOCK ACTUATOR
# ============================================================================

class DoorLockActuator(Actuator):
    """Controls smart door lock"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Door Lock")
        self.locked = True
        self.power_consumption = 2
        
    def lock(self):
        """Lock the door"""
        self.locked = True
        self.state = True
        
    def unlock(self):
        """Unlock the door"""
        self.locked = False
        self.state = False

# ============================================================================
# KITCHEN APPLIANCE ACTUATORS
# ============================================================================

class RefrigeratorActuator(Actuator):
    """Controls refrigerator (always on, cycles compressor)"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Refrigerator")
        self.power_consumption = POWER_CONSUMPTION["Refrigerator"]
        self.temperature = 4.0  # Celsius
        self.compressor_running = False
        self.state = True  # Always "on"
        
    def get_consumption(self) -> float:
        """Compressor cycles on/off"""
        # Simulate compressor cycling
        import random
        if random.random() < 0.4:  # 40% duty cycle
            self.compressor_running = True
            return self.power_consumption
        else:
            self.compressor_running = False
            return self.power_consumption * 0.1  # Standby power

class MicrowaveActuator(Actuator):
    """Controls microwave oven"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Microwave")
        self.power_consumption = POWER_CONSUMPTION["Microwave"]
        self.timer = 0  # seconds remaining

class OvenActuator(Actuator):
    """Controls kitchen oven"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Oven")
        self.power_consumption = POWER_CONSUMPTION["Oven"]
        self.temperature_setpoint = 0
        self.preheating = False

class DishwasherActuator(Actuator):
    """Controls dishwasher"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Dishwasher")
        self.power_consumption = POWER_CONSUMPTION["Dishwasher"]
        self.cycle_time = 0  # minutes remaining
        self.cycle_phase = "idle"  # idle, wash, rinse, dry

# ============================================================================
# LAUNDRY APPLIANCE ACTUATORS
# ============================================================================

class WashingMachineActuator(Actuator):
    """Controls washing machine"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Washing Machine")
        self.power_consumption = POWER_CONSUMPTION["Washing_Machine"]
        self.cycle_time = 0  # minutes remaining
        self.cycle_phase = "idle"  # idle, fill, wash, rinse, spin
        
    def start_cycle(self):
        """Start washing cycle"""
        self.state = True
        self.cycle_time = 60  # 60 minutes
        self.cycle_phase = "fill"

class DryerActuator(Actuator):
    """Controls clothes dryer"""
    
    def __init__(self, actuator_id: str, room: Room):
        super().__init__(actuator_id, room, "Dryer")
        self.power_consumption = POWER_CONSUMPTION["Dryer"]
        self.cycle_time = 0  # minutes remaining
        self.temperature = "medium"
        
    def start_cycle(self, temperature: str = "medium"):
        """Start drying cycle"""
        self.state = True
        self.cycle_time = 60  # 60 minutes
        self.temperature = temperature  # Briefly powered during unlock operation
    
    def get_consumption(self) -> float:
        """Minimal power consumption"""
        return self.power_consumption if self.state else 0.1  # Standby power
