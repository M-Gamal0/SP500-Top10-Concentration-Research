WITH ticker_history AS (
        SELECT
            ticker,
            MIN(date) AS first_date,
            MAX(date) AS last_date,
            COUNT(*) AS rows
        FROM stocks
        WHERE ticker IN (
            SELECT DISTINCT ticker
            FROM sp500
            WHERE action = 'historical'
        )
        GROUP BY ticker
    ),
    limits AS (
        SELECT
            MIN(first_date) AS min_first_date,
            MAX(last_date) AS max_last_date,
            MAX(rows) AS max_rows
        FROM ticker_history
    )
    SELECT
        ticker
    FROM ticker_history
    CROSS JOIN limits
    WHERE first_date = min_first_date
      AND last_date = max_last_date
      AND rows = max_rows
    ORDER BY ticker
