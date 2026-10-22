-- Filing documents of one symbol available in a window (metadata only, no text).
-- param: symbol symbol
-- param: start date
-- param: end date
SELECT symbol, accession_number, document_name, document_type, url, sha256, char_count, available_at
FROM {{table:filing_text}}
WHERE symbol = :symbol AND available_at BETWEEN :start AND :end
ORDER BY available_at
