-- SEC filings of one symbol filed in a window.
-- param: symbol symbol
-- param: start date
-- param: end date
SELECT symbol, accession_number, form, items, filing_date, acceptance_datetime, primary_doc_url
FROM {{table:filing}}
WHERE symbol = :symbol AND filing_date BETWEEN :start AND :end
ORDER BY acceptance_datetime
