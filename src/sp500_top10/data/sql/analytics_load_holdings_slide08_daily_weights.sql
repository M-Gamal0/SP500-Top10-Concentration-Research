SELECT
        date,
        ticker,
        ending_weight
    FROM backtest_daily_weights
    WHERE top_n = 10
      AND weighting_method = 'market_cap'
      AND date IN (SELECT UNNEST(?)::TIMESTAMP)
    ORDER BY date, ending_weight DESC
