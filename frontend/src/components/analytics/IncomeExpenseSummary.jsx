import { ArrowDownRight, ArrowUpRight } from 'lucide-react';

const IncomeExpenseSummary = ({ overview, loading, error }) => {
  if (loading && !overview) {
    return <section className="analytics-panel analytics-state" role="status">Loading income and expense totals...</section>;
  }

  if (error && !overview) {
    return <section className="analytics-panel analytics-state" role="alert">Income and expense totals are unavailable.</section>;
  }

  const totalIncome = Number(overview?.total_income || 0);
  const totalExpenses = Number(overview?.total_expenses || 0);

  return (
    <section className="analytics-summary-cards" aria-label="Income and expense summary">
      <article className="analytics-metric-card income-metric">
        <div className="analytics-metric-icon"><ArrowUpRight size={19} /></div>
        <span>Total Income</span>
        <strong>{overview ? `₹${totalIncome.toFixed(2)}` : '—'}</strong>
        <small>{overview?.income_count ?? 0} records in selected period</small>
      </article>
      <article className="analytics-metric-card expense-metric">
        <div className="analytics-metric-icon"><ArrowDownRight size={19} /></div>
        <span>Total Expenses</span>
        <strong>{overview ? `₹${totalExpenses.toFixed(2)}` : '—'}</strong>
        <small>{overview?.expense_count ?? 0} records in selected period</small>
      </article>
    </section>
  );
};

export default IncomeExpenseSummary;
