"""
Gateway Intelligence Layer
Handles protocol translation, data aggregation, security enforcement,
and renewable-energy-aware scheduling
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
import hashlib


class ProtocolTranslator:
    """Handles translation between JSON and XML/SOAP formats"""
    
    @staticmethod
    def json_to_xml(data: Dict) -> str:
        """Convert JSON data to XML format"""
        root = ET.Element('SensorData')
        
        for key, value in data.items():
            if isinstance(value, dict):
                child = ET.SubElement(root, key)
                for sub_key, sub_value in value.items():
                    sub_child = ET.SubElement(child, sub_key)
                    sub_child.text = str(sub_value)
            elif isinstance(value, list):
                child = ET.SubElement(root, key)
                for item in value:
                    item_elem = ET.SubElement(child, 'item')
                    if isinstance(item, dict):
                        for k, v in item.items():
                            sub_elem = ET.SubElement(item_elem, k)
                            sub_elem.text = str(v)
                    else:
                        item_elem.text = str(item)
            else:
                child = ET.SubElement(root, key)
                child.text = str(value)
        
        return ET.tostring(root, encoding='unicode')
    
    @staticmethod
    def xml_to_json(xml_string: str) -> Dict:
        """Convert XML data to JSON format"""
        try:
            root = ET.fromstring(xml_string)
            return ProtocolTranslator._element_to_dict(root)
        except ET.ParseError as e:
            return {'error': f'XML parsing error: {str(e)}'}
    
    @staticmethod
    def _element_to_dict(element: ET.Element) -> Dict:
        """Recursively convert XML element to dictionary"""
        result = {}
        
        # Handle attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Handle text content
        if element.text and element.text.strip():
            if len(element) == 0:  # Leaf node
                return element.text.strip()
            result['_text'] = element.text.strip()
        
        # Handle children
        for child in element:
            child_data = ProtocolTranslator._element_to_dict(child)
            if child.tag in result:
                # Multiple children with same tag -> make it a list
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    @staticmethod
    def create_soap_envelope(data: Dict) -> str:
        """Create SOAP envelope for XML data"""
        soap_template = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header>
        <MessageID>{message_id}</MessageID>
        <Timestamp>{timestamp}</Timestamp>
    </soap:Header>
    <soap:Body>
        {body}
    </soap:Body>
</soap:Envelope>'''
        
        message_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]
        timestamp = datetime.now().isoformat()
        body = ProtocolTranslator.json_to_xml(data)
        
        return soap_template.format(
            message_id=message_id,
            timestamp=timestamp,
            body=body
        )
    
    @staticmethod
    def parse_soap_envelope(soap_string: str) -> Dict:
        """Parse SOAP envelope and extract body data"""
        try:
            root = ET.fromstring(soap_string)
            # Find SOAP body
            namespaces = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
            body = root.find('soap:Body', namespaces)
            
            if body is not None and len(body) > 0:
                # Get first child of body
                data_element = body[0]
                return ProtocolTranslator._element_to_dict(data_element)
            
            return {}
        except ET.ParseError as e:
            return {'error': f'SOAP parsing error: {str(e)}'}


class GatewayIntelligence:
    """
    Smart gateway with protocol translation, energy-aware scheduling,
    and data quality assurance
    """
    
    def __init__(self, gateway_id: str):
        self.gateway_id = gateway_id
        self.translator = ProtocolTranslator()
        
        # Data buffers
        self.pending_data = deque(maxlen=1000)
        self.high_priority_queue = deque(maxlen=100)
        self.low_priority_queue = deque(maxlen=500)
        
        # Energy awareness
        self.renewable_energy_available = 0.0  # Watts
        self.energy_threshold_high = 500  # High renewable availability
        self.energy_threshold_low = 100   # Low renewable availability
        
        # Statistics
        self.total_messages_received = 0
        self.total_messages_forwarded = 0
        self.messages_buffered = 0
        self.protocol_translations = 0
        self.energy_delayed_transmissions = 0
        
        # Protocol tracking
        self.json_messages = 0
        self.xml_messages = 0
        self.soap_messages = 0
    
    def receive_sensor_data(self, data: Dict, protocol: str = 'json', 
                           priority: str = 'normal') -> Dict:
        """
        Receive sensor data from edge nodes
        
        Args:
            data: Sensor data dictionary
            protocol: 'json', 'xml', or 'soap'
            priority: 'high', 'normal', or 'low'
        
        Returns:
            Processing status
        """
        self.total_messages_received += 1
        
        # Track protocol usage
        if protocol == 'json':
            self.json_messages += 1
        elif protocol == 'xml':
            self.xml_messages += 1
        elif protocol == 'soap':
            self.soap_messages += 1
        
        # Normalize data to internal JSON format
        normalized_data = self._normalize_data(data, protocol)
        
        # Add gateway metadata
        normalized_data['gateway_id'] = self.gateway_id
        normalized_data['received_at'] = datetime.now().isoformat()
        normalized_data['original_protocol'] = protocol
        
        # Data quality validation
        if not self._validate_data(normalized_data):
            return {
                'status': 'rejected',
                'reason': 'data_validation_failed',
                'gateway_id': self.gateway_id
            }
        
        # Priority-based queuing
        if priority == 'high':
            self.high_priority_queue.append(normalized_data)
        elif priority == 'low':
            self.low_priority_queue.append(normalized_data)
        else:
            self.pending_data.append(normalized_data)
        
        self.messages_buffered += 1
        
        return {
            'status': 'accepted',
            'gateway_id': self.gateway_id,
            'queue_size': len(self.pending_data),
            'protocol': protocol
        }
    
    def _normalize_data(self, data: Any, protocol: str) -> Dict:
        """Normalize data from different protocols to internal format"""
        if protocol == 'json':
            return data if isinstance(data, dict) else {'data': data}
        
        elif protocol == 'xml':
            self.protocol_translations += 1
            if isinstance(data, str):
                return self.translator.xml_to_json(data)
            return data
        
        elif protocol == 'soap':
            self.protocol_translations += 1
            if isinstance(data, str):
                return self.translator.parse_soap_envelope(data)
            return data
        
        return {'data': data}
    
    def _validate_data(self, data: Dict) -> bool:
        """Validate data quality and integrity"""
        # Check for required fields
        if 'sensor_id' not in data and 'data' not in data:
            return False
        
        # Check for timestamp
        if 'timestamp' not in data and 'received_at' not in data:
            return False
        
        # Check for duplicate detection (simplified)
        # In production, would use message IDs and deduplication window
        
        return True
    
    def update_renewable_energy_status(self, available_power: float):
        """Update current renewable energy availability"""
        self.renewable_energy_available = available_power
    
    def should_transmit_now(self) -> bool:
        """
        Determine if data should be transmitted based on energy availability
        Energy-aware scheduling logic
        """
        # Always transmit high-priority data
        if len(self.high_priority_queue) > 0:
            return True
        
        # If renewable energy is high, transmit everything
        if self.renewable_energy_available >= self.energy_threshold_high:
            return True
        
        # If renewable energy is low, only transmit if buffer is full
        if self.renewable_energy_available < self.energy_threshold_low:
            buffer_full = len(self.pending_data) > 800
            if not buffer_full:
                self.energy_delayed_transmissions += 1
            return buffer_full
        
        # Medium energy: transmit periodically
        return len(self.pending_data) > 100
    
    def get_data_for_transmission(self, max_batch_size: int = 50) -> List[Dict]:
        """
        Get batch of data for cloud transmission
        Prioritizes based on energy availability and message priority
        """
        if not self.should_transmit_now():
            return []
        
        batch = []
        
        # First, send high-priority messages
        while len(self.high_priority_queue) > 0 and len(batch) < max_batch_size:
            batch.append(self.high_priority_queue.popleft())
        
        # Then, send normal priority
        while len(self.pending_data) > 0 and len(batch) < max_batch_size:
            batch.append(self.pending_data.popleft())
        
        # Finally, low priority if energy is abundant
        if self.renewable_energy_available >= self.energy_threshold_high:
            while len(self.low_priority_queue) > 0 and len(batch) < max_batch_size:
                batch.append(self.low_priority_queue.popleft())
        
        self.total_messages_forwarded += len(batch)
        self.messages_buffered -= len(batch)
        
        return batch
    
    def convert_to_protocol(self, data: Dict, target_protocol: str) -> Any:
        """Convert data to target protocol format"""
        if target_protocol == 'json':
            return data
        elif target_protocol == 'xml':
            return self.translator.json_to_xml(data)
        elif target_protocol == 'soap':
            return self.translator.create_soap_envelope(data)
        return data
    
    def get_gateway_statistics(self) -> Dict:
        """Get comprehensive gateway statistics"""
        return {
            'gateway_id': self.gateway_id,
            'total_received': self.total_messages_received,
            'total_forwarded': self.total_messages_forwarded,
            'currently_buffered': self.messages_buffered,
            'high_priority_queue': len(self.high_priority_queue),
            'normal_queue': len(self.pending_data),
            'low_priority_queue': len(self.low_priority_queue),
            'protocol_translations': self.protocol_translations,
            'energy_delayed': self.energy_delayed_transmissions,
            'renewable_energy': self.renewable_energy_available,
            'protocol_breakdown': {
                'json': self.json_messages,
                'xml': self.xml_messages,
                'soap': self.soap_messages
            },
            'forwarding_rate': round(
                (self.total_messages_forwarded / self.total_messages_received * 100)
                if self.total_messages_received > 0 else 0, 2
            )
        }
    
    def clear_buffers(self):
        """Clear all data buffers"""
        self.pending_data.clear()
        self.high_priority_queue.clear()
        self.low_priority_queue.clear()
        self.messages_buffered = 0
