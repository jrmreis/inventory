"""
Component classifier to help identify component types
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ComponentClassifier:
    """Classify and categorize electronic components."""

    # Component categories with keywords and characteristics
    COMPONENT_CATEGORIES = {
        'resistor': {
            'keywords': ['resistor', 'resistance', 'ohm', 'Ω', 'kΩ', 'MΩ'],
            'patterns': [r'\d+[kKmM]?[Ωω]', r'\d+\s*ohm'],
            'common_values': ['10k', '1k', '100', '220', '330', '470', '1M'],
            'description': 'Passive component that resists current flow'
        },
        'capacitor': {
            'keywords': ['capacitor', 'cap', 'farad', 'μF', 'nF', 'pF'],
            'patterns': [r'\d+[uμnp]?F', r'\d+\s*farad'],
            'common_values': ['100uF', '10uF', '1uF', '0.1uF', '100nF'],
            'description': 'Passive component that stores electrical energy'
        },
        'arduino': {
            'keywords': ['arduino', 'uno', 'mega', 'nano', 'mini', 'pro micro'],
            'manufacturers': ['Arduino'],
            'models': ['Uno R3', 'Mega 2560', 'Nano', 'Leonardo', 'Due'],
            'description': 'Microcontroller development board'
        },
        'microcontroller': {
            'keywords': ['mcu', 'microcontroller', 'atmega', 'stm32', 'esp32', 'esp8266', 'pic'],
            'manufacturers': ['Atmel', 'STMicroelectronics', 'Espressif', 'Microchip'],
            'common_series': ['ATmega', 'STM32', 'ESP32', 'ESP8266', 'PIC'],
            'description': 'Programmable integrated circuit'
        },
        'connector': {
            'keywords': ['connector', 'header', 'socket', 'jst', 'dupont', 'pin header', 'usb'],
            'types': ['JST', 'Dupont', 'Pin Header', 'USB', 'HDMI', 'RJ45'],
            'common_pitches': ['2.54mm', '2.0mm', '1.27mm'],
            'description': 'Interface for connecting components or wires'
        },
        'ic': {
            'keywords': ['ic', 'integrated circuit', 'chip', 'logic', 'timer', '555', '7805'],
            'common_series': ['74', '40', '555', '78', '79'],
            'packages': ['DIP', 'SOIC', 'QFP', 'BGA'],
            'description': 'Integrated circuit with multiple components'
        },
        'led': {
            'keywords': ['led', 'light emitting diode', 'rgb led', 'smd led'],
            'types': ['Standard', 'RGB', 'SMD', 'High Power', 'UV'],
            'common_colors': ['Red', 'Green', 'Blue', 'Yellow', 'White'],
            'description': 'Light emitting diode'
        },
        'transistor': {
            'keywords': ['transistor', 'mosfet', 'bjt', 'fet', '2n2222', 'bc547'],
            'types': ['BJT', 'MOSFET', 'JFET', 'IGBT'],
            'common_parts': ['2N2222', '2N3904', 'BC547', 'IRFZ44N'],
            'description': 'Semiconductor device for switching or amplification'
        },
        'diode': {
            'keywords': ['diode', 'rectifier', '1n4007', '1n4148', 'schottky'],
            'types': ['Rectifier', 'Schottky', 'Zener', 'LED'],
            'common_parts': ['1N4001', '1N4007', '1N4148', '1N5819'],
            'description': 'Semiconductor allowing current in one direction'
        },
        'sensor': {
            'keywords': ['sensor', 'temperature', 'humidity', 'pressure', 'motion', 'dht', 'bmp'],
            'types': ['Temperature', 'Humidity', 'Pressure', 'Motion', 'Light', 'Gas'],
            'common_parts': ['DHT11', 'DHT22', 'BMP280', 'MPU6050', 'HC-SR04'],
            'description': 'Device that detects and responds to environmental input'
        },
        'display': {
            'keywords': ['display', 'lcd', 'oled', 'tft', 'screen', '7-segment'],
            'types': ['LCD', 'OLED', 'TFT', '7-Segment', 'E-Paper'],
            'common_sizes': ['0.96"', '1.3"', '2.4"', '3.5"'],
            'description': 'Visual output device'
        },
        'module': {
            'keywords': ['module', 'board', 'breakout', 'shield'],
            'types': ['Breakout Board', 'Shield', 'Development Board', 'Adapter'],
            'description': 'Pre-assembled circuit board module'
        },
        'switch': {
            'keywords': ['switch', 'button', 'pushbutton', 'toggle', 'slide'],
            'types': ['Pushbutton', 'Toggle', 'Slide', 'Rotary', 'DIP'],
            'description': 'Mechanical device for controlling electrical flow'
        },
        'relay': {
            'keywords': ['relay', 'solid state relay', 'ssr'],
            'types': ['Electromechanical', 'Solid State', 'Reed'],
            'common_voltages': ['5V', '12V', '24V'],
            'description': 'Electrically operated switch'
        },
    }

    def classify(self, text: str) -> List[str]:
        """
        Classify component based on text description.

        Args:
            text: Text to analyze (name, description, OCR text)

        Returns:
            List of possible component types, ordered by confidence
        """
        text_lower = text.lower()
        matches = []

        for component_type, info in self.COMPONENT_CATEGORIES.items():
            score = 0

            # Check keywords
            for keyword in info.get('keywords', []):
                if keyword.lower() in text_lower:
                    score += 10

            # Check common values/parts
            for value in info.get('common_values', []) + info.get('common_parts', []):
                if value.lower() in text_lower:
                    score += 5

            # Check manufacturers
            for mfr in info.get('manufacturers', []):
                if mfr.lower() in text_lower:
                    score += 3

            if score > 0:
                matches.append((component_type, score))

        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)

        return [match[0] for match in matches]

    def get_component_info(self, component_type: str) -> Optional[Dict]:
        """
        Get information about a component type.

        Args:
            component_type: Type of component

        Returns:
            Dictionary with component information
        """
        return self.COMPONENT_CATEGORIES.get(component_type.lower())

    def suggest_storage_location(self, component_type: str) -> str:
        """
        Suggest storage location based on component type.

        Args:
            component_type: Type of component

        Returns:
            Suggested storage location category
        """
        storage_map = {
            'resistor': 'Passive Components - Resistors',
            'capacitor': 'Passive Components - Capacitors',
            'arduino': 'Development Boards',
            'microcontroller': 'ICs - Microcontrollers',
            'connector': 'Connectors & Headers',
            'ic': 'ICs - General',
            'led': 'Active Components - LEDs',
            'transistor': 'Active Components - Transistors',
            'diode': 'Active Components - Diodes',
            'sensor': 'Sensors & Modules',
            'display': 'Displays',
            'module': 'Modules & Breakouts',
            'switch': 'Switches & Buttons',
            'relay': 'Relays & Switches',
        }

        return storage_map.get(component_type.lower(), 'General Components')

    def get_all_types(self) -> List[str]:
        """Get list of all supported component types."""
        return list(self.COMPONENT_CATEGORIES.keys())

    def get_specification_template(self, component_type: str) -> Dict:
        """
        Get specification template for a component type.

        Args:
            component_type: Type of component

        Returns:
            Dictionary with specification field templates
        """
        templates = {
            'resistor': {
                'resistance': 'e.g., 10kΩ',
                'tolerance': 'e.g., ±5%',
                'power_rating': 'e.g., 0.25W',
                'package': 'e.g., 0805, through-hole'
            },
            'capacitor': {
                'capacitance': 'e.g., 100uF',
                'voltage_rating': 'e.g., 25V',
                'type': 'e.g., electrolytic, ceramic',
                'package': 'e.g., radial, SMD'
            },
            'arduino': {
                'model': 'e.g., Uno R3',
                'voltage': 'e.g., 5V',
                'microcontroller': 'e.g., ATmega328P',
                'digital_pins': 'e.g., 14',
                'analog_pins': 'e.g., 6'
            },
            'microcontroller': {
                'model': 'e.g., STM32F103',
                'architecture': 'e.g., ARM Cortex-M3',
                'frequency': 'e.g., 72MHz',
                'voltage': 'e.g., 3.3V',
                'flash': 'e.g., 64KB',
                'ram': 'e.g., 20KB'
            },
            'connector': {
                'type': 'e.g., JST, pin header',
                'pins': 'e.g., 10',
                'pitch': 'e.g., 2.54mm',
                'mounting': 'e.g., through-hole, SMD'
            },
            'led': {
                'color': 'e.g., Red, RGB',
                'forward_voltage': 'e.g., 2.0V',
                'forward_current': 'e.g., 20mA',
                'package': 'e.g., 5mm, 0603 SMD'
            },
        }

        return templates.get(component_type.lower(), {
            'value': 'Component value',
            'voltage': 'Operating voltage',
            'package': 'Package type'
        })
