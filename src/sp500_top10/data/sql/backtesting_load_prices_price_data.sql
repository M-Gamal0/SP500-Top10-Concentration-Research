SELECT
        date,
        ticker,
        close,
        closeadj
    FROM stocks
    WHERE ticker IN (
        SELECT UNNEST(?)
    )
      AND date >= ?
      AND date <= ?
    ORDER BY
        ticker,
        date
