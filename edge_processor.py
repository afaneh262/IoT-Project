"""
Edge Preprocessing Layer
Performs local filtering, smoothing, outlier removal, and data validation
before transmission to gateway
"""

import numpy as np
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class EdgePreprocessor:
    """
    Smart edge sensor preprocessing unit
    Performs outlier detection, smoothing, and data quality assurance
    """
    
    def __init__(self, window_size: int = 10, outlier_threshold: float = 3.0):
        self.window_size = window_size
        self.outlier_threshold = outlier_threshold  # Z-score threshold
        
        # Sliding windows for each sensor
        self.sensor_windows: Dict[str, deque] = {}
        self.sensor_stats: Dict[str, Dict] = {}
        
        # Quality metrics
        self.total_readings = 0
        self.filtered_readings = 0
        self.outliers_detected = 0
        
    def process_reading(self, sensor_id: str, value: float, sensor_type: str) -> Optional[Dict]:
        """
        Process a sensor reading through edge filtering pipeline
        
        Returns:
            Processed reading dict or None if filtered out
        """
        self.total_readings += 1
        
        # Initialize window for new sensor
        if sensor_id not in self.sensor_windows:
            self.sensor_windows[sensor_id] = deque(maxlen=self.window_size)
            self.sensor_stats[sensor_id] = {
                'mean': value,
                'std': 0.0,
                'min': value,
                'max': value,
                'count': 0
            }
        
        # Add to window
        window = self.sensor_windows[sensor_id]
        window.append(value)
        
        # Need at least 3 readings for statistical analysis
        if len(window) < 3:
            return self._create_processed_reading(sensor_id, value, sensor_type, 
                                                  filtered=False, smoothed=False)
        
        # Calculate statistics
        values_array = np.array(window)
        mean = np.mean(values_array)
        std = np.std(values_array)
        
        # Update sensor stats
        self.sensor_stats[sensor_id].update({
            'mean': mean,
            'std': std,
            'min': np.min(values_array),
            'max': np.max(values_array),
            'count': len(window)
        })
        
        # Outlier detection using Z-score
        if std > 0:
            z_score = abs((value - mean) / std)
            is_outlier = z_score > self.outlier_threshold
        else:
            is_outlier = False
        
        if is_outlier:
            self.outliers_detected += 1
            self.filtered_readings += 1
            # Return None to filter out outlier
            return None
        
        # Apply smoothing (moving average)
        smoothed_value = self._apply_smoothing(window, value)
        
        # Normalize if needed (for certain sensor types)
        normalized_value = self._normalize_value(smoothed_value, sensor_type)
        
        return self._create_processed_reading(sensor_id, normalized_value, sensor_type,
                                             filtered=True, smoothed=True,
                                             original_value=value)
    
    def _apply_smoothing(self, window: deque, current_value: float) -> float:
        """Apply exponential moving average smoothing"""
        if len(window) < 2:
            return current_value
        
        # Exponential moving average with alpha=0.3
        alpha = 0.3
        values = list(window)
        ema = values[0]
        
        for val in values[1:]:
            ema = alpha * val + (1 - alpha) * ema
        
        return ema
    
    def _normalize_value(self, value: float, sensor_type: str) -> float:
        """Normalize value based on sensor type"""
        # Normalization ranges for different sensor types
        normalization_ranges = {
            'Temperature': (-20, 50),  # Celsius
            'Humidity': (0, 100),      # Percentage
            'Light': (0, 1000),        # Lux
            'CO2': (400, 2000),        # ppm
            'Pressure': (950, 1050),   # hPa
            'SoilMoisture': (0, 100),  # Percentage
        }
        
        if sensor_type in normalization_ranges:
            min_val, max_val = normalization_ranges[sensor_type]
            # Clamp to range
            return max(min_val, min(max_val, value))
        
        return value
    
    def _create_processed_reading(self, sensor_id: str, value: float, 
                                  sensor_type: str, filtered: bool, 
                                  smoothed: bool, original_value: float = None) -> Dict:
        """Create processed reading dictionary"""
        return {
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'value': round(value, 2),
            'original_value': round(original_value, 2) if original_value else round(value, 2),
            'filtered': filtered,
            'smoothed': smoothed,
            'timestamp': datetime.now().isoformat(),
            'quality': 'high' if filtered and smoothed else 'medium'
        }
    
    def get_sensor_statistics(self, sensor_id: str) -> Optional[Dict]:
        """Get statistics for a specific sensor"""
        return self.sensor_stats.get(sensor_id)
    
    def get_quality_metrics(self) -> Dict:
        """Get overall edge processing quality metrics"""
        filter_rate = (self.filtered_readings / self.total_readings * 100) if self.total_readings > 0 else 0
        outlier_rate = (self.outliers_detected / self.total_readings * 100) if self.total_readings > 0 else 0
        
        return {
            'total_readings': self.total_readings,
            'filtered_readings': self.filtered_readings,
            'outliers_detected': self.outliers_detected,
            'filter_rate': round(filter_rate, 2),
            'outlier_rate': round(outlier_rate, 2),
            'active_sensors': len(self.sensor_windows)
        }
    
    def reset_statistics(self):
        """Reset quality metrics"""
        self.total_readings = 0
        self.filtered_readings = 0
        self.outliers_detected = 0


class EdgeFilteringNode:
    """
    Represents a smart sensor node with embedded edge processing
    Simulates the roof-mounted environmental sensor from the paper
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.preprocessor = EdgePreprocessor(window_size=10, outlier_threshold=3.0)
        self.enabled = True
        
    def process_sensor_data(self, sensor_id: str, value: float, 
                           sensor_type: str) -> Optional[Dict]:
        """
        Process sensor data through edge filtering
        
        Returns:
            Processed data or None if filtered out
        """
        if not self.enabled:
            return {
                'sensor_id': sensor_id,
                'sensor_type': sensor_type,
                'value': value,
                'filtered': False,
                'smoothed': False,
                'timestamp': datetime.now().isoformat(),
                'quality': 'raw'
            }
        
        return self.preprocessor.process_reading(sensor_id, value, sensor_type)
    
    def get_node_status(self) -> Dict:
        """Get edge node status and metrics"""
        return {
            'node_id': self.node_id,
            'enabled': self.enabled,
            'metrics': self.preprocessor.get_quality_metrics()
        }
