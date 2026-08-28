import os
from pathlib import Path
from PIL import Image
import torch

from backend.config import DATASET_DIR, INDEX_PATH
from backend.services.vision import vision_engine
from backend.services.catalog import catalog_service


def index_dataset():
    """Scans dataset/brl/ directory and builds visual embeddings index."""
    print("Iniciando indexação do dataset visual...")
    indexed_count = 0

    if not DATASET_DIR.exists():
        print(f"Diretório dataset {DATASET_DIR} não encontrado.")
        return 0

    # Iterate over denomination folders (e.g. 1_real)
    for denom_dir in DATASET_DIR.glob("brl/*"):
        if not denom_dir.is_dir():
            continue

        # Iterate over coin design folders (e.g. 2024_30_anos_real)
        for coin_dir in denom_dir.iterdir():
            if not coin_dir.is_dir():
                continue

            obv_dir = coin_dir / "obverse"
            rev_dir = coin_dir / "reverse"

            if not obv_dir.exists() or not rev_dir.exists():
                continue

            obv_imgs = list(obv_dir.glob("*.jpg")) + list(obv_dir.glob("*.png")) + list(obv_dir.glob("*.jpeg"))
            rev_imgs = list(rev_dir.glob("*.jpg")) + list(rev_dir.glob("*.png")) + list(rev_dir.glob("*.jpeg"))

            if not obv_imgs or not rev_imgs:
                continue

            # Load primary obverse & reverse reference images
            obv_pil = Image.open(obv_imgs[0]).convert("RGB")
            rev_pil = Image.open(rev_imgs[0]).convert("RGB")

            # Map folder name to coin catalog ID
            # e.g., 2024_30_anos_real -> brl-1-2024-30-anos-real
            coin_id_map = {
                "2024_30_anos_real": "brl-1-2024-30-anos-real",
                "2019_25_anos_real": "brl-1-2019-25-anos-real",
                "2025_60_anos_bcb": "brl-1-2025-60-anos-bcb",
                "1998_direitos_humanos": "brl-1-1998-direitos-humanos",
                "2005_40_anos_bcb": "brl-1-2005-40-anos-bcb",
                "2012_bandeira_olimpica": "brl-1-2012-bandeira-olimpica",
                "2016_rio_2016": "brl-1-2016-rio-2016",
                "regular_segunda_familia": "brl-1-regular-segunda-familia",
                "regular_50_centavos": "brl-0.50-regular-segunda-familia"
            }

            coin_id = coin_id_map.get(coin_dir.name, f"brl-1-{coin_dir.name}")
            vision_engine.register_reference(coin_id, obv_pil, rev_pil)
            indexed_count += 1
            print(f"  [OK] Indexado {coin_id} a partir de {coin_dir.name}")

    print(f"Indexação concluída! {indexed_count} emissões registradas no motor visual.")
    return indexed_count


if __name__ == "__main__":
    index_dataset()
