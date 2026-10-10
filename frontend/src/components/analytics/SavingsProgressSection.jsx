const SavingsProgressSection = ({ overview, loading, error }) => {
  if (loading && !overview) {
    return <section className="analytics-panel analytics-state" role="status">Loading savings progress...</section>;
  }

  if (error && !overview) {
    return <section className="analytics-panel analytics-state" role="alert">Savings progress is unavailable.</section>;
  }

  const goals = overview?.savings_goals;
  if (!goals || goals.total_goals_count === 0) {
    return (
      <section className="analytics-panel" aria-labelledby="savings-progress-heading">
        <div className="analytics-panel-heading">
          <div>
            <h3 id="savings-progress-heading">Savings Progress</h3>
            <p>Progress across your savings goals</p>
          </div>
        </div>
        <div className="analytics-panel-state">No savings goals yet.</div>
      </section>
    );
  }

  const progress = Number(goals.overall_progress_percentage || 0);
  const clampedProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <section className="analytics-panel" aria-labelledby="savings-progress-heading">
      <div className="analytics-panel-heading">
        <div>
          <h3 id="savings-progress-heading">Savings Progress</h3>
          <p>{goals.completed_goals_count} of {goals.total_goals_count} goals completed</p>
        </div>
        <strong className="savings-progress-value">{progress}%</strong>
      </div>
      <div className="savings-progress-track" role="progressbar" aria-valuenow={clampedProgress} aria-valuemin="0" aria-valuemax="100">
        <span style={{ width: `${clampedProgress}%` }} />
      </div>
      <div className="savings-progress-totals">
        <span>Saved <strong>₹{Number(goals.total_saved_amount || 0).toFixed(2)}</strong></span>
        <span>Target <strong>₹{Number(goals.total_target_amount || 0).toFixed(2)}</strong></span>
      </div>
    </section>
  );
};

export default SavingsProgressSection;
