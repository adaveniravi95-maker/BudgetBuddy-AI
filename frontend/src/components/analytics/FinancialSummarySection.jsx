const FinancialSummarySection = ({ overview, loading, error }) => {
  if (loading && !overview) {
    return <section className="analytics-panel analytics-state" role="status">Loading financial summary...</section>;
  }

  if (error && !overview) {
    return <section className="analytics-panel analytics-state" role="alert">Financial summary is unavailable.</section>;
  }

  if (!overview) {
    return <section className="analytics-panel analytics-state">No financial summary available.</section>;
  }

  const netSavings = Number(overview.net_savings || 0);
  const savingsGoals = overview.savings_goals || {};

  return (
    <section className="analytics-panel" aria-labelledby="financial-summary-heading">
      <div className="analytics-panel-heading">
        <div>
          <h3 id="financial-summary-heading">Financial Summary</h3>
          <p>{overview.filter_applied}</p>
        </div>
      </div>
      <div className="financial-summary-list">
        <div><span>Net savings</span><strong className={netSavings >= 0 ? 'text-success' : 'text-danger'}>₹{netSavings.toFixed(2)}</strong></div>
        <div><span>Savings rate</span><strong>{Number(overview.savings_rate || 0)}%</strong></div>
        <div><span>Budget used</span><strong>{Number(overview.budget?.utilization_percentage || 0)}%</strong></div>
        <div><span>Goals completed</span><strong>{savingsGoals.completed_goals_count || 0} / {savingsGoals.total_goals_count || 0}</strong></div>
      </div>
    </section>
  );
};

export default FinancialSummarySection;
