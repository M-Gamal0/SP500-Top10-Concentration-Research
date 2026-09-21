SELECT
        selection_date,
        ticker,
        name,
        rank,
        target_weight
    FROM quarterly_index_weights
    WHERE top_n = 10
      AND weighting_method = 'market_cap'
    ORDER BY selection_date, rank
