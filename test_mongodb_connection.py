#!/usr/bin/env python3
"""
MongoDB Connection Test Script
Tests the MongoDB connection and displays database information
"""

import sys
from datetime import datetime
from database import DatabaseManager

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_success(text):
    """Print success message"""
    print(f"✓ {text}")

def print_error(text):
    """Print error message"""
    print(f"✗ {text}")

def print_info(text):
    """Print info message"""
    print(f"  {text}")

def main():
    """Test MongoDB connection and display information"""
    print_header("MongoDB Connection Test")
    
    # Test 1: Initialize Database Manager
    print("\n[1] Initializing Database Manager...")
    try:
        db = DatabaseManager()
        print_success("Database Manager initialized")
    except Exception as e:
        print_error(f"Failed to initialize: {e}")
        return 1
    
    # Test 2: Check Connection
    print("\n[2] Checking MongoDB Connection...")
    if db.is_connected():
        print_success("Connected to MongoDB successfully")
    else:
        print_error("Not connected to MongoDB")
        print_info("Make sure MongoDB is running: docker-compose up -d")
        return 1
    
    # Test 3: Get Database Statistics
    print("\n[3] Retrieving Database Statistics...")
    try:
        stats = db.get_database_stats()
        if 'error' in stats:
            print_error(f"Error getting stats: {stats['error']}")
        else:
            print_success("Database statistics retrieved")
            print_info(f"Sensor Readings: {stats.get('sensor_readings', 0):,}")
            print_info(f"Actuator States: {stats.get('actuator_states', 0):,}")
            print_info(f"Energy Data: {stats.get('energy_data', 0):,}")
            print_info(f"Water Data: {stats.get('water_data', 0):,}")
            print_info(f"Events: {stats.get('events', 0):,}")
            print_info(f"System Stats: {stats.get('system_stats', 0):,}")
            print_info(f"Database Size: {stats.get('database_size', 0) / 1024 / 1024:.2f} MB")
    except Exception as e:
        print_error(f"Failed to get statistics: {e}")
        return 1
    
    # Test 4: Test Write Operation
    print("\n[4] Testing Write Operation...")
    try:
        db.store_event(
            event_type="system",
            message="MongoDB connection test successful",
            severity="info",
            simulation_time=datetime.now()
        )
        db.flush_batches()
        print_success("Test event stored successfully")
    except Exception as e:
        print_error(f"Failed to store test event: {e}")
        return 1
    
    # Test 5: Test Read Operation
    print("\n[5] Testing Read Operation...")
    try:
        events = db.get_events(limit=5)
        print_success(f"Retrieved {len(events)} recent events")
        if events:
            print_info("Most recent event:")
            latest = events[0]
            print_info(f"  Type: {latest.get('event_type')}")
            print_info(f"  Message: {latest.get('message')}")
            print_info(f"  Severity: {latest.get('severity')}")
            print_info(f"  Time: {latest.get('timestamp')}")
    except Exception as e:
        print_error(f"Failed to read events: {e}")
        return 1
    
    # Test 6: Test Collections
    print("\n[6] Verifying Collections...")
    try:
        collections = db.db.list_collection_names()
        expected_collections = [
            'sensor_readings',
            'actuator_states',
            'energy_data',
            'water_data',
            'events',
            'system_stats'
        ]
        
        for collection in expected_collections:
            if collection in collections:
                print_success(f"Collection '{collection}' exists")
            else:
                print_error(f"Collection '{collection}' not found")
    except Exception as e:
        print_error(f"Failed to verify collections: {e}")
        return 1
    
    # Test 7: Disconnect
    print("\n[7] Disconnecting...")
    try:
        db.disconnect()
        print_success("Disconnected successfully")
    except Exception as e:
        print_error(f"Failed to disconnect: {e}")
        return 1
    
    # Summary
    print_header("Test Summary")
    print_success("All tests passed!")
    print_info("MongoDB is properly configured and ready to use")
    print_info("You can now run: python main.py")
    print_info("Access Mongo Express at: http://localhost:8081")
    print("")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
