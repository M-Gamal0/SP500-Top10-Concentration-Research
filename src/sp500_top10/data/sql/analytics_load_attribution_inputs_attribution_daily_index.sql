SELECT
        date,
        rebalance_type,
        total_return
    FROM backtest_daily_index
    WHERE top_n = 10
      AND weighting_method = 'market_cap'
    ORDER BY date
