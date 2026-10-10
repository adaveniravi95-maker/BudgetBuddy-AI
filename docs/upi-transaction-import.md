# UPI transaction CSV import

The authenticated endpoint `POST /api/transactions/import/` accepts a multipart
form upload in the `file` field. Use `?preview=true` to validate the CSV and
return a preview without saving transactions. The dashboard uses this preview
before the user confirms an import.

The CSV must be UTF-8 (a UTF-8 BOM is supported), no larger than 5 MB, and
contain no more than 10,000 transaction rows. Its header must identify these
columns:

| Field | Accepted header names |
| --- | --- |
| Date | `Date`, `Transaction Date`, `Txn Date`, `Value Date` |
| Description | `Description`, `Details`, `Transaction Details`, `Narration`, `Remarks`, `Particulars` |
| Amount | `Amount`, `Transaction Amount`, `Txn Amount` |
| Type | `Type`, `Transaction Type`, `Txn Type`, `Dr/Cr`, `Debit/Credit` |
| UPI Reference | `UPI Reference`, `UPI Ref`, `UPI Ref No`, `UPI Reference ID`, `UPI Reference Number`, `UPI Transaction ID`, `Reference Number`, `Reference No`, `Ref No`, `Transaction ID`, `Transaction Reference`, `Txn Reference`, `Txn ID`, `Bank Reference Number`, `UTR`, `RRN` |

Header matching ignores case, spaces, and punctuation. Dates in ISO
(`YYYY-MM-DD`), day-first (`DD/MM/YYYY`, `DD-MM-YYYY`), and US
(`MM/DD/YYYY`) formats are supported. Amounts may contain a rupee/INR marker
and grouping commas and must be positive with no more than two decimal places.
Type accepts Credit/Debit and the common CR/DR abbreviations. The UPI
Reference column is required, though an individual reference value may be
empty.

Credits are saved as income with source `Other`. Debits are categorized from
their description as Food, Travel, Shopping, Education, Entertainment, or
Miscellaneous (the fallback). Invalid rows reject the whole import; duplicate
transactions are skipped. A non-empty UPI reference is the primary
per-user duplicate key. Rows without a reference use transaction type, date,
amount, and description as their duplicate identity.
