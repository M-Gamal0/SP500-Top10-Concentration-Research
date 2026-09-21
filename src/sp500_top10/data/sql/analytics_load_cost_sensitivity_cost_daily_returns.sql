SELECT
        date,
        weighting_method,
        total_return
    FROM backtest_daily_index
    WHERE top_n = 10
      AND weighting_method IN (
          'market_cap',
          'equal_weight',
          'buffered_20'
      )
    ORDER BY weighting_method, date
