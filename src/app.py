import logging
from fastapi import FastAPI

from src.modules.enrichment.routes import router as enrichment_router
from src.modules.extract.routes import router as extract_router
from src.modules.products.routes import router as products_router
from src.settings import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app.include_router(extract_router)
app.include_router(enrichment_router)
app.include_router(products_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.environment}


@app.get("/oauth/callback", tags=["auth"])
def oauth_callback(code: str | None = None, state: str | None = None, error: str | None = None) -> dict[str, str | None]:
    """Receives the OAuth redirect from Mercado Libre."""
    if error:
        return {"error": error, "state": state}
    
    print(code)

    return {"code": code, "state": state}
