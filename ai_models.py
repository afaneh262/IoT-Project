"""
AI Models for Smart Home IoT Simulation
Includes predictive energy management and anomaly detection
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import deque
import json

class EnergyPredictor:
    """Predicts energy generation and consumption using time series analysis"""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        
        # Historical data storage
        self.solar_history = deque(maxlen=history_size)
        self.wind_history = deque(maxlen=history_size)
        self.consumption_history = deque(maxlen=history_size)
        self.battery_history = deque(maxlen=history_size)
        self.time_history = deque(maxlen=history_size)
        
        # Prediction storage
        self.solar_predictions = []
        self.wind_predictions = []
        self.consumption_predictions = []
        self.battery_predictions = []
        self.prediction_times = []
        
        # Model parameters (simple moving average + trend)
        self.prediction_horizon = 24  # Predict 24 cycles ahead
        self.min_data_points = 20
        
        # Accuracy tracking
        self.prediction_errors = {
            'solar': [],
            'wind': [],
            'consumption': [],
            'battery': []
        }
        
    def add_data_point(self, solar: float, wind: float, consumption: float, 
                       battery: float, timestamp: datetime):
        """Add new data point to history"""
        self.solar_history.append(solar)
        self.wind_history.append(wind)
        self.consumption_history.append(consumption)
        self.battery_history.append(battery)
        self.time_history.append(timestamp)
        
    def _calculate_trend(self, data: deque, window: int = 10) -> float:
        """Calculate trend using linear regression"""
        if len(data) < window:
            return 0.0
        
        recent_data = list(data)[-window:]
        x = np.arange(len(recent_data))
        y = np.array(recent_data)
        
        # Simple linear regression
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            return slope
        return 0.0
    
    def _moving_average(self, data: deque, window: int = 10) -> float:
        """Calculate moving average"""
        if len(data) < window:
            window = len(data)
        if window == 0:
            return 0.0
        return np.mean(list(data)[-window:])
    
    def _seasonal_pattern(self, data: deque, current_time: datetime) -> float:
        """Detect seasonal/daily patterns"""
        if len(data) < 24:
            return 1.0
        
        # Get hour of day for seasonality
        hour = current_time.hour
        
        # Simple day/night pattern for solar
        if hour >= 6 and hour <= 18:
            return 1.2  # Daytime boost
        else:
            return 0.3  # Nighttime reduction
    
    def predict_next_values(self, current_time: datetime) -> Dict[str, float]:
        """Predict next values for solar, wind, consumption, and battery"""
        if len(self.solar_history) < self.min_data_points:
            return {
                'solar': 0.0,
                'wind': 0.0,
                'consumption': 0.0,
                'battery': 0.0,
                'confidence': 0.0
            }
        
        # Predict solar generation
        solar_ma = self._moving_average(self.solar_history, 10)
        solar_trend = self._calculate_trend(self.solar_history, 10)
        solar_seasonal = self._seasonal_pattern(self.solar_history, current_time)
        solar_pred = max(0, (solar_ma + solar_trend * 5) * solar_seasonal)
        
        # Predict wind generation
        wind_ma = self._moving_average(self.wind_history, 10)
        wind_trend = self._calculate_trend(self.wind_history, 10)
        wind_pred = max(0, wind_ma + wind_trend * 5)
        
        # Predict consumption
        consumption_ma = self._moving_average(self.consumption_history, 10)
        consumption_trend = self._calculate_trend(self.consumption_history, 10)
        consumption_pred = max(0, consumption_ma + consumption_trend * 5)
        
        # Predict battery level
        battery_ma = self._moving_average(self.battery_history, 10)
        battery_trend = self._calculate_trend(self.battery_history, 10)
        battery_pred = np.clip(battery_ma + battery_trend * 5, 0, 100)
        
        # Calculate confidence based on data stability
        confidence = min(100, (len(self.solar_history) / self.history_size) * 100)
        
        return {
            'solar': solar_pred,
            'wind': wind_pred,
            'consumption': consumption_pred,
            'battery': battery_pred,
            'confidence': confidence
        }
    
    def predict_horizon(self, current_time: datetime) -> List[Dict]:
        """Predict multiple steps ahead"""
        predictions = []
        
        if len(self.solar_history) < self.min_data_points:
            return predictions
        
        for i in range(self.prediction_horizon):
            future_time = current_time + timedelta(minutes=15 * i)
            pred = self.predict_next_values(future_time)
            pred['time'] = future_time
            pred['steps_ahead'] = i + 1
            predictions.append(pred)
        
        return predictions
    
    def update_prediction_accuracy(self, actual_solar: float, actual_wind: float,
                                   actual_consumption: float, actual_battery: float):
        """Update prediction accuracy metrics"""
        if len(self.solar_predictions) > 0:
            # Calculate errors for the most recent prediction
            solar_error = abs(actual_solar - self.solar_predictions[-1])
            wind_error = abs(actual_wind - self.wind_predictions[-1])
            consumption_error = abs(actual_consumption - self.consumption_predictions[-1])
            battery_error = abs(actual_battery - self.battery_predictions[-1])
            
            self.prediction_errors['solar'].append(solar_error)
            self.prediction_errors['wind'].append(wind_error)
            self.prediction_errors['consumption'].append(consumption_error)
            self.prediction_errors['battery'].append(battery_error)
            
            # Keep only last 100 errors
            for key in self.prediction_errors:
                if len(self.prediction_errors[key]) > 100:
                    self.prediction_errors[key] = self.prediction_errors[key][-100:]
    
    def get_accuracy_metrics(self) -> Dict:
        """Get prediction accuracy statistics"""
        metrics = {}
        
        for key, errors in self.prediction_errors.items():
            if len(errors) > 0:
                metrics[key] = {
                    'mae': np.mean(errors),  # Mean Absolute Error
                    'max_error': np.max(errors),
                    'min_error': np.min(errors),
                    'samples': len(errors)
                }
            else:
                metrics[key] = {
                    'mae': 0.0,
                    'max_error': 0.0,
                    'min_error': 0.0,
                    'samples': 0
                }
        
        return metrics
    
    def get_recommendations(self, predictions: Dict) -> List[str]:
        """Generate energy management recommendations"""
        recommendations = []
        
        if predictions['confidence'] < 50:
            recommendations.append("⚠️ Low prediction confidence - gathering more data")
            return recommendations
        
        # Solar recommendations
        if predictions['solar'] > predictions['consumption']:
            recommendations.append("☀️ Excess solar expected - consider charging battery")
        elif predictions['solar'] < predictions['consumption'] * 0.5:
            recommendations.append("🌙 Low solar expected - prepare to use battery/grid")
        
        # Battery recommendations
        if predictions['battery'] < 20:
            recommendations.append("🔋 Low battery predicted - reduce consumption or use grid")
        elif predictions['battery'] > 80:
            recommendations.append("⚡ High battery level - good time for high-power tasks")
        
        # Consumption recommendations
        if predictions['consumption'] > (predictions['solar'] + predictions['wind']):
            recommendations.append("📊 Consumption exceeds generation - grid import likely")
        
        return recommendations


class AnomalyDetector:
    """Detects anomalies in sensor readings and system behavior"""
    
    def __init__(self, sensitivity: float = 2.5):
        self.sensitivity = sensitivity  # Standard deviations for anomaly threshold
        
        # Statistical baselines for each sensor type
        self.baselines = {}
        
        # Anomaly history
        self.anomalies = []
        self.max_anomaly_history = 100
        
        # Sensor data buffers
        self.sensor_buffers = {}
        self.buffer_size = 50
        
        # Anomaly counters
        self.total_anomalies = 0
        self.anomalies_by_type = {}
        self.anomalies_by_severity = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
    def add_sensor_reading(self, sensor_id: str, sensor_type: str, 
                          value: float, room: str, timestamp: datetime):
        """Add sensor reading and check for anomalies"""
        # Initialize buffer if needed
        if sensor_id not in self.sensor_buffers:
            self.sensor_buffers[sensor_id] = deque(maxlen=self.buffer_size)
            self.baselines[sensor_id] = {
                'type': sensor_type,
                'room': room,
                'mean': 0.0,
                'std': 0.0,
                'min': float('inf'),
                'max': float('-inf'),
                'samples': 0
            }
        
        # Add to buffer
        self.sensor_buffers[sensor_id].append({
            'value': value,
            'timestamp': timestamp
        })
        
        # Update baseline statistics
        values = [reading['value'] for reading in self.sensor_buffers[sensor_id]]
        self.baselines[sensor_id]['mean'] = np.mean(values)
        self.baselines[sensor_id]['std'] = np.std(values) if len(values) > 1 else 0.0
        self.baselines[sensor_id]['min'] = min(self.baselines[sensor_id]['min'], value)
        self.baselines[sensor_id]['max'] = max(self.baselines[sensor_id]['max'], value)
        self.baselines[sensor_id]['samples'] += 1
        
        # Check for anomalies
        if len(values) >= 10:  # Need minimum data for detection
            anomaly = self._detect_anomaly(sensor_id, value, timestamp)
            if anomaly:
                self._record_anomaly(anomaly)
                return anomaly
        
        return None
    
    def _detect_anomaly(self, sensor_id: str, value: float, 
                       timestamp: datetime) -> Optional[Dict]:
        """Detect if value is anomalous"""
        baseline = self.baselines[sensor_id]
        
        # Skip if not enough variance
        if baseline['std'] < 0.01:
            return None
        
        # Calculate z-score
        z_score = abs(value - baseline['mean']) / baseline['std']
        
        # Check if anomalous
        if z_score > self.sensitivity:
            # Determine severity
            if z_score > 4.0:
                severity = 'critical'
            elif z_score > 3.5:
                severity = 'high'
            elif z_score > 3.0:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Determine anomaly type
            anomaly_type = 'spike' if value > baseline['mean'] else 'drop'
            
            return {
                'sensor_id': sensor_id,
                'sensor_type': baseline['type'],
                'room': baseline['room'],
                'value': value,
                'expected': baseline['mean'],
                'deviation': z_score,
                'severity': severity,
                'type': anomaly_type,
                'timestamp': timestamp,
                'description': self._generate_description(baseline['type'], value, 
                                                         baseline['mean'], severity, anomaly_type)
            }
        
        return None
    
    def _generate_description(self, sensor_type: str, value: float, 
                             expected: float, severity: str, anomaly_type: str) -> str:
        """Generate human-readable anomaly description"""
        direction = "spike" if anomaly_type == 'spike' else "drop"
        
        descriptions = {
            'Temperature': f"{severity.upper()}: Temperature {direction} detected - {value:.1f}°C (expected ~{expected:.1f}°C)",
            'Light': f"{severity.upper()}: Light level {direction} - {value:.0f} lux (expected ~{expected:.0f} lux)",
            'Motion': f"{severity.upper()}: Unusual motion pattern detected",
            'Humidity': f"{severity.upper()}: Humidity {direction} - {value:.1f}% (expected ~{expected:.1f}%)",
            'CO2': f"{severity.upper()}: CO2 level {direction} - {value:.0f} ppm (expected ~{expected:.0f} ppm)",
            'Power': f"{severity.upper()}: Power consumption {direction} - {value:.0f}W (expected ~{expected:.0f}W)"
        }
        
        return descriptions.get(sensor_type, 
                               f"{severity.upper()}: Anomaly in {sensor_type} - {value:.1f} (expected ~{expected:.1f})")
    
    def _record_anomaly(self, anomaly: Dict):
        """Record anomaly in history"""
        self.anomalies.append(anomaly)
        
        # Keep only recent anomalies
        if len(self.anomalies) > self.max_anomaly_history:
            self.anomalies = self.anomalies[-self.max_anomaly_history:]
        
        # Update counters
        self.total_anomalies += 1
        
        sensor_type = anomaly['sensor_type']
        if sensor_type not in self.anomalies_by_type:
            self.anomalies_by_type[sensor_type] = 0
        self.anomalies_by_type[sensor_type] += 1
        
        self.anomalies_by_severity[anomaly['severity']] += 1
    
    def get_recent_anomalies(self, count: int = 10) -> List[Dict]:
        """Get most recent anomalies"""
        return self.anomalies[-count:] if self.anomalies else []
    
    def get_anomaly_statistics(self) -> Dict:
        """Get anomaly detection statistics"""
        return {
            'total_anomalies': self.total_anomalies,
            'by_type': self.anomalies_by_type.copy(),
            'by_severity': self.anomalies_by_severity.copy(),
            'recent_count': len(self.anomalies),
            'detection_rate': (self.total_anomalies / sum(b['samples'] for b in self.baselines.values()) * 100)
                             if self.baselines else 0.0
        }
    
    def get_sensor_health(self) -> List[Dict]:
        """Get health status of all monitored sensors"""
        health_status = []
        
        for sensor_id, baseline in self.baselines.items():
            # Count recent anomalies for this sensor
            recent_anomalies = sum(1 for a in self.anomalies[-20:] 
                                  if a['sensor_id'] == sensor_id)
            
            # Determine health status
            if recent_anomalies == 0:
                status = 'healthy'
                health_score = 100
            elif recent_anomalies <= 2:
                status = 'warning'
                health_score = 75
            elif recent_anomalies <= 5:
                status = 'degraded'
                health_score = 50
            else:
                status = 'critical'
                health_score = 25
            
            health_status.append({
                'sensor_id': sensor_id,
                'sensor_type': baseline['type'],
                'room': baseline['room'],
                'status': status,
                'health_score': health_score,
                'recent_anomalies': recent_anomalies,
                'total_samples': baseline['samples']
            })
        
        return sorted(health_status, key=lambda x: x['health_score'])
    
    def clear_old_anomalies(self, hours: int = 24):
        """Clear anomalies older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.anomalies = [a for a in self.anomalies 
                         if a['timestamp'] > cutoff_time]


class AIManager:
    """Main AI manager coordinating all AI features"""
    
    def __init__(self):
        self.energy_predictor = EnergyPredictor(history_size=100)
        self.anomaly_detector = AnomalyDetector(sensitivity=2.5)
        
        self.ai_enabled = True
        self.last_prediction = None
        self.last_prediction_time = None
        
    def process_cycle(self, energy_data: Dict, sensor_readings: List[Dict], 
                     current_time: datetime):
        """Process one simulation cycle"""
        if not self.ai_enabled:
            return
        
        # Add energy data to predictor
        self.energy_predictor.add_data_point(
            solar=energy_data.get('solar', 0),
            wind=energy_data.get('wind', 0),
            consumption=energy_data.get('consumption', 0),
            battery=energy_data.get('battery_percentage', 0),
            timestamp=current_time
        )
        
        # Update prediction accuracy
        if self.last_prediction:
            self.energy_predictor.update_prediction_accuracy(
                actual_solar=energy_data.get('solar', 0),
                actual_wind=energy_data.get('wind', 0),
                actual_consumption=energy_data.get('consumption', 0),
                actual_battery=energy_data.get('battery_percentage', 0)
            )
        
        # Generate new predictions
        self.last_prediction = self.energy_predictor.predict_next_values(current_time)
        self.last_prediction_time = current_time
        
        # Process sensor readings for anomaly detection
        for reading in sensor_readings:
            self.anomaly_detector.add_sensor_reading(
                sensor_id=reading['sensor_id'],
                sensor_type=reading['sensor_type'],
                value=reading['value'],
                room=reading['room'],
                timestamp=current_time
            )
    
    def get_ai_status(self) -> Dict:
        """Get comprehensive AI system status"""
        return {
            'enabled': self.ai_enabled,
            'predictor': {
                'data_points': len(self.energy_predictor.solar_history),
                'accuracy': self.energy_predictor.get_accuracy_metrics(),
                'last_prediction': self.last_prediction,
                'last_update': self.last_prediction_time.isoformat() if self.last_prediction_time else None
            },
            'anomaly_detector': {
                'statistics': self.anomaly_detector.get_anomaly_statistics(),
                'recent_anomalies': len(self.anomaly_detector.get_recent_anomalies(10))
            }
        }
