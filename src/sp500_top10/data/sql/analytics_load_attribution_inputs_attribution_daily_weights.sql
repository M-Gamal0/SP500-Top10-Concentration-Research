SELECT
        date,
        ticker,
        rebalance_type,
        beginning_weight,
        ending_weight,
        total_return,
        total_return_contribution
    FROM backtest_daily_weights
    WHERE top_n = 10
      AND weighting_method = 'market_cap'
    ORDER BY date, ticker
