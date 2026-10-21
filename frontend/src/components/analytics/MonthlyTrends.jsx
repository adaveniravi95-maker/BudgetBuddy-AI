import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { MONTHS } from '../../constants/finance';

export default function MonthlyTrends({ trends }) {
  if (!trends?.length) {
    return (
      <div className="ana-block">
        <h4>Monthly Income / Expense Trends</h4>
        <div className="empty-state" style={{ padding: '24px 0' }}>
          <p>No monthly data in this period.</p>
        </div>
      </div>
    );
  }

  const chartData = trends.map((t) => ({
    label: `${MONTHS[t.month]?.slice(0, 3)} ${String(t.year).slice(2)}`,
    income: Number(t.income),
    expenses: Number(t.expenses),
    net: Number(t.net),
  }));

  const tooltipStyle = {
    background: '#1A2234',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 10,
    fontSize: 12,
  };

  return (
    <div className="ana-block">
      <h4>Monthly Income / Expense Trends</h4>
      <div className="ana-chart-scroll">
        <div className="ana-chart-box" style={{ minWidth: Math.min(chartData.length * 72 + 60, 1200), height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <XAxis
                dataKey="label"
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={54}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value, name) => [`INR ${Number(value).toFixed(2)}`, name]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="income" name="Income" fill="#10B981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="expenses" name="Expenses" fill="#EF4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
