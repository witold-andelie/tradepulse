-- Daily Wikipedia pageviews of one symbol.
-- param: symbol symbol
-- param: start date
-- param: end date
SELECT pool, symbol, date, views, available_at
FROM {{table:pageview}}
WHERE symbol = :symbol AND date BETWEEN :start AND :end
ORDER BY date
