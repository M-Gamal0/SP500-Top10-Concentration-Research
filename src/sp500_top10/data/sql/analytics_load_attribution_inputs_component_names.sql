SELECT
        ticker,
        arg_max(name, selection_date) AS company
    FROM quarterly_index_weights
    WHERE top_n = 10
      AND weighting_method = 'market_cap'
    GROUP BY ticker
    ORDER BY ticker
