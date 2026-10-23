-- Filing documents with their text, available in a window (input of the LLM extractor).
-- param: start date
-- param: end date
SELECT accession_number, cik, symbol, document_name, document_type, url, sha256, text, char_count, available_at, fetched_at
FROM {{table:filing_text}}
WHERE available_at BETWEEN :start AND :end
ORDER BY available_at DESC
