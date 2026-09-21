SELECT
        ticker,
        arg_max(sector, lastupdated) AS sector
    FROM tickers
    WHERE ticker IS NOT NULL
    GROUP BY ticker
    ORDER BY ticker
