import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const currency = (value) => `₹${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const compactCurrency = (value) => `₹${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

export const CategoryPieChart = ({ data }) => (
  <ResponsiveContainer width="100%" height="100%">
    <PieChart>
      <Pie data={data} dataKey="raw_total" nameKey="category" innerRadius="54%" outerRadius="82%" paddingAngle={2}>
        {data.map((entry) => <Cell key={entry.category} fill={entry.color} />)}
      </Pie>
      <Tooltip formatter={(value) => currency(value)} />
    </PieChart>
  </ResponsiveContainer>
);

export const MonthlyBarChart = ({ data }) => (
  <ResponsiveContainer width="100%" height="100%">
    <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
      <CartesianGrid stroke="var(--chart-grid, #e8edf4)" strokeDasharray="3 3" vertical={false} />
      <XAxis dataKey="month_name" tickFormatter={(value) => value.split(' ')[0]} tick={{ fill: 'var(--chart-label, #64748b)', fontSize: 11 }} axisLine={false} tickLine={false} />
      <YAxis tickFormatter={compactCurrency} tick={{ fill: 'var(--chart-label, #64748b)', fontSize: 11 }} axisLine={false} tickLine={false} width={52} />
      <Tooltip formatter={(value) => currency(value)} />
      <Legend />
      <Bar dataKey="raw_income" name="Income" fill="#0f766e" radius={[4, 4, 0, 0]} />
      <Bar dataKey="raw_expenses" name="Expenses" fill="#f97316" radius={[4, 4, 0, 0]} />
    </BarChart>
  </ResponsiveContainer>
);
