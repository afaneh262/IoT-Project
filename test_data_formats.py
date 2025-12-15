#!/usr/bin/env python3
"""
Data Format Testing Script
Demonstrates JSON, XML, and mixed format serialization
"""

from datetime import datetime
from data_formats import (
    DataFormat, JSONSerializer, XMLSerializer, 
    MixedFormatManager, format_to_string, DataFormatConverter
)

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_subheader(text):
    """Print formatted subheader"""
    print(f"\n--- {text} ---")

def test_json_format():
    """Test JSON serialization"""
    print_header("JSON Format Testing")
    
    serializer = JSONSerializer()
    
    # Test sensor reading
    print_subheader("Sensor Reading (JSON)")
    sensor_data = serializer.serialize_sensor_reading(
        sensor_id="TEMP-001",
        sensor_type="Temperature",
        room="Living Room",
        value=22.5,
        unit="°C",
        timestamp=datetime.now()
    )
    print(format_to_string(sensor_data, DataFormat.JSON))
    
    # Test actuator state
    print_subheader("Actuator State (JSON)")
    actuator_data = serializer.serialize_actuator_state(
        actuator_id="LIGHT-ACT-001",
        actuator_type="Light",
        room="Living Room",
        state=True,
        power=15.0,
        timestamp=datetime.now()
    )
    print(format_to_string(actuator_data, DataFormat.JSON))

def test_xml_format():
    """Test XML serialization"""
    print_header("XML Format Testing")
    
    serializer = XMLSerializer()
    
    # Test sensor reading
    print_subheader("Sensor Reading (XML)")
    sensor_data = serializer.serialize_sensor_reading(
        sensor_id="TEMP-001",
        sensor_type="Temperature",
        room="Living Room",
        value=22.5,
        unit="°C",
        timestamp=datetime.now()
    )
    print(format_to_string(sensor_data, DataFormat.XML))
    
    # Test actuator state
    print_subheader("Actuator State (XML)")
    actuator_data = serializer.serialize_actuator_state(
        actuator_id="LIGHT-ACT-001",
        actuator_type="Light",
        room="Living Room",
        state=True,
        power=15.0,
        timestamp=datetime.now()
    )
    print(format_to_string(actuator_data, DataFormat.XML))

def test_mixed_format():
    """Test mixed format serialization"""
    print_header("Mixed Format Testing")
    
    manager = MixedFormatManager(json_probability=0.5)
    
    print_subheader("Simulating 10 Transmissions")
    
    for i in range(10):
        # Sensor reading
        data, format_used = manager.serialize_sensor_reading(
            sensor_id=f"TEMP-{i:03d}",
            sensor_type="Temperature",
            room="Living Room",
            value=20.0 + i,
            unit="°C",
            timestamp=datetime.now()
        )
        print(f"\nTransmission {i+1}: {format_used.value.upper()}")
        
        # Show first 200 chars of serialized data
        data_str = format_to_string(data, format_used)
        preview = data_str[:200] + "..." if len(data_str) > 200 else data_str
        print(preview)
    
    # Show statistics
    print_subheader("Format Statistics")
    stats = manager.get_format_statistics()
    print(f"Total Transmissions: {stats['total_transmissions']}")
    print(f"JSON Messages: {stats['json_count']} ({stats['json_percentage']:.1f}%)")
    print(f"XML Messages: {stats['xml_count']} ({stats['xml_percentage']:.1f}%)")

def test_format_conversion():
    """Test format conversion"""
    print_header("Format Conversion Testing")
    
    # Create JSON data
    json_serializer = JSONSerializer()
    json_data = json_serializer.serialize_sensor_reading(
        sensor_id="TEMP-001",
        sensor_type="Temperature",
        room="Living Room",
        value=22.5,
        unit="°C",
        timestamp=datetime.now()
    )
    
    print_subheader("Original JSON")
    print(format_to_string(json_data, DataFormat.JSON))
    
    # Convert to XML
    print_subheader("Converted to XML")
    xml_element = DataFormatConverter.json_to_xml(json_data)
    print(format_to_string(xml_element, DataFormat.XML))
    
    # Convert back to JSON
    print_subheader("Converted Back to JSON")
    json_data_back = DataFormatConverter.xml_to_json(xml_element)
    import json
    print(json.dumps(json_data_back, indent=2))

def test_size_comparison():
    """Compare payload sizes"""
    print_header("Payload Size Comparison")
    
    json_serializer = JSONSerializer()
    xml_serializer = XMLSerializer()
    
    # Same data in both formats
    timestamp = datetime.now()
    
    # JSON
    json_data = json_serializer.serialize_sensor_reading(
        sensor_id="TEMP-001",
        sensor_type="Temperature",
        room="Living Room",
        value=22.5,
        unit="°C",
        timestamp=timestamp
    )
    json_str = format_to_string(json_data, DataFormat.JSON)
    json_size = len(json_str.encode('utf-8'))
    
    # XML
    xml_data = xml_serializer.serialize_sensor_reading(
        sensor_id="TEMP-001",
        sensor_type="Temperature",
        room="Living Room",
        value=22.5,
        unit="°C",
        timestamp=timestamp
    )
    xml_str = format_to_string(xml_data, DataFormat.XML)
    xml_size = len(xml_str.encode('utf-8'))
    
    print(f"\nJSON Payload Size: {json_size} bytes")
    print(f"XML Payload Size: {xml_size} bytes")
    print(f"Difference: {xml_size - json_size} bytes ({(xml_size/json_size - 1) * 100:.1f}% larger)")
    
    # Estimate for 1000 messages
    print(f"\nFor 1,000 messages:")
    print(f"JSON: {json_size * 1000 / 1024:.2f} KB")
    print(f"XML: {xml_size * 1000 / 1024:.2f} KB")
    print(f"Savings with JSON: {(xml_size - json_size) * 1000 / 1024:.2f} KB")

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  IoT DATA FORMAT TESTING SUITE")
    print("=" * 80)
    
    try:
        # Run tests
        test_json_format()
        test_xml_format()
        test_mixed_format()
        test_format_conversion()
        test_size_comparison()
        
        # Summary
        print_header("Test Summary")
        print("✓ All format tests completed successfully")
        print("\nKey Findings:")
        print("  - JSON is more compact and faster to parse")
        print("  - XML provides better structure and validation")
        print("  - Mixed mode simulates real heterogeneous IoT networks")
        print("  - Format conversion is possible between JSON and XML")
        print("\nNext Steps:")
        print("  1. Set DATA_FORMAT_MODE in .env (json, xml, or mixed)")
        print("  2. Run: python main.py")
        print("  3. Check MongoDB for format distribution")
        print("")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
