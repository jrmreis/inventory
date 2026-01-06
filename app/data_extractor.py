"""
AI-powered data extraction module for component recognition
Uses Groq API with Llama model for intelligent component data extraction
"""

import os
import json
import logging
import re
from typing import Dict, Optional, Any
from groq import Groq

logger = logging.getLogger(__name__)


class ComponentDataExtractor:
    """Extract structured component data from OCR text using AI."""

    def __init__(self):
        """Initialize Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not set. AI extraction will not work.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)

        self.model = "llama-3.3-70b-versatile"

    def extract_component_data(
        self,
        ocr_text: str,
        image_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract component data from OCR text using AI.

        Args:
            ocr_text: Text extracted from component image
            image_path: Optional path to image (not used yet, for future vision models)

        Returns:
            Dictionary with component data or None if extraction fails
        """
        if not self.client:
            logger.error("Groq client not initialized")
            return self._fallback_extraction(ocr_text)

        try:
            # Prepare prompt for AI
            prompt = f"""You are an expert in electronic components. Analyze the following text that was extracted from a component image using OCR.

IMPORTANT CONTEXT:
- The text may be incomplete, garbled, or minimal due to OCR limitations
- If the text contains mostly symbols or very short fragments, it might be a component with color bands (resistor) or minimal labeling
- Look for ANY recognizable patterns: part numbers, values, manufacturer codes, component type keywords
- Common boards: Arduino (Uno, Mega, Nano), ESP32, ESP8266, Raspberry Pi
- Arduino boards often have "Arduino", "ATmega", or "Made in Italy" text visible
- Development boards are usually blue PCBs with lots of pins and USB connectors

OCR Text:
{ocr_text}

Extract and return a JSON object with the following fields:
- component_type: Type of component (arduino, microcontroller, resistor, capacitor, connector, ic, led, sensor, transistor, diode, module, etc.)
- name: A descriptive name for the component
- part_number: Manufacturer part number if present
- manufacturer: Manufacturer name if present (e.g., "Arduino", "Espressif", "Atmel")
- specifications: Object with technical specs
  * For Arduino/boards: {{"model": "Mega 2560", "microcontroller": "ATmega2560", "voltage": "5V", "pins": "54 digital, 16 analog"}}
  * For resistors: {{"resistance": "10k", "tolerance": "5%", "power_rating": "0.25W"}}
  * For capacitors: {{"capacitance": "100uF", "voltage_rating": "25V", "type": "electrolytic"}}
  * For ICs/MCUs: {{"model": "ATmega328P", "voltage": "5V", "frequency": "16MHz"}}
- description: Brief description
- tags: Array of relevant tags (e.g., ["development-board", "5v", "usb"], ["smd", "through-hole"], etc.)
- recognition_confidence: Your confidence in this identification (0-100)

Rules:
- If you see "Arduino", "ATmega" with numbers, "MEGA", "UNO" - it's likely an Arduino board (component_type: "arduino")
- If text is minimal/garbled (< 10 meaningful characters), set confidence to 15 or lower
- For Arduino boards: try to identify the model (Uno, Mega 2560, Nano, etc.) and list the microcontroller chip
- For resistors: include resistance value, tolerance, power rating
- For capacitors: include capacitance, voltage rating, type (ceramic, electrolytic, etc.)
- For ICs/microcontrollers: include model number, voltage, key features
- For connectors: include pitch, pin count, type
- If a field cannot be determined, use null
- Be conservative with confidence score - if text is unclear, use low confidence (10-30)
- If NO meaningful component info can be extracted, set component_type to "unknown" and confidence to 5

Return ONLY valid JSON, no additional text."""

            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in electronic components and always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=1000,
            )

            # Parse response
            content = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            data = json.loads(content)

            # Validate and clean data
            return self._validate_and_clean(data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Response content: {content}")
            return self._fallback_extraction(ocr_text)

        except Exception as e:
            logger.error(f"AI extraction error: {e}")
            return self._fallback_extraction(ocr_text)

    def _validate_and_clean(self, data: Dict) -> Dict:
        """
        Validate and clean extracted data.

        Args:
            data: Raw extracted data

        Returns:
            Cleaned and validated data
        """
        cleaned = {
            'component_type': str(data.get('component_type', 'unknown')).lower(),
            'name': data.get('name') or 'Unknown Component',
            'part_number': data.get('part_number'),
            'manufacturer': data.get('manufacturer'),
            'specifications': data.get('specifications') or {},
            'description': data.get('description'),
            'tags': data.get('tags') or [],
            'recognition_confidence': min(100, max(0, float(data.get('recognition_confidence', 50)))),
        }

        # Ensure specifications is a dict
        if not isinstance(cleaned['specifications'], dict):
            cleaned['specifications'] = {}

        # Ensure tags is a list
        if not isinstance(cleaned['tags'], list):
            cleaned['tags'] = []

        return cleaned

    def _fallback_extraction(self, ocr_text: str) -> Optional[Dict]:
        """
        Fallback extraction using pattern matching when AI fails.

        Args:
            ocr_text: OCR extracted text

        Returns:
            Basic component data or None
        """
        logger.info("Using fallback pattern matching extraction")

        text_lower = ocr_text.lower()

        # Try to detect component type
        component_type = self._detect_component_type(text_lower)

        if component_type == 'unknown':
            return None

        # Extract part number patterns
        part_number = self._extract_part_number(ocr_text)

        # Build basic data
        data = {
            'component_type': component_type,
            'name': f"{component_type.capitalize()} - {part_number if part_number else 'Unknown'}",
            'part_number': part_number,
            'specifications': self._extract_specs_by_type(ocr_text, component_type),
            'tags': [component_type],
            'recognition_confidence': 30,  # Low confidence for fallback
        }

        return data

    def _detect_component_type(self, text: str) -> str:
        """Detect component type from text."""
        # Keywords for component detection (order matters - more specific first)
        patterns = {
            'arduino': [
                r'\barduino\b',
                r'\buno\b.*\br3\b',  # Uno R3
                r'\bmega\s*2560\b',
                r'\bmega\b.*\badk\b',  # Mega ADK
                r'\bmega\b',
                r'\bnano\b',
                r'\bmicro\b',
                r'\bleonardo\b',
                r'\bdue\b',
                r'\batmega\d+.*\b(arduino|board)\b',  # ATmega with arduino/board
                r'\b(made|designed)\s+in\s+italy\b',  # Arduino boards say this
            ],
            'microcontroller': [
                r'\batmega\d+[a-z]*\b',
                r'\bstm32\b',
                r'\besp32\b',
                r'\besp8266\b',
                r'\bpic\d+',
                r'\bmcu\b',
                r'\barm\s*cortex\b',
                r'\bsamd\d+\b',
                r'\brp2040\b',
            ],
            'resistor': [r'\b\d+[kKmM]?[Ωω]\b', r'\bresist', r'\bohm'],
            'capacitor': [r'\b\d+[uμnp]?[Ff]\b', r'\bcap\b', r'\bfarad'],
            'ic': [r'\b[0-9]{3,4}[A-Z]?\b', r'\bintegrated\s*circuit\b', r'\bchip\b'],
            'led': [r'\bled\b', r'\blight\s*emitting'],
            'connector': [r'\bconnector\b', r'\bheader\b', r'\bjst\b', r'\busb\b', r'\bpin\s*header\b'],
            'transistor': [r'\btransistor\b', r'\bmosfet\b', r'\bbjt\b', r'\b2N\d+\b'],
            'diode': [r'\bdiode\b', r'\b1N\d+\b', r'\brectifier\b'],
            'sensor': [r'\bsensor\b', r'\bdht\d+\b', r'\bbmp\d+\b', r'\bmpu\d+\b'],
        }

        for comp_type, keyword_patterns in patterns.items():
            for pattern in keyword_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return comp_type

        return 'unknown'

    def _extract_part_number(self, text: str) -> Optional[str]:
        """Extract part number from text."""
        # Common part number patterns
        patterns = [
            r'[A-Z]{2,}\d{3,}[A-Z\d-]*',  # Generic: ABC123, STM32F103
            r'\b\d{3,4}[A-Z]?\b',  # IC: 555, 7805
            r'[A-Z]\d{2,}[A-Z\d]*',  # Mixed: L7805, 2N2222
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _extract_specs_by_type(self, text: str, component_type: str) -> Dict:
        """Extract specifications based on component type."""
        specs = {}

        if component_type == 'resistor':
            # Extract resistance value
            match = re.search(r'(\d+\.?\d*)\s*([kKmM]?)[Ωω]', text)
            if match:
                value, unit = match.groups()
                specs['resistance'] = f"{value}{unit}Ω" if unit else f"{value}Ω"

            # Extract tolerance
            match = re.search(r'([±]?\d+)%', text)
            if match:
                specs['tolerance'] = f"{match.group(1)}%"

            # Extract power rating
            match = re.search(r'(\d+\.?\d*)\s*[Ww]', text)
            if match:
                specs['power_rating'] = f"{match.group(1)}W"

        elif component_type == 'capacitor':
            # Extract capacitance
            match = re.search(r'(\d+\.?\d*)\s*([uμnp]?)[Ff]', text)
            if match:
                value, unit = match.groups()
                specs['capacitance'] = f"{value}{unit}F"

            # Extract voltage
            match = re.search(r'(\d+)\s*[Vv]', text)
            if match:
                specs['voltage_rating'] = f"{match.group(1)}V"

        elif component_type in ['arduino', 'microcontroller']:
            # Extract voltage
            match = re.search(r'(\d+)\s*[Vv]', text)
            if match:
                specs['voltage'] = f"{match.group(1)}V"

            # Extract frequency
            match = re.search(r'(\d+)\s*[Mm][Hh][Zz]', text)
            if match:
                specs['frequency'] = f"{match.group(1)}MHz"

        elif component_type == 'connector':
            # Extract pin count
            match = re.search(r'(\d+)\s*pin', text, re.IGNORECASE)
            if match:
                specs['pins'] = match.group(1)

            # Extract pitch
            match = re.search(r'(\d+\.?\d*)\s*mm', text, re.IGNORECASE)
            if match:
                specs['pitch'] = f"{match.group(1)}mm"

        return specs

    def parse_specifications(self, specs_text: str, component_type: str) -> Dict:
        """
        Parse manually entered specifications text into structured format.

        Args:
            specs_text: User-entered specifications text
            component_type: Type of component

        Returns:
            Structured specifications dictionary
        """
        # Use the same extraction logic
        return self._extract_specs_by_type(specs_text, component_type)
