import { MONTHS } from '../../constants/finance';

const INR = (v) => `INR ${Number(v ?? 0).toFixed(2)}`;

export default function FinancialSummary({ data, month, year }) {
  const period =
    month > 0
      ? `${MONTHS[month]} ${year}`
      : data.filters?.start_date && data.filters?.end_date
        ? `${data.filters.start_date} → ${data.filters.end_date}`
        : 'All time';

  return (
    <div className="ana-metrics">
      <div className="ana-metric">
        <div className="ana-metric-label">Net Savings</div>
        <div
          className="ana-metric-value"
          style={{ color: data.net_savings >= 0 ? 'var(--success)' : 'var(--error)' }}
        >
          {INR(data.net_savings)}
        </div>
      </div>
      <div className="ana-metric">
        <div className="ana-metric-label">Savings Rate</div>
        <div className="ana-metric-value">{Number(data.savings_rate_percent ?? 0).toFixed(1)}%</div>
      </div>
      <div className="ana-metric">
        <div className="ana-metric-label">Income Records</div>
        <div className="ana-metric-value">{data.income_count ?? 0}</div>
      </div>
      <div className="ana-metric">
        <div className="ana-metric-label">Expense Records</div>
        <div className="ana-metric-value">{data.expense_count ?? 0}</div>
      </div>
      <div className="ana-metric">
        <div className="ana-metric-label">Period</div>
        <div className="ana-metric-value" style={{ fontSize: 14 }}>{period}</div>
      </div>
    </div>
  );
}
