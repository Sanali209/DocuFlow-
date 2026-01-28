import cv2
import numpy as np
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

def preprocess_image(input_path: str) -> str:
    """
    Applies preprocessing to an image to improve OCR acccuracy.
    Steps: Grayscale -> Denoise -> Adaptive Threshold
    Returns path to the processed temporary image.
    """
    try:
        # Load image
        img = cv2.imread(input_path)
        if img is None:
            logger.warning(f"Could not load image at {input_path}, skipping preprocessing.")
            return input_path

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Denoising
        # h=10 is a good starting point for strength
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Binarization using adaptive thresholding
        # This helps with varying lighting conditions (shadows)
        # Block size 11, C=2
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Save to temp file
        # Preserve original extension based on input if possible, or use .png which is lossless
        
        # Create a temp file path
        # We use .png for the processed intermediate
        fd, output_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        
        cv2.imwrite(output_path, binary)
        
        logger.info(f"Image preprocessed and saved to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        # Return original path on failure to try OCR anyway
        return input_path
