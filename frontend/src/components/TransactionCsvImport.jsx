import { useState } from 'react';
import { createPortal } from 'react-dom';
import { AlertTriangle, Check, FileUp, X } from 'lucide-react';
import { transactionsAPI } from '../api/api';

const TransactionCsvImport = ({ onImported }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [errors, setErrors] = useState([]);
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [action, setAction] = useState(null);

  const resetAndClose = () => {
    setIsOpen(false);
    setFile(null);
    setPreview(null);
    setErrors([]);
    setMessage(null);
    setIsComplete(false);
    setAction(null);
  };

  const loadPreview = async (selectedFile) => {
    if (!selectedFile) return;
    setIsLoading(true);
    setAction('preview');
    setPreview(null);
    setErrors([]);
    setMessage(null);
    setIsComplete(false);
    try {
      const response = await transactionsAPI.importCsv(selectedFile, true);
      setPreview(response.data);
      setErrors(response.data.errors || []);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'The CSV could not be previewed. Please check the file and try again.',
      });
    } finally {
      setIsLoading(false);
      setAction(null);
    }
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;
    setFile(selectedFile);
    if (selectedFile) {
      loadPreview(selectedFile);
    } else {
      setPreview(null);
      setErrors([]);
      setMessage(null);
      setIsComplete(false);
    }
  };

  const handlePreview = async () => {
    if (!file) {
      setMessage({ type: 'error', text: 'Choose a CSV file to preview.' });
      return;
    }
    await loadPreview(file);
  };

  const handleImport = async () => {
    if (!file || !preview || errors.length || isComplete) return;
    setIsLoading(true);
    setAction('import');
    setMessage(null);
    try {
      const response = await transactionsAPI.importCsv(file);
      const { imported_count: importedCount, duplicate_count: duplicateCount } = response.data;
      setMessage({
        type: 'success',
        text: `Imported ${importedCount} transaction${importedCount === 1 ? '' : 's'}; skipped ${duplicateCount} duplicate${duplicateCount === 1 ? '' : 's'}.`,
      });
      setIsComplete(true);
      onImported();
    } catch (error) {
      const responseErrors = error.response?.data?.errors || [];
      setErrors(responseErrors);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Transactions could not be imported. Please try again.',
      });
    } finally {
      setIsLoading(false);
      setAction(null);
    }
  };

  const previewRows = preview?.transactions || [];

  return (
    <>
      <button
        type="button"
        className="overview-import-button"
        onClick={() => setIsOpen(true)}
      >
        <FileUp size={14} /> Import Transactions
      </button>

      {isOpen && createPortal((
        <div className="modal-overlay" onMouseDown={(event) => {
          if (event.target === event.currentTarget && !isLoading) resetAndClose();
        }}>
          <section
            className="modal-card transaction-import-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="transaction-import-title"
          >
            <header className="modal-header">
              <div>
                <h3 id="transaction-import-title">Import UPI Transactions</h3>
                <p>Upload a CSV with Date, Description, Amount, Type, and UPI Reference columns.</p>
              </div>
              <button
                type="button"
                className="btn-close"
                aria-label="Close import dialog"
                onClick={resetAndClose}
                disabled={isLoading}
              >
                <X size={18} />
              </button>
            </header>

            <div className="transaction-import-content">
              <label className="transaction-import-file">
                <span>CSV file</span>
                <input
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleFileChange}
                  disabled={isLoading}
                />
                {file && <small>{file.name}</small>}
              </label>

              <p className="transaction-import-guidance" role="status">
                {action === 'preview'
                  ? 'Checking your CSV and preparing the preview...'
                  : preview
                    ? 'Review the preview below, then select Import Transactions to save these records.'
                    : 'Choose a CSV file to validate it and prepare the transaction preview.'}
              </p>

              {message && (
                <div className={`alert alert-${message.type}`} role={message.type === 'error' ? 'alert' : 'status'}>
                  {message.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
                  <span>{message.text}</span>
                </div>
              )}

              {errors.length > 0 && (
                <div className="transaction-import-errors" role="alert">
                  <strong>{errors.length} invalid row{errors.length === 1 ? '' : 's'}</strong>
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
                    <strong>CSV preview</strong>
                    <span>{preview.importable_count} ready · {preview.duplicate_count} duplicate{preview.duplicate_count === 1 ? '' : 's'}</span>
                  </div>
                  <div className="transaction-import-table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Description</th>
                          <th>Amount</th>
                          <th>Type / Category</th>
                          <th>UPI Reference</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {previewRows.slice(0, 100).map((row) => (
                          <tr key={`${row.row}-${row.upi_reference}`}>
                            <td>{row.date}</td>
                            <td>{row.description}</td>
                            <td>₹{Number(row.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                            <td>{row.type === 'credit' ? 'Income' : row.category}</td>
                            <td>{row.upi_reference || '—'}</td>
                            <td>{row.duplicate ? 'Duplicate' : 'Ready'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {previewRows.length > 100 && (
                      <p className="transaction-import-note">Showing the first 100 of {previewRows.length} rows.</p>
                    )}
                  </div>
                </div>
              )}

              <footer className="modal-actions">
                <button type="button" className="btn-secondary" onClick={resetAndClose} disabled={isLoading}>
                  {isComplete ? 'Done' : 'Cancel'}
                </button>
                <button type="button" className="btn-secondary" onClick={handlePreview} disabled={!file || isLoading}>
                  {action === 'preview' ? 'Preparing preview...' : 'Preview CSV'}
                </button>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleImport}
                  disabled={!preview || errors.length > 0 || isLoading || isComplete || preview.importable_count === 0}
                >
                  {action === 'import'
                    ? 'Importing...'
                    : preview?.importable_count === 0
                      ? 'No New Transactions'
                      : 'Import Transactions'}
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
