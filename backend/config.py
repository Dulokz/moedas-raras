import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATASET_DIR = BASE_DIR / "dataset"
TESTS_DIR = BASE_DIR / "tests"
CATALOG_PATH = DATA_DIR / "catalog-official.json"
INDEX_PATH = DATA_DIR / "reference_index.pt"

# Similarity thresholds
CONFIDENCE_STRONG = 0.70
CONFIDENCE_MEDIUM = 0.50

# Visual image normalization target size
NORM_SIZE = 224
