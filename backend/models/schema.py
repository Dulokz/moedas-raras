from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class Candidate(BaseModel):
    id: str = Field(..., description="ID estável da moeda/emissão no catálogo")
    design: str = Field(..., description="Nome do desenho/emissão")
    confidence: float = Field(..., description="Nível de confiança (0.0 a 1.0)")
    denomination: str = Field(..., description="Denominação facial ex.: 1.00")
    year: str = Field(..., description="Ano/era da moeda")
    commemorative: bool = Field(..., description="Se a moeda é comemorativa")


class History(BaseModel):
    title: Optional[str] = None
    short_summary: Optional[str] = None
    full_context: Optional[str] = None
    event: Optional[str] = None
    issue_date: Optional[str] = None


class Specifications(BaseModel):
    diameter_mm: Optional[float] = None
    weight_g: Optional[float] = None
    thickness_mm: Optional[float] = None
    material: Optional[str] = None
    edge: Optional[str] = None
    alignment: Optional[str] = None


class SideDescription(BaseModel):
    description: Optional[str] = None
    inscriptions: List[str] = Field(default_factory=list)


class Rarity(BaseModel):
    relative_rarity: Optional[str] = None
    notes: Optional[str] = None


class Reference(BaseModel):
    source: str
    url: Optional[str] = None
    evidence_level: str = "A"


class CatalogItem(BaseModel):
    id: str
    country: str = "Brasil"
    currency: str = "BRL"
    denomination: str
    family: str
    year: str
    mint_mark: str = "Nenhum"
    type: str = "regular"
    design_name: Optional[str] = "Moeda do Real"
    commemorative: bool = False
    status: str = "official"
    history: Optional[History] = None
    specifications: Optional[Specifications] = None
    mintage: Optional[int] = None
    obverse: Optional[SideDescription] = None
    reverse: Optional[SideDescription] = None
    rarity: Optional[Rarity] = None
    known_variants: List[Any] = Field(default_factory=list)
    known_errors: List[str] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)


class IdentifyResponse(BaseModel):
    identified: bool = Field(..., description="Se a moeda foi identificada com confiança")
    reason: Optional[str] = Field(None, description="Razão de aceitação ou rejeição open-set (accepted, unknown_coin, ambiguous_match, low_confidence)")
    denomination: str = Field(..., description="Denominação facial identificada ex.: 1.00")
    year: str = Field(..., description="Ano identificado ou padrão do catálogo")
    family: str = Field(..., description="Família da moeda (ex.: segunda_familia)")
    design: str = Field(..., description="Nome do desenho/emissão")
    commemorative: bool = Field(..., description="Se é comemorativa")
    confidence: float = Field(..., description="Confiança global (0.0 a 1.0)")
    coin_details: Optional[CatalogItem] = Field(None, description="Metadados completos da moeda no catálogo")
    best_candidate: Optional[Candidate] = Field(None, description="Melhor candidato retornado se a moeda for rejeitada")
    candidates: List[Candidate] = Field(default_factory=list, description="Lista de moedas candidatas com scores")
    warnings: List[str] = Field(default_factory=list, description="Alertas ou observações de triagem")
    bimetallic_detected: bool = Field(default=False, description="Se estrutura bimetálica foi detectada")
