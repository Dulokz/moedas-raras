import os
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import cv2

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset" / "brl" / "1_real"
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures" / "brl_1_2024_30_anos"


def draw_coin_base(size=400, is_bimetallic=True):
    """Generates base canvas for a bimetallic Brazilian R$ 1 coin."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r_outer = size // 2 - 10
    r_inner = int(r_outer * 0.68)
    cx, cy = size // 2, size // 2

    # Outer ring: Silver / Stainless steel texture gradient
    draw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer), fill="#C5C9CC", outline="#9FA3A7", width=3)

    # Inner core: Bronze / Gold plated steel
    draw.ellipse((cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner), fill="#D4AF37", outline="#B8860B", width=2)

    return img, (cx, cy, r_outer, r_inner)


def create_30_anos_obverse(size=400):
    """Renders reference image for 30 Anos do Real 2024 Obverse."""
    img, (cx, cy, r_out, r_in) = draw_coin_base(size)
    draw = ImageDraw.Draw(img)

    # Diagonal lines on gold core
    for offset in range(-r_in + 15, r_in - 15, 12):
        draw.line([cx - r_in + 10, cy + offset, cx + r_in - 10, cy + offset + 20], fill="#C5A028", width=2)

    # Center effigy symbol
    draw.ellipse((cx - 35, cy - 40, cx + 35, cy + 40), fill="#DAA520", outline="#B8860B", width=2)

    # Outer ring text: "30 ANOS DO REAL", "1994 - 2024", "BRASIL"
    font = ImageFont.load_default()
    draw.text((cx - 45, cy - r_out + 12), "30 ANOS DO REAL", fill="#4A4E51", font=font)
    draw.text((cx - 35, cy + r_out - 25), "1994 - 2024", fill="#4A4E51", font=font)
    draw.text((cx - 20, cy + r_in + 8), "BRASIL", fill="#4A4E51", font=font)

    # Marajoara border pattern on ring
    for angle in range(0, 360, 20):
        rad = math.radians(angle)
        px = cx + int((r_out - 8) * math.cos(rad))
        py = cy + int((r_out - 8) * math.sin(rad))
        draw.rectangle([px - 2, py - 2, px + 2, py + 2], fill="#7A7E82")

    return img.convert("RGB")


def create_30_anos_reverse(size=400):
    """Renders reference image for 30 Anos do Real 2024 Reverse (standard 1 REAL reverse)."""
    img, (cx, cy, r_out, r_in) = draw_coin_base(size)
    draw = ImageDraw.Draw(img)

    # Large 1 REAL inscription on core
    font = ImageFont.load_default()
    draw.text((cx - 12, cy - 45), "1", fill="#8B6508", font=font)
    draw.text((cx - 25, cy - 10), "REAL", fill="#8B6508", font=font)
    draw.text((cx - 22, cy + 20), "2024", fill="#8B6508", font=font)

    # Southern cross & globe diagonal band
    draw.line([cx - r_in + 5, cy - 10, cx + r_in - 5, cy + 25], fill="#C5A028", width=4)

    # Marajoara pattern on ring
    draw.text((cx - 40, cy - r_out + 12), "REPUBLICA FEDERATIVA", fill="#4A4E51", font=font)
    draw.text((cx - 30, cy + r_out - 25), "DO BRASIL", fill="#4A4E51", font=font)

    return img.convert("RGB")


def create_regular_obverse(size=400):
    """Renders reference image for Standard Regular 1 Real Obverse."""
    img, (cx, cy, r_out, r_in) = draw_coin_base(size)
    draw = ImageDraw.Draw(img)
    draw.ellipse((cx - 40, cy - 45, cx + 40, cy + 45), fill="#DAA520", outline="#B8860B", width=2)
    font = ImageFont.load_default()
    draw.text((cx - 20, cy - r_out + 12), "BRASIL", fill="#4A4E51", font=font)
    return img.convert("RGB")


def build_dataset():
    """Builds reference dataset images for all initial classes."""
    print("Gerando imagens de referência para o dataset...")

    classes = {
        "2024_30_anos_real": (create_30_anos_obverse(), create_30_anos_reverse()),
        "regular_segunda_familia": (create_regular_obverse(), create_30_anos_reverse())
    }

    for cname, (obv, rev) in classes.items():
        c_dir = DATASET_DIR / cname
        obv_d = c_dir / "obverse"
        rev_d = c_dir / "reverse"
        obv_d.mkdir(parents=True, exist_ok=True)
        rev_d.mkdir(parents=True, exist_ok=True)

        obv.save(obv_d / "ref_obverse.jpg", quality=95)
        rev.save(rev_d / "ref_reverse.jpg", quality=95)
        print(f"  [Dataset] Salvo {cname}")


def apply_photo_effects(pil_img, rotation=0, brightness=1.0, bg_color=(40, 45, 50)):
    """Simulates real camera environment: rotation, lighting, background surface, noise."""
    w, h = pil_img.size
    bg = Image.new("RGB", (w + 100, h + 100), bg_color)

    # Rotate coin
    rot = pil_img.rotate(rotation, resample=Image.BICUBIC, expand=False)

    # Paste onto background surface
    bg.paste(rot, (50, 50))

    # Adjust brightness/lighting
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(brightness)

    return bg


def build_test_fixtures():
    """Generates mandatory test fixture photo pairs for 30 Anos do Real 2024."""
    print("Gerando suíte de fixtures de teste para R$ 1 2024 (30 anos do Real)...")
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    obv = create_30_anos_obverse()
    rev = create_30_anos_reverse()

    fixtures_spec = [
        ("01_standard_0deg", 0, 1.0, (30, 35, 40), False),
        ("02_rotated_90deg", 90, 1.0, (220, 220, 215), False),
        ("03_rotated_180deg", 180, 0.95, (110, 80, 50), False),
        ("04_rotated_270deg", 270, 1.05, (50, 60, 70), False),
        ("05_dark_lighting", 45, 0.70, (20, 20, 20), False),
        ("06_bright_lighting", 135, 1.25, (240, 240, 245), False),
        ("07_swapped_sides", 0, 1.0, (45, 45, 50), True),
    ]

    for fname, rot, bright, bg, swap in fixtures_spec:
        f_img = apply_photo_effects(rev if swap else obv, rotation=rot, brightness=bright, bg_color=bg)
        b_img = apply_photo_effects(obv if swap else rev, rotation=(rot + 180) % 360, brightness=bright, bg_color=bg)

        f_path = FIXTURES_DIR / f"{fname}_front.jpg"
        b_path = FIXTURES_DIR / f"{fname}_back.jpg"

        f_img.save(f_path, quality=90)
        b_img.save(b_path, quality=90)
        print(f"  [Fixture] Criada: {fname}")


if __name__ == "__main__":
    build_dataset()
    build_test_fixtures()
