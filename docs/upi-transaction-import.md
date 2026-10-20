# UPI transaction CSV import

The authenticated dashboard importer previews a CSV before saving. It supports
comma-, semicolon-, tab-, and pipe-delimited statements and recognizes common
header aliases for transaction date, description/merchant, amount, direction,
reference, and status. Unrecognized or incomplete headers are rejected with a
description of the missing fields.

The parser detects UTF-8 (with or without BOM), UTF-16 LE/BE (with BOM or
recognizable byte order), UTF-32 BOM files, and falls back to Windows-1252 and
Latin-1 for legacy exports. Files are limited to 5 MB and 10,000 rows and must
have a `.csv` extension. Date/time values are stored using their calendar date;
timezone conversion is not applied.

Direction is taken from a Debit/Credit/DR/CR column, an explicit sign on a
signed amount, or exactly one populated debit/credit amount column. A positive,
unsigned amount with no direction is held for review instead of being guessed.
Rows with failed/cancelled/rejected statuses are never imported. Other unknown
statuses and unclear descriptions are shown as needing review.

Known merchants are categorized with local rules in `core/upi_import.py`.
Unknown expenses have no suggested category and require a user selection before
save (the existing `Uncategorized` category is available). Salary and
scholarship descriptions are suggested as income sources, but unclear credits,
refunds, and suspected own-account transfers are not counted as income. Users
can select Expense/Income and a corresponding category/source before saving.
Transfers, refunds, and unresolved rows are skipped unless the user explicitly
changes the classification in the preview.

Rows are saved to the existing per-user `Expense` and `Income` models. A
per-user unique identity uses the statement reference when present and a
direction/date/amount/normalized-description fingerprint otherwise, making
retries idempotent. Valid rows can be imported while invalid rows are returned
as failures. Other UPI provider layouts may need additional header aliases or
date formats; no provider format is claimed as supported until validated with
an actual statement.

## Try it locally

Create a UTF-8 `sample-upi.csv`:

```csv
Date,Description,Amount,Type,UPI Reference,Status
2026-10-01,Paid to LAALUS CAFE AND FOOD COURT,245.00,Debit,sample-food-1,Completed
2026-10-02,Monthly Salary,12000.00,Credit,sample-salary-1,Success
2026-10-03,Paid to unknown merchant,50.00,Debit,sample-review-1,Completed
```

Open the Dashboard, select **Import UPI CSV**, review/edit the suggested types
and categories, then choose **Confirm and Import**. The first row is suggested
as Food; the salary credit is suggested as Salary income; the unknown merchant
requires review. Re-uploading the file reports the saved rows as duplicates.
