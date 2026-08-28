import sys
import json
from pathlib import Path

def validate_catalog():
    print("=" * 65)
    print(" MOEDAS RARAS — AUDITORIA AUTOMÁTICA DO CATÁLOGO NUMISMÁTICO")
    print("=" * 65)

    catalog_dir = Path(__file__).resolve().parent.parent / "data" / "catalog"

    files_to_check = [
        "sources.json",
        "denominations.json",
        "families.json",
        "designs.json",
        "issues.json",
        "variants.json",
        "errors.json"
    ]

    # 1. Check all JSON files parse correctly
    data = {}
    for filename in files_to_check:
        filepath = catalog_dir / filename
        if not filepath.exists():
            print(f"ERRO CRÍTICO: Arquivo {filepath} não encontrado!")
            sys.exit(1)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data[filename] = json.load(f)
                print(f"  [OK] Parsed {filename}")
            except Exception as e:
                print(f"ERRO ao decodificar JSON {filename}: {e}")
                sys.exit(1)

    errors_found = 0
    warnings_found = 0

    # Index Source IDs
    source_ids = {s["id"] for s in data["sources.json"].get("sources", [])}
    print(f"\nFontes cadastradas em sources.json: {len(source_ids)}")

    # Index Denomination Values
    denom_values = {d["value"] for d in data["denominations.json"].get("denominations", [])}

    # Index Family IDs
    family_ids = {f["id"] for f in data["families.json"].get("families", [])}

    # Index Design IDs
    designs = data["designs.json"].get("designs", [])
    design_ids = {d["id"] for d in designs}
    print(f"Designs cadastrados em designs.json: {len(design_ids)}")

    # Index Issue IDs
    issues = data["issues.json"].get("issues", [])
    issue_ids = {i["id"] for i in issues}
    print(f"Emissões cadastradas em issues.json: {len(issue_ids)}")

    # 2. Validate Designs
    for d in designs:
        if d.get("family_id") not in family_ids:
            print(f"ERRO: Design {d['id']} aponta para family_id inexistente '{d.get('family_id')}'")
            errors_found += 1
        if d.get("denomination_value") not in denom_values:
            print(f"ERRO: Design {d['id']} aponta para denominação inexistente '{d.get('denomination_value')}'")
            errors_found += 1

    # 3. Validate Issues
    for iss in issues:
        iss_id = iss.get("id")
        if not iss_id:
            print("ERRO: Registro em issues.json sem campo 'id'")
            errors_found += 1
            continue

        if iss.get("design_id") not in design_ids:
            print(f"ERRO: Emissão '{iss_id}' aponta para design_id inexistente '{iss.get('design_id')}'")
            errors_found += 1

        if iss.get("denomination_value") not in denom_values:
            print(f"ERRO: Emissão '{iss_id}' aponta para denominação inexistente '{iss.get('denomination_value')}'")
            errors_found += 1

        mintage = iss.get("mintage")
        if mintage is not None and (not isinstance(mintage, int) or mintage < 0):
            print(f"ERRO: Emissão '{iss_id}' possui mintage inválida: {mintage}")
            errors_found += 1

        for src in iss.get("sources", []):
            sid = src.get("source_id")
            if sid not in source_ids:
                print(f"ERRO: Emissão '{iss_id}' aponta para source_id inexistente '{sid}'")
                errors_found += 1

    # 4. Validate Variants
    variants = data["variants.json"].get("variants", [])
    print(f"Variantes cadastradas em variants.json: {len(variants)}")
    for v in variants:
        vid = v.get("id")
        if v.get("issue_id") not in issue_ids:
            print(f"ERRO: Variante '{vid}' aponta para issue_id inexistente '{v.get('issue_id')}'")
            errors_found += 1
        for src in v.get("sources", []):
            if src.get("source_id") not in source_ids:
                print(f"ERRO: Variante '{vid}' aponta para source_id inexistente '{src.get('source_id')}'")
                errors_found += 1

    # 5. Validate Errors
    err_list = data["errors.json"].get("errors", [])
    print(f"Erros de cunhagem cadastrados em errors.json: {len(err_list)}")
    for err in err_list:
        eid = err.get("id")
        if err.get("issue_id") not in issue_ids:
            print(f"ERRO: Registro de Erro '{eid}' aponta para issue_id inexistente '{err.get('issue_id')}'")
            errors_found += 1
        for src in err.get("sources", []):
            if src.get("source_id") not in source_ids:
                print(f"ERRO: Registro de Erro '{eid}' aponta para source_id inexistente '{src.get('source_id')}'")
                errors_found += 1

    print("\n" + "=" * 65)
    print(" RESUMO DA AUDITORIA DO CATÁLOGO")
    print("=" * 65)
    print(f"  * Erros Críticos Encontrados: {errors_found}")
    print(f"  * Alertas / Incompletos:     {warnings_found}")
    print("=" * 65)

    if errors_found == 0:
        print(">>> SUCESSO: CATÁLOGO NUMISMÁTICO VÁLIDO E ESTRUTURADO! <<<")
        sys.exit(0)
    else:
        print(">>> FALHA: O CATÁLOGO POSSUI INCONSISTÊNCIAS ESTRUTURAIS. <<<")
        sys.exit(1)

if __name__ == "__main__":
    validate_catalog()
