import cv2
import numpy as np

def classify_hit(crop, contour=None):
    """
    Classify whether a detected region is a pellet hole.
    Uses circularity and contrast features.
    
    Args:
        crop: 16x16 grayscale image crop around detection
        contour: Optional contour for circularity calculation
    
    Returns:
        Probability (0.0-1.0) that this is a genuine pellet hole
    """
    if crop.shape != (16, 16):
        return 0.0
    
    # Calculate contrast - pellet holes should have good contrast
    std_dev = np.std(crop)
    if std_dev < 10:  # Too uniform, probably noise
        return 0.3
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Find contours in the crop
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        return 0.3
    
    # Use the provided contour if available, otherwise use largest in crop
    if contour is None:
        c = max(contours, key=cv2.contourArea)
    else:
        c = contour
    
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    
    if perimeter == 0 or area < 5:
        return 0.3
    
    # Circularity: 4π * area / perimeter²
    # Perfect circle = 1.0, square ≈ 0.785
    circularity = 4 * np.pi * area / (perimeter * perimeter)
    
    # Pellet holes should be reasonably circular (0.5-1.0)
    if circularity < 0.4:
        return 0.35  # Too irregular
    
    # Calculate aspect ratio for additional validation
    rect = cv2.minAreaRect(c)
    width, height = rect[1]
    if width == 0 or height == 0:
        aspect_ratio = 1.0
    else:
        aspect_ratio = max(width, height) / min(width, height)
    
    # Good pellet holes: circular (high circularity) and round (aspect ~1.0)
    circularity_score = min(circularity, 1.0)
    aspect_score = 1.0 / (1.0 + abs(aspect_ratio - 1.0))
    
    # Contrast score - good holes have clear edges
    contrast_score = min(std_dev / 50.0, 1.0)
    
    # Weighted combination
    confidence = (
        0.5 * circularity_score +
        0.3 * aspect_score +
        0.2 * contrast_score
    )
    
    # Clamp to reasonable range
    return min(max(confidence, 0.35), 0.95)


def train_classifier(positive_samples, negative_samples):
    """
    Future enhancement: Train a simple ML classifier.
    
    Args:
        positive_samples: List of 16x16 crops of real pellet holes
        negative_samples: List of 16x16 crops of false positives
    
    Returns:
        Trained classifier (to be implemented)
    """
    # TODO: Implement simple CNN or SVM classifier
    # For now, use the rule-based approach above
    pass
