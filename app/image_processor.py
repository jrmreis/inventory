"""
Image processing module for component recognition using OCR
"""

import os
import cv2
import logging
from typing import Dict, Optional, Tuple
import pytesseract
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process images to extract text using OCR."""

    def __init__(self):
        """Initialize image processor with Tesseract configuration."""
        # Tesseract config for component recognition
        # PSM 6 = uniform block of text
        # PSM 11 = sparse text (good for component labels)
        # PSM 3 = automatic page segmentation (more robust)
        self.tesseract_config = '--oem 3 --psm 11 -l eng'
        self.tesseract_config_alt = '--oem 3 --psm 3 -l eng'  # Alternative config

    def preprocess_image(
        self,
        image_path: str,
        strategy: str = "balanced"
    ) -> np.ndarray:
        """
        Preprocess image for better OCR results.

        Args:
            image_path: Path to image file
            strategy: Preprocessing strategy ('minimal', 'balanced', 'aggressive')

        Returns:
            Processed image as numpy array
        """
        # Read image
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if strategy == "minimal":
            # Just resize if needed
            if gray.shape[0] < 800:
                scale = 1200 / gray.shape[0]
                width = int(gray.shape[1] * scale)
                gray = cv2.resize(gray, (width, 1200), interpolation=cv2.INTER_CUBIC)
            return gray

        elif strategy == "balanced":
            # Resize FIRST for better processing of small text
            if gray.shape[0] < 1000:
                scale = 1500 / gray.shape[0]
                width = int(gray.shape[1] * scale)
                gray = cv2.resize(gray, (width, 1500), interpolation=cv2.INTER_CUBIC)

            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

            # Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            return enhanced

        elif strategy == "aggressive":
            # Aggressive preprocessing for difficult images
            # Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Denoise
            denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

            # Resize
            if denoised.shape[0] < 800:
                scale = 1200 / denoised.shape[0]
                width = int(denoised.shape[1] * scale)
                denoised = cv2.resize(denoised, (width, 1200), interpolation=cv2.INTER_CUBIC)

            return denoised

        return gray

    def extract_text(self, image: np.ndarray, use_alternative: bool = False) -> str:
        """
        Extract text from preprocessed image using Tesseract OCR.

        Args:
            image: Preprocessed image as numpy array
            use_alternative: Use alternative PSM configuration

        Returns:
            Extracted text
        """
        try:
            config = self.tesseract_config_alt if use_alternative else self.tesseract_config
            text = pytesseract.image_to_string(image, config=config)
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return ""

    def detect_resistor_colors(self, image_path: str) -> Optional[Dict]:
        """
        Detect resistor color bands (basic implementation).

        This is a simplified version. For production, you'd want more sophisticated
        color detection using HSV color space and contour analysis.

        Args:
            image_path: Path to resistor image

        Returns:
            Dictionary with detected colors and calculated value
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None

            # Check if image is too large (likely a PCB/module, not a resistor)
            img_area = img.shape[0] * img.shape[1]

            # Check for text density - PCBs have lots of text
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = cv2.countNonZero(edges) / img_area

            # If image has high edge density, it's likely a complex PCB, not a resistor
            if edge_density > 0.15:  # PCBs have lots of edges
                logger.info(f"High edge density ({edge_density:.3f}) - likely a PCB/module, skipping color detection")
                return None

            # Color ranges in HSV for resistor color bands
            # Improved ranges for better accuracy
            color_ranges = {
                'black': ([0, 0, 0], [180, 255, 40]),
                'brown': ([5, 40, 20], [25, 255, 150]),
                'red': ([0, 70, 50], [10, 255, 255]),
                'orange': ([11, 100, 100], [25, 255, 255]),
                'yellow': ([25, 100, 100], [35, 255, 255]),
                'green': ([35, 50, 50], [85, 255, 255]),
                'blue': ([85, 80, 50], [130, 255, 255]),
                'violet': ([130, 50, 50], [160, 255, 255]),
                'gray': ([0, 0, 50], [180, 40, 200]),
                'white': ([0, 0, 200], [180, 25, 255]),
                'gold': ([20, 100, 100], [30, 255, 255]),
                'silver': ([0, 0, 180], [180, 25, 220]),
            }

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            detected_colors = []
            total_pixels = img_area

            for color_name, (lower, upper) in color_ranges.items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                pixel_count = cv2.countNonZero(mask)

                # Require at least 100 pixels AND less than 40% of image
                # (too many pixels of one color = not a resistor band)
                if pixel_count > 100 and (pixel_count / total_pixels) < 0.4:
                    detected_colors.append((color_name, pixel_count))

            # Special handling for red (wraps around in HSV space)
            if 'red' not in [c[0] for c in detected_colors]:
                red_upper_mask = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
                red_upper_count = cv2.countNonZero(red_upper_mask)
                if red_upper_count > 100 and (red_upper_count / total_pixels) < 0.4:
                    detected_colors.append(('red', red_upper_count))

            # Sort by pixel count to prioritize dominant colors
            detected_colors.sort(key=lambda x: x[1], reverse=True)

            # If we have too many colors detected (>6), it's probably not a resistor
            if len(detected_colors) > 6:
                logger.info(f"Too many colors detected ({len(detected_colors)}) - not a resistor")
                return None

            if not detected_colors:
                return None

            return {
                'detected_colors': [c[0] for c in detected_colors[:4]],
                'note': 'Color detection is experimental. Please verify the resistance value.'
            }

        except Exception as e:
            logger.error(f"Color detection error: {e}")
            return None

    def process_image(
        self,
        image_path: str,
        detect_colors: bool = True
    ) -> Dict:
        """
        Process component image with multiple strategies.

        Args:
            image_path: Path to component image
            detect_colors: Whether to attempt color detection for resistors

        Returns:
            Dictionary with OCR results and metadata
        """
        results = {
            'text': '',
            'confidence': 0,
            'strategy_used': '',
            'colors': None
        }

        # Try color detection FIRST (for resistors, diodes, etc.)
        if detect_colors:
            try:
                logger.info("Attempting color detection...")
                colors = self.detect_resistor_colors(image_path)
                if colors and colors.get('detected_colors'):
                    results['colors'] = colors
                    logger.info(f"Colors detected: {colors.get('detected_colors')}")
            except Exception as e:
                logger.warning(f"Color detection failed: {e}")

        # Try different preprocessing strategies for OCR
        strategies = ['balanced', 'minimal', 'aggressive']

        for strategy in strategies:
            try:
                logger.info(f"Trying OCR with {strategy} preprocessing...")

                # Preprocess image
                processed = self.preprocess_image(image_path, strategy)

                # Extract text with both PSM configurations
                text = self.extract_text(processed, use_alternative=False)

                # If first attempt gave minimal results, try alternative config
                if not text or len(text) < 5:
                    logger.info(f"Trying alternative OCR config for {strategy}...")
                    text_alt = self.extract_text(processed, use_alternative=True)
                    if len(text_alt) > len(text):
                        text = text_alt

                if text and len(text) > len(results['text']):
                    results['text'] = text
                    results['strategy_used'] = strategy
                    logger.info(f"OCR found {len(text)} characters with {strategy}")

                    # If we got good text, stop trying
                    if len(text) > 15:
                        break

            except Exception as e:
                logger.warning(f"OCR with {strategy} failed: {e}")
                continue

        logger.info(f"Final OCR text length: {len(results['text'])}")
        return results

    def extract_component_region(
        self,
        image_path: str,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Attempt to isolate component from background using edge detection.

        Args:
            image_path: Path to image
            output_path: Optional path to save cropped image

        Returns:
            Cropped image or None
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                return None

            # Get largest contour (likely the component)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get bounding box
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Add padding
            padding = 20
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.shape[1] - x, w + 2 * padding)
            h = min(img.shape[0] - y, h + 2 * padding)

            # Crop image
            cropped = img[y:y+h, x:x+w]

            if output_path:
                cv2.imwrite(output_path, cropped)

            return cropped

        except Exception as e:
            logger.error(f"Component extraction error: {e}")
            return None


# Resistor color code mapping for reference
RESISTOR_COLOR_CODES = {
    'black': 0,
    'brown': 1,
    'red': 2,
    'orange': 3,
    'yellow': 4,
    'green': 5,
    'blue': 6,
    'violet': 7,
    'gray': 8,
    'grey': 8,
    'white': 9,
}

RESISTOR_MULTIPLIERS = {
    'black': 1,
    'brown': 10,
    'red': 100,
    'orange': 1000,
    'yellow': 10000,
    'green': 100000,
    'blue': 1000000,
    'violet': 10000000,
    'gold': 0.1,
    'silver': 0.01,
}

RESISTOR_TOLERANCE = {
    'brown': '1%',
    'red': '2%',
    'gold': '5%',
    'silver': '10%',
    'none': '20%',
}


def calculate_resistor_value(colors: list) -> Optional[str]:
    """
    Calculate resistor value from color bands.

    Args:
        colors: List of color names in order (3-4 colors)

    Returns:
        Resistance value as string (e.g., "10kΩ ±5%")
    """
    try:
        if len(colors) < 3:
            return None

        # 4-band resistor (most common)
        if len(colors) >= 3:
            digit1 = RESISTOR_COLOR_CODES.get(colors[0].lower())
            digit2 = RESISTOR_COLOR_CODES.get(colors[1].lower())
            multiplier = RESISTOR_MULTIPLIERS.get(colors[2].lower())

            if digit1 is None or digit2 is None or multiplier is None:
                return None

            value = (digit1 * 10 + digit2) * multiplier

            # Format value
            if value >= 1_000_000:
                formatted = f"{value / 1_000_000:.1f}MΩ"
            elif value >= 1_000:
                formatted = f"{value / 1_000:.1f}kΩ"
            else:
                formatted = f"{value:.1f}Ω"

            # Add tolerance if available
            if len(colors) >= 4:
                tolerance = RESISTOR_TOLERANCE.get(colors[3].lower(), '±20%')
                formatted += f" {tolerance}"

            return formatted

    except Exception as e:
        logger.error(f"Resistor calculation error: {e}")
        return None
