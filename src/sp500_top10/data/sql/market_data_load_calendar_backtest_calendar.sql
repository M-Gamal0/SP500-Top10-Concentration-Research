SELECT DISTINCT date
        FROM backtest_daily_index
        WHERE date BETWEEN ? AND ?
        ORDER BY date
