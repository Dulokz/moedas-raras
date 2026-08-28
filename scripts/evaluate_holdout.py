import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.vision import vision_engine
from backend.services.dataset_indexer import index_dataset
from backend.services.catalog import catalog_service


def evaluate_holdout():
    print("=" * 65)
    print(" EVALUATION OF REAL PHONE HOLDOUT PHOTO")
    print("=" * 65)

    catalog_service.load_catalog()
    index_dataset()

    obv_path = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "holdout_real_phone_obverse.jpg"
    rev_path = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "holdout_real_phone_reverse.jpg"

    if not obv_path.exists() or not rev_path.exists():
        print("ERRO: Imagens do holdout não encontradas!")
        return

    with open(obv_path, "rb") as f:
        obv_bytes = f.read()
    with open(rev_path, "rb") as f:
        rev_bytes = f.read()

    res = vision_engine.identify(obv_bytes, rev_bytes)

    print("\n--- RESULTADO DA PREDIÇÃO ATUAL NO HOLDOUT ---")
    print(f"Identified:          {res.identified}")
    print(f"Denomination:        {res.denomination}")
    print(f"Year:                {res.year}")
    print(f"Design:              {res.design}")
    print(f"Commemorative:       {res.commemorative}")
    print(f"Confidence:          {res.confidence*100:.2f}%")
    print(f"Bimetallic Detected: {res.bimetallic_detected}")
    print(f"Warnings:            {res.warnings}")
    print("\nCandidates:")
    for c in res.candidates:
        print(f"  - [{c.id}] {c.design} (Conf: {c.confidence*100:.2f}%)")
    print("=" * 65)


if __name__ == "__main__":
    evaluate_holdout()
