-- All reported values of one XBRL tag for one symbol, filed up to a date (point-in-time).
-- param: symbol symbol
-- param: tag tag
-- param: end date
SELECT symbol, tag, unit, value, period_start, period_end, fiscal_year, fiscal_period, form, filed, accession_number
FROM {{table:fundamental_fact}}
WHERE symbol = :symbol AND tag = :tag AND filed <= :end
ORDER BY period_end, filed
