SELECT
        date,
        COUNT(DISTINCT ticker) AS ticker_count
    FROM stocks
    WHERE ticker IN (
        SELECT UNNEST(?)
    )
    GROUP BY date
    ORDER BY date
