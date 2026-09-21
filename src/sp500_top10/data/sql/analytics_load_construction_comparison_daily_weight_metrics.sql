SELECT
        weighting_method,
        MAX(ending_weight) AS max_issuer_weight
    FROM backtest_daily_weights
    WHERE top_n = 10
      AND weighting_method IN (
          'market_cap',
          'equal_weight',
          'buffered_20'
      )
    GROUP BY weighting_method
