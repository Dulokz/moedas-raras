import sys
import math
import numpy as np
import cv2
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.vision import vision_engine


def detect_coin_in_frame(img):
    """Refined frame detector testing circularity C = 4pi*A / P^2 >= 0.65."""
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 1.5)

    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_coin_found = False

    for cnt in contours:
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)
        if area > (w * h * 0.05) and perimeter > 0:
            circularity = (4 * math.pi * area) / (perimeter * perimeter)
            if circularity >= 0.65:
                valid_coin_found = True
                break

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=h//3,
        param1=100, param2=30, minRadius=int(min(h, w)*0.2), maxRadius=int(min(h, w)*0.48)
    )

    return valid_coin_found or (circles is not None)


def test_no_coin_frame():
    """Validates that a frame without a coin (flat texture / noise) is rejected."""
    print("Testing frame WITHOUT coin...")
    img = np.full((400, 400, 3), 128, dtype=np.uint8)
    noise = np.random.randint(-15, 15, (400, 400, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    has_coin = detect_coin_in_frame(img)
    print(f"  Result: has_coin = {has_coin} (Expected: False)")
    assert has_coin is False, "FAIL: Frame without coin was incorrectly accepted as coin!"
    print("  [PASS] Frame without coin correctly rejected!")


def test_centered_coin_frame():
    """Validates that a centered coin frame is accepted."""
    print("\nTesting frame WITH centered coin...")
    img = np.full((400, 400, 3), 40, dtype=np.uint8)
    # Draw centered bimetallic coin
    cv2.circle(img, (200, 200), 120, (195, 200, 205), -1)  # outer ring
    cv2.circle(img, (200, 200), 75, (45, 175, 212), -1)   # inner gold core

    has_coin = detect_coin_in_frame(img)
    print(f"  Result: has_coin = {has_coin} (Expected: True)")
    assert has_coin is True, "FAIL: Centered coin frame was not detected!"
    print("  [PASS] Centered coin frame correctly detected!")


if __name__ == "__main__":
    print("=" * 60)
    print(" CAMERA AUTO-CAPTURE DETECTOR AUTOMATED TESTS")
    print("=" * 60)
    test_no_coin_frame()
    test_centered_coin_frame()
    print("=" * 60)
    print("ALL AUTO-CAPTURE DETECTOR TESTS PASSED PERFECTLY!")
    print("=" * 60)
