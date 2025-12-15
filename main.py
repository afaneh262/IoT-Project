"""
ADVANCED SMART HOME IoT SIMULATION
===================================

A realistic, modular simulation of a self-sustainable smart home with:
- Modern CustomTkinter UI with dark/light themes
- Detailed floor plan with accurate room layout
- Real-time data visualization
- IoT sensors and smart actuators
- Renewable energy system (solar + wind)
- Rainwater collection system
- Interactive controls and monitoring

INSTALLATION:
    pip install -r requirements.txt

HOW TO RUN:
    python main.py

FEATURES:
    - Modern, responsive UI with dark/light theme toggle
    - Real-time monitoring and control
    - Interactive room selection
    - Detailed statistics panels
    - Event log with filtering
    - Auto-run mode with speed control
"""

import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from datetime import datetime, timedelta
from typing import List, Dict
import threading
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Matplotlib for charts
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

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
from event_log import EventLog
from realistic_behaviors import (OccupancyPattern, Weather, ApplianceScheduler,
                                SecuritySystem, CostTracker, EmergencyManager)
from database import DatabaseManager
from data_formats import DataFormat, MixedFormatManager, JSONSerializer, XMLSerializer, format_to_string

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

# ============================================================================
# MODERN SMART HOME APPLICATION
# ============================================================================

class SmartHomeModernApp(ctk.CTk):
    """Modern Smart Home Application with CustomTkinter"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("🏠 Advanced Smart Home IoT Simulation")
        self.geometry("1600x900")
        
        # Simulation state
        self.running = True
        self.auto_run = False
        self.auto_run_speed = "Normal"
        self.show_wiring = True
        self.selected_room = None
        
        # Time management
        self.current_time = datetime(2024, 6, 15, 8, 0)
        self.num_people = 4
        self.cycle_count = 0
        
        # Event log system
        self.event_log = EventLog()
        
        # Database connection
        self.db = DatabaseManager()
        self.data_storage_enabled = os.getenv('DATA_STORAGE_ENABLED', 'true').lower() == 'true'
        
        # Data format manager for sensor-to-server communication
        # Get format from environment or default to MIXED
        format_mode = os.getenv('DATA_FORMAT_MODE', 'mixed').lower()
        if format_mode == 'json':
            self.data_format = DataFormat.JSON
            self.format_manager = JSONSerializer()
        elif format_mode == 'xml':
            self.data_format = DataFormat.XML
            self.format_manager = XMLSerializer()
        else:  # mixed
            self.data_format = DataFormat.MIXED
            self.format_manager = MixedFormatManager(json_probability=0.5)
        
        # Data size tracking for growth chart
        self.data_size_history = {
            'time': [],
            'datetime': [],
            'json_size': [],
            'xml_size': [],
            'total_size': [],
            'message_count': []
        }
        self.cumulative_json_size = 0
        self.cumulative_xml_size = 0
        self.cumulative_message_count = 0
        
        # Energy data tracking for charts (keep last 100 data points)
        self.energy_history = {
            'time': [],
            'datetime': [],  # Store actual datetime objects
            'solar': [],
            'wind': [],
            'total_generation': [],
            'consumption': []
        }
        self.max_history_points = 100
        
        # Realistic behavior systems
        self.occupancy = OccupancyPattern(self.num_people)
        self.weather = Weather()
        self.scheduler = ApplianceScheduler()
        self.security = SecuritySystem()
        self.cost_tracker = CostTracker()
        self.emergency_mgr = EmergencyManager()
        
        # Initialize simulation components
        self.setup_simulation()
        
        # Create UI
        self.create_ui()
        
        # Auto-run thread
        self.auto_run_thread = None
        
        # Log startup
        self.event_log.add_event("system", f"Smart Home initialized - {len(self.rooms)} rooms", "info")
        self.update_event_log()
        
        # Store initial event in database
        if self.db.is_connected():
            self.db.store_event("system", f"Smart Home initialized - {len(self.rooms)} rooms", "info", 
                              simulation_time=self.current_time)
        
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
            if "Bathroom" in room.name or room.name == "Technical Room":
                continue
            
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
            
            self.actuators.append(LightActuator(f"LIGHT-ACT-{actuator_id:03d}", room, "LED"))
            actuator_id += 1
            
            if ("Bedroom" in room.name or room.name in ["Living Room", "Salon", "Dining Room"]):
                self.actuators.append(FanActuator(f"FAN-{actuator_id:03d}", room))
                actuator_id += 1
            
            if "Bedroom" in room.name or room.name == "Living Room":
                self.actuators.append(HeaterActuator(f"HEAT-{actuator_id:03d}", room))
                actuator_id += 1
            
            if room.name == "Kitchen":
                self.actuators.append(RefrigeratorActuator(f"FRIDGE-{actuator_id:03d}", room))
                actuator_id += 1
                self.actuators.append(DishwasherActuator(f"DISH-{actuator_id:03d}", room))
                actuator_id += 1
            
            if room.name == "Laundry Room":
                self.actuators.append(WashingMachineActuator(f"WASHER-{actuator_id:03d}", room))
                actuator_id += 1
                self.actuators.append(DryerActuator(f"DRYER-{actuator_id:03d}", room))
                actuator_id += 1
            
            room.actuators = [a for a in self.actuators if a.room == room]
        
        print(f"✓ Created {len(self.actuators)} actuators")
        
        # Create systems
        self.energy_system = EnergySystem()
        self.water_system = WaterSystem()
        self.network = IoTNetwork()
        self._setup_network()
        
        tech_room = next(r for r in self.rooms if r.name == "Technical Room")
        self.power_grid = PowerGrid(tech_room)
        self.water_network = WaterNetwork((1200, 250))
        
        self.controller = SmartHomeController(
            self.rooms, self.sensors, self.actuators,
            self.energy_system, self.water_system, self.network
        )
        
        print(f"✓ Simulation ready!\n")
    
    def _setup_network(self):
        """Setup IoT network topology"""
        tech_room = next(r for r in self.rooms if r.name == "Technical Room")
        hub_node = NetworkNode("HUB-001", "hub", tech_room, tech_room.get_center())
        self.network.add_node(hub_node)
        
        for sensor in self.sensors:
            cx, cy = sensor.room.get_center()
            offset_x = (hash(sensor.sensor_id) % 40) - 20
            offset_y = (hash(sensor.sensor_id) % 30) - 15
            node = NetworkNode(sensor.sensor_id, "sensor", sensor.room, (cx + offset_x, cy + offset_y))
            self.network.add_node(node)
        
        for actuator in self.actuators:
            cx, cy = actuator.room.get_center()
            offset_x = (hash(actuator.actuator_id) % 40) - 20
            offset_y = (hash(actuator.actuator_id) % 30) - 15
            node = NetworkNode(actuator.actuator_id, "actuator", actuator.room, (cx + offset_x, cy + offset_y))
            self.network.add_node(node)
        
        self.network.auto_connect_to_hub()
    
    def create_ui(self):
        """Create the modern UI layout"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left sidebar - Controls
        self.create_sidebar()
        
        # Main content area
        self.create_main_content()
        
        # Right sidebar - Statistics
        self.create_stats_panel()
    
    def create_sidebar(self):
        """Create left sidebar with controls"""
        sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_rowconfigure(10, weight=1)
        
        # Logo/Title
        title_label = ctk.CTkLabel(sidebar, text="🏠 Smart Home", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        subtitle = ctk.CTkLabel(sidebar, text="IoT Simulation", 
                               font=ctk.CTkFont(size=14))
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Date/Time Display
        self.datetime_label = ctk.CTkLabel(sidebar, text="", 
                                          font=ctk.CTkFont(size=12))
        self.datetime_label.grid(row=2, column=0, padx=20, pady=10)
        
        # Start Date Selection
        date_frame = ctk.CTkFrame(sidebar)
        date_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(date_frame, text="📅 Start Date:", 
                    font=ctk.CTkFont(size=11)).pack(pady=(5, 2))
        
        date_input_frame = ctk.CTkFrame(date_frame)
        date_input_frame.pack(pady=5)
        
        # Year
        self.year_var = tk.StringVar(value="2024")
        year_entry = ctk.CTkEntry(date_input_frame, textvariable=self.year_var, width=60)
        year_entry.pack(side="left", padx=2)
        
        ctk.CTkLabel(date_input_frame, text="/").pack(side="left")
        
        # Month
        self.month_var = tk.StringVar(value="06")
        month_entry = ctk.CTkEntry(date_input_frame, textvariable=self.month_var, width=40)
        month_entry.pack(side="left", padx=2)
        
        ctk.CTkLabel(date_input_frame, text="/").pack(side="left")
        
        # Day
        self.day_var = tk.StringVar(value="15")
        day_entry = ctk.CTkEntry(date_input_frame, textvariable=self.day_var, width=40)
        day_entry.pack(side="left", padx=2)
        
        # Set Date Button
        set_date_btn = ctk.CTkButton(date_frame, text="Set Date", 
                                     command=self.set_start_date,
                                     height=25, font=ctk.CTkFont(size=10))
        set_date_btn.pack(pady=5)
        
        # Control Buttons
        self.start_button = ctk.CTkButton(sidebar, text="▶ Start Auto-Run",
                                         command=self.toggle_auto_run,
                                         fg_color="green", hover_color="darkgreen")
        self.start_button.grid(row=4, column=0, padx=20, pady=10)
        
        self.step_button = ctk.CTkButton(sidebar, text="⏭ Next Step",
                                        command=self.advance_simulation)
        self.step_button.grid(row=5, column=0, padx=20, pady=10)
        
        # Speed Control
        speed_label = ctk.CTkLabel(sidebar, text="Simulation Speed:",
                                  font=ctk.CTkFont(size=12))
        speed_label.grid(row=6, column=0, padx=20, pady=(20, 5))
        
        self.speed_var = tk.StringVar(value="Normal")
        speed_menu = ctk.CTkOptionMenu(sidebar, values=["Slow", "Normal", "Fast", "Ultra"],
                                      variable=self.speed_var,
                                      command=self.change_speed)
        speed_menu.grid(row=7, column=0, padx=20, pady=5)
        
        # Occupancy Control
        occupancy_label = ctk.CTkLabel(sidebar, text="👥 Occupants:",
                                      font=ctk.CTkFont(size=12))
        occupancy_label.grid(row=8, column=0, padx=20, pady=(20, 5))
        
        occupancy_frame = ctk.CTkFrame(sidebar)
        occupancy_frame.grid(row=9, column=0, padx=20, pady=5)
        
        minus_btn = ctk.CTkButton(occupancy_frame, text="-", width=40,
                                 command=lambda: self.adjust_occupants(-1))
        minus_btn.grid(row=0, column=0, padx=5)
        
        self.occupants_label = ctk.CTkLabel(occupancy_frame, text=str(self.num_people),
                                           font=ctk.CTkFont(size=16, weight="bold"))
        self.occupants_label.grid(row=0, column=1, padx=10)
        
        plus_btn = ctk.CTkButton(occupancy_frame, text="+", width=40,
                                command=lambda: self.adjust_occupants(1))
        plus_btn.grid(row=0, column=2, padx=5)
        
        # Theme Toggle
        self.theme_switch = ctk.CTkSwitch(sidebar, text="🌙 Dark Mode",
                                         command=self.toggle_theme)
        self.theme_switch.grid(row=10, column=0, padx=20, pady=(20, 10))
        self.theme_switch.select()
        
        # Wiring Toggle
        self.wiring_switch = ctk.CTkSwitch(sidebar, text="🔌 Show Wiring",
                                          command=self.toggle_wiring)
        self.wiring_switch.grid(row=11, column=0, padx=20, pady=10)
        self.wiring_switch.select()
        
        # Data Format Selection
        format_label = ctk.CTkLabel(sidebar, text="📡 Data Format:",
                                   font=ctk.CTkFont(size=12))
        format_label.grid(row=12, column=0, padx=20, pady=(20, 5))
        
        self.format_var = tk.StringVar(value=self.data_format.value.upper())
        format_menu = ctk.CTkOptionMenu(sidebar, values=["JSON", "XML", "MIXED"],
                                       variable=self.format_var,
                                       command=self.change_data_format)
        format_menu.grid(row=13, column=0, padx=20, pady=5)
        
        # Statistics Summary
        stats_frame = ctk.CTkFrame(sidebar)
        stats_frame.grid(row=14, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(stats_frame, text="Quick Stats", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        self.quick_stats_label = ctk.CTkLabel(stats_frame, text="", 
                                             font=ctk.CTkFont(size=10),
                                             justify="left")
        self.quick_stats_label.pack(pady=5, padx=10)
    
    def create_main_content(self):
        """Create main content area with tabs"""
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Tabview
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create tabs
        self.tabview.add("🏠 Floor Plan")
        self.tabview.add("📊 Dashboard")
        self.tabview.add("📈 Energy Analytics")
        self.tabview.add("📊 Data Size Analytics")
        self.tabview.add("📝 Event Log")
        self.tabview.add("⚙️ Devices")
        
        # Floor Plan Tab
        self.create_floor_plan_tab()
        
        # Dashboard Tab
        self.create_dashboard_tab()
        
        # Energy Analytics Tab
        self.create_energy_analytics_tab()
        
        # Data Size Analytics Tab
        self.create_data_size_analytics_tab()
        
        # Event Log Tab
        self.create_event_log_tab()
        
        # Devices Tab
        self.create_devices_tab()
    
    def create_floor_plan_tab(self):
        """Create floor plan visualization"""
        floor_tab = self.tabview.tab("🏠 Floor Plan")
        
        # Canvas for floor plan with scrollbars
        canvas_frame = ctk.CTkFrame(floor_tab)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollbars
        h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")
        
        v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")
        
        # Canvas with scrollbars
        self.floor_canvas = tk.Canvas(canvas_frame, bg="#2b2b2b", 
                                     highlightthickness=0,
                                     height=700,
                                     scrollregion=(0, 0, 2000, 1000),  # Large scrollable area
                                     xscrollcommand=h_scrollbar.set,
                                     yscrollcommand=v_scrollbar.set)
        self.floor_canvas.pack(side="left", fill="both", expand=True)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.floor_canvas.xview)
        v_scrollbar.config(command=self.floor_canvas.yview)
        
        # Draw floor plan
        self.draw_floor_plan()
        
        # Bind click events
        self.floor_canvas.bind("<Button-1>", self.on_room_click)
    
    def create_dashboard_tab(self):
        """Create dashboard with real-time data"""
        dash_tab = self.tabview.tab("📊 Dashboard")
        
        # Energy Section
        energy_frame = ctk.CTkFrame(dash_tab)
        energy_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(energy_frame, text="⚡ Energy System", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.energy_info = ctk.CTkTextbox(energy_frame, height=100)
        self.energy_info.pack(fill="x", padx=10, pady=5)
        
        # Water Section
        water_frame = ctk.CTkFrame(dash_tab)
        water_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(water_frame, text="💧 Water System", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.water_info = ctk.CTkTextbox(water_frame, height=80)
        self.water_info.pack(fill="x", padx=10, pady=5)
        
        # Weather Section
        weather_frame = ctk.CTkFrame(dash_tab)
        weather_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(weather_frame, text="🌤️ Weather & Environment", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.weather_info = ctk.CTkTextbox(weather_frame, height=80)
        self.weather_info.pack(fill="x", padx=10, pady=5)
        
        # Network Section
        network_frame = ctk.CTkFrame(dash_tab)
        network_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(network_frame, text="📡 Network Status", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.network_info = ctk.CTkTextbox(network_frame, height=80)
        self.network_info.pack(fill="x", padx=10, pady=5)
    
    def create_energy_analytics_tab(self):
        """Create energy analytics with charts"""
        analytics_tab = self.tabview.tab("📈 Energy Analytics")
        
        if not MATPLOTLIB_AVAILABLE:
            # Show message if matplotlib not available
            msg_frame = ctk.CTkFrame(analytics_tab)
            msg_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(msg_frame, 
                        text="📊 Energy Analytics",
                        font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
            
            ctk.CTkLabel(msg_frame,
                        text="Matplotlib is required for charts.\nInstall with: pip install matplotlib",
                        font=ctk.CTkFont(size=14)).pack(pady=10)
            return
        
        # Title
        title_frame = ctk.CTkFrame(analytics_tab)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(title_frame, 
                    text="⚡ Energy Generation vs Consumption",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=5)
        
        # Chart frame
        chart_frame = ctk.CTkFrame(analytics_tab)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        self.energy_fig = Figure(figsize=(12, 6), facecolor='#2b2b2b')
        self.energy_ax = self.energy_fig.add_subplot(111)
        
        # Style the plot for dark theme
        self.energy_ax.set_facecolor('#1e1e1e')
        self.energy_ax.tick_params(colors='white', which='both')
        self.energy_ax.spines['bottom'].set_color('white')
        self.energy_ax.spines['top'].set_color('white')
        self.energy_ax.spines['left'].set_color('white')
        self.energy_ax.spines['right'].set_color('white')
        self.energy_ax.xaxis.label.set_color('white')
        self.energy_ax.yaxis.label.set_color('white')
        self.energy_ax.title.set_color('white')
        
        # Create canvas
        self.energy_canvas = FigureCanvasTkAgg(self.energy_fig, chart_frame)
        self.energy_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Legend info
        legend_frame = ctk.CTkFrame(analytics_tab)
        legend_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(legend_frame, text="🟡 Solar", 
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkLabel(legend_frame, text="🔵 Wind", 
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkLabel(legend_frame, text="🟢 Total Generation", 
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkLabel(legend_frame, text="🔴 Consumption", 
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        
        # Stats frame
        stats_frame = ctk.CTkFrame(analytics_tab)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.analytics_stats = ctk.CTkTextbox(stats_frame, height=80)
        self.analytics_stats.pack(fill="x", padx=10, pady=5)
    
    def create_data_size_analytics_tab(self):
        """Create data size analytics with charts"""
        analytics_tab = self.tabview.tab("📊 Data Size Analytics")
        
        if not MATPLOTLIB_AVAILABLE:
            # Show message if matplotlib not available
            msg_frame = ctk.CTkFrame(analytics_tab)
            msg_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(msg_frame, 
                        text="📊 Data Size Analytics",
                        font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
            
            ctk.CTkLabel(msg_frame,
                        text="Matplotlib is required for charts.\\nInstall with: pip install matplotlib",
                        font=ctk.CTkFont(size=14)).pack(pady=10)
            return
        
        # Title
        title_frame = ctk.CTkFrame(analytics_tab)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(title_frame, 
                    text="📊 Data Storage Growth by Format",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=5)
        
        # Chart frame
        chart_frame = ctk.CTkFrame(analytics_tab)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        self.data_size_fig = Figure(figsize=(12, 6), facecolor='#2b2b2b')
        self.data_size_ax = self.data_size_fig.add_subplot(111)
        
        # Style the plot for dark theme
        self.data_size_ax.set_facecolor('#1e1e1e')
        self.data_size_ax.tick_params(colors='white', which='both')
        self.data_size_ax.spines['bottom'].set_color('white')
        self.data_size_ax.spines['top'].set_color('white')
        self.data_size_ax.spines['left'].set_color('white')
        self.data_size_ax.spines['right'].set_color('white')
        self.data_size_ax.xaxis.label.set_color('white')
        self.data_size_ax.yaxis.label.set_color('white')
        self.data_size_ax.title.set_color('white')
        
        # Create canvas
        self.data_size_canvas = FigureCanvasTkAgg(self.data_size_fig, chart_frame)
        self.data_size_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Legend info
        legend_frame = ctk.CTkFrame(analytics_tab)
        legend_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(legend_frame, text="🟡 JSON Size", 
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkLabel(legend_frame, text="🔵 XML Size", 
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkLabel(legend_frame, text="🟢 Total Size", 
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkLabel(legend_frame, text="🔴 Message Count", 
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        
        # Stats frame
        stats_frame = ctk.CTkFrame(analytics_tab)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.data_size_stats = ctk.CTkTextbox(stats_frame, height=100)
        self.data_size_stats.pack(fill="x", padx=10, pady=5)
    
    def create_event_log_tab(self):
        """Create event log display"""
        log_tab = self.tabview.tab("📝 Event Log")
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(log_tab)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Filter:").pack(side="left", padx=5)
        
        ctk.CTkButton(filter_frame, text="All", width=60,
                     command=lambda: self.filter_log("all")).pack(side="left", padx=2)
        ctk.CTkButton(filter_frame, text="Info", width=60,
                     command=lambda: self.filter_log("info")).pack(side="left", padx=2)
        ctk.CTkButton(filter_frame, text="Warning", width=60,
                     command=lambda: self.filter_log("warning")).pack(side="left", padx=2)
        ctk.CTkButton(filter_frame, text="Critical", width=60,
                     command=lambda: self.filter_log("critical")).pack(side="left", padx=2)
        ctk.CTkButton(filter_frame, text="Clear", width=60,
                     command=self.clear_log).pack(side="right", padx=5)
        
        # Event log textbox
        self.event_log_text = ctk.CTkTextbox(log_tab, font=ctk.CTkFont(family="Courier", size=11))
        self.event_log_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_devices_tab(self):
        """Create interactive devices control panel"""
        devices_tab = self.tabview.tab("⚙️ Devices")
        
        # Title and summary
        title_frame = ctk.CTkFrame(devices_tab, height=60)
        title_frame.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkLabel(title_frame, text="🏠 Device Control Panel", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=15, pady=10)
        
        # Summary stats
        self.device_summary_label = ctk.CTkLabel(title_frame, 
                                                 text="",
                                                 font=ctk.CTkFont(size=13))
        self.device_summary_label.pack(side="right", padx=15, pady=10)
        
        # Scrollable frame for devices with increased dimensions
        scroll_frame = ctk.CTkScrollableFrame(devices_tab, width=1200, height=600)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Store device controls for updates
        self.device_controls = {}
        
        # Group by room
        for room in self.rooms:
            if not room.actuators:
                continue
            
            room_frame = ctk.CTkFrame(scroll_frame)
            room_frame.pack(fill="x", padx=10, pady=20)
            
            # Room header
            header_frame = ctk.CTkFrame(room_frame, height=60)
            header_frame.pack(fill="x", padx=12, pady=12)
            header_frame.pack_propagate(False)  # Maintain fixed height
            
            ctk.CTkLabel(header_frame, text=f"📍 {room.name}", 
                        font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=15, pady=15)
            
            # Room power consumption
            room_power_label = ctk.CTkLabel(header_frame, text="", 
                                           font=ctk.CTkFont(size=14, weight="bold"))
            room_power_label.pack(side="right", padx=15, pady=15)
            self.device_controls[f"room_power_{room.name}"] = room_power_label
            
            # Actuators with controls
            for actuator in room.actuators:
                device_frame = ctk.CTkFrame(room_frame, height=80)
                device_frame.pack(fill="x", padx=20, pady=12)
                device_frame.pack_propagate(False)  # Maintain fixed height
                
                # Device info
                info_frame = ctk.CTkFrame(device_frame)
                info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)
                
                # Device name and type
                device_name = f"{actuator.actuator_type}"
                name_label = ctk.CTkLabel(info_frame, text=device_name, 
                                         font=ctk.CTkFont(size=14, weight="bold"))
                name_label.pack(side="left", padx=8)
                
                # Device ID
                id_label = ctk.CTkLabel(info_frame, text=f"({actuator.actuator_id})", 
                                       font=ctk.CTkFont(size=11))
                id_label.pack(side="left", padx=8)
                
                # Power consumption
                power_label = ctk.CTkLabel(info_frame, text="", 
                                          font=ctk.CTkFont(size=12))
                power_label.pack(side="left", padx=15)
                self.device_controls[actuator.actuator_id] = power_label
                
                # Control buttons
                control_frame = ctk.CTkFrame(device_frame)
                control_frame.pack(side="right", padx=15, pady=15)
                
                # Status indicator
                status_label = ctk.CTkLabel(control_frame, text="", 
                                           font=ctk.CTkFont(size=13, weight="bold"))
                status_label.pack(side="left", padx=8)
                self.device_controls[f"status_{actuator.actuator_id}"] = status_label
                
                # ON/OFF buttons (disable for always-on devices)
                is_always_on = actuator.actuator_type in ["Refrigerator", "Router", "IoT Hub"]
                
                if is_always_on:
                    # Show "ALWAYS ON" label instead of buttons
                    always_on_label = ctk.CTkLabel(control_frame, text="⚡ ALWAYS ON",
                                                   font=ctk.CTkFont(size=12, weight="bold"),
                                                   text_color="orange")
                    always_on_label.pack(side="left", padx=8)
                else:
                    on_btn = ctk.CTkButton(control_frame, text="ON", width=70, height=40,
                                          command=lambda a=actuator: self.toggle_device(a, True),
                                          fg_color="green", hover_color="darkgreen",
                                          font=ctk.CTkFont(size=13, weight="bold"))
                    on_btn.pack(side="left", padx=5)
                    
                    off_btn = ctk.CTkButton(control_frame, text="OFF", width=70, height=40,
                                           command=lambda a=actuator: self.toggle_device(a, False),
                                           fg_color="red", hover_color="darkred",
                                           font=ctk.CTkFont(size=13, weight="bold"))
                    off_btn.pack(side="left", padx=5)
        
        # Update device display
        self.update_device_display()
    
    def toggle_device(self, actuator, state):
        """Manually toggle a device on/off"""
        # Prevent turning off always-on devices
        always_on_devices = ["Refrigerator", "Router", "IoT Hub"]
        if actuator.actuator_type in always_on_devices and not state:
            self.event_log.add_event("control", 
                                    f"Cannot turn off {actuator.actuator_type} - Always-on device",
                                    "warning")
            self.update_event_log()
            return
        
        actuator.set_state(state)
        self.update_device_display()
        self.event_log.add_event("control", 
                                f"Manual override: {actuator.actuator_type} in {actuator.room.name} turned {'ON' if state else 'OFF'}",
                                "info")
        self.update_event_log()
    
    def update_device_display(self):
        """Update device status and power consumption display"""
        total_consumption = 0
        active_devices = 0
        
        for room in self.rooms:
            room_consumption = sum(act.get_consumption() for act in room.actuators)
            total_consumption += room_consumption
            
            # Update room power label
            if f"room_power_{room.name}" in self.device_controls:
                self.device_controls[f"room_power_{room.name}"].configure(
                    text=f"⚡ {room_consumption:.0f}W"
                )
            
            # Update individual devices
            for actuator in room.actuators:
                power = actuator.get_consumption()
                if actuator.state:
                    active_devices += 1
                
                # Update power label
                if actuator.actuator_id in self.device_controls:
                    self.device_controls[actuator.actuator_id].configure(
                        text=f"⚡ {power:.0f}W"
                    )
                
                # Update status indicator
                status_key = f"status_{actuator.actuator_id}"
                if status_key in self.device_controls:
                    # Special status for refrigerator showing compressor state
                    if actuator.actuator_type == "Refrigerator":
                        if hasattr(actuator, 'compressor_running') and actuator.compressor_running:
                            status_emoji = "🟢 COOLING"
                        else:
                            status_emoji = "🟡 STANDBY"
                    else:
                        status_emoji = "🟢 ON" if actuator.state else "🔴 OFF"
                    self.device_controls[status_key].configure(text=status_emoji)
        
        # Update summary
        base_load = 300  # Base load + fridge
        total_with_base = total_consumption + base_load
        self.device_summary_label.configure(
            text=f"Active: {active_devices}/{len(self.actuators)} | Devices: {total_consumption:.0f}W | Base Load: {base_load}W | Total: {total_with_base:.0f}W"
        )
    
    def create_stats_panel(self):
        """Create right sidebar with detailed statistics"""
        stats_sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        stats_sidebar.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(0, 0))
        stats_sidebar.grid_rowconfigure(5, weight=1)
        
        # Title
        ctk.CTkLabel(stats_sidebar, text="📊 System Statistics", 
                    font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        # Cycle Info
        self.cycle_label = ctk.CTkLabel(stats_sidebar, text="Cycle: 0", 
                                       font=ctk.CTkFont(size=12))
        self.cycle_label.grid(row=1, column=0, padx=20, pady=5)
        
        # Battery Progress
        battery_frame = ctk.CTkFrame(stats_sidebar)
        battery_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(battery_frame, text="🔋 Battery", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
        
        self.battery_progress = ctk.CTkProgressBar(battery_frame)
        self.battery_progress.pack(fill="x", padx=10, pady=5)
        self.battery_progress.set(0.66)
        
        self.battery_label = ctk.CTkLabel(battery_frame, text="66%")
        self.battery_label.pack(pady=2)
        
        # Water Progress
        water_frame = ctk.CTkFrame(stats_sidebar)
        water_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(water_frame, text="💧 Water Tank", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
        
        self.water_progress = ctk.CTkProgressBar(water_frame)
        self.water_progress.pack(fill="x", padx=10, pady=5)
        self.water_progress.set(0.70)
        
        self.water_label = ctk.CTkLabel(water_frame, text="70%")
        self.water_label.pack(pady=2)
        
        # Detailed Stats
        details_frame = ctk.CTkScrollableFrame(stats_sidebar)
        details_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        
        self.details_text = ctk.CTkTextbox(details_frame, font=ctk.CTkFont(size=10))
        self.details_text.pack(fill="both", expand=True)
        
        # Security Status
        security_frame = ctk.CTkFrame(stats_sidebar)
        security_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        self.security_label = ctk.CTkLabel(security_frame, text="🔓 Security: Disarmed",
                                          font=ctk.CTkFont(size=12))
        self.security_label.pack(pady=10)
    
    def draw_floor_plan(self):
        """Draw the floor plan on canvas"""
        self.floor_canvas.delete("all")
        
        # Scale factor for canvas - increased for better visibility
        scale = 1.0  # Increased from 0.8 to 1.0
        offset_x = 30
        offset_y = 30
        
        # Draw rooms
        self.room_rects = {}
        for room in self.rooms:
            x1 = room.x * scale + offset_x
            y1 = room.y * scale + offset_y
            x2 = (room.x + room.width) * scale + offset_x
            y2 = (room.y + room.height) * scale + offset_y
            
            # Room color based on type
            if "Bedroom" in room.name:
                color = "#4a6fa5"
            elif "Bathroom" in room.name:
                color = "#5a8db8"
            elif room.name in ["Kitchen", "Dining Room"]:
                color = "#e07a5f"
            elif room.name == "Living Room":
                color = "#81b29a"
            elif room.name == "Hallway":
                color = "#3d405b"
            else:
                color = "#6c757d"
            
            rect_id = self.floor_canvas.create_rectangle(x1, y1, x2, y2, 
                                                         fill=color, outline="white", width=2)
            self.room_rects[room.name] = rect_id
            
            # Room label
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            self.floor_canvas.create_text(cx, cy, text=room.name, 
                                         fill="white", font=("Arial", 12, "bold"))
            
            # Sensor/Actuator count
            sensor_count = len(room.sensors)
            actuator_count = len(room.actuators)
            if sensor_count > 0 or actuator_count > 0:
                info_text = f"📡{sensor_count} ⚙️{actuator_count}"
                self.floor_canvas.create_text(cx, cy + 18, text=info_text, 
                                             fill="white", font=("Arial", 10))
    
    def on_room_click(self, event):
        """Handle room click event"""
        # Find which room was clicked
        for room in self.rooms:
            scale = 1.0
            offset_x = 30
            offset_y = 30
            x1 = room.x * scale + offset_x
            y1 = room.y * scale + offset_y
            x2 = (room.x + room.width) * scale + offset_x
            y2 = (room.y + room.height) * scale + offset_y
            
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.show_room_details(room)
                break
    
    def show_room_details(self, room):
        """Show detailed information about a room"""
        details = f"Room: {room.name}\n\n"
        
        # Sensors
        details += "Sensors:\n"
        hour = self.current_time.hour + self.current_time.minute / 60
        season = self.get_season()
        for sensor in room.sensors:
            value = sensor.read(hour, season, self.num_people)
            details += f"  • {sensor.sensor_type}: {value:.1f}\n"
        
        # Actuators
        details += "\nActuators:\n"
        for actuator in room.actuators:
            state = "ON" if actuator.state else "OFF"
            power = actuator.get_consumption() if actuator.state else 0
            details += f"  • {actuator.actuator_type}: {state} ({power}W)\n"
        
        # Show in details panel
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", details)
    
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
        
        # Update systems
        self.weather.update(hour, season)
        self.num_people = self.occupancy.get_occupancy(hour, day_of_week)
        
        # Log cycle
        if self.cycle_count % 4 == 0:
            self.event_log.add_event("system", 
                f"Cycle {self.cycle_count} | {self.current_time.strftime('%H:%M')} | " +
                f"{self.num_people} home | {self.weather.get_condition_emoji()} {self.weather.current_condition}",
                "info")
        
        # Run controller
        self.controller.process_cycle(hour, season, self.num_people, verbose=False)
        
        # Store data in database
        if self.data_storage_enabled and self.db.is_connected():
            self.store_simulation_data()
        
        # Update UI
        self.update_ui()
    
    def add_event(self, event_type: str, message: str, severity: str = "info", room: str = None):
        """
        Add event to log and database
        
        Args:
            event_type: Type of event (sensor, actuator, control, energy, water, network, system)
            message: Event message
            severity: Severity level (info, warning, critical)
            room: Associated room (optional)
        """
        # Add to in-memory event log
        self.event_log.add_event(event_type, message, severity)
        
        # Store in database if connected
        if self.db.is_connected():
            self.db.store_event(event_type, message, severity, room, self.current_time)
    
    def store_simulation_data(self):
        """Store current simulation data to MongoDB"""
        try:
            # Store sensor readings (sample every cycle to avoid overwhelming DB)
            for sensor in self.sensors:
                if hasattr(sensor, 'value') and sensor.value is not None:
                    # Serialize data in specified format
                    if self.data_format == DataFormat.MIXED:
                        serialized_data, format_used = self.format_manager.serialize_sensor_reading(
                            sensor.sensor_id, sensor.sensor_type, sensor.room.name,
                            float(sensor.value), sensor.get_unit(), self.current_time
                        )
                        format_str = format_used.value
                        data_str = format_to_string(serialized_data, format_used)
                    elif self.data_format == DataFormat.JSON:
                        serialized_data = self.format_manager.serialize_sensor_reading(
                            sensor.sensor_id, sensor.sensor_type, sensor.room.name,
                            float(sensor.value), sensor.get_unit(), self.current_time
                        )
                        format_str = 'json'
                        data_str = format_to_string(serialized_data, DataFormat.JSON)
                    else:  # XML
                        serialized_data = self.format_manager.serialize_sensor_reading(
                            sensor.sensor_id, sensor.sensor_type, sensor.room.name,
                            float(sensor.value), sensor.get_unit(), self.current_time
                        )
                        format_str = 'xml'
                        data_str = format_to_string(serialized_data, DataFormat.XML)
                    
                    # Track data size
                    data_size = len(data_str.encode('utf-8'))
                    if format_str == 'json':
                        self.cumulative_json_size += data_size
                    else:
                        self.cumulative_xml_size += data_size
                    self.cumulative_message_count += 1
                    
                    # Store in database with format metadata
                    self.db.store_sensor_reading(
                        sensor_id=sensor.sensor_id,
                        sensor_type=sensor.sensor_type,
                        room=sensor.room.name,
                        value=float(sensor.value),
                        unit=sensor.get_unit(),
                        simulation_time=self.current_time,
                        transmission_format=format_str,
                        serialized_data=data_str[:500] if len(data_str) > 500 else data_str  # Limit size
                    )
            
            # Store actuator states
            for actuator in self.actuators:
                # Serialize data in specified format
                if self.data_format == DataFormat.MIXED:
                    serialized_data, format_used = self.format_manager.serialize_actuator_state(
                        actuator.actuator_id, actuator.actuator_type, actuator.room.name,
                        actuator.state, actuator.get_consumption(), self.current_time
                    )
                    format_str = format_used.value
                    data_str = format_to_string(serialized_data, format_used)
                elif self.data_format == DataFormat.JSON:
                    serialized_data = self.format_manager.serialize_actuator_state(
                        actuator.actuator_id, actuator.actuator_type, actuator.room.name,
                        actuator.state, actuator.get_consumption(), self.current_time
                    )
                    format_str = 'json'
                    data_str = format_to_string(serialized_data, DataFormat.JSON)
                else:  # XML
                    serialized_data = self.format_manager.serialize_actuator_state(
                        actuator.actuator_id, actuator.actuator_type, actuator.room.name,
                        actuator.state, actuator.get_consumption(), self.current_time
                    )
                    format_str = 'xml'
                    data_str = format_to_string(serialized_data, DataFormat.XML)
                
                # Track data size
                data_size = len(data_str.encode('utf-8'))
                if format_str == 'json':
                    self.cumulative_json_size += data_size
                else:
                    self.cumulative_xml_size += data_size
                self.cumulative_message_count += 1
                
                # Store in database with format metadata
                self.db.store_actuator_state(
                    actuator_id=actuator.actuator_id,
                    actuator_type=actuator.actuator_type,
                    room=actuator.room.name,
                    state=actuator.state,
                    power_consumption=actuator.get_consumption(),
                    simulation_time=self.current_time,
                    transmission_format=format_str,
                    serialized_data=data_str[:500] if len(data_str) > 500 else data_str  # Limit size
                )
            
            # Store energy data
            self.db.store_energy_data(
                solar_generation=self.energy_system.current_solar,
                wind_generation=self.energy_system.current_wind,
                total_generation=self.energy_system.current_solar + self.energy_system.current_wind,
                total_consumption=self.energy_system.total_consumption,
                battery_level=self.energy_system.battery_level,
                battery_percentage=self.energy_system.get_battery_percentage(),
                grid_import=self.energy_system.grid_import,
                grid_export=self.energy_system.grid_export,
                simulation_time=self.current_time
            )
            
            # Store water data
            self.db.store_water_data(
                rainwater_level=self.water_system.current_level,
                rainwater_percentage=self.water_system.get_level_percentage(),
                consumption=self.water_system.current_usage_rate,
                rainfall=self.water_system.rainfall_intensity,
                simulation_time=self.current_time
            )
            
            # Store system statistics (every 10 cycles to reduce DB load)
            if self.cycle_count % 10 == 0:
                active_actuators = sum(1 for a in self.actuators if a.state)
                self.db.store_system_stats(
                    cycle_count=self.cycle_count,
                    num_people=self.num_people,
                    active_sensors=len(self.sensors),
                    active_actuators=active_actuators,
                    network_packets=len(self.network.active_transmissions),
                    simulation_time=self.current_time
                )
            
            # Flush batches periodically (every 20 cycles)
            if self.cycle_count % 20 == 0:
                self.db.flush_batches()
                
        except Exception as e:
            print(f"Error storing simulation data: {e}")
    
    def update_ui(self):
        """Update all UI elements - only active tab for performance"""
        # Date/Time
        date_str = self.current_time.strftime("%a, %b %d, %Y\n%H:%M")
        self.datetime_label.configure(text=date_str)
        
        # Cycle
        self.cycle_label.configure(text=f"Cycle: {self.cycle_count}")
        
        # Occupants
        self.occupants_label.configure(text=str(self.num_people))
        
        # Battery
        battery_pct = self.energy_system.get_battery_percentage()
        self.battery_progress.set(battery_pct / 100)
        self.battery_label.configure(text=f"{battery_pct:.1f}%")
        
        # Water
        water_pct = self.water_system.get_level_percentage()
        self.water_progress.set(water_pct / 100)
        self.water_label.configure(text=f"{water_pct:.1f}%")
        
        # Security
        security_icon = "🔒" if self.security.armed else "🔓"
        security_text = "Armed" if self.security.armed else "Disarmed"
        self.security_label.configure(text=f"{security_icon} Security: {security_text}")
        
        # Quick stats
        stats = f"⚡ {self.energy_system.current_solar:.0f}W Solar\n"
        stats += f"🌬️ {self.energy_system.current_wind:.0f}W Wind\n"
        stats += f"💧 {self.water_system.get_level_percentage():.0f}% Water\n"
        stats += f"💰 ₪{self.cost_tracker.total_saved:.2f} Saved"
        self.quick_stats_label.configure(text=stats)
        
        # Get current active tab
        active_tab = self.tabview.get()
        
        # Only update the active tab to improve performance
        if active_tab == "📊 Dashboard":
            self.update_dashboard()
        elif active_tab == "📈 Energy Analytics":
            self.update_energy_analytics()
        elif active_tab == "📊 Data Size Analytics":
            self.update_data_size_analytics()
        elif active_tab == "⚙️ Devices":
            self.update_device_display()
        elif active_tab == "📝 Event Log":
            self.update_event_log()
    
    def update_dashboard(self):
        """Update dashboard information"""
        # Energy
        energy_text = f"Solar Generation: {self.energy_system.current_solar:.0f}W\n"
        energy_text += f"Wind Generation: {self.energy_system.current_wind:.0f}W\n"
        energy_text += f"Total Consumption: {self.energy_system.total_consumption:.0f}W\n"
        energy_text += f"Battery: {self.energy_system.get_battery_percentage():.1f}% ({self.energy_system.get_battery_status()})\n"
        self.energy_info.delete("1.0", "end")
        self.energy_info.insert("1.0", energy_text)
        
        # Water
        water_text = f"Tank Level: {self.water_system.get_level_percentage():.1f}%\n"
        water_text += f"Current Usage: {self.water_system.current_usage_rate:.1f} L/h\n"
        water_text += f"Total Collected: {self.water_system.total_collected:.1f} L\n"
        self.water_info.delete("1.0", "end")
        self.water_info.insert("1.0", water_text)
        
        # Weather
        weather_text = f"Condition: {self.weather.get_condition_emoji()} {self.weather.current_condition}\n"
        weather_text += f"Cloud Cover: {self.weather.cloud_cover:.0f}%\n"
        weather_text += f"Wind Factor: {self.weather.wind_factor:.2f}x\n"
        weather_text += f"Raining: {'Yes' if self.weather.is_raining else 'No'}\n"
        self.weather_info.delete("1.0", "end")
        self.weather_info.insert("1.0", weather_text)
        
        # Network
        network_text = f"Total Nodes: {len(self.network.nodes)}\n"
        network_text += f"Active Transmissions: {len(self.network.active_transmissions)}\n"
        network_text += f"Hub: {NETWORK_HUB_LOCATION}\n"
        self.network_info.delete("1.0", "end")
        self.network_info.insert("1.0", network_text)
    
    def update_energy_analytics(self):
        """Update energy analytics chart and statistics"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Track energy data
        solar_power = self.energy_system.current_solar
        wind_power = self.energy_system.current_wind
        total_generation = solar_power + wind_power
        consumption = self.energy_system.total_consumption
        
        # Add to history with datetime
        self.energy_history['time'].append(self.cycle_count)
        self.energy_history['datetime'].append(self.current_time)
        self.energy_history['solar'].append(solar_power)
        self.energy_history['wind'].append(wind_power)
        self.energy_history['total_generation'].append(total_generation)
        self.energy_history['consumption'].append(consumption)
        
        # Keep only last N points
        if len(self.energy_history['time']) > self.max_history_points:
            for key in self.energy_history:
                self.energy_history[key] = self.energy_history[key][-self.max_history_points:]
        
        # Update chart only every 3 cycles to reduce rendering overhead
        if len(self.energy_history['time']) > 1 and self.cycle_count % 3 == 0:
            self.energy_ax.clear()
            
            # Use datetime for x-axis
            import matplotlib.dates as mdates
            
            # Plot lines with datetime on x-axis
            self.energy_ax.plot(self.energy_history['datetime'], 
                               self.energy_history['solar'], 
                               color='#FFD700', linewidth=2, label='Solar', marker='o', markersize=3)
            self.energy_ax.plot(self.energy_history['datetime'], 
                               self.energy_history['wind'], 
                               color='#4169E1', linewidth=2, label='Wind', marker='s', markersize=3)
            self.energy_ax.plot(self.energy_history['datetime'], 
                               self.energy_history['total_generation'], 
                               color='#32CD32', linewidth=2.5, label='Total Generation', marker='^', markersize=4)
            self.energy_ax.plot(self.energy_history['datetime'], 
                               self.energy_history['consumption'], 
                               color='#FF4500', linewidth=2, label='Consumption', marker='v', markersize=3)
            
            # Style
            self.energy_ax.set_facecolor('#1e1e1e')
            self.energy_ax.tick_params(colors='white', which='both')
            self.energy_ax.spines['bottom'].set_color('white')
            self.energy_ax.spines['top'].set_color('white')
            self.energy_ax.spines['left'].set_color('white')
            self.energy_ax.spines['right'].set_color('white')
            
            # Format x-axis to show date and time
            self.energy_ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            self.energy_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            
            # Rotate date labels for better readability
            self.energy_fig.autofmt_xdate(rotation=45, ha='right')
            
            self.energy_ax.set_xlabel('Date & Time', color='white', fontsize=12)
            self.energy_ax.set_ylabel('Power (W)', color='white', fontsize=12)
            self.energy_ax.set_title('Energy Generation vs Consumption', color='white', fontsize=14, fontweight='bold')
            self.energy_ax.legend(loc='upper left', facecolor='#2b2b2b', edgecolor='white', labelcolor='white')
            self.energy_ax.grid(True, alpha=0.2, color='white')
            
            # Refresh canvas
            self.energy_canvas.draw()
        
        # Update statistics
        if len(self.energy_history['time']) > 0:
            avg_solar = sum(self.energy_history['solar']) / len(self.energy_history['solar'])
            avg_wind = sum(self.energy_history['wind']) / len(self.energy_history['wind'])
            avg_generation = sum(self.energy_history['total_generation']) / len(self.energy_history['total_generation'])
            avg_consumption = sum(self.energy_history['consumption']) / len(self.energy_history['consumption'])
            
            self_sufficiency = (avg_generation / avg_consumption * 100) if avg_consumption > 0 else 0
            
            stats_text = f"📊 Statistics (Last {len(self.energy_history['time'])} cycles):\n"
            stats_text += f"Average Solar: {avg_solar:.0f}W | "
            stats_text += f"Average Wind: {avg_wind:.0f}W | "
            stats_text += f"Average Total Generation: {avg_generation:.0f}W | "
            stats_text += f"Average Consumption: {avg_consumption:.0f}W\n"
            stats_text += f"Self-Sufficiency: {self_sufficiency:.1f}% | "
            stats_text += f"Total Saved: ₪{self.cost_tracker.total_saved:.2f}"
            
            self.analytics_stats.delete("1.0", "end")
            self.analytics_stats.insert("1.0", stats_text)
    
    def update_data_size_analytics(self):
        """Update data size analytics chart"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Track data sizes (update every cycle)
        self.data_size_history['time'].append(self.cycle_count)
        self.data_size_history['datetime'].append(self.current_time)
        self.data_size_history['json_size'].append(self.cumulative_json_size / 1024)  # KB
        self.data_size_history['xml_size'].append(self.cumulative_xml_size / 1024)  # KB
        self.data_size_history['total_size'].append((self.cumulative_json_size + self.cumulative_xml_size) / 1024)  # KB
        self.data_size_history['message_count'].append(self.cumulative_message_count)
        
        # Keep only last N points
        if len(self.data_size_history['time']) > self.max_history_points:
            for key in self.data_size_history:
                self.data_size_history[key] = self.data_size_history[key][-self.max_history_points:]
        
        # Update chart only every 3 cycles to reduce rendering overhead
        if len(self.data_size_history['time']) > 1 and self.cycle_count % 3 == 0:
            self.data_size_ax.clear()
            
            # Use datetime for x-axis
            import matplotlib.dates as mdates
            
            # Create twin axis for message count
            ax2 = self.data_size_ax.twinx()
            
            # Plot size data on primary axis
            self.data_size_ax.plot(self.data_size_history['datetime'], 
                                   self.data_size_history['json_size'], 
                                   color='#FFD700', linewidth=2, label='JSON Size', marker='o', markersize=3)
            self.data_size_ax.plot(self.data_size_history['datetime'], 
                                   self.data_size_history['xml_size'], 
                                   color='#4169E1', linewidth=2, label='XML Size', marker='s', markersize=3)
            self.data_size_ax.plot(self.data_size_history['datetime'], 
                                   self.data_size_history['total_size'], 
                                   color='#32CD32', linewidth=2.5, label='Total Size', marker='^', markersize=4)
            
            # Plot message count on secondary axis
            ax2.plot(self.data_size_history['datetime'], 
                    self.data_size_history['message_count'], 
                    color='#FF4500', linewidth=2, label='Message Count', marker='v', markersize=3, linestyle='--')
            
            # Style primary axis
            self.data_size_ax.set_facecolor('#1e1e1e')
            self.data_size_ax.tick_params(colors='white', which='both')
            self.data_size_ax.spines['bottom'].set_color('white')
            self.data_size_ax.spines['top'].set_color('white')
            self.data_size_ax.spines['left'].set_color('white')
            self.data_size_ax.spines['right'].set_color('white')
            
            # Style secondary axis
            ax2.set_facecolor('#1e1e1e')
            ax2.tick_params(colors='white', which='both')
            ax2.spines['right'].set_color('white')
            ax2.yaxis.label.set_color('white')
            
            # Format x-axis
            self.data_size_ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            self.data_size_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.data_size_fig.autofmt_xdate(rotation=45, ha='right')
            
            # Labels
            self.data_size_ax.set_xlabel('Date & Time', color='white', fontsize=12)
            self.data_size_ax.set_ylabel('Data Size (KB)', color='white', fontsize=12)
            ax2.set_ylabel('Message Count', color='white', fontsize=12)
            self.data_size_ax.set_title('Data Storage Growth by Format', color='white', fontsize=14, fontweight='bold')
            
            # Combine legends
            lines1, labels1 = self.data_size_ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            self.data_size_ax.legend(lines1 + lines2, labels1 + labels2, 
                                    loc='upper left', facecolor='#2b2b2b', 
                                    edgecolor='white', labelcolor='white')
            
            self.data_size_ax.grid(True, alpha=0.2, color='white')
            
            # Refresh canvas
            self.data_size_canvas.draw()
        
        # Update statistics
        if len(self.data_size_history['time']) > 0:
            total_json_kb = self.cumulative_json_size / 1024
            total_xml_kb = self.cumulative_xml_size / 1024
            total_kb = total_json_kb + total_xml_kb
            
            json_pct = (total_json_kb / total_kb * 100) if total_kb > 0 else 0
            xml_pct = (total_xml_kb / total_kb * 100) if total_kb > 0 else 0
            
            # Get format statistics if using mixed mode
            format_stats_text = ""
            if self.data_format == DataFormat.MIXED and hasattr(self.format_manager, 'get_format_statistics'):
                format_stats = self.format_manager.get_format_statistics()
                format_stats_text = f"\\nFormat Distribution: JSON {format_stats['json_count']:,} ({format_stats['json_percentage']:.1f}%) | XML {format_stats['xml_count']:,} ({format_stats['xml_percentage']:.1f}%)"
            
            stats_text = f"📊 Data Storage Statistics:\\n"
            stats_text += f"Total Messages: {self.cumulative_message_count:,} | "
            stats_text += f"Total Size: {total_kb:.2f} KB ({total_kb/1024:.2f} MB)\\n"
            stats_text += f"JSON Data: {total_json_kb:.2f} KB ({json_pct:.1f}%) | "
            stats_text += f"XML Data: {total_xml_kb:.2f} KB ({xml_pct:.1f}%)\\n"
            stats_text += f"Avg Message Size: {(total_kb * 1024 / self.cumulative_message_count):.0f} bytes" if self.cumulative_message_count > 0 else "0 bytes"
            stats_text += format_stats_text
            
            self.data_size_stats.delete("1.0", "end")
            self.data_size_stats.insert("1.0", stats_text)
    
    def update_event_log(self):
        """Update event log display"""
        self.event_log_text.delete("1.0", "end")
        
        # Convert deque to list for slicing
        events_list = list(self.event_log.events)
        for event in events_list[-50:]:  # Show last 50 events
            timestamp = event["time"].strftime("%H:%M:%S")
            event_type = event["type"]
            message = event["message"]
            severity = event["severity"]
            
            # Color based on severity
            if severity == "critical":
                prefix = "🔴"
            elif severity == "warning":
                prefix = "🟡"
            elif event_type == "energy":
                prefix = "⚡"
            else:
                prefix = "ℹ️"
            
            log_line = f"{prefix} [{timestamp}] {event_type}: {message}\n"
            self.event_log_text.insert("end", log_line)
        
        # Auto-scroll to bottom
        self.event_log_text.see("end")
    
    def toggle_auto_run(self):
        """Toggle auto-run mode"""
        self.auto_run = not self.auto_run
        
        if self.auto_run:
            self.start_button.configure(text="⏸ Pause Auto-Run", fg_color="red", hover_color="darkred")
            self.step_button.configure(state="disabled")
            self.start_auto_run_thread()
        else:
            self.start_button.configure(text="▶ Start Auto-Run", fg_color="green", hover_color="darkgreen")
            self.step_button.configure(state="normal")
    
    def start_auto_run_thread(self):
        """Start auto-run in a separate thread"""
        def run_loop():
            while self.auto_run:
                self.advance_simulation()
                delay = AUTO_RUN_SPEEDS[self.speed_var.get()]
                time.sleep(delay)
        
        self.auto_run_thread = threading.Thread(target=run_loop, daemon=True)
        self.auto_run_thread.start()
    
    def change_speed(self, value):
        """Change simulation speed"""
        self.auto_run_speed = value
    
    def change_data_format(self, value):
        """Change data transmission format"""
        format_str = value.lower()
        
        # Update format
        if format_str == 'json':
            self.data_format = DataFormat.JSON
            self.format_manager = JSONSerializer()
        elif format_str == 'xml':
            self.data_format = DataFormat.XML
            self.format_manager = XMLSerializer()
        else:  # mixed
            self.data_format = DataFormat.MIXED
            self.format_manager = MixedFormatManager(json_probability=0.5)
        
        # Log the change
        self.add_event("system", f"Data format changed to {value}", "info")
        self.update_event_log()
    
    def adjust_occupants(self, delta):
        """Adjust number of occupants"""
        self.num_people = max(0, min(10, self.num_people + delta))
        self.occupants_label.configure(text=str(self.num_people))
    
    def set_start_date(self):
        """Set the simulation start date"""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            
            # Validate date
            new_date = datetime(year, month, day, 8, 0)  # Start at 8 AM
            
            # Reset simulation with new date
            self.current_time = new_date
            self.cycle_count = 0
            
            # Clear energy history
            self.energy_history = {
                'time': [],
                'datetime': [],
                'solar': [],
                'wind': [],
                'total_generation': [],
                'consumption': []
            }
            
            self.event_log.add_event("system", 
                                    f"Simulation date set to {new_date.strftime('%Y-%m-%d')}",
                                    "info")
            self.update_event_log()
            self.update_ui()
            
        except ValueError as e:
            self.event_log.add_event("system", 
                                    f"Invalid date format. Please use YYYY/MM/DD",
                                    "warning")
            self.update_event_log()
    
    def toggle_theme(self):
        """Toggle between dark and light mode"""
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
    
    def toggle_wiring(self):
        """Toggle wiring display"""
        self.show_wiring = self.wiring_switch.get()
        self.draw_floor_plan()
    
    def filter_log(self, level):
        """Filter event log by level"""
        # Implementation for filtering
        pass
    
    def clear_log(self):
        """Clear event log"""
        self.event_log.clear()
        self.event_log.add_event("system", "Event log cleared", "info")
        self.update_event_log()
    
    def run(self):
        """Start the application"""
        print("\n" + "="*80)
        print("SMART HOME SIMULATION STARTED (Modern UI)")
        print("="*80)
        print("Features:")
        print("  - Modern CustomTkinter interface")
        print("  - Real-time monitoring and control")
        print("  - Interactive floor plan")
        print("  - Detailed statistics and logs")
        if self.db.is_connected():
            print("  - MongoDB data persistence enabled")
        else:
            print("  - Running in offline mode (no data persistence)")
        print(f"  - Data transmission format: {self.data_format.value.upper()}")
        print("="*80 + "\n")
        
        # Initial UI update
        self.update_ui()
        
        # Register cleanup on window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start main loop
        self.mainloop()
    
    def on_closing(self):
        """Handle application shutdown"""
        print("\nShutting down Smart Home Simulation...")
        
        # Stop auto-run if active
        if self.auto_run:
            self.auto_run = False
            if self.auto_run_thread:
                self.auto_run_thread.join(timeout=2)
        
        # Flush remaining data and disconnect from database
        if self.db.is_connected():
            print("Flushing remaining data to database...")
            self.db.flush_batches()
            
            # Store final event
            self.db.store_event(
                "system",
                f"Simulation ended at cycle {self.cycle_count}",
                "info",
                simulation_time=self.current_time
            )
            
            # Get and print database statistics
            stats = self.db.get_database_stats()
            if 'error' not in stats:
                print("\n" + "="*80)
                print("DATABASE STATISTICS")
                print("="*80)
                print(f"  Sensor Readings: {stats.get('sensor_readings', 0):,}")
                print(f"  Actuator States: {stats.get('actuator_states', 0):,}")
                print(f"  Energy Data Points: {stats.get('energy_data', 0):,}")
                print(f"  Water Data Points: {stats.get('water_data', 0):,}")
                print(f"  Events Logged: {stats.get('events', 0):,}")
                print(f"  System Stats: {stats.get('system_stats', 0):,}")
                print(f"  Database Size: {stats.get('database_size', 0) / 1024 / 1024:.2f} MB")
                print("="*80 + "\n")
            
            # Print format statistics if using mixed mode
            if self.data_format == DataFormat.MIXED:
                format_stats = self.format_manager.get_format_statistics()
                print("\n" + "="*80)
                print("DATA TRANSMISSION FORMAT STATISTICS")
                print("="*80)
                print(f"  Total Transmissions: {format_stats['total_transmissions']:,}")
                print(f"  JSON Messages: {format_stats['json_count']:,} ({format_stats['json_percentage']:.1f}%)")
                print(f"  XML Messages: {format_stats['xml_count']:,} ({format_stats['xml_percentage']:.1f}%)")
                print("="*80 + "\n")
            
            self.db.disconnect()
        
        print("✓ Shutdown complete")
        self.destroy()

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    app = SmartHomeModernApp()
    app.run()

if __name__ == "__main__":
    main()
