-- Daily Wikipedia pageviews of every member of one pool.
-- param: pool pool
-- param: start date
-- param: end date
SELECT pool, symbol, date, views, available_at
FROM {{table:pageview}}
WHERE pool = :pool AND date BETWEEN :start AND :end
ORDER BY symbol, date
