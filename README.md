# Smart Home IoT Simulation

A comprehensive Smart Home IoT simulation system with modern GUI, MongoDB data warehousing, and support for multiple data transmission formats (JSON/XML/Mixed).

## 🚀 How to Run

### Prerequisites
- Python 3.9+
- Docker and Docker Compose

### Quick Start

1. **Start MongoDB**
   ```bash
   docker-compose up -d
   ```

2. **Run the Application**
   ```bash
   python main.py
   ```

3. **Access Services**
   - Application: GUI window opens automatically
   - MongoDB: `localhost:27017`
   - Mongo Express: http://localhost:8081 (login: admin/pass)

### Stop Services
```bash
docker-compose down
```

## 🔐 Security Features

The simulation includes comprehensive security measures:

- **AES-256 Encryption**: All sensor data is encrypted before transmission and storage
- **Device Authentication**: Each sensor and actuator is authenticated with unique tokens
- **Message Integrity**: HMAC signatures verify data hasn't been tampered with
- **Security Levels**: Real-time monitoring of security status (Low/Medium/High)

Security is enabled by default. To disable encryption, set `ENCRYPTION_ENABLED=false` in your `.env` file.

## 🤖 AI Features

The simulation includes advanced AI capabilities as specified in the IEEE paper:

### 1. Predictive Energy Management (Statistical AI)
- **Solar/Wind Forecasting**: Predicts future generation based on historical patterns and time-of-day
- **Consumption Prediction**: Forecasts energy usage trends
- **Battery Optimization**: Predicts optimal battery charge/discharge cycles
- **Smart Recommendations**: AI-generated suggestions for energy efficiency
- **Accuracy Tracking**: Real-time monitoring of prediction accuracy (MAE metrics)

### 2. Anomaly Detection
- **Real-time Monitoring**: Detects unusual sensor readings using statistical analysis (z-score)
- **Severity Classification**: Categorizes anomalies as Low, Medium, High, or Critical
- **Sensor Health Tracking**: Monitors health status of all sensors
- **Pattern Recognition**: Identifies deviations from normal operating parameters
- **Alert System**: Provides detailed descriptions of detected anomalies
- **Sensor Failure Detection**: Identifies malfunctioning sensors
- **Security Threat Detection**: Detects unusual patterns indicating security issues
- **Energy Waste Detection**: Identifies inefficient energy usage patterns

### 3. ML Prescriptive Control (Random Forest Classifier)
- **Automated Actuator Control**: ML model predicts optimal actuator states
- **Multi-Model Architecture**: Separate Random Forest models for HVAC, lighting, irrigation, ventilation, and alarms
- **Feature Extraction**: Uses 14 features including sensors, energy, and time data
- **High Accuracy**: Target 92%+ accuracy as per IEEE paper requirements
- **Energy-Aware Decisions**: Considers renewable energy availability in predictions
- **Continuous Learning**: Collects training data and retrains periodically
- **Safety Constraints**: Validates all ML predictions against safety rules

### 4. Edge Preprocessing Layer
- **Local Filtering**: Outlier detection and removal at sensor level
- **Data Smoothing**: Exponential moving average for noise reduction
- **Quality Assurance**: Data validation before transmission
- **Bandwidth Reduction**: Filters out ~18% of noisy data
- **Statistical Analysis**: Real-time mean, std, min, max tracking

### 5. Gateway Intelligence
- **Protocol Translation**: Converts between JSON, XML, and SOAP formats
- **Energy-Aware Scheduling**: Prioritizes data transmission during high renewable availability
- **Priority Queuing**: High/normal/low priority message handling
- **Data Buffering**: Local storage during low energy periods
- **Security Enforcement**: Message integrity and authentication

Access AI features through the **🤖 AI Intelligence** tab with nested **Predictions** and **Anomaly Detection** sub-tabs.

## 🌟 Features

- Modern GUI with real-time monitoring
- Interactive floor plan visualization
- Energy management (solar/wind/battery)
- Water system with rainwater harvesting
- MongoDB data persistence with encryption
- Multiple data formats (JSON/XML/Mixed)
- Real-time analytics and charts
- Device authentication and secure communication
- **AI-powered predictive energy management**
- **Real-time anomaly detection for sensors**