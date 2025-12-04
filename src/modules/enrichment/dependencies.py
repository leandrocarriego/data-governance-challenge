from src.modules.enrichment.db import EnrichedProductsRepository

def get_products_repo() -> EnrichedProductsRepository:
    return EnrichedProductsRepository()