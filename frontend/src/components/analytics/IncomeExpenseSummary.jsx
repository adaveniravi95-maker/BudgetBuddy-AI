const INR = (v) => `INR ${Number(v ?? 0).toFixed(2)}`;

export default function IncomeExpenseSummary({ data }) {
  return (
    <div className="stats-grid">
      <div className="stat-card is-income">
        <div className="stat-indicator income">In</div>
        <span className="stat-label">Total Income</span>
        <span className="stat-value income">{INR(data.total_income)}</span>
      </div>
      <div className="stat-card is-expense">
        <div className="stat-indicator expense">Ex</div>
        <span className="stat-label">Total Expenses</span>
        <span className="stat-value expense">{INR(data.total_expenses)}</span>
      </div>
    </div>
  );
}
