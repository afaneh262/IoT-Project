"""
Smart Home Central Controller
"""

from datetime import datetime
from typing import List, Dict
from models import Room, SystemStatus
from sensors import Sensor
from actuators import Actuator, LightActuator, FanActuator, ACActuator, HeaterActuator
from energy_system import EnergySystem
from water_system import WaterSystem
from network import IoTNetwork
from config import (Season, TEMP_HOT_THRESHOLD, TEMP_COLD_THRESHOLD,
                   LIGHT_DARK_THRESHOLD, TEMP_COMFORT_MIN, TEMP_COMFORT_MAX)

# ============================================================================
# CENTRAL CONTROLLER
# ============================================================================

class SmartHomeController:
    """Central intelligence for smart home automation"""
    
    def __init__(self, rooms: List[Room], sensors: List[Sensor], 
                 actuators: List[Actuator], energy_system: EnergySystem,
                 water_system: WaterSystem, network: IoTNetwork):
        self.rooms = rooms
        self.sensors = sensors
        self.actuators = actuators
        self.energy_system = energy_system
        self.water_system = water_system
        self.network = network
        
        # System state
        self.system_status = SystemStatus()
        self.power_saving_mode = False
        self.emergency_mode = False
        self.cycle_count = 0
        
        # Control strategies
        self.strategies = {
            "lighting": True,
            "climate": True,
            "energy_optimization": True,
            "water_management": True
        }
        
        # Learning parameters (simple adaptive control)
        self.occupancy_patterns = {}  # room -> time -> probability
        self.comfort_preferences = {
            "temperature": 22,
            "light_threshold": 30
        }
        
    def process_cycle(self, time_hour: int, season: Season, num_people: int,
                     verbose: bool = True) -> Dict:
        """
        Execute one control cycle
        Returns dict with cycle statistics
        """
        self.cycle_count += 1
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"CYCLE {self.cycle_count} | Hour: {time_hour:02d}:00 | "
                  f"Season: {season.value} | People: {num_people}")
            print(f"{'='*80}")
        
        # Phase 1: Read all sensors
        sensor_readings = self._read_sensors(time_hour, season, num_people, verbose)
        
        # Phase 2: Analyze and make decisions
        decisions = self._make_control_decisions(time_hour, verbose)
        
        # Phase 3: Execute actuator commands
        self._execute_actuator_commands(decisions)
        
        # Phase 4: Update energy system
        total_consumption = sum(act.get_consumption() for act in self.actuators)
        self.energy_system.update_generation(time_hour, season)
        net_power = self.energy_system.update_battery(total_consumption)
        
        # Phase 5: Update water system
        water_status = self.water_system.update(season, num_people, time_hour)
        
        # Phase 6: System monitoring and alerts
        self._check_system_health()
        
        # Phase 7: Network communication simulation
        self._simulate_network_traffic()
        
        if verbose:
            self._print_status_summary(total_consumption)
        
        # Return cycle statistics
        return {
            "cycle": self.cycle_count,
            "sensor_readings": len(sensor_readings),
            "decisions_made": len(decisions),
            "power_consumption": total_consumption,
            "power_generation": self.energy_system.total_generation,
            "net_power": net_power,
            "battery_level": self.energy_system.get_battery_percentage(),
            "water_level": self.water_system.get_level_percentage(),
            "active_actuators": sum(1 for a in self.actuators if a.state)
        }
    
    def _read_sensors(self, time_hour: int, season: Season, num_people: int,
                     verbose: bool) -> List[Dict]:
        """Read all sensors and collect data"""
        readings = []
        
        if verbose:
            print("\n--- SENSOR READINGS ---")
        
        for sensor in self.sensors:
            value = sensor.read(time_hour, season, num_people)
            readings.append({
                "sensor_id": sensor.sensor_id,
                "type": sensor.sensor_type,
                "room": sensor.room.name,
                "value": value,
                "unit": sensor.get_unit()
            })
            
            if verbose:
                print(f"{sensor.room.name:20s} | {sensor.sensor_type:12s} = "
                      f"{value:6.1f} {sensor.get_unit()}")
        
        # Update system status
        self.system_status.active_sensors = len(readings)
        
        return readings
    
    def _make_control_decisions(self, time_hour: int, verbose: bool) -> List[Dict]:
        """Analyze sensor data and make control decisions"""
        decisions = []
        
        if verbose:
            print("\n--- CONTROL DECISIONS ---")
        
        # Check for special modes
        self.power_saving_mode = self.energy_system.is_power_saving_needed()
        self.emergency_mode = self.energy_system.is_critical_power()
        
        if self.power_saving_mode and verbose:
            print("⚠️  POWER SAVING MODE ACTIVATED (Battery < 20%)")
        
        if self.emergency_mode and verbose:
            print("🚨 EMERGENCY MODE (Battery < 10%) - Essential systems only")
        
        # Group actuators by type and room
        lights = [a for a in self.actuators if isinstance(a, LightActuator)]
        fans = [a for a in self.actuators if isinstance(a, FanActuator)]
        acs = [a for a in self.actuators if isinstance(a, ACActuator)]
        heaters = [a for a in self.actuators if isinstance(a, HeaterActuator)]
        
        # Strategy 1: Lighting control
        if self.strategies["lighting"]:
            decisions.extend(self._control_lighting(lights, verbose))
        
        # Strategy 2: Climate control
        if self.strategies["climate"]:
            decisions.extend(self._control_cooling(fans, acs, verbose))
            decisions.extend(self._control_heating(heaters, verbose))
        
        return decisions
    
    def _control_lighting(self, lights: List[LightActuator], 
                         verbose: bool) -> List[Dict]:
        """Control lighting based on motion and light levels"""
        decisions = []
        
        for light in lights:
            room = light.room
            action = None
            reason = ""
            
            # Emergency mode: turn off all non-essential lights
            if self.emergency_mode:
                if light.state and room.name not in ["Technical Room", "Hallway"]:
                    light.turn_off()
                    action = "OFF"
                    reason = "Emergency mode"
            
            # Power saving: stricter thresholds
            elif self.power_saving_mode:
                if room.motion_detected and room.light_level < 15:
                    if not light.state:
                        light.turn_on()
                        light.set_brightness(50)  # Dimmed in power saving
                        action = "ON (50%)"
                        reason = f"Motion + Very dark (light={room.light_level:.0f})"
                else:
                    if light.state:
                        light.turn_off()
                        action = "OFF"
                        reason = "Power saving"
            
            # Normal operation
            else:
                light_threshold = self.comfort_preferences.get("light_threshold", 
                                                               LIGHT_DARK_THRESHOLD)
                
                if room.motion_detected and room.light_level < light_threshold:
                    if not light.state:
                        light.turn_on()
                        action = "ON"
                        reason = f"Motion + Dark (light={room.light_level:.0f})"
                else:
                    if light.state and (not room.motion_detected or 
                                       room.light_level >= light_threshold):
                        light.turn_off()
                        action = "OFF"
                        reason = "No motion or sufficient light"
            
            if action and verbose:
                print(f"{room.name:20s} | Light {action} - {reason}")
                decisions.append({"actuator": light.actuator_id, 
                                 "action": action, "reason": reason})
        
        return decisions
    
    def _control_cooling(self, fans: List[FanActuator], acs: List[ACActuator],
                        verbose: bool) -> List[Dict]:
        """Control fans and AC units based on temperature"""
        decisions = []
        
        # Process fans
        for fan in fans:
            room = fan.room
            action = None
            reason = ""
            
            if self.emergency_mode:
                if fan.state:
                    fan.turn_off()
                    action = "OFF"
                    reason = "Emergency mode"
            
            elif self.power_saving_mode:
                # Only run fans if very hot
                if room.temperature > TEMP_HOT_THRESHOLD + 3:
                    if not fan.state:
                        fan.turn_on()
                        fan.set_speed(1)  # Low speed
                        action = "ON (Low)"
                        reason = f"Very hot (temp={room.temperature:.1f}°C)"
                else:
                    if fan.state:
                        fan.turn_off()
                        action = "OFF"
                        reason = "Power saving"
            
            else:
                # Normal cooling strategy
                if room.temperature > TEMP_HOT_THRESHOLD:
                    if not fan.state:
                        fan.turn_on()
                        # Set speed based on temperature
                        if room.temperature > TEMP_HOT_THRESHOLD + 4:
                            fan.set_speed(3)
                            action = "ON (High)"
                        elif room.temperature > TEMP_HOT_THRESHOLD + 2:
                            fan.set_speed(2)
                            action = "ON (Medium)"
                        else:
                            fan.set_speed(1)
                            action = "ON (Low)"
                        reason = f"Hot (temp={room.temperature:.1f}°C)"
                elif room.temperature < TEMP_COMFORT_MAX:
                    if fan.state:
                        fan.turn_off()
                        action = "OFF"
                        reason = "Comfortable temperature"
            
            if action and verbose:
                print(f"{room.name:20s} | Fan {action} - {reason}")
                decisions.append({"actuator": fan.actuator_id, 
                                 "action": action, "reason": reason})
        
        # AC units would be controlled similarly but with higher power cost
        # Omitted for brevity, similar logic
        
        return decisions
    
    def _control_heating(self, heaters: List[HeaterActuator], 
                        verbose: bool) -> List[Dict]:
        """Control heaters based on temperature"""
        decisions = []
        
        for heater in heaters:
            room = heater.room
            action = None
            reason = ""
            
            # No heating in emergency mode
            if self.emergency_mode:
                if heater.state:
                    heater.turn_off()
                    action = "OFF"
                    reason = "Emergency mode"
            
            # Limited heating in power saving
            elif self.power_saving_mode:
                if room.temperature < TEMP_COLD_THRESHOLD - 2:
                    if not heater.state:
                        heater.turn_on()
                        heater.set_target_temperature(19)  # Lower target
                        action = "ON (19°C)"
                        reason = f"Very cold (temp={room.temperature:.1f}°C)"
                else:
                    if heater.state:
                        heater.turn_off()
                        action = "OFF"
                        reason = "Power saving"
            
            # Normal heating
            else:
                if room.temperature < TEMP_COLD_THRESHOLD:
                    if not heater.state:
                        heater.turn_on()
                        heater.set_target_temperature(
                            self.comfort_preferences.get("temperature", 22)
                        )
                        action = f"ON ({heater.target_temperature}°C)"
                        reason = f"Cold (temp={room.temperature:.1f}°C)"
                elif room.temperature > TEMP_COMFORT_MIN:
                    if heater.state:
                        heater.turn_off()
                        action = "OFF"
                        reason = "Comfortable temperature"
            
            if action and verbose:
                print(f"{room.name:20s} | Heater {action} - {reason}")
                decisions.append({"actuator": heater.actuator_id, 
                                 "action": action, "reason": reason})
        
        return decisions
    
    def _execute_actuator_commands(self, decisions: List[Dict]):
        """Execute actuator commands (already done in decision phase)"""
        # Actuators are already controlled in decision phase
        # This phase is for network communication simulation
        pass
    
    def _check_system_health(self):
        """Monitor system health and generate alerts"""
        # Check battery level
        if self.energy_system.is_critical_power():
            self.system_status.add_alert(
                "Critical battery level! Emergency mode activated.",
                "error"
            )
        elif self.energy_system.is_power_saving_needed():
            self.system_status.add_alert(
                "Low battery level. Power saving mode activated.",
                "warning"
            )
        
        # Check water level
        if self.water_system.is_water_shortage():
            self.system_status.add_alert(
                "Water shortage! Tank level critical.",
                "error"
            )
        
        # Check for grid dependency
        if self.energy_system.grid_import > 1000:  # More than 1 kWh imported
            self.system_status.add_alert(
                "High grid dependency. Check renewable generation.",
                "warning"
            )
    
    def _simulate_network_traffic(self):
        """Simulate IoT network traffic for visualization"""
        # Sensors send readings to hub
        if self.network.hub_node:
            for sensor in self.sensors[::5]:  # Send every 5th sensor for visualization
                packet = sensor.create_data_packet(self.network.hub_node.node_id)
                self.network.send_packet(packet)
    
    def _print_status_summary(self, total_consumption: float):
        """Print status summary"""
        print(f"\n--- ENERGY STATUS ---")
        print(f"Solar Generation:     {self.energy_system.current_solar:8.0f} W")
        print(f"Wind Generation:      {self.energy_system.current_wind:8.0f} W")
        print(f"Total Generation:     {self.energy_system.total_generation:8.0f} W")
        print(f"Total Consumption:    {total_consumption:8.0f} W")
        print(f"Net Power:            {self.energy_system.total_generation - total_consumption:8.0f} W")
        print(f"Battery Level:        {self.energy_system.battery_level:8.0f} Wh "
              f"({self.energy_system.get_battery_percentage():.1f}%)")
        print(f"Battery Status:       {self.energy_system.get_battery_status()}")
        
        print(f"\n--- WATER STATUS ---")
        print(f"Tank Level:           {self.water_system.current_level:8.0f} L "
              f"({self.water_system.get_level_percentage():.1f}%)")
        print(f"Collection Rate:      {self.water_system.current_collection_rate:8.0f} L/hour")
        print(f"Usage Rate:           {self.water_system.current_usage_rate:8.0f} L/hour")
        print(f"Raining:              {'Yes' if self.water_system.is_raining else 'No'}")
        
        print(f"\n--- SYSTEM STATUS ---")
        print(f"Active Sensors:       {self.system_status.active_sensors}")
        print(f"Active Actuators:     {sum(1 for a in self.actuators if a.state)}")
        print(f"Network Packets:      {self.network.total_packets_sent}")
        print(f"System Mode:          {'EMERGENCY' if self.emergency_mode else 'POWER SAVING' if self.power_saving_mode else 'NORMAL'}")
    
    def get_system_summary(self) -> Dict:
        """Get comprehensive system summary"""
        return {
            "cycle_count": self.cycle_count,
            "power_saving_mode": self.power_saving_mode,
            "emergency_mode": self.emergency_mode,
            "energy": self.energy_system.get_statistics(),
            "water": self.water_system.get_statistics(),
            "network": self.network.get_statistics(),
            "alerts": self.system_status.get_recent_alerts()
        }
