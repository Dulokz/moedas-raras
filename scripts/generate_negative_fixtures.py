import os
import cv2
import numpy as np
from pathlib import Path


def generate_negative_fixtures():
    out_dir = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "negatives"
    out_dir.mkdir(parents=True, exist_ok=True)

    size = 1200
    cx, cy = size // 2, size // 2

    print(f"Gerando fixtures negativas em: {out_dir}")

    # 1. R$ 1,00 Centenário de Juscelino Kubitschek (2002) - HOLDOUT NEGATIVO
    obv_jk = np.full((size, size, 3), 20, dtype=np.uint8)
    # Bimetallic outer ring (silver)
    cv2.circle(obv_jk, (cx, cy), 540, (200, 205, 210), -1)
    # Bimetallic inner core (gold)
    cv2.circle(obv_jk, (cx, cy), 340, (40, 175, 215), -1)
    # Draw JK profile portrait & inscriptions (distinct from 30 anos / Republic efígie)
    cv2.ellipse(obv_jk, (cx - 20, cy), (160, 220), 0, 0, 360, (20, 80, 110), -1)
    cv2.circle(obv_jk, (cx - 40, cy - 80), 50, (20, 80, 110), -1)
    cv2.putText(obv_jk, "JUSCELINO KUBITSCHEK", (cx - 300, cy + 300), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (20, 80, 110), 4)
    cv2.putText(obv_jk, "1902 - 2002", (cx - 140, cy + 380), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (20, 80, 110), 3)
    cv2.putText(obv_jk, "CENTENARIO", (cx - 260, cy - 380), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (200, 205, 210), 4)
    cv2.putText(obv_jk, "BRASIL", (cx - 100, cy + 480), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (200, 205, 210), 4)

    # Standard reverse of 2002
    rev_jk = np.full((size, size, 3), 20, dtype=np.uint8)
    cv2.circle(rev_jk, (cx, cy), 540, (200, 205, 210), -1)
    cv2.circle(rev_jk, (cx, cy), 340, (40, 175, 215), -1)
    cv2.putText(rev_jk, "1 REAL", (cx - 150, cy - 40), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (20, 80, 110), 6)
    cv2.putText(rev_jk, "2002", (cx - 100, cy + 140), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (20, 80, 110), 5)

    cv2.imwrite(str(out_dir / "jk_1_real_2002_obverse.jpg"), obv_jk)
    cv2.imwrite(str(out_dir / "jk_1_real_2002_reverse.jpg"), rev_jk)
    print("  [OK] Criado jk_1_real_2002 (Holdout Negativo)")

    # 2. Medalha / Ficha Não Numismática
    obv_medal = np.full((size, size, 3), 15, dtype=np.uint8)
    cv2.circle(obv_medal, (cx, cy), 520, (50, 140, 200), -1)  # Copper/Bronze medal
    cv2.putText(obv_medal, "CLUBE DE REGATAS", (cx - 280, cy - 100), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (10, 40, 70), 4)
    cv2.putText(obv_medal, "SOCIO #409", (cx - 160, cy + 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (10, 40, 70), 4)

    rev_medal = np.full((size, size, 3), 15, dtype=np.uint8)
    cv2.circle(rev_medal, (cx, cy), 520, (50, 140, 200), -1)
    cv2.putText(rev_medal, "VALE 1 CAFE", (cx - 200, cy), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (10, 40, 70), 5)

    cv2.imwrite(str(out_dir / "non_coin_medal_obverse.jpg"), obv_medal)
    cv2.imwrite(str(out_dir / "non_coin_medal_reverse.jpg"), rev_medal)
    print("  [OK] Criado non_coin_medal (Holdout Negativo)")

    print("\nFixtures negativas geradas com sucesso!")


if __name__ == "__main__":
    generate_negative_fixtures()
