"""
Configuration and Constants for Smart Home IoT Simulation
"""

from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class Season(Enum):
    """Seasons affecting temperature, solar power, and water collection"""
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"

class DeviceStatus(Enum):
    """Status of IoT devices"""
    ONLINE = "Online"
    OFFLINE = "Offline"
    ERROR = "Error"

# ============================================================================
# COLORS
# ============================================================================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
LIGHT_GRAY = (230, 230, 230)
BLUE = (100, 150, 255)
DARK_BLUE = (50, 100, 200)
YELLOW = (255, 255, 100)
BRIGHT_YELLOW = (255, 255, 0)
GREEN = (100, 255, 100)
DARK_GREEN = (0, 150, 0)
RED = (255, 100, 100)
DARK_RED = (200, 0, 0)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
LIGHT_BLUE = (173, 216, 230)
CYAN = (0, 255, 255)
PURPLE = (200, 100, 255)
PINK = (255, 150, 200)

# Network colors
NETWORK_DATA = (0, 255, 150)
NETWORK_POWER = (255, 200, 0)
NETWORK_WATER = (0, 150, 255)

# ============================================================================
# SIMULATION SETTINGS
# ============================================================================

# Screen settings
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1000
FPS = 60

# Time settings
MINUTES_PER_CYCLE = 15  # Each simulation cycle = 15 minutes
AUTO_RUN_SPEEDS = {
    "Slow": 1.0,    # 1 second per cycle
    "Normal": 0.5,  # 0.5 seconds per cycle
    "Fast": 0.2,    # 0.2 seconds per cycle
    "Ultra": 0.05   # 0.05 seconds per cycle
}

# ============================================================================
# LOCATION SETTINGS (Ramallah, Palestine)
# ============================================================================

LATITUDE = 31.9  # Ramallah latitude
LONGITUDE = 35.2  # Ramallah longitude
TIMEZONE = "Asia/Jerusalem"
ELEVATION = 880  # meters above sea level

# Climate data for Ramallah
# Average wind speeds (m/s) by season
RAMALLAH_WIND_SPEED = {
    Season.WINTER: 4.5,   # Dec-Feb: Moderate winds
    Season.SPRING: 5.2,   # Mar-May: Higher winds
    Season.SUMMER: 3.8,   # Jun-Aug: Light winds
    Season.AUTUMN: 4.8    # Sep-Nov: Moderate winds
}

# Average solar irradiance (kWh/m²/day) by season
RAMALLAH_SOLAR_IRRADIANCE = {
    Season.WINTER: 3.5,   # Lower due to clouds, shorter days
    Season.SPRING: 6.0,   # Good conditions
    Season.SUMMER: 7.5,   # Peak sunshine, clear skies
    Season.AUTUMN: 5.5    # Decreasing but still good
}

# ============================================================================
# HOUSE SPECIFICATIONS
# ============================================================================

# Realistic house dimensions (in pixels, 1 pixel ≈ 0.1 meter)
# Total house: ~200m² realistic single-story home
# Clean rectangular grid layout

# Base coordinates
HOUSE_X = 80
HOUSE_Y = 100

HOUSE_LAYOUT = {
    # Format: "Room Name": (x, y, width, height)
    
    # LEFT COLUMN - Bedrooms (3m x 4m typical bedroom)
    "Master Bedroom": (HOUSE_X, HOUSE_Y, 200, 160),
    "Bedroom 2": (HOUSE_X, HOUSE_Y + 160, 200, 140),
    "Bedroom 3": (HOUSE_X, HOUSE_Y + 300, 200, 140),
    
    # LEFT-CENTER - Bathrooms (2m x 2.5m)
    "Master Bathroom": (HOUSE_X + 200, HOUSE_Y, 100, 80),
    "Bathroom 2": (HOUSE_X + 200, HOUSE_Y + 160, 100, 140),
    "Bathroom 3": (HOUSE_X + 200, HOUSE_Y + 300, 100, 140),
    
    # CENTER - Hallway (runs full length)
    "Hallway": (HOUSE_X + 300, HOUSE_Y, 120, 440),
    
    # RIGHT-CENTER - Living areas
    "Living Room": (HOUSE_X + 420, HOUSE_Y, 240, 180),
    "Dining Room": (HOUSE_X + 420, HOUSE_Y + 180, 240, 140),
    
    # RIGHT - Kitchen and utilities (4m x 3.5m kitchen)
    "Kitchen": (HOUSE_X + 660, HOUSE_Y, 200, 160),
    "Laundry Room": (HOUSE_X + 660, HOUSE_Y + 160, 200, 140),
    "Storage": (HOUSE_X + 660, HOUSE_Y + 300, 100, 140),
    
    # BOTTOM RIGHT - Garage and Technical
    "Garage": (HOUSE_X + 760, HOUSE_Y + 300, 100, 140),
    "Technical Room": (HOUSE_X + 420, HOUSE_Y + 320, 240, 120),
}

# Door connections (room1, room2) - defines wiring paths
DOOR_CONNECTIONS = [
    # Bedrooms to bathrooms
    ("Master Bedroom", "Master Bathroom"),
    ("Bedroom 2", "Bathroom 2"),
    ("Bedroom 3", "Bathroom 3"),
    
    # Bedrooms to hallway
    ("Master Bedroom", "Hallway"),
    ("Master Bathroom", "Hallway"),
    ("Bedroom 2", "Hallway"),
    ("Bedroom 3", "Hallway"),
    
    # Living areas to hallway
    ("Living Room", "Hallway"),
    ("Dining Room", "Hallway"),
    ("Kitchen", "Hallway"),
    
    # Utilities to hallway
    ("Laundry Room", "Hallway"),
    ("Storage", "Hallway"),
    ("Garage", "Hallway"),
    ("Technical Room", "Hallway"),
    
    # Adjacent connections
    ("Living Room", "Dining Room"),
    ("Dining Room", "Kitchen"),
    ("Kitchen", "Laundry Room"),
    ("Laundry Room", "Storage"),
    ("Storage", "Garage"),
]

# Wiring offset from walls (pixels)
WIRE_OFFSET_FROM_WALL = 20
WIRE_VERTICAL_SPACING = 10  # Space between parallel wires
WIRE_CORNER_RADIUS = 15  # Rounded corners for realistic wiring

# ============================================================================
# ENERGY SYSTEM SETTINGS
# ============================================================================

SOLAR_PANEL_CAPACITY = 8000  # 8 kW solar array
WIND_TURBINE_CAPACITY = 5000  # 5 kW wind turbine
BATTERY_CAPACITY = 30000  # 30 kWh battery storage
BATTERY_INITIAL = 20000  # Start at 66% charge

# Power consumption (Watts)
POWER_CONSUMPTION = {
    "LED_Light": 12,
    "CFL_Light": 60,
    "Fan": 75,
    "AC_Unit": 2000,
    "Heater": 1500,
    "Router": 10,
    "IoT_Hub": 5,
    "Sensor": 0.5,
    "Pump": 750,
    
    # Kitchen appliances
    "Refrigerator": 150,      # Always on, cycles
    "Freezer": 100,           # Always on
    "Microwave": 1200,        # When in use
    "Oven": 2500,             # When in use
    "Stove": 2000,            # When in use
    "Dishwasher": 1800,       # Cycle ~1.5 hours
    "Coffee_Maker": 1000,     # Morning use
    "Kettle": 1500,           # Short bursts
    "Toaster": 800,           # Morning use
    
    # Laundry appliances
    "Washing_Machine": 500,   # Cycle ~1 hour
    "Dryer": 3000,            # Cycle ~1 hour
    
    # Entertainment
    "TV": 100,
    "TV_Large": 250,          # Living room
    "Computer": 200,
    
    # Other
    "Vacuum": 1400,           # Occasional use
    "Iron": 1200,             # Occasional use
}

# ============================================================================
# WATER SYSTEM SETTINGS
# ============================================================================

WATER_TANK_CAPACITY = 10000  # 10,000 liters
WATER_INITIAL = 7000  # Start at 70% full
WATER_CONSUMPTION_PER_PERSON = 150  # Liters per day per person

# ============================================================================
# NETWORK SETTINGS
# ============================================================================

# IoT Network topology
NETWORK_HUB_LOCATION = "Technical Room"

# Event log settings
MAX_LOG_ENTRIES = 100
LOG_PANEL_WIDTH = 350
LOG_PANEL_HEIGHT = 400
DATA_PACKET_SIZE = 32  # bytes
NETWORK_LATENCY = 0.05  # seconds
TRANSMISSION_SPEED = 1000  # packets per second

# ============================================================================
# SENSOR SETTINGS
# ============================================================================

SENSOR_READ_INTERVAL = 5  # seconds (in real-time)
SENSOR_ACCURACY = 0.95  # 95% accuracy

# Temperature ranges (Celsius)
TEMP_COMFORT_MIN = 20
TEMP_COMFORT_MAX = 26
TEMP_HOT_THRESHOLD = 28
TEMP_COLD_THRESHOLD = 18

# Light levels
LIGHT_DARK_THRESHOLD = 30
LIGHT_BRIGHT_THRESHOLD = 70
