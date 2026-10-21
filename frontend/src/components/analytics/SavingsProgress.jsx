const INR = (v) => `INR ${Number(v ?? 0).toFixed(2)}`;

export default function SavingsProgress({ summary }) {
  const s = summary || {};
  const goals = s.total_goals ?? 0;

  return (
    <div className="ana-block">
      <h4>Savings Progress</h4>
      {goals === 0 ? (
        <div className="empty-state" style={{ padding: '24px 0' }}>
          <p>No savings goals yet.</p>
        </div>
      ) : (
        <>
          <div className="ana-savings-head">
            <span>
              {INR(s.total_saved)} / {INR(s.total_target)}
            </span>
            <span>{Number(s.overall_progress_percent ?? 0).toFixed(1)}%</span>
          </div>
          <div
            className="savings-bar"
            role="progressbar"
            aria-valuenow={Number(s.overall_progress_percent ?? 0)}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className={`savings-fill ${Number(s.overall_progress_percent) >= 100 ? 'completed' : ''}`}
              style={{ width: `${Math.min(Number(s.overall_progress_percent ?? 0), 100)}%` }}
            />
          </div>
          <div className="ana-metrics" style={{ marginTop: 14 }}>
            <div className="ana-metric">
              <div className="ana-metric-label">Goals</div>
              <div className="ana-metric-value">{goals}</div>
            </div>
            <div className="ana-metric">
              <div className="ana-metric-label">Completed</div>
              <div className="ana-metric-value">{s.completed_goals ?? 0}</div>
            </div>
            <div className="ana-metric">
              <div className="ana-metric-label">Still to Save</div>
              <div className="ana-metric-value" style={{ fontSize: 15 }}>
                {INR(Math.max(Number(s.total_target ?? 0) - Number(s.total_saved ?? 0), 0))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
