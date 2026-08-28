# Guia de Instalação, Execução e Testes — Moedas Raras V2

## Requisitos
- Python 3.10+
- Pip
- Navegador Web moderno (Chrome, Safari, Edge ou Firefox com suporte a PWA/MediaDevices API)

---

## 1. Instalação das Dependências

Instale os pacotes Python necessários:

```bash
pip install fastapi uvicorn torch torchvision opencv-python pillow pydantic numpy
```

---

## 2. Gerar Dataset e Fixtures de Teste

Execute o script de geração das referências do dataset e das fotos fixtures de teste:

```bash
python scripts/generate_dataset_and_fixtures.py
```

Isso criará a estrutura em `dataset/brl/1_real/` e as fotos de teste sob `tests/fixtures/brl_1_2024_30_anos/`.

---

## 3. Execução da Suíte de Testes Automatizados

Rode a suíte de testes de reconhecimento para verificar a acurácia no caso obrigatório (**R$ 1,00 - 2024 - 30 anos do Real**):

```bash
python tests/run_recognition_tests.py
```

O script testará o modelo contra várias fotos fixtures sob rotações (0°, 90°, 180°, 270°), iluminações variadas, fundos diferentes e lados invertidos.

---

## 4. Executando o Backend FastAPI

Inicie o servidor de desenvolvimento em porta local 8000:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints disponíveis:
- Documentação Swagger: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/api/health`
- Reconhecimento: `POST http://localhost:8000/api/identify`

---

## 5. Executando o Frontend PWA

Abra o arquivo `index.html` em um servidor HTTP estático (ou `npx serve .` / GitHub Pages).
O PWA se comunicará automaticamente com o backend em `http://localhost:8000/api/identify`.
