"""
Visual component recognition using AI vision models
Supports multiple providers: OpenAI GPT-4 Vision, Google Vision, etc.
"""

import os
import base64
import logging
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionRecognizer:
    """Visual component recognition using AI vision models."""

    def __init__(self):
        """Initialize vision recognizer with available API keys."""
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.google_key = os.getenv("GOOGLE_VISION_API_KEY")

        # Determine which service to use
        if self.openai_key:
            self.provider = "openai"
            logger.info("Using OpenAI GPT-4 Vision for visual recognition")
        elif self.google_key:
            self.provider = "google"
            logger.info("Using Google Cloud Vision for visual recognition")
        else:
            self.provider = None
            logger.warning("No vision API keys configured. Visual recognition disabled.")

    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 for API transmission.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def recognize_with_openai(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Recognize component using OpenAI GPT-4 Vision.

        Args:
            image_path: Path to component image

        Returns:
            Dictionary with component data or None
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.openai_key)
            base64_image = self.encode_image(image_path)

            response = client.chat.completions.create(
                model="gpt-4o",  # GPT-4 with vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """You are an expert in electronic components. Analyze this image and identify the component.

Return a JSON object with:
- component_type: Type (arduino, resistor, capacitor, ic, led, sensor, transistor, diode, module, etc.)
- name: Descriptive name
- part_number: Part number if visible
- manufacturer: Manufacturer if visible
- specifications: Technical specs as object
- description: What you see in the image
- visual_features: What makes this component identifiable (color bands, shape, markings, etc.)
- recognition_confidence: Your confidence (0-100)

For resistors, identify color bands and calculate resistance.
For Arduino/boards, identify the model and microcontroller.
For ICs, read the part number from the chip.

Return ONLY valid JSON."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )

            import json
            import re

            # Get response content
            content = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            content = content.strip()

            # Parse JSON
            result = json.loads(content)
            result['recognition_method'] = 'openai_vision'

            logger.info(f"OpenAI Vision recognized: {result.get('component_type')} with {result.get('recognition_confidence')}% confidence")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"OpenAI response content: {response.choices[0].message.content[:500]}")
            return None
        except Exception as e:
            logger.error(f"OpenAI Vision recognition error: {e}")
            return None

    def recognize_with_google(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Recognize component using Google Cloud Vision.

        Args:
            image_path: Path to component image

        Returns:
            Dictionary with component data or None
        """
        try:
            from google.cloud import vision

            client = vision.ImageAnnotatorClient()

            with open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            # Detect labels (what Google thinks the object is)
            labels_response = client.label_detection(image=image)
            labels = [label.description for label in labels_response.label_annotations[:10]]

            # Detect text (OCR)
            text_response = client.text_detection(image=image)
            texts = text_response.text_annotations
            ocr_text = texts[0].description if texts else ""

            # Detect objects
            objects_response = client.object_localization(image=image)
            objects = [obj.name for obj in objects_response.localized_object_annotations[:5]]

            # Combine results
            result = {
                'component_type': self._infer_type_from_labels(labels, ocr_text),
                'labels': labels,
                'objects_detected': objects,
                'ocr_text': ocr_text,
                'recognition_method': 'google_vision',
                'recognition_confidence': 60  # Google doesn't provide direct confidence
            }

            logger.info(f"Google Vision detected: {labels[:3]}")
            return result

        except Exception as e:
            logger.error(f"Google Vision recognition error: {e}")
            return None

    def _infer_type_from_labels(self, labels: list, text: str) -> str:
        """Infer component type from Google Vision labels and text."""
        labels_text = ' '.join(labels).lower() + ' ' + text.lower()

        if 'resistor' in labels_text or 'resistance' in labels_text:
            return 'resistor'
        elif 'capacitor' in labels_text:
            return 'capacitor'
        elif 'arduino' in labels_text or 'microcontroller' in labels_text:
            return 'arduino'
        elif 'circuit' in labels_text or 'board' in labels_text:
            return 'module'
        elif 'led' in labels_text or 'diode' in labels_text:
            return 'led'
        else:
            return 'unknown'

    def recognize_component(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Recognize component using best available vision service.

        Args:
            image_path: Path to component image

        Returns:
            Dictionary with component data or None
        """
        if not self.provider:
            logger.warning("No vision provider available")
            return None

        if self.provider == "openai":
            return self.recognize_with_openai(image_path)
        elif self.provider == "google":
            return self.recognize_with_google(image_path)

        return None

    def is_available(self) -> bool:
        """Check if vision recognition is available."""
        return self.provider is not None


# Example usage and testing
if __name__ == "__main__":
    recognizer = VisionRecognizer()

    if recognizer.is_available():
        # Test with a sample image
        test_image = "/tmp/test_component.jpg"
        result = recognizer.recognize_component(test_image)

        if result:
            print("Recognition Result:")
            print(json.dumps(result, indent=2))
    else:
        print("Vision recognition not configured")
        print("Set OPENAI_API_KEY or GOOGLE_VISION_API_KEY in .env")
