// MongoDB Initialization Script
// This script runs when the MongoDB container is first created

// Switch to the smart home database
db = db.getSiblingDB('smart_home_iot');

// Create collections with validation schemas
db.createCollection('sensor_readings', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['sensor_id', 'sensor_type', 'room', 'value', 'timestamp'],
            properties: {
                sensor_id: {
                    bsonType: 'string',
                    description: 'Unique sensor identifier'
                },
                sensor_type: {
                    bsonType: 'string',
                    description: 'Type of sensor (Temperature, Light, Motion, etc.)'
                },
                room: {
                    bsonType: 'string',
                    description: 'Room where sensor is located'
                },
                value: {
                    bsonType: 'double',
                    description: 'Sensor reading value'
                },
                unit: {
                    bsonType: 'string',
                    description: 'Unit of measurement'
                },
                timestamp: {
                    bsonType: 'date',
                    description: 'Time of reading'
                },
                simulation_time: {
                    bsonType: 'date',
                    description: 'Simulated time in the application'
                }
            }
        }
    }
});

db.createCollection('actuator_states', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['actuator_id', 'actuator_type', 'room', 'state', 'timestamp'],
            properties: {
                actuator_id: {
                    bsonType: 'string',
                    description: 'Unique actuator identifier'
                },
                actuator_type: {
                    bsonType: 'string',
                    description: 'Type of actuator'
                },
                room: {
                    bsonType: 'string',
                    description: 'Room where actuator is located'
                },
                state: {
                    bsonType: 'bool',
                    description: 'On/Off state'
                },
                power_consumption: {
                    bsonType: 'double',
                    description: 'Current power consumption in watts'
                },
                timestamp: {
                    bsonType: 'date',
                    description: 'Time of state change'
                },
                simulation_time: {
                    bsonType: 'date',
                    description: 'Simulated time in the application'
                }
            }
        }
    }
});

db.createCollection('energy_data', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'solar_generation', 'wind_generation', 'total_consumption'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Time of measurement'
                },
                simulation_time: {
                    bsonType: 'date',
                    description: 'Simulated time in the application'
                },
                solar_generation: {
                    bsonType: 'double',
                    description: 'Solar power generation in watts'
                },
                wind_generation: {
                    bsonType: 'double',
                    description: 'Wind power generation in watts'
                },
                total_generation: {
                    bsonType: 'double',
                    description: 'Total renewable generation in watts'
                },
                total_consumption: {
                    bsonType: 'double',
                    description: 'Total power consumption in watts'
                },
                battery_level: {
                    bsonType: 'double',
                    description: 'Battery charge level in kWh'
                },
                battery_percentage: {
                    bsonType: 'double',
                    description: 'Battery charge percentage'
                },
                grid_import: {
                    bsonType: 'double',
                    description: 'Power imported from grid in watts'
                },
                grid_export: {
                    bsonType: 'double',
                    description: 'Power exported to grid in watts'
                }
            }
        }
    }
});

db.createCollection('water_data', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'rainwater_level', 'consumption'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Time of measurement'
                },
                simulation_time: {
                    bsonType: 'date',
                    description: 'Simulated time in the application'
                },
                rainwater_level: {
                    bsonType: 'double',
                    description: 'Rainwater tank level in liters'
                },
                rainwater_percentage: {
                    bsonType: 'double',
                    description: 'Rainwater tank percentage'
                },
                consumption: {
                    bsonType: 'double',
                    description: 'Water consumption in liters'
                },
                rainfall: {
                    bsonType: 'double',
                    description: 'Rainfall amount in mm'
                }
            }
        }
    }
});

db.createCollection('events', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'event_type', 'message', 'severity'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Time of event'
                },
                simulation_time: {
                    bsonType: 'date',
                    description: 'Simulated time in the application'
                },
                event_type: {
                    bsonType: 'string',
                    enum: ['sensor', 'actuator', 'control', 'energy', 'water', 'network', 'system'],
                    description: 'Type of event'
                },
                message: {
                    bsonType: 'string',
                    description: 'Event message'
                },
                severity: {
                    bsonType: 'string',
                    enum: ['info', 'warning', 'critical'],
                    description: 'Event severity level'
                },
                room: {
                    bsonType: 'string',
                    description: 'Associated room (if applicable)'
                }
            }
        }
    }
});

db.createCollection('system_stats', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'cycle_count'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Time of measurement'
                },
                simulation_time: {
                    bsonType: 'date',
                    description: 'Simulated time in the application'
                },
                cycle_count: {
                    bsonType: 'int',
                    description: 'Simulation cycle number'
                },
                num_people: {
                    bsonType: 'int',
                    description: 'Number of occupants'
                },
                active_sensors: {
                    bsonType: 'int',
                    description: 'Number of active sensors'
                },
                active_actuators: {
                    bsonType: 'int',
                    description: 'Number of active actuators'
                },
                network_packets: {
                    bsonType: 'int',
                    description: 'Network packets transmitted'
                }
            }
        }
    }
});

// Create indexes for better query performance
db.sensor_readings.createIndex({ 'timestamp': -1 });
db.sensor_readings.createIndex({ 'sensor_id': 1, 'timestamp': -1 });
db.sensor_readings.createIndex({ 'room': 1, 'timestamp': -1 });
db.sensor_readings.createIndex({ 'sensor_type': 1, 'timestamp': -1 });

db.actuator_states.createIndex({ 'timestamp': -1 });
db.actuator_states.createIndex({ 'actuator_id': 1, 'timestamp': -1 });
db.actuator_states.createIndex({ 'room': 1, 'timestamp': -1 });

db.energy_data.createIndex({ 'timestamp': -1 });
db.energy_data.createIndex({ 'simulation_time': -1 });

db.water_data.createIndex({ 'timestamp': -1 });
db.water_data.createIndex({ 'simulation_time': -1 });

db.events.createIndex({ 'timestamp': -1 });
db.events.createIndex({ 'event_type': 1, 'timestamp': -1 });
db.events.createIndex({ 'severity': 1, 'timestamp': -1 });

db.system_stats.createIndex({ 'timestamp': -1 });
db.system_stats.createIndex({ 'cycle_count': 1 });

print('✓ Smart Home IoT database initialized successfully');
print('✓ Collections created with validation schemas');
print('✓ Indexes created for optimal query performance');
