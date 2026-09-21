SELECT
        top_n,
        MAX(ending_weight) AS max_issuer_weight
    FROM backtest_daily_weights
    WHERE weighting_method = 'market_cap'
      AND top_n IN (10, 20)
    GROUP BY top_n
    ORDER BY top_n
