from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime

from src.db import get_connection
from src.modules.enrichment.db import queries as enriched_products_queries
from src.modules.enrichment.schemas import EnrichedProduct


class EnrichedProductsRepository:
    """Repository for enriched_products stored in SQLite."""

    def __init__(self, connection_factory: Callable = get_connection) -> None:
        self._connection_factory = connection_factory
        self._init_db()

    def _init_db(self) -> None:
        """Ensure the enriched_products table exists."""

        with self._connection_factory() as connection:
            connection.execute(enriched_products_queries.INIT_DB)
            connection.commit()

    def insert_many(self, items: Iterable[dict]) -> None:
        """Insert many enriched items; ids autoincrement, item_id may repeat."""

        with self._connection_factory() as connection:
            for item in items:
                created_at = item.get("created_at") or datetime.utcnow().isoformat()
                connection.execute(
                    enriched_products_queries.INSERT_ONE,
                    (
                        item.get("item_id", ""),
                        item.get("original_description", ""),
                        item.get("enriched_description", ""),
                        created_at,
                    ),
                )
            connection.commit()

    def list(self) -> list[EnrichedProduct]:
        """Return all enriched products."""

        with self._connection_factory() as connection:
            rows = connection.execute(enriched_products_queries.LIST_ALL).fetchall()

        return [EnrichedProduct(**dict(row)) for row in rows]

    def get(self, item_id: str) -> EnrichedProduct | None:
        """Retrieve a product by item_id (latest match)."""

        with self._connection_factory() as connection:
            row = connection.execute(enriched_products_queries.GET_BY_ID, (item_id,)).fetchone()
        
        if not row:
            return None
        
        return EnrichedProduct(**dict(row))

    def search(
        self,
        q: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[EnrichedProduct], int]:
        """Search enriched products with filters and pagination."""
        
        conditions: list[str] = []
        params: list[str | int] = []

        if q:
            conditions.append("(original_description LIKE ? OR enriched_description LIKE ?)")
            like_term = f"%{q}%"
            params.extend([like_term, like_term])

        if created_from:
            conditions.append("created_at >= ?")
            params.append(created_from)

        if created_to:
            conditions.append("created_at <= ?")
            params.append(created_to)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        sql = enriched_products_queries.SEARCH.format(where_clause=where_clause)
        params_paginated = params + [limit, offset]
        count_sql = enriched_products_queries.COUNT.format(where_clause=where_clause)

        with self._connection_factory() as conn:
            rows = conn.execute(sql, params_paginated).fetchall()
            total = conn.execute(count_sql, params).fetchone()["cnt"]

        return [EnrichedProduct(**dict(row)) for row in rows], int(total)
