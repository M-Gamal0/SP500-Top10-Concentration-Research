SELECT
        date,
        weighting_method,
        total_index_value
    FROM backtest_daily_index
    WHERE top_n = 10
      AND weighting_method IN (
          'market_cap',
          'equal_weight',
          'buffered_20'
      )
    ORDER BY date, weighting_method
