SELECT
        date,
        weighting_method,
        absolute_weight_change,
        turnover
    FROM backtest_turnover
    WHERE top_n = 10
      AND weighting_method IN (
          'market_cap',
          'equal_weight',
          'buffered_20'
      )
    ORDER BY date, weighting_method
