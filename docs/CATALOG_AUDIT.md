# Audit do Catálogo Numismático Antigo — Moedas Raras

**Data do Diagnóstico:** 28 de agosto de 2026  
**Status do Mapeamento:** Concluído com sucesso  

---

## 1. Contexto e Diagnóstico da Estrutura Antiga

A versão prévia do projeto utilizava um arquivo monolítico `data/catalog-official.json` contendo um array genérico de moedas com schema v2/v3 preliminar, acompanhado por `data/source-registry.json`.

### Inconsistências e Problemas Encontrados na Auditoria:

1. **Duplicação de Histórias e Especificações:**
   - As descrições do anverso/reverso, especificações físicas (diâmetro, peso, material) e histórias eram repetidas para cada moeda como se cada ano fosse uma peça completamente isolada, gerando duplicidade desnecessária no repositório.
2. **Conflito de Nível de Evidência e Fontes Desconectadas:**
   - As fontes em `data/source-registry.json` usavam a nomenclatura `tier` (`"A"`, `"B"`, `"C"`) em vez da nomenclatura unificada `level` (`"A"`, `"B"`, `"C"`, `"D"`).
   - As entradas do catálogo continham URLs soltas sem chave estrangeira para o registro central de fontes.
3. **Ausência de Desacoplamento entre Desenho (Design) e Emissão Anual (Issue):**
   - Não havia separação clara entre a arte visual (ex.: *R$ 1 Regular 2ª Família*) e a emissão física de um determinado ano (ex.: *R$ 1 2024*).
4. **Variantes e Erros Misturados:**
   - Algumas variantes de cunho (ex.: *Marca A da Royal Dutch Mint*) estavam listadas como erros genéricos, e erros de cunhagem (ex.: *Reverso Invertido*) não possuíam campos estruturados de verificação numismática.
5. **Falta de Validador de Integridade Referencial:**
   - Não existia script para validar automaticamente se um `source_id` existia ou se uma tiragem possuía valor numérico válido.

---

## 2. Decisão de Redesign e Modelo Normalizado

Para solucionar essas deficiências de arquitetura e garantir auditabilidade e facilidade de manutenção no Git, os dados foram migrados e desacoplados no diretório `data/catalog/`:

- `data/catalog/sources.json`: Cadastro central e imutável de fontes com identificadores únicos.
- `data/catalog/denominations.json`: Definição das 6 denominações do Real.
- `data/catalog/families.json`: 1ª Família (Inox/Bronze) e 2ª Família (Bimetálica/Aço Revestido).
- `data/catalog/designs.json`: Desenhos artísticos e histórias compartilhadas.
- `data/catalog/issues.json`: Emissões físicas anuais com tiragens oficiais do BCB.
- `data/catalog/variants.json`: Variantes catalogadas e comprovadas.
- `data/catalog/errors.json`: Erros de cunhagem documentados.

---

## 3. Matriz de Qualidade dos Dados

| Componente Antigo | Qualidade Antiga | Ação Corretiva Aplicada |
| :--- | :--- | :--- |
| Registro de Fontes | 🟡 Parcial (`tier` A, B, C) | Migrado para `sources.json` com `level` A, B, C, D e campos padronizados |
| Moedas de R$ 1,00 | 🟡 Parcial (Apenas 8 emissões) | Expandido em `issues.json` para **todas as 35+ emissões de 1994 a 2025** |
| Especificações Físicas | ⚠️ Incompletas em alguns registros | Preenchidas via dados oficiais do Banco Central do Brasil |
| Variantes & Erros | ⚠️ Incompletos / Não padronizados | Separados em `variants.json` e `errors.json` com `diagnostic_features` |
