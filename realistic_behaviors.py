"""
Realistic Behaviors and Patterns for Smart Home
Includes occupancy patterns, weather, appliance scheduling, and emergencies
"""

import random
from datetime import datetime, time
from enum import Enum
from typing import Dict, List, Tuple
from config import Season

# ============================================================================
# OCCUPANCY PATTERNS
# ============================================================================

class OccupancyPattern:
    """Manages realistic occupancy patterns for household members"""
    
    def __init__(self, num_people: int):
        self.num_people = num_people
        self.people_at_home = num_people
        
        # Define person types with schedules
        self.schedules = {
            "adult_1": {"type": "worker", "work_hours": (8, 17)},
            "adult_2": {"type": "worker", "work_hours": (9, 18)},
            "child_1": {"type": "student", "school_hours": (7, 15)},
            "child_2": {"type": "student", "school_hours": (7, 15)},
        }
        
    def get_occupancy(self, hour: float, day_of_week: int) -> int:
        """
        Get number of people at home based on time and day
        day_of_week: 0=Monday, 6=Sunday
        """
        is_weekend = day_of_week >= 5  # Saturday, Sunday
        
        people_home = 0
        
        for person_id, schedule in list(self.schedules.items())[:self.num_people]:
            at_home = True
            
            if not is_weekend:
                # Weekday schedules
                if schedule["type"] == "worker":
                    work_start, work_end = schedule["work_hours"]
                    # Leave 30 min before work, return 30 min after
                    if work_start - 0.5 <= hour <= work_end + 0.5:
                        at_home = False
                
                elif schedule["type"] == "student":
                    school_start, school_end = schedule["school_hours"]
                    if school_start <= hour <= school_end:
                        at_home = False
            
            # Everyone sleeps 23:00 - 6:00
            if hour >= 23 or hour < 6:
                at_home = True
            
            if at_home:
                people_home += 1
        
        return max(1, people_home)  # At least 1 person always

    def get_active_rooms(self, hour: float, num_people: int) -> Dict[str, bool]:
        """Get which rooms are actively being used"""
        active = {}
        
        # Morning routine (6-9 AM)
        if 6 <= hour < 9:
            active["Master Bedroom"] = True
            active["Master Bathroom"] = True
            active["Kitchen"] = True
            if num_people > 2:
                active["Bedroom 2"] = True
                active["Bathroom 2"] = True
        
        # Daytime (9 AM - 5 PM) - fewer people
        elif 9 <= hour < 17:
            if num_people <= 2:
                active["Living Room"] = True
                active["Kitchen"] = random.random() < 0.3
            else:
                active["Living Room"] = True
                active["Bedroom 3"] = True  # Someone home
        
        # Evening (5-10 PM) - everyone home
        elif 17 <= hour < 22:
            active["Living Room"] = True
            active["Dining Room"] = True
            active["Kitchen"] = True
            active["Master Bedroom"] = random.random() < 0.4
            if num_people > 2:
                active["Bedroom 2"] = True
                active["Bedroom 3"] = True
        
        # Night (10 PM - 6 AM) - sleeping
        else:
            active["Master Bedroom"] = True
            if num_people > 1:
                active["Bedroom 2"] = True
            if num_people > 2:
                active["Bedroom 3"] = True
        
        return active

# ============================================================================
# WEATHER SYSTEM
# ============================================================================

class Weather:
    """Realistic weather system affecting generation and comfort"""
    
    def __init__(self):
        self.current_condition = "clear"  # clear, cloudy, overcast, rain
        self.cloud_cover = 0  # 0-100%
        self.is_raining = False
        self.outside_temp = 20.0
        self.wind_factor = 1.0
        
    def update(self, hour: float, season: Season):
        """Update weather conditions"""
        # Time of day affects weather stability
        is_afternoon = 12 <= hour <= 18
        
        # Seasonal base temperatures for Ramallah
        base_temps = {
            Season.WINTER: 8.0,
            Season.SPRING: 18.0,
            Season.SUMMER: 28.0,
            Season.AUTUMN: 20.0
        }
        
        # Daily temperature variation
        temp_variation = 8 * math.sin((hour - 6) * math.pi / 12)
        self.outside_temp = base_temps[season] + temp_variation
        
        # Weather changes (more stable in summer)
        if random.random() < 0.05:  # 5% chance of change
            if season == Season.SUMMER:
                # Mostly clear in summer
                self.current_condition = random.choice(
                    ["clear", "clear", "clear", "cloudy"])
            elif season == Season.WINTER:
                # More clouds and rain in winter
                self.current_condition = random.choice(
                    ["clear", "cloudy", "cloudy", "overcast", "rain"])
            else:
                # Variable in spring/autumn
                self.current_condition = random.choice(
                    ["clear", "cloudy", "overcast", "rain"])
        
        # Update cloud cover based on condition
        condition_clouds = {
            "clear": (0, 20),
            "cloudy": (40, 70),
            "overcast": (80, 100),
            "rain": (90, 100)
        }
        
        low, high = condition_clouds[self.current_condition]
        target = random.randint(low, high)
        # Smooth transition
        self.cloud_cover += (target - self.cloud_cover) * 0.1
        
        # Rain only if overcast/rain condition
        if self.current_condition == "rain":
            self.is_raining = True
        else:
            self.is_raining = False
        
        # Wind variation
        self.wind_factor = random.uniform(0.7, 1.3)
    
    def get_solar_reduction(self) -> float:
        """Get solar generation reduction factor (0-1)"""
        # Cloud cover reduces solar
        return 1.0 - (self.cloud_cover / 100) * 0.8
    
    def get_condition_emoji(self) -> str:
        """Get emoji for current weather"""
        return {
            "clear": "☀️",
            "cloudy": "⛅",
            "overcast": "☁️",
            "rain": "🌧️"
        }[self.current_condition]

# ============================================================================
# APPLIANCE SCHEDULER
# ============================================================================

class ApplianceScheduler:
    """Schedules appliances based on realistic usage patterns"""
    
    def __init__(self):
        self.last_cooking = 0
        self.last_laundry = 0
        self.last_dishwasher = 0
        
    def should_cook(self, hour: float, num_people: int) -> Dict[str, bool]:
        """Determine if cooking should happen"""
        schedule = {}
        
        # Breakfast (6-9 AM)
        if 6.5 <= hour < 8.5:
            schedule["coffee"] = random.random() < 0.8
            schedule["toaster"] = random.random() < 0.5
            schedule["stove"] = random.random() < 0.3
        
        # Lunch (12-2 PM) - if people home
        elif 12 <= hour < 14 and num_people > 1:
            schedule["microwave"] = random.random() < 0.6
            schedule["stove"] = random.random() < 0.4
        
        # Dinner (6-8 PM) - main cooking time
        elif 18 <= hour < 20:
            schedule["oven"] = random.random() < 0.4
            schedule["stove"] = random.random() < 0.7
            schedule["microwave"] = random.random() < 0.3
        
        return schedule
    
    def should_run_dishwasher(self, hour: float, cycle_count: int) -> bool:
        """Dishwasher typically runs at night after dinner"""
        # Run between 9 PM - 11 PM, once per day
        if 21 <= hour < 23:
            if cycle_count - self.last_dishwasher > 96:  # ~24 hours
                if random.random() < 0.3:
                    self.last_dishwasher = cycle_count
                    return True
        return False
    
    def should_run_laundry(self, hour: float, day_of_week: int, 
                          cycle_count: int) -> Dict[str, bool]:
        """Laundry typically on weekends or evenings"""
        laundry = {"washer": False, "dryer": False}
        
        is_weekend = day_of_week >= 5
        
        # Weekends: morning or afternoon
        if is_weekend and 9 <= hour < 16:
            if cycle_count - self.last_laundry > 192:  # ~48 hours
                if random.random() < 0.4:
                    laundry["washer"] = True
                    self.last_laundry = cycle_count
        
        # Weekdays: evening only
        elif not is_weekend and 19 <= hour < 21:
            if cycle_count - self.last_laundry > 288:  # ~72 hours
                if random.random() < 0.2:
                    laundry["washer"] = True
                    self.last_laundry = cycle_count
        
        # Dryer runs 60-90 minutes after washer
        # This would be tracked separately in the actuator
        
        return laundry
    
    def get_entertainment_usage(self, hour: float, num_people: int) -> Dict[str, bool]:
        """TV and computer usage patterns"""
        usage = {}
        
        # Morning news (6-8 AM)
        if 6 <= hour < 8 and num_people > 1:
            usage["tv_living"] = random.random() < 0.5
        
        # Daytime (9-5 PM) - minimal if people at work
        elif 9 <= hour < 17:
            usage["computer"] = num_people > 1 and random.random() < 0.3
        
        # Evening prime time (6-11 PM)
        elif 18 <= hour < 23:
            usage["tv_living"] = random.random() < 0.8
            usage["computer"] = random.random() < 0.4
        
        return usage

# ============================================================================
# SECURITY SYSTEM
# ============================================================================

class SecuritySystem:
    """Home security system with motion detection and alerts"""
    
    def __init__(self):
        self.armed = False
        self.intrusion_detected = False
        self.last_activity_time = 0
        
    def should_arm(self, hour: float, people_at_home: int) -> bool:
        """Arm system when everyone is away or sleeping"""
        # Arm during work hours if nobody home
        if 9 <= hour < 17 and people_at_home == 0:
            return True
        # Arm at night
        if hour >= 23 or hour < 6:
            return True
        return False
    
    def check_intrusion(self, motion_detected: bool, people_at_home: int) -> bool:
        """Check for potential intrusion"""
        if self.armed and motion_detected and people_at_home == 0:
            if random.random() < 0.01:  # Very rare event
                return True
        return False

# ============================================================================
# COST TRACKING
# ============================================================================

class CostTracker:
    """Track energy costs and savings"""
    
    def __init__(self):
        # Electricity prices (NIS per kWh) - Israel Electric Corporation rates
        self.peak_price = 0.6317  # Peak hours (7 AM - 11 PM)
        self.off_peak_price = 0.3158  # Off-peak hours (11 PM - 7 AM)
        
        self.total_saved = 0.0
        self.total_would_have_cost = 0.0
        self.solar_money_saved = 0.0
        self.wind_money_saved = 0.0
        
    def is_peak_hour(self, hour: float) -> bool:
        """Determine if current hour is peak pricing"""
        return 7 <= hour < 23
    
    def calculate_savings(self, solar_generated: float, wind_generated: float, 
                         consumed: float, hour: float) -> Dict[str, float]:
        """Calculate money saved from renewable energy"""
        price = self.peak_price if self.is_peak_hour(hour) else self.off_peak_price
        
        # Convert Wh to kWh and calculate cost
        solar_saved = (solar_generated / 1000) * price
        wind_saved = (wind_generated / 1000) * price
        
        self.solar_money_saved += solar_saved
        self.wind_money_saved += wind_saved
        self.total_saved += solar_saved + wind_saved
        
        # Calculate what it would have cost
        would_cost = (consumed / 1000) * price
        self.total_would_have_cost += would_cost
        
        return {
            "solar_saved": solar_saved,
            "wind_saved": wind_saved,
            "current_price": price,
            "total_saved": self.total_saved,
            "savings_percent": (self.total_saved / self.total_would_have_cost * 100) 
                              if self.total_would_have_cost > 0 else 0
        }

# ============================================================================
# EMERGENCY SCENARIOS
# ============================================================================

class EmergencyManager:
    """Manages random emergency scenarios"""
    
    def __init__(self):
        self.active_emergency = None
        self.emergency_start_cycle = 0
        
    def check_for_emergency(self, cycle_count: int) -> str:
        """Randomly trigger emergency scenarios"""
        if self.active_emergency:
            # Emergency lasts 1-2 hours
            if cycle_count - self.emergency_start_cycle > random.randint(4, 8):
                self.active_emergency = None
            return self.active_emergency
        
        # Very rare events
        if random.random() < 0.001:  # 0.1% per cycle
            emergency_types = [
                "power_outage",
                "water_leak", 
                "high_temperature",
                "sensor_failure"
            ]
            self.active_emergency = random.choice(emergency_types)
            self.emergency_start_cycle = cycle_count
            return self.active_emergency
        
        return None

import math
