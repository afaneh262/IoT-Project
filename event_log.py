"""
Event Logging System
Tracks all control decisions, rule evaluations, and system events
"""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    # Create dummy pygame module for type hints
    class DummyPygame:
        class Surface:
            pass
    pygame = DummyPygame()

from datetime import datetime
from typing import List, Tuple
from collections import deque
from config import (MAX_LOG_ENTRIES, LOG_PANEL_WIDTH, LOG_PANEL_HEIGHT,
                   WHITE, LIGHT_GRAY, DARK_GRAY, BRIGHT_YELLOW, ORANGE, RED, YELLOW)

# ============================================================================
# EVENT LOG
# ============================================================================

class EventLog:
    """Manages and displays system events and control decisions"""
    
    def __init__(self):
        self.events = deque(maxlen=MAX_LOG_ENTRIES)
        self.scroll_offset = 0
        self.max_visible_entries = 20
        
    def add_event(self, event_type: str, message: str, severity: str = "info"):
        """
        Add an event to the log
        event_type: sensor, actuator, control, energy, water, network, system
        severity: info, warning, critical
        """
        timestamp = datetime.now()
        self.events.append({
            "time": timestamp,
            "type": event_type,
            "message": message,
            "severity": severity
        })
        
    def log_sensor_reading(self, sensor_type: str, room: str, value: float):
        """Log a sensor reading"""
        self.add_event("sensor", 
                      f"{room}: {sensor_type} = {value:.1f}",
                      "info")
    
    def log_control_decision(self, actuator: str, room: str, action: str, reason: str):
        """Log a control decision with reasoning"""
        self.add_event("control",
                      f"{room}: {action} {actuator} - {reason}",
                      "info")
    
    def log_rule_evaluation(self, rule_name: str, result: bool, conditions: str):
        """Log rule evaluation"""
        result_str = "✓ PASS" if result else "✗ FAIL"
        self.add_event("control",
                      f"Rule '{rule_name}': {result_str} ({conditions})",
                      "info")
    
    def log_energy_event(self, event: str, details: str):
        """Log energy system event"""
        self.add_event("energy", f"{event}: {details}", "info")
    
    def log_water_event(self, event: str, details: str):
        """Log water system event"""
        self.add_event("water", f"{event}: {details}", "info")
    
    def log_network_event(self, event: str, details: str):
        """Log network event"""
        self.add_event("network", f"{event}: {details}", "info")
    
    def log_warning(self, message: str):
        """Log a warning"""
        self.add_event("system", message, "warning")
    
    def log_critical(self, message: str):
        """Log a critical event"""
        self.add_event("system", message, "critical")
    
    def scroll_up(self):
        """Scroll log up"""
        if self.scroll_offset > 0:
            self.scroll_offset -= 1
    
    def scroll_down(self):
        """Scroll log down"""
        max_scroll = max(0, len(self.events) - self.max_visible_entries)
        if self.scroll_offset < max_scroll:
            self.scroll_offset += 1
    
    def get_visible_events(self) -> List[dict]:
        """Get currently visible events based on scroll"""
        events_list = list(self.events)
        events_list.reverse()  # Most recent first
        
        start_idx = self.scroll_offset
        end_idx = start_idx + self.max_visible_entries
        
        return events_list[start_idx:end_idx]
    
    def clear(self):
        """Clear all events"""
        self.events.clear()
        self.scroll_offset = 0


# ============================================================================
# EVENT LOG RENDERER
# ============================================================================

class EventLogRenderer:
    """Renders the event log panel"""
    
    def __init__(self, screen: pygame.Surface):
        if not PYGAME_AVAILABLE:
            raise ImportError("EventLogRenderer requires pygame")
        self.screen = screen
        self.font_small = pygame.font.Font(None, 16)
        self.font_tiny = pygame.font.Font(None, 14)
        self.font_title = pygame.font.Font(None, 20)
        
        # Colors by event type
        self.type_colors = {
            "sensor": (100, 150, 255),      # Light blue
            "actuator": (255, 200, 100),    # Orange
            "control": (100, 255, 100),     # Green
            "energy": (255, 255, 100),      # Yellow
            "water": (100, 200, 255),       # Cyan
            "network": (200, 100, 255),     # Purple
            "system": (150, 150, 150),      # Gray
        }
        
        # Colors by severity
        self.severity_colors = {
            "info": WHITE,
            "warning": ORANGE,
            "critical": RED
        }
        
        # Icon symbols
        self.type_icons = {
            "sensor": "📊",
            "actuator": "🔧",
            "control": "🎛️",
            "energy": "⚡",
            "water": "💧",
            "network": "📡",
            "system": "⚙️"
        }
    
    def draw_log_panel(self, event_log: EventLog, x: int, y: int):
        """Draw the event log panel"""
        width = LOG_PANEL_WIDTH
        height = LOG_PANEL_HEIGHT
        
        # Panel background
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, WHITE, panel_rect, 2)
        
        # Title bar
        title_rect = pygame.Rect(x, y, width, 30)
        pygame.draw.rect(self.screen, (20, 20, 30), title_rect)
        pygame.draw.rect(self.screen, WHITE, title_rect, 2)
        
        title_text = self.font_title.render("📋 Event Log", True, BRIGHT_YELLOW)
        self.screen.blit(title_text, (x + 10, y + 7))
        
        # Event count
        count_text = self.font_tiny.render(f"{len(event_log.events)} events", True, LIGHT_GRAY)
        self.screen.blit(count_text, (x + width - 80, y + 10))
        
        # Draw events
        visible_events = event_log.get_visible_events()
        entry_y = y + 35
        line_height = 18
        
        for event in visible_events:
            if entry_y + line_height > y + height - 5:
                break
            
            # Event type icon and color
            event_type = event["type"]
            icon = self.type_icons.get(event_type, "•")
            type_color = self.type_colors.get(event_type, WHITE)
            severity_color = self.severity_colors.get(event["severity"], WHITE)
            
            # Time
            time_str = event["time"].strftime("%H:%M:%S")
            time_surf = self.font_tiny.render(time_str, True, LIGHT_GRAY)
            self.screen.blit(time_surf, (x + 5, entry_y))
            
            # Icon
            icon_surf = self.font_small.render(icon, True, type_color)
            self.screen.blit(icon_surf, (x + 65, entry_y))
            
            # Message (truncate if too long)
            message = event["message"]
            if len(message) > 35:
                message = message[:32] + "..."
            
            msg_surf = self.font_small.render(message, True, severity_color)
            self.screen.blit(msg_surf, (x + 85, entry_y))
            
            entry_y += line_height
        
        # Scroll indicator
        if len(event_log.events) > event_log.max_visible_entries:
            scroll_text = f"↑↓ {event_log.scroll_offset + 1}/{len(event_log.events)}"
            scroll_surf = self.font_tiny.render(scroll_text, True, YELLOW)
            self.screen.blit(scroll_surf, (x + width - 60, y + height - 20))
        
        # Instructions
        help_text = "Scroll: ↑↓ | Clear: C"
        help_surf = self.font_tiny.render(help_text, True, DARK_GRAY)
        self.screen.blit(help_surf, (x + 5, y + height - 20))
