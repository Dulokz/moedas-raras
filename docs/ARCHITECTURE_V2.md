# Arquitetura do Mecanismo de Reconhecimento Numismático — Moedas Raras V2

## Visão Geral

O sistema **Moedas Raras V2** adota uma abordagem **Visual-First (Motor de Visão Computacional)**. As tentativas frágeis baseadas em OCR geral da moeda e heurísticas regex em JavaScript foram substituídas por um pipeline em camadas operado por um backend **Python + FastAPI + OpenCV + PyTorch/torchvision**.

---

## Diagrama da Arquitetura

```
  ┌─────────────────────────────────────────────────────────────┐
  │                    FRONTEND / PWA                           │
  │  Captura dupla (Frente + Verso) com foco & nitidez adaptativa│
  └──────────────────────────────┬──────────────────────────────┘
                                 │ POST /api/identify
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                     BACKEND FASTAPI                         │
  │                                                             │
  │  1. RECORTE E NORMALIZAÇÃO CIRCULAR (OpenCV)               │
  │     - Hough Circles / Contornos                             │
  │     - Crop com margem dinâmica (224x224)                    │
  │     - Mascaramento e remoção do fundo                       │
  │                                                             │
  │  2. EXTRAÇÃO DE EMBEDDINGS VISUAIS (PyTorch/torchvision)    │
  │     - Redes Convolucionais (MobileNetV3 / ResNet)           │
  │     - Rotações Cardinais (0°, 90°, 180°, 270°)              │
  │     - Vetor denso L2-normalizado                            │
  │                                                             │
  │  3. ASSINATURA FÍSICA E BIMETALISMO                         │
  │     - Análise de núcleos e anéis em espaço HSV/LAB          │
  │     - Verificação de núcleo dourado + anel prateado (R$1)    │
  │                                                             │
  │  4. CLASSIFICAÇÃO E CONSULTA AO CATÁLOGO                    │
  │     - Cosine Similarity contra índice de referências        │
  │     - Consulta ao banco `catalog-official.json`             │
  │     - Derivação automática de Ano, Tipo e Comemorativa      │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              RESPOSTA JSON ESTRUTURADA                      │
  │  { denomination, year, design, commemorative, confidence }   │
  └─────────────────────────────────────────────────────────────┘
```

---

## Camadas do Pipeline

### 1. Detecção e Normalização (OpenCV)
- Identifica a moeda na imagem capturada utilizando a Transformada de Círculos de Hough e contornos circulares.
- Ajusta a escala e faz o recorte centralizado com margem de 5%.
- Redimensiona para **224×224 pixels** e converte a cor para espaço de cor RGB/HSV normalizado.

### 2. Extrator de Características Visuais (PyTorch / torchvision)
- Utiliza um backbone convolucional leve e eficiente (`MobileNet_V3_Small` com pesos ImageNet) sem a camada final de classificação.
- Extrai vetores de embeddings denso de 576 dimensões para a frente e o verso.
- Para garantir **invariância à rotação da câmera (0°, 90°, 180°, 270°)**, o modelo extrai embeddings das rotações cardinais e calcula a máxima similaridade de cosseno.

### 3. Detetor de Bimetalismo
- Para moedas de R$ 1,00 (bimetálicas com núcleo de aço revestido de bronze e anel de aço inoxidável), o motor verifica o tom de cor e saturação no núcleo (raio de 0 a 22%) versus anel externo (raio de 30% a 45%).

### 4. Casamento com Catálogo Estruturado
- A similaridade é comparada contra o índice pré-calculado das emissões oficiais cadastradas em `data/catalog-official.json`.
- Se a assinatura visual corresponde a `"30 anos do Real"`, a denominação (`R$ 1,00`), o ano (`2024`), o tipo (`comemorativa`) e as tiragens são retornados diretamente do catálogo com alta confiança sem depender de leitura de dígitos gravados.
