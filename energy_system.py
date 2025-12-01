"""
Renewable Energy System for Smart Home
"""

import math
import random
from datetime import datetime
from typing import Tuple
from config import (Season, SOLAR_PANEL_CAPACITY, WIND_TURBINE_CAPACITY,
                   BATTERY_CAPACITY, BATTERY_INITIAL, LATITUDE,
                   RAMALLAH_WIND_SPEED, RAMALLAH_SOLAR_IRRADIANCE)

# ============================================================================
# ENERGY SYSTEM
# ============================================================================

class EnergySystem:
    """Manages renewable energy generation and battery storage"""
    
    def __init__(self):
        # Generation capacity
        self.solar_capacity = SOLAR_PANEL_CAPACITY
        self.wind_capacity = WIND_TURBINE_CAPACITY
        
        # Battery storage
        self.battery_capacity = BATTERY_CAPACITY
        self.battery_level = BATTERY_INITIAL
        self.battery_health = 100  # Percentage (degrades over time)
        
        # Current generation
        self.current_solar = 0.0
        self.current_wind = 0.0
        self.current_wind_speed = 0.0  # m/s
        self.total_generation = 0.0
        
        # Consumption tracking
        self.total_consumption = 0.0
        self.peak_consumption = 0.0
        
        # Statistics
        self.total_solar_generated = 0.0
        self.total_wind_generated = 0.0
        self.total_consumed = 0.0
        self.battery_charge_cycles = 0
        self.grid_import = 0.0  # If we need to import from grid
        self.grid_export = 0.0  # If we export excess to grid
        
        # Solar panel parameters
        self.solar_panel_count = 20
        self.solar_panel_efficiency = 0.20  # 20% efficiency
        self.solar_panel_area = 2.0  # m² per panel
        
        # Wind turbine parameters
        self.wind_turbine_height = 15  # meters
        self.wind_turbine_radius = 2.5  # meters
        self.cut_in_speed = 3.0  # m/s
        self.rated_speed = 12.0  # m/s
        self.cut_out_speed = 25.0  # m/s
        
    def calculate_solar_generation(self, time_hour: int, season: Season) -> float:
        """
        Calculate solar power generation based on time and season
        Uses realistic solar irradiance model for Ramallah, Palestine
        """
        # Sunrise and sunset times vary by season in Ramallah
        sunrise_times = {
            Season.WINTER: 6.5,   # ~6:30 AM
            Season.SPRING: 6.0,   # ~6:00 AM
            Season.SUMMER: 5.5,   # ~5:30 AM
            Season.AUTUMN: 6.0    # ~6:00 AM
        }
        
        sunset_times = {
            Season.WINTER: 17.0,  # ~5:00 PM
            Season.SPRING: 18.5,  # ~6:30 PM
            Season.SUMMER: 19.5,  # ~7:30 PM
            Season.AUTUMN: 18.0   # ~6:00 PM
        }
        
        sunrise = sunrise_times[season]
        sunset = sunset_times[season]
        
        # No generation at night
        if time_hour < sunrise or time_hour > sunset:
            return 0.0
        
        # Calculate solar elevation angle
        # Solar noon is around 12:30 in Ramallah
        solar_noon = 12.5
        hour_angle = (time_hour - solar_noon) * 15  # degrees
        
        # Seasonal declination angle
        season_declination = {
            Season.WINTER: -23.5,   # Low sun angle
            Season.SPRING: 0,       # Equinox
            Season.SUMMER: 23.5,    # High sun angle
            Season.AUTUMN: 0        # Equinox
        }[season]
        
        # Calculate solar elevation for Ramallah (latitude 31.9°)
        latitude = LATITUDE
        # Simplified calculation: elevation = 90 - |latitude - declination| at noon
        max_elevation = 90 - abs(latitude - season_declination)
        
        # Adjust for time of day (parabolic curve)
        day_length = sunset - sunrise
        time_factor = 1 - ((time_hour - solar_noon) / (day_length / 2)) ** 2
        time_factor = max(0, time_factor)
        
        solar_elevation = max_elevation * time_factor
        
        # Get Ramallah-specific irradiance data
        daily_irradiance = RAMALLAH_SOLAR_IRRADIANCE[season]  # kWh/m²/day
        # Convert to instantaneous irradiance (W/m²)
        # Peak irradiance occurs at solar noon
        peak_irradiance = (daily_irradiance * 1000) / (day_length * 0.65)  # 65% efficiency factor
        irradiance = peak_irradiance * math.sin(math.radians(solar_elevation))
        
        # Weather effects (Ramallah has some cloudy days)
        weather_variability = {
            Season.WINTER: (0.5, 0.9),   # More clouds in winter
            Season.SPRING: (0.7, 1.0),   # Variable
            Season.SUMMER: (0.85, 1.0),  # Mostly clear
            Season.AUTUMN: (0.7, 0.95)   # Variable
        }[season]
        weather_factor = random.uniform(*weather_variability)
        
        # Dust and atmospheric effects (Ramallah specific)
        atmospheric_factor = 0.92  # Slight reduction due to dust
        
        # Calculate total power
        total_area = self.solar_panel_count * self.solar_panel_area
        generated_power = (irradiance * total_area * self.solar_panel_efficiency *
                          weather_factor * atmospheric_factor)
        
        # Panel degradation over time
        degradation_factor = self.battery_health / 100
        
        return min(self.solar_capacity, generated_power * degradation_factor)
    
    def calculate_wind_generation(self, season: Season, time_hour: int) -> float:
        """
        Calculate wind power generation based on wind speed
        Uses wind turbine power curve with Ramallah-specific wind data
        """
        # Base wind speed by season for Ramallah
        base_wind_speed = RAMALLAH_WIND_SPEED[season]
        
        # Wind patterns in Ramallah:
        # - Stronger in afternoons due to thermal effects
        # - Morning calm, picks up after 10 AM
        # - Evening winds moderate
        if 4 <= time_hour < 10:
            # Morning calm
            time_factor = 0.7
        elif 10 <= time_hour < 16:
            # Afternoon thermal winds (stronger)
            time_factor = 1.3
        elif 16 <= time_hour < 20:
            # Evening moderate
            time_factor = 1.0
        else:
            # Night calm
            time_factor = 0.8
        
        # Random wind gusts and variation (more realistic)
        wind_variation = random.uniform(0.6, 1.4)
        
        # Calculate current wind speed
        wind_speed = base_wind_speed * time_factor * wind_variation
        
        # Add occasional gusts
        if random.random() < 0.15:  # 15% chance of gust
            wind_speed *= random.uniform(1.2, 1.5)
        
        # Wind turbine power curve (cubic relationship below rated speed)
        if wind_speed < self.cut_in_speed:
            # Too slow to generate
            power = 0.0
        elif wind_speed >= self.cut_out_speed:
            # Too fast, turbine shuts down for safety
            power = 0.0
        elif wind_speed < self.rated_speed:
            # Cubic power curve: power increases with cube of wind speed
            power_ratio = ((wind_speed - self.cut_in_speed) / 
                          (self.rated_speed - self.cut_in_speed))
            power = self.wind_capacity * (power_ratio ** 3)
        else:
            # Constant power at rated speed
            power = self.wind_capacity
        
        # Store current wind speed for display
        self.current_wind_speed = wind_speed
        
        return power
    
    def update_generation(self, time_hour: int, season: Season) -> Tuple[float, float]:
        """Update power generation from all sources"""
        self.current_solar = self.calculate_solar_generation(time_hour, season)
        self.current_wind = self.calculate_wind_generation(season, time_hour)
        self.total_generation = self.current_solar + self.current_wind
        
        # Update statistics
        self.total_solar_generated += self.current_solar / 60  # Wh
        self.total_wind_generated += self.current_wind / 60  # Wh
        
        return self.current_solar, self.current_wind
    
    def update_battery(self, consumption: float, time_delta: float = 1/60) -> float:
        """
        Update battery level based on generation and consumption
        time_delta in hours (default: 1 minute)
        """
        self.total_consumption = consumption
        self.peak_consumption = max(self.peak_consumption, consumption)
        
        # Net power (positive = charging, negative = discharging)
        net_power = self.total_generation - consumption
        
        # Energy change in Wh
        energy_change = net_power * time_delta
        
        # Update battery level
        previous_level = self.battery_level
        self.battery_level += energy_change
        
        # Check if we need grid import/export
        if self.battery_level < 0:
            # Battery depleted, import from grid
            self.grid_import += abs(self.battery_level)
            self.battery_level = 0
        elif self.battery_level > self.battery_capacity:
            # Battery full, export to grid
            excess = self.battery_level - self.battery_capacity
            self.grid_export += excess
            self.battery_level = self.battery_capacity
        
        # Track charge cycles
        if previous_level < self.battery_level and previous_level < self.battery_capacity * 0.5:
            if self.battery_level >= self.battery_capacity * 0.5:
                self.battery_charge_cycles += 0.5
        
        # Update statistics
        self.total_consumed += consumption / 60  # Wh
        
        return net_power
    
    def get_battery_percentage(self) -> float:
        """Get battery level as percentage"""
        return (self.battery_level / self.battery_capacity) * 100
    
    def get_battery_status(self) -> str:
        """Get battery status description"""
        percentage = self.get_battery_percentage()
        if percentage > 80:
            return "Excellent"
        elif percentage > 50:
            return "Good"
        elif percentage > 20:
            return "Low"
        else:
            return "Critical"
    
    def is_power_saving_needed(self) -> bool:
        """Check if power saving mode should be activated"""
        return self.battery_level < (self.battery_capacity * 0.2)
    
    def is_critical_power(self) -> bool:
        """Check if power is critically low"""
        return self.battery_level < (self.battery_capacity * 0.1)
    
    def get_energy_flow_direction(self) -> str:
        """Get current energy flow direction"""
        net = self.total_generation - self.total_consumption
        if net > 100:
            return "charging"
        elif net < -100:
            return "discharging"
        else:
            return "balanced"
    
    def get_self_sufficiency(self) -> float:
        """Calculate self-sufficiency ratio (%)"""
        if self.total_consumed == 0:
            return 100.0
        
        grid_dependency = (self.grid_import / self.total_consumed) * 100
        return max(0, 100 - grid_dependency)
    
    def get_statistics(self) -> dict:
        """Get comprehensive energy statistics"""
        return {
            "solar_generated": self.total_solar_generated,
            "wind_generated": self.total_wind_generated,
            "total_generated": self.total_solar_generated + self.total_wind_generated,
            "total_consumed": self.total_consumed,
            "battery_cycles": self.battery_charge_cycles,
            "grid_import": self.grid_import,
            "grid_export": self.grid_export,
            "self_sufficiency": self.get_self_sufficiency(),
            "battery_health": self.battery_health
        }
