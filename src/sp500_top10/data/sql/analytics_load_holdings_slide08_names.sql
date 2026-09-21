WITH snapshot_dates AS (
        SELECT UNNEST(?)::TIMESTAMP AS date
    ),

    applicable_selection AS (
        SELECT
            s.date,
            MAX(q.selection_date) AS selection_date
        FROM snapshot_dates s
        JOIN quarterly_index_weights q
            ON q.selection_date <= s.date
           AND q.top_n = 10
           AND q.weighting_method = 'market_cap'
        GROUP BY s.date
    )

    SELECT DISTINCT
        a.date,
        q.ticker,
        q.name
    FROM applicable_selection a
    JOIN quarterly_index_weights q
        ON q.selection_date = a.selection_date
       AND q.top_n = 10
       AND q.weighting_method = 'market_cap'
