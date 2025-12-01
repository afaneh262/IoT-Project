"""
Water Collection and Management System
"""

import random
from config import (Season, WATER_TANK_CAPACITY, WATER_INITIAL,
                   WATER_CONSUMPTION_PER_PERSON)

# ============================================================================
# WATER SYSTEM
# ============================================================================

class WaterSystem:
    """Manages rainwater collection, storage, and distribution"""
    
    def __init__(self):
        # Tank specifications
        self.tank_capacity = WATER_TANK_CAPACITY
        self.current_level = WATER_INITIAL
        
        # Collection system
        self.roof_area = 250  # m² (collection surface)
        self.collection_efficiency = 0.85  # 85% efficiency
        self.current_collection_rate = 0  # L/hour
        
        # Distribution
        self.current_usage_rate = 0  # L/hour
        self.pump_active = False
        
        # Statistics
        self.total_collected = 0.0
        self.total_consumed = 0.0
        self.overflow_loss = 0.0
        
        # Weather state
        self.is_raining = False
        self.rainfall_intensity = 0  # mm/hour
        
    def calculate_rainfall(self, season: Season, time_hour: int) -> float:
        """
        Calculate rainfall based on season and time
        Returns rainfall intensity in mm/hour
        """
        # Rain probability by season
        rain_probability = {
            Season.WINTER: 0.25,
            Season.SPRING: 0.35,
            Season.SUMMER: 0.15,
            Season.AUTUMN: 0.30
        }[season]
        
        # Rain more likely during certain hours
        if 14 <= time_hour <= 20:
            # Afternoon/evening rain more common
            time_factor = 1.5
        else:
            time_factor = 1.0
        
        # Determine if it's raining
        if random.random() < rain_probability * time_factor:
            self.is_raining = True
            
            # Rainfall intensity varies
            # Light: 0-2.5 mm/h, Moderate: 2.5-10 mm/h, Heavy: 10-50 mm/h
            intensity_roll = random.random()
            if intensity_roll < 0.6:
                # Light rain (60%)
                intensity = random.uniform(0.5, 2.5)
            elif intensity_roll < 0.9:
                # Moderate rain (30%)
                intensity = random.uniform(2.5, 10)
            else:
                # Heavy rain (10%)
                intensity = random.uniform(10, 30)
            
            # Seasonal intensity modifier
            season_modifier = {
                Season.WINTER: 1.2,
                Season.SPRING: 1.0,
                Season.SUMMER: 0.8,
                Season.AUTUMN: 1.1
            }[season]
            
            self.rainfall_intensity = intensity * season_modifier
        else:
            self.is_raining = False
            self.rainfall_intensity = 0
        
        return self.rainfall_intensity
    
    def calculate_collection(self) -> float:
        """
        Calculate water collection rate based on rainfall
        Returns collection rate in L/hour
        """
        if not self.is_raining or self.rainfall_intensity == 0:
            return 0.0
        
        # Collection formula: roof_area (m²) × rainfall (mm/h) × efficiency
        # 1 mm of rain on 1 m² = 1 liter
        collection_rate = (self.roof_area * self.rainfall_intensity * 
                          self.collection_efficiency)
        
        return collection_rate
    
    def calculate_consumption(self, num_people: int, time_hour: int) -> float:
        """
        Calculate water consumption based on number of people and time of day
        Returns consumption rate in L/hour
        """
        # Base consumption per person per day
        daily_consumption = WATER_CONSUMPTION_PER_PERSON  # liters
        
        # Usage patterns throughout the day
        # Peak usage: morning (6-9) and evening (18-22)
        if 6 <= time_hour <= 9:
            # Morning peak (showers, breakfast)
            usage_factor = 1.8
        elif 18 <= time_hour <= 22:
            # Evening peak (cooking, showers, dishes)
            usage_factor = 2.0
        elif 12 <= time_hour <= 14:
            # Lunch time
            usage_factor = 1.0
        elif 22 <= time_hour or time_hour <= 6:
            # Night (minimal usage)
            usage_factor = 0.2
        else:
            # Normal usage
            usage_factor = 0.8
        
        # Calculate hourly consumption
        hourly_base = daily_consumption / 24
        consumption_rate = hourly_base * num_people * usage_factor
        
        # Add random variation (±20%)
        variation = random.uniform(0.8, 1.2)
        consumption_rate *= variation
        
        return consumption_rate
    
    def update(self, season: Season, num_people: int, time_hour: int, 
               time_delta: float = 1/60) -> dict:
        """
        Update water system for one time step
        time_delta in hours (default: 1 minute)
        """
        # Calculate rainfall and collection
        self.calculate_rainfall(season, time_hour)
        self.current_collection_rate = self.calculate_collection()
        
        # Calculate consumption
        self.current_usage_rate = self.calculate_consumption(num_people, time_hour)
        
        # Update water level
        # Collection
        collected = self.current_collection_rate * time_delta
        self.current_level += collected
        self.total_collected += collected
        
        # Check for overflow
        if self.current_level > self.tank_capacity:
            overflow = self.current_level - self.tank_capacity
            self.overflow_loss += overflow
            self.current_level = self.tank_capacity
        
        # Consumption
        consumed = self.current_usage_rate * time_delta
        self.current_level -= consumed
        self.total_consumed += consumed
        
        # Don't go below zero
        if self.current_level < 0:
            # Water shortage
            actual_consumed = consumed + self.current_level
            self.current_level = 0
            shortage = consumed - actual_consumed
        else:
            shortage = 0
        
        # Determine if pump should be active
        self.pump_active = self.current_usage_rate > 0 and self.current_level > 0
        
        return {
            "collection_rate": self.current_collection_rate,
            "usage_rate": self.current_usage_rate,
            "is_raining": self.is_raining,
            "rainfall": self.rainfall_intensity,
            "shortage": shortage,
            "pump_active": self.pump_active
        }
    
    def get_level_percentage(self) -> float:
        """Get tank level as percentage"""
        return (self.current_level / self.tank_capacity) * 100
    
    def get_tank_status(self) -> str:
        """Get tank status description"""
        percentage = self.get_level_percentage()
        if percentage > 80:
            return "Full"
        elif percentage > 50:
            return "Good"
        elif percentage > 20:
            return "Low"
        else:
            return "Critical"
    
    def is_water_shortage(self) -> bool:
        """Check if there's a water shortage"""
        return self.current_level < (self.tank_capacity * 0.1)
    
    def get_days_remaining(self, num_people: int) -> float:
        """Estimate days of water remaining based on current consumption"""
        if num_people == 0:
            return float('inf')
        
        daily_consumption = WATER_CONSUMPTION_PER_PERSON * num_people
        if daily_consumption == 0:
            return float('inf')
        
        return self.current_level / daily_consumption
    
    def get_statistics(self) -> dict:
        """Get comprehensive water statistics"""
        efficiency = 0
        if self.total_consumed > 0:
            efficiency = (self.total_collected / 
                         (self.total_collected + self.total_consumed)) * 100
        
        return {
            "total_collected": self.total_collected,
            "total_consumed": self.total_consumed,
            "overflow_loss": self.overflow_loss,
            "collection_efficiency": efficiency,
            "current_level": self.current_level,
            "tank_capacity": self.tank_capacity
        }
