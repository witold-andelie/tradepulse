-- All members of one pool.
-- param: pool pool
SELECT pool, symbol, name, sector, country, currency, cik, wikipedia_title, index_membership
FROM {{table:universe_member}}
WHERE pool = :pool
ORDER BY symbol
