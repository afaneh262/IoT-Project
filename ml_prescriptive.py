"""
Machine Learning Prescriptive Control Module
Random Forest Classifier for actuator decision making
Implements the ML-driven prescriptive analytics from the IEEE paper
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pickle
import os


class PrescriptiveMLController:
    """
    Random Forest-based prescriptive controller for smart home actuators
    Predicts optimal actuator states based on sensor data and renewable energy availability
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or "ml_prescriptive_model.pkl"
        self.scaler = StandardScaler()
        
        # Separate models for different actuator types
        self.models = {
            'hvac': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            'lighting': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            'irrigation': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            'ventilation': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            'alarm': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        }
        
        # Training data buffers
        self.training_data = {
            'features': [],
            'labels': {}
        }
        
        for actuator_type in self.models.keys():
            self.training_data['labels'][actuator_type] = []
        
        # Model performance metrics
        self.metrics = {
            'hvac': {},
            'lighting': {},
            'irrigation': {},
            'ventilation': {},
            'alarm': {}
        }
        
        # Feature names for interpretability
        self.feature_names = [
            'temperature', 'humidity', 'light_level', 'motion_detected',
            'co2_level', 'gas_level', 'soil_moisture', 'vibration',
            'solar_power', 'wind_power', 'battery_level',
            'hour_of_day', 'occupancy', 'renewable_available'
        ]
        
        self.is_trained = False
        self.min_training_samples = 100
        
    def extract_features(self, sensor_data: Dict, energy_data: Dict, 
                        time_data: Dict) -> np.ndarray:
        """
        Extract feature vector from sensor, energy, and time data
        
        Args:
            sensor_data: Dictionary of sensor readings
            energy_data: Renewable energy availability data
            time_data: Time and occupancy information
        
        Returns:
            Feature vector as numpy array
        """
        features = [
            sensor_data.get('temperature', 20.0),
            sensor_data.get('humidity', 50.0),
            sensor_data.get('light_level', 300.0),
            1.0 if sensor_data.get('motion_detected', False) else 0.0,
            sensor_data.get('co2_level', 400.0),
            sensor_data.get('gas_level', 0.0),
            sensor_data.get('soil_moisture', 50.0),
            sensor_data.get('vibration', 0.0),
            energy_data.get('solar_power', 0.0),
            energy_data.get('wind_power', 0.0),
            energy_data.get('battery_level', 50.0),
            time_data.get('hour_of_day', 12),
            time_data.get('occupancy', 0),
            1.0 if energy_data.get('renewable_available', 0) > 500 else 0.0
        ]
        
        return np.array(features).reshape(1, -1)
    
    def add_training_sample(self, features: np.ndarray, actuator_states: Dict):
        """
        Add a training sample to the buffer
        
        Args:
            features: Feature vector
            actuator_states: Dictionary of actuator states (0 or 1)
        """
        self.training_data['features'].append(features.flatten())
        
        for actuator_type in self.models.keys():
            state = actuator_states.get(actuator_type, 0)
            self.training_data['labels'][actuator_type].append(state)
    
    def train_models(self, test_size: float = 0.2) -> Dict:
        """
        Train all Random Forest models
        
        Returns:
            Dictionary of training metrics for each model
        """
        if len(self.training_data['features']) < self.min_training_samples:
            return {
                'status': 'insufficient_data',
                'samples': len(self.training_data['features']),
                'required': self.min_training_samples
            }
        
        # Convert to numpy arrays
        X = np.array(self.training_data['features'])
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        results = {}
        
        # Train each actuator model
        for actuator_type, model in self.models.items():
            y = np.array(self.training_data['labels'][actuator_type])
            
            # Skip if no positive samples
            if np.sum(y) == 0 or np.sum(y) == len(y):
                results[actuator_type] = {
                    'status': 'skipped',
                    'reason': 'no_variation_in_labels'
                }
                continue
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            # Store metrics
            self.metrics[actuator_type] = {
                'accuracy': round(accuracy, 4),
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'f1_score': round(f1, 4),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'trained_at': datetime.now().isoformat()
            }
            
            results[actuator_type] = self.metrics[actuator_type].copy()
            results[actuator_type]['status'] = 'success'
        
        self.is_trained = True
        
        return results
    
    def predict_actuator_states(self, sensor_data: Dict, energy_data: Dict,
                               time_data: Dict) -> Dict:
        """
        Predict optimal actuator states using trained models
        
        Returns:
            Dictionary of predicted actuator states and confidence scores
        """
        if not self.is_trained:
            return {
                'status': 'model_not_trained',
                'predictions': {}
            }
        
        # Extract and normalize features
        features = self.extract_features(sensor_data, energy_data, time_data)
        features_scaled = self.scaler.transform(features)
        
        predictions = {}
        
        for actuator_type, model in self.models.items():
            if actuator_type not in self.metrics or not self.metrics[actuator_type]:
                continue
            
            # Predict state
            predicted_state = model.predict(features_scaled)[0]
            
            # Get prediction probability (confidence)
            probabilities = model.predict_proba(features_scaled)[0]
            confidence = max(probabilities)
            
            predictions[actuator_type] = {
                'state': int(predicted_state),
                'confidence': round(confidence, 3),
                'action': 'turn_on' if predicted_state == 1 else 'turn_off'
            }
        
        return {
            'status': 'success',
            'predictions': predictions,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_feature_importance(self, actuator_type: str) -> Optional[Dict]:
        """Get feature importance for a specific actuator model"""
        if actuator_type not in self.models or not self.is_trained:
            return None
        
        model = self.models[actuator_type]
        
        if not hasattr(model, 'feature_importances_'):
            return None
        
        importances = model.feature_importances_
        
        # Create feature importance dictionary
        feature_importance = {}
        for name, importance in zip(self.feature_names, importances):
            feature_importance[name] = round(importance, 4)
        
        # Sort by importance
        sorted_features = sorted(feature_importance.items(), 
                               key=lambda x: x[1], reverse=True)
        
        return {
            'actuator_type': actuator_type,
            'features': dict(sorted_features),
            'top_3_features': [f[0] for f in sorted_features[:3]]
        }
    
    def get_all_metrics(self) -> Dict:
        """Get performance metrics for all models"""
        return {
            'is_trained': self.is_trained,
            'training_samples': len(self.training_data['features']),
            'models': self.metrics,
            'overall_accuracy': self._calculate_overall_accuracy()
        }
    
    def _calculate_overall_accuracy(self) -> float:
        """Calculate average accuracy across all models"""
        accuracies = []
        for metrics in self.metrics.values():
            if 'accuracy' in metrics:
                accuracies.append(metrics['accuracy'])
        
        return round(np.mean(accuracies), 4) if accuracies else 0.0
    
    def save_models(self, path: str = None):
        """Save trained models to disk"""
        save_path = path or self.model_path
        
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        with open(save_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_models(self, path: str = None):
        """Load trained models from disk"""
        load_path = path or self.model_path
        
        if not os.path.exists(load_path):
            return False
        
        try:
            with open(load_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.metrics = model_data['metrics']
            self.feature_names = model_data['feature_names']
            self.is_trained = model_data['is_trained']
            
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def generate_synthetic_training_data(self, num_samples: int = 1000):
        """
        Generate synthetic training data for initial model training
        Simulates realistic smart home scenarios
        """
        np.random.seed(42)
        
        for _ in range(num_samples):
            # Random time and conditions
            hour = np.random.randint(0, 24)
            occupancy = np.random.randint(0, 5)
            
            # Sensor data
            temp = np.random.normal(22, 5)
            humidity = np.random.normal(50, 15)
            light = np.random.normal(400, 200) if 6 <= hour <= 20 else np.random.normal(50, 30)
            motion = 1 if occupancy > 0 and np.random.random() > 0.3 else 0
            co2 = 400 + occupancy * np.random.uniform(100, 200)
            gas = np.random.uniform(0, 10) if np.random.random() < 0.05 else 0
            soil = np.random.uniform(30, 70)
            vibration = np.random.uniform(0, 20)
            
            # Energy data
            solar = max(0, np.random.normal(300, 150)) if 6 <= hour <= 18 else 0
            wind = max(0, np.random.normal(150, 100))
            battery = np.random.uniform(20, 90)
            renewable_available = solar + wind
            
            sensor_data = {
                'temperature': temp,
                'humidity': humidity,
                'light_level': light,
                'motion_detected': motion,
                'co2_level': co2,
                'gas_level': gas,
                'soil_moisture': soil,
                'vibration': vibration
            }
            
            energy_data = {
                'solar_power': solar,
                'wind_power': wind,
                'battery_level': battery,
                'renewable_available': renewable_available
            }
            
            time_data = {
                'hour_of_day': hour,
                'occupancy': occupancy
            }
            
            # Generate labels based on rules
            actuator_states = {
                'hvac': 1 if (temp > 25 or temp < 18) and renewable_available > 300 else 0,
                'lighting': 1 if (light < 200 and occupancy > 0 and 6 <= hour <= 22) else 0,
                'irrigation': 1 if soil < 40 and renewable_available > 200 else 0,
                'ventilation': 1 if co2 > 800 or gas > 5 else 0,
                'alarm': 1 if gas > 8 or vibration > 50 else 0
            }
            
            features = self.extract_features(sensor_data, energy_data, time_data)
            self.add_training_sample(features, actuator_states)
