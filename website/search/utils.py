import logging
from django.db import connection

logger = logging.getLogger(__name__)

def save_unsanitized_query(query: str):
    """Background function to log query into unsanitized_searches table."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE unsanitized_searches
                SET count = count + 1
                WHERE query = %s
                RETURNING id
                """,
                [query],
            )
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    """
                    INSERT INTO unsanitized_searches (query, count)
                    VALUES (%s, 1)
                    RETURNING id
                    """,
                    [query],
                )
                cursor.fetchone()
    except Exception as e:
        logger.exception("Failed to log unsanitized search: %s", e)
