"""
Data Format Serializers for IoT Sensor Communication
Supports JSON, XML, and mixed format transmissions
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Literal
from enum import Enum
import random

# ============================================================================
# DATA FORMAT TYPES
# ============================================================================

class DataFormat(Enum):
    """Supported data transmission formats"""
    JSON = "json"
    XML = "xml"
    MIXED = "mixed"  # Randomly alternates between JSON and XML

# ============================================================================
# JSON SERIALIZER
# ============================================================================

class JSONSerializer:
    """Serialize sensor data to JSON format"""
    
    @staticmethod
    def serialize_sensor_reading(sensor_id: str, sensor_type: str, room: str,
                                value: float, unit: str, timestamp: datetime) -> Dict[str, Any]:
        """
        Serialize sensor reading to JSON
        
        Returns:
            Dictionary representing JSON structure
        """
        return {
            "protocol": "JSON",
            "message_type": "sensor_reading",
            "timestamp": timestamp.isoformat(),
            "sensor": {
                "id": sensor_id,
                "type": sensor_type,
                "location": room
            },
            "measurement": {
                "value": value,
                "unit": unit
            },
            "metadata": {
                "format_version": "1.0",
                "encoding": "utf-8"
            }
        }
    
    @staticmethod
    def serialize_actuator_state(actuator_id: str, actuator_type: str, room: str,
                                state: bool, power: float, timestamp: datetime) -> Dict[str, Any]:
        """Serialize actuator state to JSON"""
        return {
            "protocol": "JSON",
            "message_type": "actuator_state",
            "timestamp": timestamp.isoformat(),
            "actuator": {
                "id": actuator_id,
                "type": actuator_type,
                "location": room
            },
            "state": {
                "active": state,
                "power_consumption": power,
                "unit": "watts"
            },
            "metadata": {
                "format_version": "1.0",
                "encoding": "utf-8"
            }
        }
    
    @staticmethod
    def to_string(data: Dict[str, Any]) -> str:
        """Convert to JSON string"""
        return json.dumps(data, indent=2)

# ============================================================================
# XML SERIALIZER
# ============================================================================

class XMLSerializer:
    """Serialize sensor data to XML format"""
    
    @staticmethod
    def serialize_sensor_reading(sensor_id: str, sensor_type: str, room: str,
                                value: float, unit: str, timestamp: datetime) -> ET.Element:
        """
        Serialize sensor reading to XML
        
        Returns:
            XML Element tree
        """
        root = ET.Element("iot_message", protocol="XML", version="1.0")
        
        # Message type
        msg_type = ET.SubElement(root, "message_type")
        msg_type.text = "sensor_reading"
        
        # Timestamp
        ts = ET.SubElement(root, "timestamp")
        ts.text = timestamp.isoformat()
        
        # Sensor info
        sensor = ET.SubElement(root, "sensor")
        sensor_id_elem = ET.SubElement(sensor, "id")
        sensor_id_elem.text = sensor_id
        sensor_type_elem = ET.SubElement(sensor, "type")
        sensor_type_elem.text = sensor_type
        location = ET.SubElement(sensor, "location")
        location.text = room
        
        # Measurement
        measurement = ET.SubElement(root, "measurement")
        value_elem = ET.SubElement(measurement, "value")
        value_elem.text = str(value)
        unit_elem = ET.SubElement(measurement, "unit")
        unit_elem.text = unit
        
        # Metadata
        metadata = ET.SubElement(root, "metadata")
        encoding = ET.SubElement(metadata, "encoding")
        encoding.text = "utf-8"
        
        return root
    
    @staticmethod
    def serialize_actuator_state(actuator_id: str, actuator_type: str, room: str,
                                state: bool, power: float, timestamp: datetime) -> ET.Element:
        """Serialize actuator state to XML"""
        root = ET.Element("iot_message", protocol="XML", version="1.0")
        
        # Message type
        msg_type = ET.SubElement(root, "message_type")
        msg_type.text = "actuator_state"
        
        # Timestamp
        ts = ET.SubElement(root, "timestamp")
        ts.text = timestamp.isoformat()
        
        # Actuator info
        actuator = ET.SubElement(root, "actuator")
        actuator_id_elem = ET.SubElement(actuator, "id")
        actuator_id_elem.text = actuator_id
        actuator_type_elem = ET.SubElement(actuator, "type")
        actuator_type_elem.text = actuator_type
        location = ET.SubElement(actuator, "location")
        location.text = room
        
        # State
        state_elem = ET.SubElement(root, "state")
        active = ET.SubElement(state_elem, "active")
        active.text = str(state).lower()
        power_elem = ET.SubElement(state_elem, "power_consumption")
        power_elem.text = str(power)
        unit_elem = ET.SubElement(state_elem, "unit")
        unit_elem.text = "watts"
        
        # Metadata
        metadata = ET.SubElement(root, "metadata")
        encoding = ET.SubElement(metadata, "encoding")
        encoding.text = "utf-8"
        
        return root
    
    @staticmethod
    def to_string(element: ET.Element) -> str:
        """Convert XML element to string"""
        ET.indent(element, space="  ")
        return ET.tostring(element, encoding='unicode')

# ============================================================================
# MIXED FORMAT MANAGER
# ============================================================================

class MixedFormatManager:
    """
    Manages mixed format transmissions
    Randomly selects between JSON and XML for each transmission
    """
    
    def __init__(self, json_probability: float = 0.5):
        """
        Initialize mixed format manager
        
        Args:
            json_probability: Probability of using JSON (0.0 to 1.0)
        """
        self.json_probability = json_probability
        self.json_serializer = JSONSerializer()
        self.xml_serializer = XMLSerializer()
        self.transmission_log = []
    
    def select_format(self) -> DataFormat:
        """Randomly select format based on probability"""
        return DataFormat.JSON if random.random() < self.json_probability else DataFormat.XML
    
    def serialize_sensor_reading(self, sensor_id: str, sensor_type: str, room: str,
                                value: float, unit: str, timestamp: datetime,
                                force_format: DataFormat = None) -> tuple[Any, DataFormat]:
        """
        Serialize sensor reading in mixed format
        
        Returns:
            Tuple of (serialized_data, format_used)
        """
        format_used = force_format or self.select_format()
        
        if format_used == DataFormat.JSON:
            data = self.json_serializer.serialize_sensor_reading(
                sensor_id, sensor_type, room, value, unit, timestamp
            )
        else:  # XML
            data = self.xml_serializer.serialize_sensor_reading(
                sensor_id, sensor_type, room, value, unit, timestamp
            )
        
        # Log transmission
        self.transmission_log.append({
            'type': 'sensor_reading',
            'format': format_used.value,
            'sensor_id': sensor_id,
            'timestamp': timestamp
        })
        
        return data, format_used
    
    def serialize_actuator_state(self, actuator_id: str, actuator_type: str, room: str,
                                state: bool, power: float, timestamp: datetime,
                                force_format: DataFormat = None) -> tuple[Any, DataFormat]:
        """
        Serialize actuator state in mixed format
        
        Returns:
            Tuple of (serialized_data, format_used)
        """
        format_used = force_format or self.select_format()
        
        if format_used == DataFormat.JSON:
            data = self.json_serializer.serialize_actuator_state(
                actuator_id, actuator_type, room, state, power, timestamp
            )
        else:  # XML
            data = self.xml_serializer.serialize_actuator_state(
                actuator_id, actuator_type, room, state, power, timestamp
            )
        
        # Log transmission
        self.transmission_log.append({
            'type': 'actuator_state',
            'format': format_used.value,
            'actuator_id': actuator_id,
            'timestamp': timestamp
        })
        
        return data, format_used
    
    def get_format_statistics(self) -> Dict[str, Any]:
        """Get statistics about format usage"""
        if not self.transmission_log:
            return {
                'total_transmissions': 0,
                'json_count': 0,
                'xml_count': 0,
                'json_percentage': 0.0,
                'xml_percentage': 0.0
            }
        
        json_count = sum(1 for t in self.transmission_log if t['format'] == 'json')
        xml_count = sum(1 for t in self.transmission_log if t['format'] == 'xml')
        total = len(self.transmission_log)
        
        return {
            'total_transmissions': total,
            'json_count': json_count,
            'xml_count': xml_count,
            'json_percentage': (json_count / total * 100) if total > 0 else 0.0,
            'xml_percentage': (xml_count / total * 100) if total > 0 else 0.0
        }
    
    def clear_log(self):
        """Clear transmission log"""
        self.transmission_log.clear()

# ============================================================================
# DATA FORMAT CONVERTER
# ============================================================================

class DataFormatConverter:
    """Convert between JSON and XML formats"""
    
    @staticmethod
    def json_to_xml(json_data: Dict[str, Any]) -> ET.Element:
        """Convert JSON data to XML"""
        root = ET.Element("iot_message")
        DataFormatConverter._dict_to_xml(json_data, root)
        return root
    
    @staticmethod
    def _dict_to_xml(data: Dict[str, Any], parent: ET.Element):
        """Recursively convert dictionary to XML"""
        for key, value in data.items():
            if isinstance(value, dict):
                child = ET.SubElement(parent, key)
                DataFormatConverter._dict_to_xml(value, child)
            elif isinstance(value, list):
                for item in value:
                    child = ET.SubElement(parent, key)
                    if isinstance(item, dict):
                        DataFormatConverter._dict_to_xml(item, child)
                    else:
                        child.text = str(item)
            else:
                child = ET.SubElement(parent, key)
                child.text = str(value)
    
    @staticmethod
    def xml_to_json(xml_element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to JSON"""
        result = {}
        
        # Add attributes
        if xml_element.attrib:
            result.update(xml_element.attrib)
        
        # Add text content
        if xml_element.text and xml_element.text.strip():
            result['_text'] = xml_element.text.strip()
        
        # Add children
        for child in xml_element:
            child_data = DataFormatConverter.xml_to_json(child)
            if child.tag in result:
                # Convert to list if multiple children with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_serializer(format_type: DataFormat) -> Any:
    """Get appropriate serializer for format type"""
    if format_type == DataFormat.JSON:
        return JSONSerializer()
    elif format_type == DataFormat.XML:
        return XMLSerializer()
    elif format_type == DataFormat.MIXED:
        return MixedFormatManager()
    else:
        raise ValueError(f"Unknown format type: {format_type}")

def format_to_string(data: Any, format_type: DataFormat) -> str:
    """Convert serialized data to string representation"""
    if format_type == DataFormat.JSON:
        return JSONSerializer.to_string(data)
    elif format_type == DataFormat.XML:
        return XMLSerializer.to_string(data)
    else:
        # For mixed format, determine type from data
        if isinstance(data, dict):
            return JSONSerializer.to_string(data)
        elif isinstance(data, ET.Element):
            return XMLSerializer.to_string(data)
        else:
            return str(data)
