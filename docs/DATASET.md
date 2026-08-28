# Estrutura do Dataset Numismático — Moedas Raras

## Estrutura de Diretórios

O dataset visual está organizado sob o diretório `dataset/brl/` no seguinte formato:

```
dataset/
  brl/
    1_real/
      2024_30_anos_real/
        obverse/
          ref_obverse.jpg
          photo_01.jpg
        reverse/
          ref_reverse.jpg
          photo_01.jpg
        metadata.json
      2019_25_anos_real/
      1998_direitos_humanos/
      2005_40_anos_bcb/
      2012_bandeira_olimpica/
      2016_rio_2016/
      2025_60_anos_bcb/
      regular_segunda_familia/
```

---

## Esquema de Metadados (`metadata.json`)

Cada diretório de emissão pode conter um arquivo `metadata.json` com o esquema:

```json
{
  "coin_id": "brl-1-2024-30-anos-real",
  "denomination": "1.00",
  "year": "2024",
  "design": "30 anos do Real",
  "commemorative": true,
  "family": "segunda_familia",
  "material": "bimetallic",
  "sources": [
    {
      "name": "Banco Central do Brasil",
      "level": "A",
      "license": "Oficial BCB"
    }
  ]
}
```

---

## Hierarquia de Evidência e Origem das Imagens

1. **Nível A (Oficial):** Imagens do Banco Central do Brasil, Casa da Moeda do Brasil e Museu de Valores.
2. **Nível B (Catálogos Consolidados):** Numista, CRMB, Catálogo Bentes, Amato/Neves e Vieira.
3. **Nível C (Bases Especializadas):** uCoin, Numismática Castro, Rocha Numismática.
4. **Nível D (Comunidade):** Fotografias próprias cedidas por colecionadores autorizadas para o projeto.

---

## Diretrizes de Coleta e Licenciamento

- **Não realizar cópias em massa** de imagens protegidas por direitos autorais de catálogos comerciais.
- Utilizar fotos próprias, imagens oficiais de domínio público ou contribuições de usuários sob licença aberta.
