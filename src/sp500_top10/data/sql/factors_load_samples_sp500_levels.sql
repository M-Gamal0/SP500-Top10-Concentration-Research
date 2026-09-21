SELECT
        date,
        close
    FROM benchmark_daily
    WHERE ticker = '^SP500TR'
      AND benchmark_type = 'TR_index'
    ORDER BY date
