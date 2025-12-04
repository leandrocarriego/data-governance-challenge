from src.services.mercadolibre import MeliExtractService
from src.modules.extract.service import ExtractService


def get_extract_service() -> ExtractService:
    """Provide the extract orchestration service."""
    return ExtractService(meli_service=MeliExtractService())
