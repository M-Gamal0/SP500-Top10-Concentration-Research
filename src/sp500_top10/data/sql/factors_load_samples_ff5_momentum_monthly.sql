SELECT
        month_end,
        mkt_rf AS ff5_mkt_rf,
        smb AS ff5_smb,
        hml AS ff5_hml,
        rmw,
        cma,
        mom,
        rf AS ff5_rf
    FROM fama_french_5_momentum_monthly
    ORDER BY month_end
