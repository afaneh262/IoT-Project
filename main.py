"""
ADVANCED SMART HOME IoT SIMULATION
===================================

A realistic, modular simulation of a self-sustainable smart home with:
- Detailed floor plan with accurate room layout
- Complete infrastructure visualization (power, data, water)
- IoT sensors and smart actuators
- Renewable energy system (solar + wind)
- Rainwater collection system
- Real-time data flow visualization
- Auto-run mode with adjustable speed

INSTALLATION:
    pip install pygame  (or: conda install pygame)

HOW TO RUN:
    python main.py

CONTROLS:
    - Click "Start/Pause" to toggle auto-run mode
    - Use speed slider to adjust simulation speed
    - Click "Next Step" for manual step-by-step
    - Use +/- buttons to adjust occupants
    - Toggle "Show Wiring" to view infrastructure
    - Mouse over rooms to see detailed stats
"""

import pygame
import sys
from datetime import datetime, timedelta
from typing import List, Dict

# Import all modules
from config import *
from models import Room, NetworkNode
from sensors import (TemperatureSensor, LightSensor, MotionSensor, 
                    HumiditySensor, PowerMeterSensor, CO2Sensor)
from actuators import (LightActuator, FanActuator, HeaterActuator, 
                      ACActuator, SmartOutletActuator, RefrigeratorActuator,
                      WashingMachineActuator, DryerActuator, DishwasherActuator)
from energy_system import EnergySystem
from water_system import WaterSystem
from network import IoTNetwork, PowerGrid, WaterNetwork
from controller import SmartHomeController
from floor_plan import FloorPlanRenderer, InfrastructureRenderer, OutdoorRenderer
from wiring import WiringPathGenerator, ImprovedWiringRenderer
from event_log import EventLog, EventLogRenderer
from realistic_behaviors import (OccupancyPattern, Weather, ApplianceScheduler,
                                SecuritySystem, CostTracker, EmergencyManager)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class SmartHomeApp:
    """Main application with GUI and simulation loop"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Advanced Smart Home IoT Simulation")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_small = pygame.font.Font(None, 18)
        self.font_medium = pygame.font.Font(None, 22)
        self.font_large = pygame.font.Font(None, 28)
        self.font_title = pygame.font.Font(None, 36)
        
        # Simulation state
        self.running = True
        self.auto_run = False
        self.auto_run_speed = "Normal"
        self.last_cycle_time = 0
        self.show_wiring = True
        self.show_data_flow = True
        
        # Time management
        self.current_time = datetime(2024, 6, 15, 8, 0)  # Start summer morning
        self.num_people = 4
        self.cycle_count = 0
        
        # Animation
        self.animation_time = 0
        self.turbine_angle = 0
        
        # Event log system (initialize before simulation setup)
        self.event_log = EventLog()
        self.log_renderer = EventLogRenderer(self.screen)
        
        # Realistic behavior systems
        self.occupancy = OccupancyPattern(self.num_people)
        self.weather = Weather()
        self.scheduler = ApplianceScheduler()
        self.security = SecuritySystem()
        self.cost_tracker = CostTracker()
        self.emergency_mgr = EmergencyManager()
        
        # Initialize simulation components
        self.setup_simulation()
        
        # Renderers
        self.floor_plan_renderer = FloorPlanRenderer(self.screen)
        self.infra_renderer = InfrastructureRenderer(self.screen)
        self.outdoor_renderer = OutdoorRenderer(self.screen)
        self.wiring_renderer = ImprovedWiringRenderer()
        
        # Generate wall-following wiring
        self.wiring_generator = WiringPathGenerator(self.rooms, DOOR_CONNECTIONS)
        
        # UI elements
        self.setup_ui_elements()
        
        # Log startup
        self.event_log.add_event("system", f"Smart Home initialized - {len(self.rooms)} rooms", "info")
        
    def setup_simulation(self):
        """Initialize all simulation components"""
        print("Initializing Smart Home Simulation...")
        
        # Create rooms
        self.rooms = []
        for name, (x, y, w, h) in HOUSE_LAYOUT.items():
            self.rooms.append(Room(name, x, y, w, h))
        
        print(f"✓ Created {len(self.rooms)} rooms")
        
        # Create sensors
        self.sensors = []
        sensor_id = 1
        
        for room in self.rooms:
            # Skip bathrooms and technical room for some sensors
            if "Bathroom" in room.name or room.name == "Technical Room":
                continue
            
            # Add sensors to room
            self.sensors.append(TemperatureSensor(f"TEMP-{sensor_id:03d}", room))
            sensor_id += 1
            self.sensors.append(LightSensor(f"LIGHT-{sensor_id:03d}", room))
            sensor_id += 1
            self.sensors.append(MotionSensor(f"MOTION-{sensor_id:03d}", room))
            sensor_id += 1
            self.sensors.append(HumiditySensor(f"HUMID-{sensor_id:03d}", room))
            sensor_id += 1
            
            if room.name in ["Living Room", "Kitchen", "Master Bedroom"]:
                self.sensors.append(CO2Sensor(f"CO2-{sensor_id:03d}", room))
                sensor_id += 1
        
        print(f"✓ Created {len(self.sensors)} sensors")
        
        # Create actuators
        self.actuators = []
        actuator_id = 1
        
        for room in self.rooms:
            room.sensors = [s for s in self.sensors if s.room == room]
            
            # Lights for all rooms
            self.actuators.append(LightActuator(f"LIGHT-ACT-{actuator_id:03d}", 
                                               room, "LED"))
            actuator_id += 1
            
            # Fans for bedrooms, living areas
            if ("Bedroom" in room.name or room.name in ["Living Room", "Salon", 
                                                        "Dining Room"]):
                self.actuators.append(FanActuator(f"FAN-{actuator_id:03d}", room))
                actuator_id += 1
            
            # Heaters for bedrooms and living room
            if "Bedroom" in room.name or room.name == "Living Room":
                self.actuators.append(HeaterActuator(f"HEAT-{actuator_id:03d}", room))
                actuator_id += 1
            
            # Kitchen appliances
            if room.name == "Kitchen":
                self.actuators.append(RefrigeratorActuator(f"FRIDGE-{actuator_id:03d}", room))
                actuator_id += 1
                self.actuators.append(DishwasherActuator(f"DISH-{actuator_id:03d}", room))
                actuator_id += 1
                self.event_log.add_event("system", f"Kitchen appliances added to {room.name}", "info")
            
            # Laundry appliances
            if room.name == "Laundry Room":
                self.actuators.append(WashingMachineActuator(f"WASHER-{actuator_id:03d}", room))
                actuator_id += 1
                self.actuators.append(DryerActuator(f"DRYER-{actuator_id:03d}", room))
                actuator_id += 1
                self.event_log.add_event("system", f"Laundry appliances added to {room.name}", "info")
            
            room.actuators = [a for a in self.actuators if a.room == room]
        
        print(f"✓ Created {len(self.actuators)} actuators")
        
        # Create energy system
        self.energy_system = EnergySystem()
        print(f"✓ Energy system initialized (Solar: {SOLAR_PANEL_CAPACITY}W, "
              f"Wind: {WIND_TURBINE_CAPACITY}W)")
        
        # Create water system
        self.water_system = WaterSystem()
        print(f"✓ Water system initialized (Tank: {WATER_TANK_CAPACITY}L)")
        
        # Create IoT network
        self.network = IoTNetwork()
        self._setup_network()
        print(f"✓ IoT network created ({len(self.network.nodes)} nodes)")
        
        # Create power grid
        tech_room = next(r for r in self.rooms if r.name == "Technical Room")
        self.power_grid = PowerGrid(tech_room)
        self._setup_power_grid()
        print(f"✓ Power grid configured")
        
        # Create water network
        self.water_network = WaterNetwork((1200, 250))
        self._setup_water_network()
        print(f"✓ Water network configured")
        
        # Create controller (will set event_log reference later)
        self.controller = SmartHomeController(
            self.rooms, self.sensors, self.actuators,
            self.energy_system, self.water_system, self.network
        )
        print(f"✓ Central controller initialized")
        print("\nSimulation ready!\n")
    
    def _setup_network(self):
        """Setup IoT network topology"""
        # Create hub node in technical room
        tech_room = next(r for r in self.rooms if r.name == "Technical Room")
        hub_node = NetworkNode("HUB-001", "hub", tech_room, tech_room.get_center())
        self.network.add_node(hub_node)
        
        # Create sensor nodes
        for sensor in self.sensors:
            cx, cy = sensor.room.get_center()
            # Offset sensors around room
            offset_x = (hash(sensor.sensor_id) % 40) - 20
            offset_y = (hash(sensor.sensor_id) % 30) - 15
            node = NetworkNode(sensor.sensor_id, "sensor", sensor.room, 
                             (cx + offset_x, cy + offset_y))
            self.network.add_node(node)
        
        # Create actuator nodes
        for actuator in self.actuators:
            cx, cy = actuator.room.get_center()
            offset_x = (hash(actuator.actuator_id) % 40) - 20
            offset_y = (hash(actuator.actuator_id) % 30) - 15
            node = NetworkNode(actuator.actuator_id, "actuator", actuator.room,
                             (cx + offset_x, cy + offset_y))
            self.network.add_node(node)
        
        # Connect all nodes to hub
        self.network.auto_connect_to_hub()
    
    def _setup_power_grid(self):
        """Setup electrical wiring"""
        tech_room = next(r for r in self.rooms if r.name == "Technical Room")
        hub_pos = tech_room.get_center()
        
        # Create circuits for different zones
        self.power_grid.add_circuit("Bedrooms", 
            ["Master Bedroom", "Bedroom 2", "Bedroom 3", "Bedroom 4"])
        self.power_grid.add_circuit("Common Areas", 
            ["Living Room", "Dining Room", "Kitchen", "Salon"])
        self.power_grid.add_circuit("Utilities", 
            ["Laundry Room", "Storage", "Garage"])
        
        # Add power lines to major rooms
        for room in self.rooms:
            if room.name not in ["Master Closet"]:  # Skip some small rooms
                room_center = room.get_center()
                self.power_grid.add_power_line(hub_pos, room_center)
    
    def _setup_water_network(self):
        """Setup water piping"""
        tank_pos = self.water_network.tank_position
        
        # Main water rooms
        water_rooms = ["Kitchen", "Laundry Room", "Master Bathroom", 
                      "Bathroom 2", "Bathroom 3", "Bathroom 4", "Guest Bathroom"]
        
        for room_name in water_rooms:
            room = next((r for r in self.rooms if r.name == room_name), None)
            if room:
                self.water_network.add_pipe(tank_pos, room.get_center())
    
    def setup_ui_elements(self):
        """Setup UI buttons and controls"""
        panel_x = 50
        panel_y = 750
        
        # Start/Pause button
        self.start_button = pygame.Rect(panel_x, panel_y, 120, 40)
        
        # Next step button
        self.next_button = pygame.Rect(panel_x + 140, panel_y, 120, 40)
        
        # People controls
        self.people_plus = pygame.Rect(panel_x + 280, panel_y, 40, 40)
        self.people_minus = pygame.Rect(panel_x + 330, panel_y, 40, 40)
        
        # Speed slider
        self.speed_slider_rect = pygame.Rect(panel_x + 400, panel_y + 10, 200, 20)
        self.speed_slider_handle = pygame.Rect(panel_x + 500, panel_y + 5, 10, 30)
        
        # Toggle wiring button
        self.wiring_button = pygame.Rect(panel_x + 620, panel_y, 150, 40)
    
    def get_season(self) -> Season:
        """Determine current season"""
        month = self.current_time.month
        if month in [3, 4, 5]:
            return Season.SPRING
        elif month in [6, 7, 8]:
            return Season.SUMMER
        elif month in [9, 10, 11]:
            return Season.AUTUMN
        else:
            return Season.WINTER
    
    def advance_simulation(self):
        """Advance simulation by one time step"""
        self.cycle_count += 1
        self.current_time += timedelta(minutes=MINUTES_PER_CYCLE)
        
        hour = self.current_time.hour + self.current_time.minute / 60
        season = self.get_season()
        day_of_week = self.current_time.weekday()
        
        # Update weather system
        self.weather.update(hour, season)
        
        # Update realistic occupancy
        self.num_people = self.occupancy.get_occupancy(hour, day_of_week)
        active_rooms = self.occupancy.get_active_rooms(hour, self.num_people)
        
        # Log cycle advancement every hour with weather
        if self.cycle_count % 4 == 0:  # Every hour (4 cycles of 15 min each)
            self.event_log.add_event("system", 
                f"Cycle {self.cycle_count} | {self.current_time.strftime('%H:%M')} | " +
                f"{self.num_people} home | {self.weather.get_condition_emoji()} {self.weather.current_condition}",
                "info")
        
        # Check for emergencies
        emergency = self.emergency_mgr.check_for_emergency(self.cycle_count)
        if emergency and self.emergency_mgr.emergency_start_cycle == self.cycle_count:
            self.event_log.log_critical(f"EMERGENCY: {emergency.replace('_', ' ').title()}!")
        
        # Security system
        security_armed = self.security.should_arm(hour, self.num_people)
        if security_armed != self.security.armed:
            self.security.armed = security_armed
            status = "ARMED" if security_armed else "DISARMED"
            self.event_log.add_event("system", f"Security system {status}", "info")
        
        # Appliance scheduling
        cooking = self.scheduler.should_cook(hour, self.num_people)
        if cooking:
            for appliance, should_run in cooking.items():
                if should_run:
                    self.event_log.add_event("control", 
                        f"Kitchen: {appliance.title()} activated - Meal time", "info")
        
        # Dishwasher scheduling
        if self.scheduler.should_run_dishwasher(hour, self.cycle_count):
            self.event_log.add_event("control",
                "Kitchen: Dishwasher cycle started (night mode)", "info")
        
        # Laundry scheduling
        laundry = self.scheduler.should_run_laundry(hour, day_of_week, self.cycle_count)
        if laundry["washer"]:
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week]
            self.event_log.add_event("control",
                f"Laundry Room: Washing machine started ({day_name})", "info")
        
        # Entertainment scheduling
        entertainment = self.scheduler.get_entertainment_usage(hour, self.num_people)
        
        # Run controller with realistic behaviors
        self.controller.process_cycle(
            self.current_time.hour,
            season,
            self.num_people,
            verbose=False  # Don't print to console in auto-run
        )
        
        # Log energy events
        battery_pct = self.energy_system.get_battery_percentage()
        if battery_pct < 20:
            self.event_log.log_warning(f"Battery low: {battery_pct:.1f}%")
        elif battery_pct > 95:
            if self.cycle_count % 10 == 0:
                self.event_log.log_energy_event("Battery", f"Fully charged: {battery_pct:.1f}%")
        
        # Apply weather effects to energy generation
        solar_generated = self.energy_system.current_solar
        wind_generated = self.energy_system.current_wind
        
        # Weather reduces solar (clouds block sun)
        weather_factor = self.weather.get_solar_reduction()
        solar_generated *= weather_factor
        
        # Weather affects wind
        wind_generated *= self.weather.wind_factor
        
        # Calculate cost savings
        consumed_this_cycle = sum(a.get_consumption() for room in self.rooms for a in room.actuators) / 4  # 15min = 1/4 hour
        savings = self.cost_tracker.calculate_savings(
            solar_generated / 4, wind_generated / 4, consumed_this_cycle, hour)
        
        # Log solar/wind generation changes with weather
        if self.cycle_count % 8 == 0:  # Every 2 hours
            wind_speed = getattr(self.energy_system, 'current_wind_speed', 0)
            weather_note = f"({self.weather.current_condition}, {self.weather.cloud_cover:.0f}% clouds)"
            self.event_log.log_energy_event("Generation",
                f"Solar: {solar_generated:.0f}W {weather_note}, Wind: {wind_generated:.0f}W ({wind_speed:.1f} m/s)")
        
        # Log cost savings periodically
        if self.cycle_count % 24 == 0:  # Every 6 hours
            savings_pct = (self.cost_tracker.total_saved / self.cost_tracker.total_would_have_cost * 100) if self.cost_tracker.total_would_have_cost > 0 else 0
            self.event_log.log_energy_event("Savings",
                f"Total saved: ₪{self.cost_tracker.total_saved:.2f} ({savings_pct:.1f}% self-sufficient)")
        
        # Log water events
        water_pct = self.water_system.get_level_percentage()
        if water_pct < 30:
            self.event_log.log_warning(f"Water tank low: {water_pct:.1f}%")
        
        # Update network animations
        self.network.update_transmissions(0.016)  # ~1 frame at 60fps
        
        # Update power grid
        room_loads = {}
        for room in self.rooms:
            room_loads[room.name] = sum(a.get_consumption() for a in room.actuators)
        self.power_grid.update_loads(room_loads)
        
        # Log high power consumption
        total_consumption = sum(room_loads.values())
        if total_consumption > 4000:
            self.event_log.log_energy_event("Consumption", 
                f"High load: {total_consumption:.0f}W")
        
        # Update water network
        self.water_network.update_flow(self.water_system.current_usage_rate)
    
    def handle_events(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                # Start/Pause button
                if self.start_button.collidepoint(pos):
                    self.auto_run = not self.auto_run
                    if self.auto_run:
                        self.last_cycle_time = pygame.time.get_ticks() / 1000
                
                # Next step button
                elif self.next_button.collidepoint(pos) and not self.auto_run:
                    self.advance_simulation()
                
                # People controls
                elif self.people_plus.collidepoint(pos):
                    self.num_people = min(10, self.num_people + 1)
                elif self.people_minus.collidepoint(pos):
                    self.num_people = max(1, self.num_people - 1)
                
                # Wiring toggle
                elif self.wiring_button.collidepoint(pos):
                    self.show_wiring = not self.show_wiring
            
            elif event.type == pygame.KEYDOWN:
                # Event log controls
                if event.key == pygame.K_UP:
                    self.event_log.scroll_up()
                elif event.key == pygame.K_DOWN:
                    self.event_log.scroll_down()
                elif event.key == pygame.K_c:
                    self.event_log.clear()
                    self.event_log.add_event("system", "Event log cleared", "info")
            
            elif event.type == pygame.MOUSEMOTION:
                # Handle speed slider
                if pygame.mouse.get_pressed()[0]:  # Left button held
                    pos = pygame.mouse.get_pos()
                    if self.speed_slider_rect.collidepoint(pos):
                        # Update slider position
                        relative_x = pos[0] - self.speed_slider_rect.x
                        slider_pos = relative_x / self.speed_slider_rect.width
                        slider_pos = max(0, min(1, slider_pos))
                        
                        # Update speed
                        if slider_pos < 0.25:
                            self.auto_run_speed = "Slow"
                        elif slider_pos < 0.5:
                            self.auto_run_speed = "Normal"
                        elif slider_pos < 0.75:
                            self.auto_run_speed = "Fast"
                        else:
                            self.auto_run_speed = "Ultra"
    
    def update(self):
        """Update simulation state"""
        current_time = pygame.time.get_ticks() / 1000
        
        # Auto-run logic
        if self.auto_run:
            cycle_delay = AUTO_RUN_SPEEDS[self.auto_run_speed]
            if current_time - self.last_cycle_time >= cycle_delay:
                self.advance_simulation()
                self.last_cycle_time = current_time
        
        # Update animations
        self.animation_time += 0.016  # Assuming ~60 FPS
        self.turbine_angle = (self.turbine_angle + 
                             self.energy_system.current_wind / 1000) % 360
    
    def draw(self):
        """Render everything"""
        self.screen.fill(WHITE)
        
        # Draw prominent date/time display at top
        self.draw_datetime_header()
        
        # Draw floor plan
        self.floor_plan_renderer.draw_all_rooms(self.rooms)
        self.floor_plan_renderer.draw_all_doors(self.rooms, DOOR_CONNECTIONS)
        
        # Draw infrastructure if enabled
        if self.show_wiring:
            # Draw wall-following wiring from Technical Room to all rooms
            tech_room = next((r for r in self.rooms if r.name == "Technical Room"), None)
            if tech_room:
                tech_center = tech_room.get_center()
                
                # Draw power lines (yellow/orange) following walls
                for room in self.rooms:
                    if room.name != "Technical Room":
                        wire_path = self.wiring_renderer.create_wall_following_wire(
                            tech_room, room, "power", offset=0)
                        self.infra_renderer.draw_wall_following_wire(
                            wire_path, "power", True, True, self.animation_time)
                
                # Draw data network (green) following walls
                for room in self.rooms:
                    if room.name != "Technical Room":
                        wire_path = self.wiring_renderer.create_wall_following_wire(
                            tech_room, room, "data", offset=8)
                        self.infra_renderer.draw_wall_following_wire(
                            wire_path, "data", True, True, self.animation_time)
                
                # Draw Technical Room hub
                pygame.draw.rect(self.screen, DARK_GRAY, 
                               (tech_center[0] - 20, tech_center[1] - 20, 40, 40))
                pygame.draw.rect(self.screen, BRIGHT_YELLOW, 
                               (tech_center[0] - 20, tech_center[1] - 20, 40, 40), 3)
                hub_label = self.font_small.render("HUB", True, WHITE)
                self.screen.blit(hub_label, (tech_center[0] - 15, tech_center[1] - 8))
        
        # Draw sensors with clear icons (always visible)
        time_hour = self.current_time.hour + self.current_time.minute / 60
        season = self.get_season()
        
        for room in self.rooms:
            cx, cy = room.get_center()
            
            # Draw sensors in a row at top of room
            sensor_offset = -40
            sensor_y = cy - 30
            for sensor in room.sensors:
                pos = (cx + sensor_offset, sensor_y)
                # Get sensor value
                value = sensor.read(time_hour, season, self.num_people)
                self.infra_renderer.draw_sensor_icon(
                    pos, sensor.sensor_type, value, True)
                sensor_offset += 30
            
            # Draw actuator states at bottom
            if self.show_wiring:
                actuator_offset = -30
                actuator_y = cy + 50
                for actuator in room.actuators:
                    pos = (cx + actuator_offset, actuator_y)
                    self.infra_renderer.draw_actuator_icon(
                        pos, actuator.actuator_type, actuator.state)
                    actuator_offset += 25
        
        # Draw outdoor infrastructure (below header)
        self.outdoor_renderer.draw_solar_panels(
            (400, 600), 
            self.energy_system.current_solar,
            self.energy_system.solar_capacity)
        
        self.outdoor_renderer.draw_wind_turbine(
            (1300, 200),
            self.energy_system.current_wind,
            self.energy_system.wind_capacity,
            self.turbine_angle)
        
        # Draw UI
        self.draw_ui()
        
        # Draw event log panel
        log_x = SCREEN_WIDTH - LOG_PANEL_WIDTH - 20
        log_y = 100
        self.log_renderer.draw_log_panel(self.event_log, log_x, log_y)
        
    def draw_ui(self):
        """Draw user interface"""
        panel_y = 750
        
        # Title
        title = self.font_title.render("SMART HOME CONTROL CENTER", True, BLACK)
        self.screen.blit(title, (50, 700))
        
        # Start/Pause button
        btn_color = RED if self.auto_run else GREEN
        pygame.draw.rect(self.screen, btn_color, self.start_button)
        pygame.draw.rect(self.screen, BLACK, self.start_button, 2)
        btn_text = "⏸ Pause" if self.auto_run else "▶ Start"
        text = self.font_medium.render(btn_text, True, WHITE if self.auto_run else BLACK)
        text_rect = text.get_rect(center=self.start_button.center)
        self.screen.blit(text, text_rect)
        
        # Next step button
        pygame.draw.rect(self.screen, BLUE if not self.auto_run else GRAY, 
                        self.next_button)
        pygame.draw.rect(self.screen, BLACK, self.next_button, 2)
        text = self.font_medium.render("Next Step", True, WHITE)
        text_rect = text.get_rect(center=self.next_button.center)
        self.screen.blit(text, text_rect)
        
        # People controls
        pygame.draw.rect(self.screen, GREEN, self.people_plus)
        pygame.draw.rect(self.screen, RED, self.people_minus)
        pygame.draw.rect(self.screen, BLACK, self.people_plus, 2)
        pygame.draw.rect(self.screen, BLACK, self.people_minus, 2)
        
        plus_text = self.font_large.render("+", True, BLACK)
        minus_text = self.font_large.render("-", True, BLACK)
        self.screen.blit(plus_text, (self.people_plus.centerx - 8, 
                                     self.people_plus.centery - 12))
        self.screen.blit(minus_text, (self.people_minus.centerx - 8, 
                                      self.people_minus.centery - 12))
        
        people_text = self.font_medium.render(f"👥 {self.num_people}", True, BLACK)
        self.screen.blit(people_text, (self.people_plus.x - 70, panel_y + 10))
        
        # Speed slider
        pygame.draw.rect(self.screen, GRAY, self.speed_slider_rect)
        pygame.draw.rect(self.screen, BLACK, self.speed_slider_rect, 2)
        
        # Speed handle position
        speed_values = list(AUTO_RUN_SPEEDS.keys())
        speed_index = speed_values.index(self.auto_run_speed)
        handle_x = (self.speed_slider_rect.x + 
                   (speed_index / (len(speed_values) - 1)) * 
                   self.speed_slider_rect.width)
        self.speed_slider_handle.centerx = int(handle_x)
        
        pygame.draw.rect(self.screen, BLUE, self.speed_slider_handle)
        pygame.draw.rect(self.screen, BLACK, self.speed_slider_handle, 2)
        
        speed_label = self.font_small.render(f"Speed: {self.auto_run_speed}", 
                                            True, BLACK)
        self.screen.blit(speed_label, (self.speed_slider_rect.x, panel_y - 15))
        
        # Wiring toggle
        pygame.draw.rect(self.screen, GREEN if self.show_wiring else GRAY, 
                        self.wiring_button)
        pygame.draw.rect(self.screen, BLACK, self.wiring_button, 2)
        wiring_text = self.font_medium.render("🔌 Wiring: " + 
                                             ("ON" if self.show_wiring else "OFF"),
                                             True, BLACK)
        text_rect = wiring_text.get_rect(center=self.wiring_button.center)
        self.screen.blit(wiring_text, text_rect)
        
        # Status panel
        self.draw_status_panel()
    
    def draw_datetime_header(self):
        """Draw prominent date/time header at top of screen"""
        # Background bar
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 45)
        pygame.draw.rect(self.screen, DARK_BLUE, header_rect)
        
        # Date and time
        date_str = self.current_time.strftime("%A, %B %d, %Y")
        time_str = self.current_time.strftime("%H:%M")
        season = self.get_season()
        
        # Large time display
        time_surface = self.font_title.render(time_str, True, BRIGHT_YELLOW)
        self.screen.blit(time_surface, (50, 8))
        
        # Date and location
        date_surface = self.font_medium.render(
            f"{date_str} | {season.value} | Ramallah, Palestine 🇵🇸", 
            True, WHITE)
        self.screen.blit(date_surface, (200, 12))
        
        # Wind speed display
        wind_speed = getattr(self.energy_system, 'current_wind_speed', 0)
        wind_text = f"🌬️ {wind_speed:.1f} m/s"
        wind_surface = self.font_medium.render(wind_text, True, CYAN)
        self.screen.blit(wind_surface, (SCREEN_WIDTH - 200, 12))
    
    def draw_status_panel(self):
        """Draw status information panel"""
        x = 800
        y = 700
        
        # Get wind speed for display
        wind_speed = getattr(self.energy_system, 'current_wind_speed', 0)
        
        # Weather effects
        weather_emoji = self.weather.get_condition_emoji()
        weather_reduction = (1 - self.weather.get_solar_reduction()) * 100
        
        # Security status
        security_icon = "🔒" if self.security.armed else "🔓"
        
        info_lines = [
            f"🔋 Battery: {self.energy_system.get_battery_percentage():.1f}% "
                f"({self.energy_system.get_battery_status()})",
            f"⚡ Solar: {self.energy_system.current_solar:.0f}W | "
                f"Wind: {self.energy_system.current_wind:.0f}W ({wind_speed:.1f} m/s)",
            f"{weather_emoji} Weather: {self.weather.current_condition} "
                f"(solar -{weather_reduction:.0f}%)",
            f"📊 Consumption: {self.energy_system.total_consumption:.0f}W | "
                f"Saved: ₪{self.cost_tracker.total_saved:.2f}",
            f"💧 Water: {self.water_system.get_level_percentage():.1f}% "
                f"({weather_emoji if self.weather.is_raining else '☀️'})",
            f"{security_icon} Security: {'Armed' if self.security.armed else 'Disarmed'} | "
                f"📡 {len(self.network.active_transmissions)} packets",
            f"🏠 Cycle: {self.cycle_count} | {self.num_people} home"
        ]
        
        for i, line in enumerate(info_lines):
            text = self.font_small.render(line, True, BLACK)
            self.screen.blit(text, (x, y + i * 20))
    
    def run(self):
        """Main application loop"""
        print("\n" + "="*80)
        print("SMART HOME SIMULATION STARTED")
        print("="*80)
        print("Controls:")
        print("  - Click 'Start' to begin auto-run mode")
        print("  - Adjust speed slider for faster/slower simulation")
        print("  - Click 'Next Step' for manual step-by-step")
        print("  - Use +/- to adjust number of occupants")
        print("  - Toggle 'Wiring' to show/hide infrastructure")
        print("="*80 + "\n")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        
        # Print final statistics
        print("\n" + "="*80)
        print("SIMULATION ENDED")
        print("="*80)
        print(f"Total cycles: {self.cycle_count}")
        print(f"Total runtime: {(self.current_time - datetime(2024, 6, 15, 8, 0)).total_seconds() / 3600:.1f} hours simulated")
        stats = self.controller.get_system_summary()
        print(f"\nEnergy Statistics:")
        print(f"  Solar generated: {stats['energy']['solar_generated']:.1f} Wh")
        print(f"  Wind generated: {stats['energy']['wind_generated']:.1f} Wh")
        print(f"  Total consumed: {stats['energy']['total_consumed']:.1f} Wh")
        print(f"  Self-sufficiency: {stats['energy']['self_sufficiency']:.1f}%")
        print(f"\nWater Statistics:")
        print(f"  Total collected: {stats['water']['total_collected']:.1f} L")
        print(f"  Total consumed: {stats['water']['total_consumed']:.1f} L")
        print("="*80)

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    app = SmartHomeApp()
    app.run()

if __name__ == "__main__":
    main()
