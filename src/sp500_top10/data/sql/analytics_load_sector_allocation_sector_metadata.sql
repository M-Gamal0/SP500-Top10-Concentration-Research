SELECT
        ticker,
        sector,
        lastupdated
    FROM tickers
    WHERE ticker IS NOT NULL
    ORDER BY ticker, lastupdated
