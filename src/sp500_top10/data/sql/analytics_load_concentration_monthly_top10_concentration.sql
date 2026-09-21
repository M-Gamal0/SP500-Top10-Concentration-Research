WITH month_ends AS (
        SELECT
            MAX(date) AS observation_date
        FROM daily
        WHERE date >= ?
        GROUP BY
            YEAR(date),
            MONTH(date)
    ),

    latest_universe_date AS (
        SELECT
            m.observation_date,
            MAX(s.date) AS universe_date
        FROM month_ends m
        INNER JOIN sp500 s
            ON s.action = 'historical'
           AND s.date <= m.observation_date
        GROUP BY m.observation_date
    ),

    monthly_universe AS (
        SELECT
            u.observation_date,
            u.universe_date,
            s.ticker,
            s.name
        FROM latest_universe_date u
        INNER JOIN sp500 s
            ON s.date = u.universe_date
           AND s.action = 'historical'
    ),

    monthly_market_caps AS (
        SELECT
            u.observation_date,
            u.universe_date,
            u.ticker,
            u.name,
            d.date AS marketcap_date,
            d.marketcap AS resolved_marketcap

        FROM monthly_universe u

        ASOF LEFT JOIN (
            SELECT
                ticker,
                date,
                marketcap
            FROM daily
            WHERE marketcap IS NOT NULL
        ) d
            ON u.ticker = d.ticker
           AND u.observation_date >= d.date
    ),

    ranked AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY observation_date
                ORDER BY resolved_marketcap DESC NULLS LAST
            ) AS marketcap_rank
        FROM monthly_market_caps
    )

    SELECT
        observation_date,
        universe_date,

        COUNT(*) AS sp500_company_count,

        COUNT(*) FILTER (
            WHERE resolved_marketcap IS NOT NULL
        ) AS companies_with_market_cap,

        SUM(resolved_marketcap) AS sp500_total_market_cap,

        SUM(
            CASE
                WHEN marketcap_rank <= 10
                THEN resolved_marketcap
                ELSE 0
            END
        ) AS top10_total_market_cap,

        SUM(
            CASE
                WHEN marketcap_rank <= 10
                THEN resolved_marketcap
                ELSE 0
            END
        ) / SUM(resolved_marketcap) AS top10_market_cap_share

    FROM ranked

    GROUP BY
        observation_date,
        universe_date

    ORDER BY observation_date
