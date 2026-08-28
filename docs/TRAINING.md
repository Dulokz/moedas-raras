# Guia de Indexação e Treinamento — Moedas Raras

## Indexação de Referências Visuais

Para indexar novas moedas ou atualizar os embeddings visuais das referências existentes no dataset:

1. Adicione a nova pasta de emissão sob `dataset/brl/<denominação>/<nome_emissão>/` com as subpastas `obverse/` e `reverse/`.
2. Adicione pelo menos uma imagem representativa da frente e do verso.
3. Execute o script de indexação:

```bash
python backend/services/dataset_indexer.py
```

O script irá extrair embeddings invariantes à rotação para cada imagem e atualizar o índice em memória e no cache.

---

## Adicionando Novas Emissões ao Catálogo

Para cadastrar uma nova moeda:
1. Abra `data/catalog-official.json`.
2. Adicione o objeto numismático seguindo a estrutura:

```json
{
  "id": "brl-1-2025-60-anos-bcb",
  "denomination": "1.00",
  "year": "2025",
  "family": "segunda_familia",
  "type": "commemorative",
  "commemorative": true,
  "design_name": "60 anos do Banco Central do Brasil",
  "material": "bimetallic",
  "diameter_mm": 27.0,
  "weight_g": 7.0,
  "official": true
}
```

3. Crie a pasta correspondente no dataset e coloque as fotos de referência.
