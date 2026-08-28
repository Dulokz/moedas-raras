import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.vision import vision_engine
from backend.services.dataset_indexer import index_dataset
from backend.services.catalog import catalog_service


def run_open_set_tests():
    print("=" * 65)
    print(" MOEDAS RARAS V2 -- OPEN-SET RECOGNITION (OOD) TEST SUITE")
    print("=" * 65)

    catalog_service.load_catalog()
    index_dataset()

    base_dir = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
    known_dir = base_dir / "brl_1_2024_30_anos"
    neg_dir = base_dir / "negatives"

    # Known fixtures (indexed in visual database)
    known_fixtures = [
        ("01_standard_0deg", known_dir / "01_standard_0deg_front.jpg", known_dir / "01_standard_0deg_back.jpg", "1.00", "2024", "brl-1-2024-30-anos-real"),
        ("02_rotated_90deg", known_dir / "02_rotated_90deg_front.jpg", known_dir / "02_rotated_90deg_back.jpg", "1.00", "2024", "brl-1-2024-30-anos-real"),
        ("07_swapped_sides", known_dir / "07_swapped_sides_front.jpg", known_dir / "07_swapped_sides_back.jpg", "1.00", "2024", "brl-1-2024-30-anos-real")
    ]

    # Unknown / Negative fixtures (NOT indexed in visual database)
    unknown_fixtures = [
        ("JK 2002 (Centenário Juscelino Kubitschek)", neg_dir / "jk_1_real_2002_obverse.jpg", neg_dir / "jk_1_real_2002_reverse.jpg"),
        ("Medalha / Ficha Não Numismática", neg_dir / "non_coin_medal_obverse.jpg", neg_dir / "non_coin_medal_reverse.jpg")
    ]

    print("\n[1/2] Testando emissões CONHECIDAS (Expectation: identified = True)...")
    known_pass = 0
    for name, obv, rev, exp_denom, exp_year, exp_id in known_fixtures:
        with open(obv, "rb") as f:
            obv_b = f.read()
        with open(rev, "rb") as f:
            rev_b = f.read()

        res = vision_engine.identify(obv_b, rev_b)
        top_id = res.best_candidate.id if res.best_candidate else (res.coin_details.id if res.coin_details else "")
        is_ok = res.identified is True and top_id == exp_id
        if is_ok:
            known_pass += 1
            status = "[PASS]"
        else:
            status = "[FAIL]"

        print(f"  {status} | {name:<25} | Identified: {res.identified} | Conf: {res.confidence*100:.1f}% | Reason: {res.reason}")

    print("\n[2/2] Testando emissões DESCONHECIDAS / HOLDOUTS (Expectation: identified = False)...")
    unknown_pass = 0
    for name, obv, rev in unknown_fixtures:
        with open(obv, "rb") as f:
            obv_b = f.read()
        with open(rev, "rb") as f:
            rev_b = f.read()

        res = vision_engine.identify(obv_b, rev_b)
        is_ok = res.identified is False
        if is_ok:
            unknown_pass += 1
            status = "[PASS]"
        else:
            status = "[FAIL - FALSE POSITIVE]"

        best_name = res.best_candidate.design if res.best_candidate else "Nenhum"
        print(f"  {status} | {name:<40} | Identified: {res.identified} | Reason: {res.reason} | Best Cand: {best_name} ({res.confidence*100:.1f}%)")

    kar = (known_pass / len(known_fixtures)) * 100.0
    urr = (unknown_pass / len(unknown_fixtures)) * 100.0
    far = ((len(unknown_fixtures) - unknown_pass) / len(unknown_fixtures)) * 100.0

    print("\n" + "=" * 65)
    print(" MÉTRICAS DE OPEN-SET RECOGNITION (OOD)")
    print("=" * 65)
    print(f"  * Known Acceptance Rate (KAR):   {kar:.1f}% ({known_pass}/{len(known_fixtures)})")
    print(f"  * Unknown Rejection Rate (URR): {urr:.1f}% ({unknown_pass}/{len(unknown_fixtures)})")
    print(f"  * False Acceptance Rate (FAR):  {far:.1f}%")
    print("=" * 65)

    if kar >= 90.0 and urr == 100.0 and far == 0.0:
        print("RESULTADO: SUITE OPEN-SET APROVADA COM SUCESSO! (FAR = 0.0%)")
        sys.exit(0)
    else:
        print("RESULTADO: FALHA NA SUITE OPEN-SET.")
        sys.exit(1)


if __name__ == "__main__":
    run_open_set_tests()
