SELECT
        date,
        top_n,
        total_index_value
    FROM backtest_daily_index
    WHERE weighting_method = 'market_cap'
      AND top_n IN (10, 20)
    ORDER BY date, top_n
