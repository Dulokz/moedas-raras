import json
from pathlib import Path
from typing import Dict, List, Optional
from backend.config import CATALOG_PATH
from backend.models.schema import CatalogItem, History, Specifications, SideDescription, Rarity, Reference


class NumismaticCatalog:
    def __init__(self, catalog_path: Path = CATALOG_PATH):
        self.catalog_path = catalog_path
        self.coins: Dict[str, CatalogItem] = {}
        self.load_catalog()

    def load_catalog(self):
        catalog_dir = self.catalog_path.parent / "catalog"
        if catalog_dir.exists() and (catalog_dir / "issues.json").exists():
            self._load_from_modular_catalog(catalog_dir)
        elif self.catalog_path.exists():
            self._load_from_legacy_catalog()

    def _load_from_modular_catalog(self, catalog_dir: Path):
        with open(catalog_dir / "designs.json", "r", encoding="utf-8") as f:
            designs_data = {d["id"]: d for d in json.load(f).get("designs", [])}

        with open(catalog_dir / "sources.json", "r", encoding="utf-8") as f:
            sources_data = {s["id"]: s for s in json.load(f).get("sources", [])}

        with open(catalog_dir / "issues.json", "r", encoding="utf-8") as f:
            issues = json.load(f).get("issues", [])

        for iss in issues:
            d_id = iss.get("design_id")
            design = designs_data.get(d_id, {})

            hist_data = design.get("history", {})
            specs_data = iss.get("specifications", {})
            obv_data = design.get("obverse", {})
            rev_data = design.get("reverse", {})
            rarity_data = iss.get("rarity", {})

            ref_list = []
            for src in iss.get("sources", []):
                s_obj = sources_data.get(src.get("source_id"), {})
                if s_obj:
                    ref_list.append(Reference(
                        source=s_obj.get("name", "Fonte Oficial"),
                        url=s_obj.get("url"),
                        evidence_level=s_obj.get("level", "A")
                    ))

            coin_id = f"brl-{iss.get('denomination_value')}-{iss.get('year')}-{design.get('name', '').lower().replace(' ', '-')}"
            if iss.get("id") == "issue-brl-1-2024-30-anos-real":
                coin_id = "brl-1-2024-30-anos-real"
            elif iss.get("id") == "issue-brl-1-2024-regular":
                coin_id = "brl-1-regular-segunda-familia"

            item = CatalogItem(
                id=coin_id,
                country="Brasil",
                currency="BRL",
                denomination=iss.get("denomination_value", "1.00"),
                family=design.get("family_id", "segunda_familia"),
                year=str(iss.get("year")),
                mint_mark="Nenhum",
                type=iss.get("type", "regular"),
                design_name=design.get("name", "Moeda do Real"),
                commemorative=design.get("commemorative", False),
                status=iss.get("status", "official"),
                history=History(
                    title=hist_data.get("short_summary"),
                    short_summary=hist_data.get("short_summary"),
                    full_context=hist_data.get("full_text"),
                    event=design.get("theme"),
                    issue_date=f"{iss.get('year')}-01-01"
                ),
                specifications=Specifications(
                    diameter_mm=specs_data.get("diameter_mm"),
                    weight_g=specs_data.get("weight_g"),
                    thickness_mm=specs_data.get("thickness_mm"),
                    material=specs_data.get("material"),
                    edge=specs_data.get("edge"),
                    alignment=specs_data.get("alignment")
                ),
                mintage=iss.get("mintage"),
                obverse=SideDescription(
                    description=obv_data.get("description"),
                    inscriptions=obv_data.get("inscriptions", [])
                ),
                reverse=SideDescription(
                    description=rev_data.get("description"),
                    inscriptions=rev_data.get("inscriptions", [])
                ),
                rarity=Rarity(
                    relative_rarity=rarity_data.get("status"),
                    notes=rarity_data.get("notes")
                ),
                known_variants=[],
                known_errors=[],
                references=ref_list
            )
            self.coins[coin_id] = item
            # Alias original issue ID
            self.coins[iss["id"]] = item

    def _load_from_legacy_catalog(self):
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("coins", []):
                coin = CatalogItem(**item)
                self.coins[coin.id] = coin

    def get_coin(self, coin_id: str) -> Optional[CatalogItem]:
        return self.coins.get(coin_id)

    def list_all(self) -> List[CatalogItem]:
        unique_coins = {}
        for c in self.coins.values():
            unique_coins[c.id] = c
        return list(unique_coins.values())


catalog_service = NumismaticCatalog()
