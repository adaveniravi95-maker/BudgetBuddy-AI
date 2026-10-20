import codecs
import csv
import hashlib
import io
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .models import Expense, ImportedTransactionIdentity, Income


MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 10000
TRANSACTION_TYPES = {'expense', 'income', 'transfer', 'refund', 'needs_review'}

HEADER_ALIASES = {
    'date': {
        'date', 'transactiondate', 'txndate', 'valuedate', 'timestamp',
        'transactiondatetime', 'datetime', 'initiatedat', 'createdat',
    },
    'description': {
        'description', 'details', 'transactiondetails', 'narration', 'remarks',
        'particulars', 'merchant', 'merchantname', 'payee', 'counterparty',
        'transactionnote', 'note',
    },
    'amount': {
        'amount', 'transactionamount', 'txnamount', 'amountinr', 'amountrs',
        'transactionvalue',
    },
    'type': {
        'type', 'transactiontype', 'txntype', 'drcr', 'debitcredit',
        'direction', 'transactiondirection', 'paymenttype',
    },
    'debit_amount': {
        'debit', 'debitamount', 'debitamt', 'withdrawal', 'withdrawals',
        'withdrawalamount', 'paidout',
    },
    'credit_amount': {
        'credit', 'creditamount', 'creditamt', 'deposit', 'deposits',
        'depositamount', 'paidin',
    },
    'upi_reference': {
        'upireference', 'upiref', 'upirefno', 'upireferencenumber',
        'upireferenceno', 'upireferenceid', 'upitransactionid',
        'upitransactionreference', 'referencenumber', 'referenceno',
        'refno', 'transactionid', 'transactionreference', 'txnreference',
        'txnid', 'bankreferencenumber', 'utr', 'rrn',
    },
    'status': {
        'status', 'transactionstatus', 'txnstatus', 'paymentstatus',
        'result',
    },
}

DATE_FORMATS = (
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M',
    '%d-%m-%Y %H:%M:%S',
    '%d-%m-%Y %H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%d/%m/%Y',
    '%d-%m-%Y',
    '%d/%m/%y',
    '%d-%m-%y',
    '%d %b %Y',
    '%d %B %Y',
    '%b %d, %Y',
    '%m/%d/%Y',
)

CATEGORY_KEYWORDS = {
    'Food': (
        'restaurant', 'food court', 'foodcourt', 'food', 'cafe', 'coffee',
        'canteen', 'dhaba', 'swiggy', 'zomato', 'grocery', 'groceries',
        'dining', 'bakery', 'pizza', 'dominos', 'mcdonalds', 'kfc',
    ),
    'Travel': (
        'uber', 'ola', 'rapido', 'taxi', 'cab', 'metro', 'bus', 'railway',
        'railways', 'train', 'flight', 'travel', 'fuel', 'petrol', 'diesel',
        'filling station', 'petrol pump', 'gas station', 'parking', 'toll',
    ),
    'Shopping': (
        'amazon', 'flipkart', 'shopping', 'myntra', 'ajio', 'meesho',
        'nykaa', 'retail',
    ),
    'Education': (
        'school', 'college', 'university', 'education', 'educational',
        'course', 'tuition', 'udemy', 'coursera', 'institute',
    ),
    'Entertainment': (
        'movie', 'cinema', 'netflix', 'spotify', 'hotstar', 'prime video',
        'entertainment', 'theatre', 'theater', 'bookmyshow',
    ),
}

INCOME_KEYWORDS = {
    'Salary': ('salary', 'payroll', 'wages'),
    'Scholarship': ('scholarship', 'stipend', 'grant'),
    'Pocket Money': ('pocket money', 'allowance', 'family support'),
    'Freelance Income': ('freelance', 'client payment', 'consulting'),
    'Part-time Job': ('part time job', 'part-time job', 'parttime job'),
}

SUCCESS_STATUSES = {
    'success', 'successful', 'completed', 'complete', 'paid', 'settled',
    'processed', 'done',
}
FAILED_STATUSES = {
    'failed', 'failure', 'declined', 'cancelled', 'canceled', 'rejected',
    'reversed', 'expired',
}
PENDING_STATUSES = {'pending', 'processing', 'initiated', 'waiting'}


def _normalise_text(value):
    text = unicodedata.normalize('NFKD', value or '').casefold()
    text = ''.join(character for character in text if not unicodedata.combining(character))
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def _normalise_header(value):
    return re.sub(r'[^a-z0-9]', '', (value or '').strip().casefold())


def _decode_csv(data):
    if data.startswith(codecs.BOM_UTF32_LE) or data.startswith(codecs.BOM_UTF32_BE):
        encoding = 'utf-32'
    elif data.startswith(codecs.BOM_UTF8):
        encoding = 'utf-8-sig'
    elif data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        encoding = 'utf-16'
    else:
        sample = data[:512]
        even_nulls = sum(sample[index] == 0 for index in range(0, len(sample), 2))
        odd_nulls = sum(sample[index] == 0 for index in range(1, len(sample), 2))
        pairs = max(1, len(sample) // 2)
        if odd_nulls / pairs > 0.25:
            encodings = ('utf-16-le',)
        elif even_nulls / pairs > 0.25:
            encodings = ('utf-16-be',)
        else:
            encodings = ('utf-8', 'cp1252', 'latin-1')
        for encoding in encodings:
            try:
                return data.decode(encoding), encoding
            except UnicodeDecodeError:
                continue
        raise ValueError('The CSV text encoding is not supported.')

    try:
        return data.decode(encoding), encoding
    except UnicodeDecodeError as exc:
        raise ValueError('The CSV text encoding is not supported or the file is corrupted.') from exc


def _parse_date(value):
    cleaned = (value or '').strip()
    if not cleaned:
        raise ValueError('Date cannot be blank.')
    iso_value = cleaned.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(iso_value).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(cleaned[:10])
    except ValueError:
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(cleaned, date_format).date()
            except ValueError:
                continue
    raise ValueError('Date must use a supported format such as YYYY-MM-DD or DD/MM/YYYY.')


def _parse_amount(value):
    cleaned = (value or '').strip().replace(',', '').replace('₹', '')
    cleaned = re.sub(r'^(INR|Rs\.?)\s*', '', cleaned, flags=re.IGNORECASE)
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = cleaned[1:-1]
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        raise ValueError('Amount must be a valid number.')
    if not amount.is_finite() or amount == 0:
        raise ValueError('Amount must be a non-zero valid amount.')
    amount = amount.copy_abs()
    if amount.as_tuple().exponent < -2 or amount > Decimal('99999999.99'):
        raise ValueError('Amount must have at most two decimal places and fit within the supported limit.')
    return amount.quantize(Decimal('0.01'))


def _parse_direction(value):
    token = _normalise_text(value)
    if token in {'credit', 'cr', 'credited', 'received', 'deposit', 'in', 'money in'}:
        return 'credit'
    if token in {
        'debit', 'dr', 'debited', 'paid', 'payment', 'sent', 'withdrawal',
        'out', 'money out',
    }:
        return 'debit'
    return None


def _guess_category(description):
    text = f' {_normalise_text(description)} '
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(f' {_normalise_text(keyword)} ' in text for keyword in keywords):
            return category
    return None


def _guess_income_source(description):
    text = f' {_normalise_text(description)} '
    for source, keywords in INCOME_KEYWORDS.items():
        if any(f' {_normalise_text(keyword)} ' in text for keyword in keywords):
            return source
    return 'Other'


def _classify(description, direction):
    text = f' {_normalise_text(description)} '
    if any(
        f' {_normalise_text(keyword)} ' in text
        for keyword in (
            'refund', 'refunded', 'reversal', 'reversed', 'chargeback',
            'cashback',
        )
    ):
        return 'refund', None, None
    if any(
        f' {_normalise_text(keyword)} ' in text
        for keyword in (
            'self transfer', 'own account', 'between own accounts',
            'transfer to self', 'account transfer', 'loan repayment',
            'loan emi', 'emi repayment',
        )
    ):
        return 'transfer', None, None
    if direction == 'debit':
        category = _guess_category(description)
        if category:
            return 'expense', category, None
        if any(f' {_normalise_text(word)} ' in text for word in ('transfer', 'sent to')):
            return 'transfer', None, None
        return 'needs_review', None, None
    if direction == 'credit':
        source = _guess_income_source(description)
        if source != 'Other':
            return 'income', None, source
        if any(f' {_normalise_text(word)} ' in text for word in ('transfer', 'received from')):
            return 'transfer', None, None
        return 'needs_review', None, None
    return 'needs_review', None, None


def _parse_amount_and_direction(row, columns):
    raw_type = (row.get(columns['type']) or '').strip() if 'type' in columns else ''
    direction = _parse_direction(raw_type)

    if 'amount' in columns:
        raw_amount = (row.get(columns['amount']) or '').strip()
        amount = _parse_amount(raw_amount)
        if not direction:
            try:
                signed = Decimal(
                    re.sub(r'^(INR|Rs\.?)\s*', '', raw_amount.replace(',', '').replace('₹', ''), flags=re.IGNORECASE)
                    .strip()
                    .strip('()')
                )
            except (InvalidOperation, ValueError):
                signed = Decimal('0')
            if signed < 0:
                direction = 'debit'
        return amount, direction

    populated = []
    for field, field_direction in (('debit_amount', 'debit'), ('credit_amount', 'credit')):
        column = columns.get(field)
        if not column:
            continue
        raw_value = (row.get(column) or '').strip()
        if not raw_value:
            continue
        zero_candidate = raw_value.replace(',', '').replace('₹', '')
        zero_candidate = re.sub(r'^(INR|Rs\.?)\s*', '', zero_candidate, flags=re.IGNORECASE)
        try:
            if Decimal(zero_candidate.strip().strip('()')) == 0:
                continue
        except (InvalidOperation, ValueError):
            pass
        populated.append((field_direction, raw_value))

    if len(populated) != 1:
        raise ValueError('Provide an amount in exactly one of the Debit or Credit columns.')
    detected_direction, raw_amount = populated[0]
    if direction and direction != detected_direction:
        raise ValueError('Type conflicts with the populated Debit or Credit amount column.')
    return _parse_amount(raw_amount), detected_direction


def _transaction_identity(transaction):
    reference = transaction['upi_reference']
    if reference:
        normalised_reference = unicodedata.normalize('NFKC', reference).casefold().strip()
        raw_identity = f"reference:{normalised_reference}"
    else:
        raw_identity = 'row:{}:{}:{}:{}'.format(
            transaction['direction'],
            transaction['date'].isoformat(),
            transaction['amount'],
            _normalise_text(transaction['description']),
        )
    return hashlib.sha256(raw_identity.encode('utf-8')).hexdigest()


def parse_upi_csv(uploaded_file):
    if not uploaded_file.name.lower().endswith('.csv'):
        raise ValueError('Choose a CSV file with a .csv extension.')
    if uploaded_file.size == 0:
        raise ValueError('The CSV file is empty.')
    if uploaded_file.size > MAX_CSV_BYTES:
        raise ValueError('CSV file must be 5 MB or smaller.')
    text, encoding = _decode_csv(uploaded_file.read())

    try:
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=',;\t|')
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(text, newline=''), dialect=dialect, strict=True)
        if not reader.fieldnames:
            raise ValueError('CSV must include a header row.')
        columns = {}
        for original_header in reader.fieldnames:
            normalised = _normalise_header(original_header)
            for field, aliases in HEADER_ALIASES.items():
                if normalised in aliases:
                    columns[field] = original_header
                    break
        missing = [
            label for field, label in (
                ('date', 'Date'),
                ('description', 'Description or merchant'),
            ) if field not in columns
        ]
        if 'amount' not in columns and not (
            'debit_amount' in columns or 'credit_amount' in columns
        ):
            missing.append('Amount or Debit/Credit amount')
        if 'type' not in columns and 'amount' in columns and not (
            'debit_amount' in columns or 'credit_amount' in columns
        ):
            missing.append('Debit/Credit Type')
        if missing:
            raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}.")

        transactions = []
        errors = []
        row_count = 0
        for row_number, row in enumerate(reader, start=2):
            if not row or not any(
                value.strip() if isinstance(value, str) else bool(value)
                for value in row.values()
                if value is not None
            ):
                continue
            row_count += 1
            if row_count > MAX_CSV_ROWS:
                raise ValueError(f'CSV cannot contain more than {MAX_CSV_ROWS} transactions.')
            try:
                if row.get(None):
                    raise ValueError('Row contains more values than the CSV header.')
                date_value = row.get(columns['date']) or ''
                description = (row.get(columns['description']) or '').strip()
                if not description:
                    raise ValueError('Description cannot be blank.')
                if len(description) > 255:
                    raise ValueError('Description cannot exceed 255 characters.')
                reference = (row.get(columns.get('upi_reference')) or '').strip()
                if len(reference) > 150:
                    raise ValueError('Transaction reference cannot exceed 150 characters.')
                amount, direction = _parse_amount_and_direction(row, columns)
                transaction_date = _parse_date(date_value)
                raw_status = (row.get(columns.get('status')) or '').strip()
                normalised_status = _normalise_text(raw_status)
                status_words = set(normalised_status.split())
                failed_status = bool(status_words.intersection(FAILED_STATUSES))
                pending_status = bool(status_words.intersection(PENDING_STATUSES))
                successful_status = bool(status_words.intersection(SUCCESS_STATUSES))
                if failed_status or pending_status:
                    transaction_type, category, income_source = 'needs_review', None, None
                    review_message = f'Transaction status is {raw_status or "not complete"}.'
                    transaction_status = 'skipped'
                else:
                    transaction_type, category, income_source = _classify(description, direction)
                    review_message = ''
                    transaction_status = 'ready'
                    if raw_status and not successful_status:
                        transaction_type, category, income_source = 'needs_review', None, None
                        review_message = f'Transaction status "{raw_status}" needs verification.'
                        transaction_status = 'needs_review'
                    elif transaction_type in {'needs_review', 'transfer', 'refund'}:
                        review_message = {
                            'needs_review': 'Purpose or direction is unclear.',
                            'transfer': 'Possible transfer; excluded from income and expenses.',
                            'refund': 'Possible refund; excluded from income and expenses.',
                        }[transaction_type]
                        transaction_status = 'needs_review'
                transaction = {
                    'row': row_number,
                    'date': transaction_date,
                    'description': description,
                    'amount': amount,
                    'direction': direction,
                    'transaction_type': transaction_type,
                    'category': category,
                    'income_source': income_source,
                    'upi_reference': reference,
                    'transaction_status': transaction_status,
                    'status_text': raw_status,
                    'review_message': review_message,
                    'identity_key': '',
                }
                transaction['identity_key'] = _transaction_identity(transaction)
                transactions.append(transaction)
            except ValueError as exc:
                errors.append({'row': row_number, 'message': str(exc)})
        if not transactions and not errors:
            raise ValueError('CSV contains no transaction rows.')
    except csv.Error as exc:
        raise ValueError(f'Could not parse CSV: {exc}') from exc
    return transactions, errors, encoding


def mark_duplicate_transactions(user, transactions):
    identity_keys = [item['identity_key'] for item in transactions]
    existing_keys = set(
        ImportedTransactionIdentity.objects.filter(
            user=user,
            identity_key__in=identity_keys,
        ).values_list('identity_key', flat=True)
    )
    known_references = set()
    known_fingerprints = set()
    for model, direction in ((Expense, 'debit'), (Income, 'credit')):
        for date_value, amount, description, reference in model.objects.filter(
            user=user
        ).values_list('date', 'amount', 'description', 'upi_reference'):
            if reference:
                known_references.add(reference.casefold())
            else:
                known_fingerprints.add((
                    direction,
                    date_value.isoformat(),
                    str(amount),
                    _normalise_text(description),
                ))

    seen = set()
    for item in transactions:
        key = item['identity_key']
        reference = item['upi_reference'].casefold()
        fingerprint = (
            item['direction'],
            item['date'].isoformat(),
            str(item['amount']),
            _normalise_text(item['description']),
        )
        fingerprints = [fingerprint]
        if item['direction'] is None:
            fingerprints = [
                (direction, *fingerprint[1:])
                for direction in ('debit', 'credit')
            ]
        item['duplicate'] = (
            key in existing_keys
            or key in seen
            or (reference and reference in known_references)
            or any(candidate in known_fingerprints for candidate in fingerprints)
        )
        seen.add(key)


def serialize_preview(transactions):
    result = []
    for item in transactions:
        transaction_status = 'duplicate' if item.get('duplicate') else item['transaction_status']
        result.append({
            'row': item['row'],
            'date': item['date'].isoformat(),
            'description': item['description'],
            'amount': f"{item['amount']:.2f}",
            'direction': item['direction'],
            'transaction_type': item['transaction_type'],
            'category': item['category'],
            'income_source': item['income_source'],
            'upi_reference': item['upi_reference'],
            'status': transaction_status,
            'status_text': item['status_text'],
            'review_message': item['review_message'],
            'duplicate': bool(item.get('duplicate')),
        })
    return result
