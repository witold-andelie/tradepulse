-- All reported values of one XBRL tag for every symbol, filed up to a date (point-in-time).
-- param: tag tag
-- param: end date
SELECT symbol, tag, unit, value, period_start, period_end, fiscal_year, fiscal_period, form, filed, accession_number
FROM {{table:fundamental_fact}}
WHERE tag = :tag AND filed <= :end
ORDER BY symbol, period_end, filed
