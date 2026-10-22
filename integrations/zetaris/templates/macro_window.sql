-- One macro series between two dates.
-- param: series series
-- param: start date
-- param: end date
SELECT series_id, date, value, available_at
FROM {{table:macro_point}}
WHERE series_id = :series AND date BETWEEN :start AND :end
ORDER BY date
