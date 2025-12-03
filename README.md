# Enriched Items API

Demo FastAPI para enriquecer productos de MercadoLibre con LLM.

## Setup con uv (Python 3.11+)
```bash
uv venv .venv
source .venv/bin/activate
uv sync  # instala dependencias declaradas en pyproject.toml
```
Para agregar nuevas dependencias: `uv add <paquete>`.

## Ejecutar
```bash
export DATA_FILE=data/enriched_items_sample.json  # opcional
uvicorn src.main:app --reload --port 8000
# Docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

## Configuración
Variables con prefijo `APP_` (pydantic-settings):
- `APP_APP_NAME` (default: Enriched Items API)
- `APP_VERSION` (default: 0.1.0)
- `APP_ENV` (default: local)
- `APP_MELI_ACCESS_TOKEN` (requerido para consumir las APIs de Mercado Libre)
