INIT_DB = """
    CREATE TABLE IF NOT EXISTS enriched_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT,
        original_description TEXT,
        enriched_description TEXT,
        created_at TEXT
        )
    """

INSERT_ONE = """
    INSERT INTO enriched_products (item_id, original_description, enriched_description, created_at)
    VALUES (?, ?, ?, ?)
    """

LIST_ALL = """
    SELECT id, item_id, original_description, enriched_description, created_at
    FROM enriched_products
    """
    
GET_BY_ID = """
    SELECT id, item_id, original_description, enriched_description, created_at 
    FROM enriched_products 
    WHERE item_id=?
    """

SEARCH = """
    SELECT id, item_id, original_description, enriched_description, created_at
    FROM enriched_products
    {where_clause}
    ORDER BY created_at DESC
    LIMIT ? OFFSET ?
    """

COUNT = """
    SELECT COUNT(1) as cnt 
    FROM enriched_products {where_clause}
    """
