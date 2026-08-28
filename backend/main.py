import base64
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models.schema import IdentifyResponse
from backend.services.vision import vision_engine
from backend.services.catalog import catalog_service
from backend.services.dataset_indexer import index_dataset

app = FastAPI(
    title="Moedas Raras API",
    description="API de reconhecimento visual de moedas brasileiras do Real",
    version="2.0.0"
)

# Enable CORS for PWA frontend (local dev & production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    print("Iniciando Moedas Raras V2 Backend...")
    index_dataset()


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "engine": "Moedas Raras V2 (Visual-First OpenCV/NumPy)",
        "catalog_size": len(catalog_service.coins),
        "indexed_references": len(vision_engine.reference_index)
    }


@app.get("/api/catalog")
def get_catalog():
    return {"coins": catalog_service.list_all()}


class Base64IdentifyPayload(BaseModel):
    front: str  # Base64 encoded string or Data URL
    back: str   # Base64 encoded string or Data URL


def decode_base64_img(data_str: str) -> bytes:
    if "," in data_str:
        data_str = data_str.split(",", 1)[1]
    return base64.b64decode(data_str)


@app.post("/api/identify", response_model=IdentifyResponse)
async def identify(
    request: Request,
    front: Optional[UploadFile] = File(None),
    back: Optional[UploadFile] = File(None)
):
    try:
        front_bytes = None
        back_bytes = None

        # Check if request content type is JSON
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body_json = await request.json()
            front_str = body_json.get("front", "")
            back_str = body_json.get("back", "")
            if front_str and back_str:
                front_bytes = decode_base64_img(front_str)
                back_bytes = decode_base64_img(back_str)
        elif front and back:
            front_bytes = await front.read()
            back_bytes = await back.read()

        if not front_bytes or not back_bytes:
            raise HTTPException(
                status_code=400,
                detail="Por favor envie as fotos 'front' e 'back' (como Multipart Upload ou Base64 JSON)."
            )

        result = vision_engine.identify(front_bytes, back_bytes)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro no processamento visual: {e}")
        raise HTTPException(status_code=500, detail=str(e))
