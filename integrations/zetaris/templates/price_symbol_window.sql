-- Daily bars of one symbol between two dates (inclusive).
-- param: symbol symbol
-- param: start date
-- param: end date
SELECT pool, symbol, date, open, high, low, close, adj_close, volume
FROM {{table:price_bar}}
WHERE symbol = :symbol AND date BETWEEN :start AND :end
ORDER BY date
