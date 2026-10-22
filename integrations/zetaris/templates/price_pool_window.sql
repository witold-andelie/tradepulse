-- Daily bars of one pool between two dates (inclusive).
-- param: pool pool
-- param: start date
-- param: end date
SELECT pool, symbol, date, open, high, low, close, adj_close, volume
FROM {{table:price_bar}}
WHERE pool = :pool AND date BETWEEN :start AND :end
ORDER BY symbol, date
