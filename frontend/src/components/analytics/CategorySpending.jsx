import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { EXPENSE_COLORS, catLabel } from '../../constants/finance';

const FALLBACK = '#6366F1';

export default function CategorySpending({ categories }) {
  if (!categories?.length) {
    return (
      <div className="ana-block">
        <h4>Category-wise Spending</h4>
        <div className="empty-state" style={{ padding: '24px 0' }}>
          <p>No expenses in this period.</p>
        </div>
      </div>
    );
  }

  const chartData = categories.map((c) => ({
    name: catLabel(c.category),
    value: Number(c.total),
    color: EXPENSE_COLORS[c.category] || FALLBACK,
    count: c.count,
    percent: Number(c.percent_of_expenses),
  }));

  return (
    <div className="ana-block">
      <h4>Category-wise Spending</h4>
      <div className="ana-chart-box" style={{ height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              stroke="none"
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: '#1A2234',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 10,
                fontSize: 12,
              }}
              formatter={(value, name) => [`INR ${Number(value).toFixed(2)}`, name]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div style={{ marginTop: 8 }}>
        {chartData.map((c) => (
          <div key={c.name} className="ana-cat-row">
            <div className="ana-cat-head">
              <span className="ana-cat-name">
                <span className="ana-cat-dot" style={{ backgroundColor: c.color }} />
                {c.name}
              </span>
              <span className="ana-cat-amt">INR {c.value.toFixed(2)}</span>
            </div>
            <div className="ana-cat-track">
              <div className="ana-cat-fill" style={{ width: `${Math.min(c.percent, 100)}%`, backgroundColor: c.color }} />
            </div>
            <div className="ana-cat-pct">{c.count} transactions · {c.percent.toFixed(1)}% of expenses</div>
          </div>
        ))}
      </div>
    </div>
  );
}
