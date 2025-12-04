# Enriched Items API
FastAPI para extraer descripciones públicas de Mercado Libre y enriquecerlas con Gemini. Incluye jobs en background con auditoría, persistencia SQLite, discoverability (búsqueda/paginación) y documentación Swagger.

## Setup (Python 3.11+, uv)
```bash
uv venv .venv
source .venv/bin/activate
uv sync
```
Agregar dependencias: `uv add <paquete>`.

## Variables de entorno clave
- `APP_ENV` (default `local`)
- `MELI_ACCESS_TOKEN` (requerido para consumir MELI)
- `GEMINI_API_KEY` (requerido para enriquecer con Gemini)
- `GEMINI_MODEL` (default `gemini-2.0-flash`)
- `APP_DB_PATH` (default `data/app.db`)
- Opcionales: `MELI_REFRESH_TOKEN`, `MELI_CLIENT_ID`, `MELI_CLIENT_SECRET`, `MELI_REDIRECT_URI`.

## Ejecutar la API
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
# Swagger: http://localhost:8000/docs
# Redoc:   http://localhost:8000/redoc
# Health:  http://localhost:8000/health
```

## Endpoints principales
- `POST /extract/items/descriptions` encola extracción de descripciones para `item_ids`.
- `GET /extract/jobs` y `GET /extract/jobs/{id}`: auditoría de jobs (started_at, finished_at, duration_seconds, total_tasks, resultado).
- `POST /enrichment/run` encola enriquecimiento (`item_ids`, `tone`, `max_words`, `model`). Valida modelo contra `GET /enrichment/models`.
- `GET /enrichment/jobs`, `GET /enrichment/jobs/{id}`: auditoría de jobs de enriquecimiento.
- `GET /enrichment/enriched` lista productos enriquecidos con filtros de texto/fecha y paginación.
- `GET /enrichment/enriched/{item_id}` obtiene un enriquecido puntual.
- `GET /enrichment/models` lista modelos disponibles de Gemini.

## Persistencia
- SQLite en `APP_DB_PATH`. Tabla `enriched_products` con `id` autoincremental, `item_id` puede repetirse (no se sobrescriben registros).

## Idempotency y errores
- Idempotency-Key: header opcional en endpoints de encolado para evitar duplicados.
- Códigos: 400 (modelo inválido), 404 (job/producto no encontrado), 429 (rate limit Gemini gestionado y logueado), 500 (errores inesperados logueados).

## Colab (resumen)
- Instalar deps, setear `MELI_ACCESS_TOKEN` y `GEMINI_API_KEY`, exponer con ngrok, arrancar uvicorn, probar Swagger en `/docs`.
- Flujos de ejemplo: extraer → consultar job → enriquecer → consultar job → listar enriquecidos → listar modelos.

## Observabilidad
- Logging en inglés, jobs con auditoría (inicio/fin/duración/tareas), healthcheck. Para métricas/traceo se puede integrar fácilmente con middlewares de FastAPI.
