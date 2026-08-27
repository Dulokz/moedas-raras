# Arquitetura de reconhecimento — direção definida

## Benchmark
- Coinoscope: reconhecimento visual + catálogo + análise avançada; imagens são enviadas ao servidor do próprio serviço. Os termos proíbem acesso direto de terceiros ao motor sem autorização.
- Maktun: busca por foto usando catálogo próprio de grande escala.
- CoinVision (open source): projeto brasileiro usando detecção circular + SIFT + bag-of-visual-words + classificador.
- Dataset Brazilian Coins (Kaggle): útil para treinar identificação de denominação, não suficiente sozinho para variantes/ano.

## Decisão
O app não deve depender de OCR geral da moeda. A arquitetura final é híbrida:
1. Captura automática com foco/estabilidade.
2. Detecção e normalização circular da moeda.
3. Classificação visual da denominação/família.
4. Alinhamento com referência conhecida.
5. Leitura dirigida do ano na ROI prevista para aquele modelo.
6. Comparação visual por regiões para anomalias e variantes.
7. Se confiança insuficiente: RETER/REVISAR, nunca liberar como comum.

## Fase atual
`recognizer-v2.js` melhora imediatamente a leitura de ano/valor usando ROIs pequenas e rotações, substituindo o OCR geral na UI assim que carregado. É uma ponte até o modelo visual treinado.

## Próximo dataset próprio
Salvar, mediante consentimento, frente/verso de exemplares normais e variantes, rotulados por valor, ano, família e tipo. Isso permitirá treinar o classificador e o detector de anomalias com as condições reais da câmera do app.
