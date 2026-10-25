import { MONTHS, EXPENSE_COLORS, catLabel } from '../../constants/finance';

const INR = (v) => `INR ${Number(v ?? 0).toFixed(2)}`;

export default function BudgetSummary({ summary }) {
  return (
    <div className="ana-block">
      <h4>
        Budget Summary
        {summary ? ` · ${MONTHS[summary.month]} ${summary.year}` : ''}
      </h4>
      {!summary ? (
        <div className="empty-state" style={{ padding: '24px 0' }}>
          <p>Select a month to see budget utilization.</p>
        </div>
      ) : (
        <>
          <div className="ana-savings-head">
            <span>
              {INR(summary.total_spent)} / {INR(summary.total_budget)}
            </span>
            <span>{Number(summary.utilization_percent ?? 0).toFixed(1)}%</span>
          </div>
          <div className="savings-bar">
            <div
              className="savings-fill"
              style={{
                width: `${Math.min(Number(summary.utilization_percent ?? 0), 100)}%`,
                background:
                  summary.utilization_percent >= 100
                    ? 'linear-gradient(90deg, var(--error), #F87171)'
                    : summary.utilization_percent >= 80
                      ? 'linear-gradient(90deg, var(--warning), #FBBF24)'
                      : undefined,
              }}
            />
          </div>
          <div className="ana-metrics" style={{ marginTop: 14 }}>
            <div className="ana-metric">
              <div className="ana-metric-label">Remaining</div>
              <div className="ana-metric-value" style={{ fontSize: 15 }}>
                {INR(summary.remaining)}
              </div>
            </div>
            <div className="ana-metric">
              <div className="ana-metric-label">Allocations</div>
              <div className="ana-metric-value">{summary.allocations?.length ?? 0}</div>
            </div>
          </div>
          {summary.allocations?.length > 0 && (
            <div className="item-list" style={{ marginTop: 12 }}>
              {summary.allocations.map((a) => (
                <div key={a.category} className="list-item" style={{ padding: '8px 0' }}>
                  <div
                    className="item-tag"
                    style={{ backgroundColor: EXPENSE_COLORS[a.category] || 'var(--primary)' }}
                  >
                    {catLabel(a.category)}
                  </div>
                  <div className="item-content">
                    <div className="item-title" style={{ fontSize: 13 }}>
                      {Number(a.utilization_percent ?? 0).toFixed(1)}% used
                    </div>
                    <div className="item-meta">
                      {INR(a.spent)} of {INR(a.budgeted)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
