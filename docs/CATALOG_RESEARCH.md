# Pesquisa de fontes — catálogo visual numismático

Objetivo: construir uma base própria para triagem automática de moedas do padrão Real, distinguindo emissão oficial, variante catalogada, erro de cunhagem e simples dano/desgaste pós-cunhagem.

## Hierarquia de evidência

### Nível A — fonte oficial
- Banco Central do Brasil (BCB): moedas emitidas, famílias do Real, características técnicas, tiragens e moedas comemorativas.
- Museu de Valores / acervo do BCB: referência histórica e imagens oficiais quando disponíveis.
- Casa da Moeda do Brasil: processo/fabricação e documentação técnica quando disponível.

Uso: verdade primária para existência da emissão, desenho esperado, material, diâmetro, peso, bordo, alinhamento, ano e tiragem.

### Nível B — catálogos numismáticos consolidados
- Numista: tipos, variantes, referências KM/Bentes e imagens; útil para cruzamento internacional e exemplos visuais.
- Moedas do Brasil / CRMB: catálogo brasileiro com características, emissões e cruzamento de códigos Amato, Vieira, Bentes, KM e BCB.
- Catálogo Bentes: catálogo didático-descritivo, incluindo variantes de cunho.
- Livro das Moedas do Brasil — Amato/Neves.
- Catálogo Vieira.
- Catálogo Moedas com Erros do Brasil — Lucimar Bueno e Edil Gomes; fonte especializada em erros, reversos e anomalias.

Uso: confirmar nomenclatura e ocorrência conhecida de variantes/erros. Uma ocorrência deve idealmente ser confirmada em mais de uma referência antes de virar regra de alta confiança.

### Nível C — bases e comerciantes especializados
- uCoin: exemplos de tipos/erros e dados de catálogo.
- Numismática Castro: exemplos fotográficos de erros anunciados (cunho marcado, cunho fraco, rotação, batida dupla etc.).
- Rocha Numismática: exemplos fotográficos de erros e variantes.

Uso: descoberta e coleta de hipóteses/exemplos. Não usar preço de anúncio como valor numismático comprovado e não promover uma alegação a “catalogada” sem cruzamento.

### Nível D — comunidade
- Grupos de numismática, fóruns, vídeos e colecionadores.

Uso: descoberta de possíveis variedades e, futuramente, dataset colaborativo. Nunca tratar uma postagem isolada como prova.

## Fontes encontradas

- BCB — Moedas comemorativas do Real em circulação: https://www.bcb.gov.br/cedulasemoedas/moedascirculacaocomemorativas
- BCB — Moedas comemorativas: https://www.bcb.gov.br/cedulasemoedas/moedascomemorativas
- BCB — FAQ moedas comemorativas: https://www.bcb.gov.br/meubc/faqs/p/moedas-comemorativas
- BCB — Museu de Valores / acervo e exposições: https://www.bcb.gov.br/
- Numista — catálogo Brasil: https://pt.numista.com/catalogue/bresil-21.html
- Numista — 50 centavos mula 2012: https://pt.numista.com/94947
- Moedas do Brasil / CRMB: https://www.moedasdobrasil.com.br/moedas/catalogo.asp
- Bentes: https://www.bentes.com/coins-catalog
- Catálogo Amigo — Moedas do Real: Erros e Variantes: https://www.catalogoamigo.com/produto/catalogo-moedas-do-real-erros-e-variantes/
- uCoin — Brasil: https://pt.ucoin.net/
- Numismática Castro — moedas com erros: https://www.numismaticacastro.com.br/moedas-nacionais/moedas-com-erros/
- Rocha Numismática — moedas com erros: https://rochanumismatica.com.br/moedas-nacionais/moedas-com-erros/

## Modelo de dados desejado

Cada emissão/variante deverá possuir:

- id estável
- valor facial
- família
- ano e marca de casa da moeda
- tipo: regular / comemorativa / variante / erro
- nome do desenho
- tiragem oficial quando conhecida
- material, diâmetro, peso, espessura e bordo
- alinhamento/eixo esperado
- descrição do anverso e reverso
- regiões visuais esperadas (ROI): valor, ano, estrelas, efígie, legenda, símbolo, borda, núcleo/anel
- características geométricas esperadas
- lista de variantes/erros conhecidos
- instrução de identificação
- fontes e nível de evidência por afirmação
- referências de catálogo (CRMB, KM, Bentes, Amato, Vieira, Numista etc.)
- imagens de referência próprias/licenciadas, com origem/licença registradas

## Regra crítica para imagens

Não copiar em massa imagens de sites/catálogos sem verificar licença/permissão. Dados factuais e referências podem formar nossa base, mas o dataset visual do classificador deve usar imagens oficiais com uso permitido, imagens licenciadas ou fotos próprias/cedidas por colecionadores.

Isso também é uma oportunidade: o app pode permitir que colecionadores enviem fotos de exemplares confirmados e autorizem seu uso para melhorar o modelo.

## Arquitetura do reconhecimento

1. Captura automática quando nitidez/estabilidade atingirem limiar.
2. Segmentação da moeda e remoção do fundo.
3. Normalização de escala, perspectiva, iluminação e rotação.
4. Classificador de denominação/família/desenho.
5. Determinação de ano/marca por visão + OCR como sinal auxiliar.
6. Seleção do gabarito correto.
7. Alinhamento da foto com o gabarito.
8. Comparação por regiões semânticas.
9. Detectores específicos: rotação, descentralização, duplicação, cunho fraco/entupido, elementos ausentes, núcleo/anel, bordo e mula.
10. Separação entre desgaste/dano provável e anomalia de cunhagem.
11. Resultado conservador: normal / inconclusivo / anomalia / compatível com variante catalogada.

## Princípio do produto

O sistema não “certifica” raridade. Ele faz triagem visual automática de alta sensibilidade. Se houver dúvida, a moeda é separada para revisão humana.
