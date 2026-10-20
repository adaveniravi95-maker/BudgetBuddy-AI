import { useState } from 'react';
import { createPortal } from 'react-dom';
import { AlertTriangle, Check, FileUp, X } from 'lucide-react';
import { transactionsAPI } from '../api/api';

const TYPE_OPTIONS = [
  ['expense', 'Expense'],
  ['income', 'Income'],
  ['transfer', 'Transfer'],
  ['refund', 'Refund'],
  ['needs_review', 'Needs Review'],
];

const TransactionCsvImport = ({ onImported }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [rows, setRows] = useState([]);
  const [errors, setErrors] = useState([]);
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const closeDialog = () => {
    if (isLoading) return;
    setIsOpen(false);
    setFile(null);
    setPreview(null);
    setRows([]);
    setErrors([]);
    setMessage(null);
    setIsComplete(false);
  };

  const loadPreview = async (selectedFile) => {
    if (!selectedFile) return;
    setIsLoading(true);
    setPreview(null);
    setRows([]);
    setErrors([]);
    setMessage(null);
    setIsComplete(false);
    try {
      const response = await transactionsAPI.importCsv(selectedFile, true);
      setPreview(response.data);
      setRows(response.data.transactions || []);
      setErrors(response.data.errors || []);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'The CSV could not be previewed. Check the file and try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const updateRow = (rowNumber, changes) => {
    setRows((current) => current.map((row) => (
      row.row === rowNumber ? { ...row, ...changes } : row
    )));
  };

  const handleTypeChange = (row, transactionType) => {
    updateRow(row.row, {
      transaction_type: transactionType,
      category: transactionType === 'expense' ? row.category || 'Uncategorized' : null,
      income_source: transactionType === 'income' ? row.income_source || 'Other' : null,
    });
  };

  const handleImport = async () => {
    if (!file || !preview || isComplete) return;
    setIsLoading(true);
    setMessage(null);
    try {
      const decisions = Object.fromEntries(rows.map((row) => [
        String(row.row),
        {
          transaction_type: row.transaction_type,
          category: row.category,
          income_source: row.income_source,
        },
      ]));
      const response = await transactionsAPI.importCsv(file, false, decisions);
      setErrors(response.data.errors || []);
      setMessage({
        type: response.data.failed_count ? 'error' : 'success',
        text: response.data.message,
      });
      setIsComplete(true);
      if (response.data.imported_count > 0) onImported();
    } catch (error) {
      setErrors(error.response?.data?.errors || []);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Transactions could not be imported. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const setSelectedFile = (event) => {
    const selectedFile = event.target.files?.[0] || null;
    setFile(selectedFile);
    setPreview(null);
    setRows([]);
    setErrors([]);
    setMessage(null);
    setIsComplete(false);
    if (selectedFile) loadPreview(selectedFile);
  };

  const canImport = rows.some((row) => !row.duplicate && row.status !== 'skipped');

  return (
    <>
      <button type="button" className="overview-import-button" onClick={() => setIsOpen(true)}>
        <FileUp size={14} /> Import UPI CSV
      </button>

      {isOpen && createPortal((
        <div className="modal-overlay" onMouseDown={(event) => {
          if (event.target === event.currentTarget) closeDialog();
        }}>
          <section
            className="modal-card transaction-import-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="transaction-import-title"
          >
            <header className="modal-header">
              <div>
                <h3 id="transaction-import-title">Review UPI transactions</h3>
                <p>Preview and confirm each transaction before it is added to your account.</p>
              </div>
              <button type="button" className="btn-close" aria-label="Close import dialog" onClick={closeDialog} disabled={isLoading}>
                <X size={18} />
              </button>
            </header>

            <div className="transaction-import-content">
              <label className="transaction-import-file">
                <span>Statement CSV (up to 5 MB)</span>
                <input type="file" accept=".csv,text/csv" onChange={setSelectedFile} disabled={isLoading} />
                {file && <small>{file.name}</small>}
              </label>

              {isLoading && <p className="transaction-import-guidance" role="status">Reading and validating your statement...</p>}
              {preview && (
                <p className="transaction-import-guidance">
                  Detected encoding: {preview.encoding}. Transfers, refunds, uncertain direction, and unclear purpose need review.
                </p>
              )}

              {message && (
                <div className={`alert alert-${message.type}`} role={message.type === 'error' ? 'alert' : 'status'}>
                  {message.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
                  <span>{message.text}</span>
                </div>
              )}

              {errors.length > 0 && (
                <div className="transaction-import-errors" role="alert">
                  <strong>{errors.length} row(s) need correction</strong>
                  <ul>
                    {errors.slice(0, 10).map((error) => (
                      <li key={`${error.row}-${error.message}`}>Row {error.row}: {error.message}</li>
                    ))}
                  </ul>
                  {errors.length > 10 && <small>And {errors.length - 10} more row errors.</small>}
                </div>
              )}

              {preview && (
                <div className="transaction-import-preview">
                  <div className="transaction-import-summary">
                    <strong>Statement preview</strong>
                    <span>{preview.importable_count} likely ready · {preview.needs_review_count} need review · {preview.duplicate_count} duplicate</span>
                  </div>
                  <div className="transaction-import-table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Description</th>
                          <th>Amount</th>
                          <th>Transaction type</th>
                          <th>Category / Source</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((row) => {
                          const rowLocked = row.duplicate || row.status === 'skipped' || isComplete;
                          return (
                            <tr key={row.row}>
                              <td>{row.date}</td>
                              <td title={row.description}>{row.description}</td>
                              <td>₹{Number(row.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                              <td>
                                <select
                                  aria-label={`Transaction type for row ${row.row}`}
                                  value={row.transaction_type}
                                  disabled={rowLocked || isLoading}
                                  onChange={(event) => handleTypeChange(row, event.target.value)}
                                >
                                  {TYPE_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                                </select>
                              </td>
                              <td>
                                {row.transaction_type === 'expense' ? (
                                  <select
                                    aria-label={`Expense category for row ${row.row}`}
                                    value={row.category || ''}
                                    disabled={rowLocked || isLoading}
                                    onChange={(event) => updateRow(row.row, { category: event.target.value })}
                                  >
                                    <option value="">Choose category</option>
                                    {(preview.category_choices || []).map((choice) => (
                                      <option key={choice.value} value={choice.value}>{choice.label}</option>
                                    ))}
                                  </select>
                                ) : row.transaction_type === 'income' ? (
                                  <select
                                    aria-label={`Income source for row ${row.row}`}
                                    value={row.income_source || ''}
                                    disabled={rowLocked || isLoading}
                                    onChange={(event) => updateRow(row.row, { income_source: event.target.value })}
                                  >
                                    <option value="">Choose source</option>
                                    {(preview.income_sources || []).map((source) => (
                                      <option key={source.value} value={source.value}>{source.label}</option>
                                    ))}
                                  </select>
                                ) : '—'}
                              </td>
                              <td>
                                {row.duplicate ? 'Duplicate' : row.status === 'skipped' ? 'Not completed' : row.transaction_type === 'needs_review' ? (
                                  <span title={row.review_message}>Needs Review</span>
                                ) : row.status === 'needs_review' ? 'Reviewed' : row.transaction_type === 'transfer' || row.transaction_type === 'refund' ? row.transaction_type : 'Ready'}
                                {row.review_message && !row.duplicate && <small className="transaction-import-row-note">{row.review_message}</small>}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                    {rows.length > 100 && <p className="transaction-import-note">Showing all {rows.length} rows.</p>}
                  </div>
                </div>
              )}

              <footer className="modal-actions">
                <button type="button" className="btn-secondary" onClick={closeDialog} disabled={isLoading}>
                  {isComplete ? 'Done' : 'Cancel'}
                </button>
                <button type="button" className="btn-primary" onClick={handleImport} disabled={!preview || !canImport || isLoading || isComplete}>
                  {isLoading ? 'Importing...' : 'Confirm and Import'}
                </button>
              </footer>
            </div>
          </section>
        </div>
      ), document.body)}
    </>
  );
};

export default TransactionCsvImport;
