-- Daily bars of several symbols between two dates (inclusive).
-- param: symbols symbols
-- param: start date
-- param: end date
SELECT pool, symbol, date, open, high, low, close, adj_close, volume
FROM {{table:price_bar}}
WHERE symbol IN :symbols AND date BETWEEN :start AND :end
ORDER BY symbol, date
