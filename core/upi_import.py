import csv
import hashlib
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .models import Expense, ImportedTransactionIdentity, Income


MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 10000

HEADER_ALIASES = {
    'date': {'date', 'transactiondate', 'txndate', 'valuedate'},
    'description': {
        'description', 'details', 'transactiondetails', 'narration', 'remarks',
        'particulars',
    },
    'amount': {'amount', 'transactionamount', 'txnamount'},
    'type': {'type', 'transactiontype', 'txntype', 'drcr', 'debitcredit'},
    'upi_reference': {
        'upireference', 'upiref', 'upirefno', 'upireferencenumber',
        'upireferenceno', 'upireferenceid', 'upitransactionid',
        'upitransactionreference', 'referencenumber', 'referenceno',
        'refno', 'transactionid', 'transactionreference', 'txnreference',
        'txnid', 'bankreferencenumber', 'utr', 'rrn',
    },
}

CATEGORY_KEYWORDS = {
    'Food': (
        'restaurant', 'food', 'cafe', 'coffee', 'swiggy', 'zomato',
        'grocery', 'groceries', 'dining', 'bakery', 'pizza',
    ),
    'Travel': (
        'uber', 'ola', 'rapido', 'taxi', 'cab', 'metro', 'bus', 'train',
        'flight', 'travel', 'fuel', 'petrol', 'parking', 'toll',
    ),
    'Shopping': (
        'amazon', 'flipkart', 'shopping', 'mall', 'store', 'retail',
        'myntra', 'ajio', 'bigbasket',
    ),
    'Education': (
        'school', 'college', 'university', 'education', 'course', 'tuition',
        'books', 'udemy', 'coursera',
    ),
    'Entertainment': (
        'movie', 'cinema', 'netflix', 'spotify', 'hotstar', 'prime video',
        'entertainment', 'game', 'theatre',
    ),
}

DATE_FORMATS = (
    '%d/%m/%Y',
    '%d-%m-%Y',
    '%d/%m/%y',
    '%d-%m-%y',
    '%d %b %Y',
    '%d %B %Y',
    '%m/%d/%Y',
)


def _normalise_header(value):
    return re.sub(r'[^a-z0-9]', '', (value or '').strip().lower())


def _parse_date(value):
    value = (value or '').strip()
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
    raise ValueError('Date must use a supported date format such as YYYY-MM-DD or DD/MM/YYYY.')


def _parse_amount(value):
    cleaned = (value or '').strip().replace(',', '').replace('₹', '')
    cleaned = re.sub(r'^(INR|Rs\.?)\s*', '', cleaned, flags=re.IGNORECASE)
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = cleaned[1:-1]
    try:
        amount = Decimal(cleaned).copy_abs()
    except (InvalidOperation, ValueError):
        raise ValueError('Amount must be a valid number.')
    if not amount.is_finite() or amount <= 0:
        raise ValueError('Amount must be greater than zero.')
    if amount.as_tuple().exponent < -2 or amount > Decimal('99999999.99'):
        raise ValueError('Amount must have at most two decimal places and fit within the supported limit.')
    return amount.quantize(Decimal('0.01'))


def _parse_type(value):
    transaction_type = (value or '').strip().lower()
    if transaction_type in {'credit', 'cr', 'credited'}:
        return 'credit'
    if transaction_type in {'debit', 'dr', 'debited'}:
        return 'debit'
    raise ValueError('Type must be Credit or Debit.')


def _guess_category(description):
    text = (description or '').lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(
            re.search(r'(?<![a-z0-9])' + re.escape(keyword) + r'(?![a-z0-9])', text)
            for keyword in keywords
        ):
            return category
    return 'Miscellaneous'


def _identity_key(transaction):
    reference = transaction['upi_reference'].strip().casefold()
    if reference:
        identity = f"reference:{reference}"
    else:
        identity = 'row:{}:{}:{}:{}'.format(
            transaction['type'],
            transaction['date'].isoformat(),
            transaction['amount'],
            transaction['description'].strip().casefold(),
        )
    return hashlib.sha256(identity.encode('utf-8')).hexdigest()


def parse_upi_csv(uploaded_file):
    if uploaded_file.size > MAX_CSV_BYTES:
        raise ValueError('CSV file must be 5 MB or smaller.')

    try:
        text = uploaded_file.read().decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('CSV must be encoded as UTF-8.') from exc

    try:
        reader = csv.DictReader(io.StringIO(text), strict=True)
        if not reader.fieldnames:
            raise ValueError('CSV must include a header row.')

        columns = {}
        for original_header in reader.fieldnames:
            normalised = _normalise_header(original_header)
            for field, aliases in HEADER_ALIASES.items():
                if normalised in aliases:
                    columns[field] = original_header
                    break

        missing = [field.replace('_', ' ').title() for field in HEADER_ALIASES if field not in columns]
        if missing:
            raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}.")

        transactions = []
        errors = []
        row_count = 0
        for row_number, row in enumerate(reader, start=2):
            if not row or not any((value or '').strip() for value in row.values() if value is not None):
                continue
            row_count += 1
            if row_count > MAX_CSV_ROWS:
                raise ValueError(f'CSV cannot contain more than {MAX_CSV_ROWS} transactions.')
            try:
                description = (row.get(columns['description']) or '').strip()
                if not description:
                    raise ValueError('Description cannot be blank.')
                if len(description) > 255:
                    raise ValueError('Description cannot exceed 255 characters.')
                upi_reference = (row.get(columns['upi_reference']) or '').strip()
                if len(upi_reference) > 150:
                    raise ValueError('UPI Reference cannot exceed 150 characters.')

                transaction_type = _parse_type(row.get(columns['type']))
                parsed = {
                    'row': row_number,
                    'date': _parse_date(row.get(columns['date'])),
                    'description': description,
                    'amount': _parse_amount(row.get(columns['amount'])),
                    'type': transaction_type,
                    'upi_reference': upi_reference,
                }
                parsed['category'] = _guess_category(description) if transaction_type == 'debit' else None
                parsed['identity_key'] = _identity_key(parsed)
                transactions.append(parsed)
            except ValueError as exc:
                errors.append({'row': row_number, 'message': str(exc)})

        if not transactions and not errors:
            raise ValueError('CSV contains no transaction rows.')

    except csv.Error as exc:
        raise ValueError(f'Could not parse CSV: {exc}') from exc

    return transactions, errors


def mark_duplicate_transactions(user, transactions):
    keys = [transaction['identity_key'] for transaction in transactions]
    existing_keys = set(
        ImportedTransactionIdentity.objects.filter(
            user=user,
            identity_key__in=keys,
        ).values_list('identity_key', flat=True)
    )
    seen_keys = set()
    for transaction in transactions:
        key = transaction['identity_key']
        transaction['duplicate'] = key in existing_keys or key in seen_keys
        seen_keys.add(key)

        if transaction['duplicate']:
            continue

        if transaction['upi_reference']:
            duplicate = (
                Income.objects.filter(
                    user=user,
                    upi_reference__iexact=transaction['upi_reference'],
                ).exists()
                or Expense.objects.filter(
                    user=user,
                    upi_reference__iexact=transaction['upi_reference'],
                ).exists()
            )
            if not duplicate and transaction['type'] == 'credit':
                duplicate = Income.objects.filter(
                    user=user,
                    date=transaction['date'],
                    amount=transaction['amount'],
                    description=transaction['description'],
                    upi_reference='',
                ).exists()
            elif not duplicate:
                duplicate = Expense.objects.filter(
                    user=user,
                    date=transaction['date'],
                    amount=transaction['amount'],
                    description=transaction['description'],
                    upi_reference='',
                ).exists()
        elif transaction['type'] == 'credit':
            duplicate = Income.objects.filter(
                user=user,
                date=transaction['date'],
                amount=transaction['amount'],
                description=transaction['description'],
            ).exists()
        else:
            duplicate = Expense.objects.filter(
                user=user,
                date=transaction['date'],
                amount=transaction['amount'],
                description=transaction['description'],
            ).exists()
        transaction['duplicate'] = duplicate


def serialize_preview(transactions):
    return [
        {
            'row': transaction['row'],
            'date': transaction['date'].isoformat(),
            'description': transaction['description'],
            'amount': f"{transaction['amount']:.2f}",
            'type': transaction['type'],
            'upi_reference': transaction['upi_reference'],
            'category': transaction['category'],
            'duplicate': transaction['duplicate'],
        }
        for transaction in transactions
    ]
