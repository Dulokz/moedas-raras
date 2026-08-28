import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.vision import vision_engine
from backend.services.dataset_indexer import index_dataset
from backend.services.catalog import catalog_service


def run_tests():
    print("=" * 65)
    print(" MOEDAS RARAS V2 -- SUITE DE TESTES AUTOMATIZADOS DE RECONHECIMENTO")
    print("=" * 65)

    # 1. Ensure catalog and visual dataset index are loaded
    print("\n[1/3] Carregando catalogo e indexando dataset...")
    catalog_service.load_catalog()
    index_dataset()

    # 2. Find test fixture pairs in tests/fixtures/brl_1_2024_30_anos
    fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "brl_1_2024_30_anos"
    if not fixtures_dir.exists():
        print(f"ERRO: Diretorio de fixtures {fixtures_dir} nao foi encontrado!")
        sys.exit(1)

    front_files = sorted(list(fixtures_dir.glob("*_front.jpg")))
    if not front_files:
        print("ERRO: Nenhuma foto fixture encontrada em tests/fixtures/brl_1_2024_30_anos")
        sys.exit(1)

    print(f"\n[2/3] Executando testes em {len(front_files)} fotos fixtures de R$1 2024 (30 anos do Real)...")
    print("-" * 65)

    passed = 0
    failed = 0
    total = len(front_files)
    latencies = []

    for front_path in front_files:
        test_name = front_path.name.replace("_front.jpg", "")
        back_path = fixtures_dir / f"{test_name}_back.jpg"

        if not back_path.exists():
            print(f"  [SKIP] Verso nao encontrado para {test_name}")
            continue

        with open(front_path, "rb") as f:
            front_bytes = f.read()
        with open(back_path, "rb") as f:
            back_bytes = f.read()

        t0 = time.time()
        res = vision_engine.identify(front_bytes, back_bytes)
        t_elapsed = (time.time() - t0) * 1000
        latencies.append(t_elapsed)

        # Mandatory test criteria assertions
        ok_denom = res.denomination in ["1.00", "1"]
        ok_year = res.year == "2024"
        ok_design = "30 anos" in res.design.lower() or "30 anos do real" in res.design.lower()
        ok_comm = res.commemorative is True
        ok_identified = res.identified is True

        is_pass = ok_denom and ok_year and ok_design and ok_comm and ok_identified

        if is_pass:
            passed += 1
            status = "[PASS]"
        else:
            failed += 1
            status = "[FAIL]"

        print(f"{status} | {test_name:<22} | R${res.denomination:<4} | {res.year:<4} | {res.design:<20} | Conf: {res.confidence*100:.1f}% | {t_elapsed:.0f}ms")
        if not is_pass:
            print(f"       |- Falha nos criterios: denom={ok_denom}, ano={ok_year}, design={ok_design}, comemorativa={ok_comm}")

    # 3. Report summary & metrics
    print("-" * 65)
    accuracy = (passed / total) * 100 if total > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    print(f"\n[3/3] RESUMO DAS METRICAS:")
    print(f"  * Total de Testes:   {total}")
    print(f"  * Aprovados (PASS):  {passed}")
    print(f"  * Reprovados (FAIL): {failed}")
    print(f"  * Top-1 Accuracy:    {accuracy:.1f}%")
    print(f"  * Latencia Media:    {avg_latency:.1f} ms")
    print("=" * 65)

    if accuracy >= 95.0:
        print("RESULTADO: SUITE DE TESTES APROVADA COM SUCESSO! (>95% acuracia)")
        sys.exit(0)
    else:
        print("RESULTADO: FALHA NA SUITE DE TESTES (acuracia abaixo da meta de 95%)")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
