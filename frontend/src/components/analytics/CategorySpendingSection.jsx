import { lazy, Suspense } from 'react';

const CategoryPieChart = lazy(() => import('./AnalyticsCharts').then((module) => ({ default: module.CategoryPieChart })));

const currency = (value) => `₹${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const CategorySpendingSection = ({ categories = [], periodLabel, loading, error }) => {
  const data = categories.filter((item) => Number(item.raw_total) > 0);

  return (
    <section className="analytics-panel" aria-labelledby="category-spending-heading">
      <div className="analytics-panel-heading">
        <div>
          <h3 id="category-spending-heading">Category-wise Spending</h3>
          <p>{periodLabel ? `Actual expenses for ${periodLabel}` : 'Actual expenses by category for the selected period'}</p>
        </div>
      </div>
      {loading && data.length === 0 ? (
        <div className="analytics-panel-state" role="status">Loading category spending...</div>
      ) : error && data.length === 0 ? (
        <div className="analytics-panel-state" role="alert">Category spending is unavailable.</div>
      ) : data.length === 0 ? (
        <div className="analytics-panel-state">No expenses recorded for this period.</div>
      ) : (
        <div className="category-chart-layout">
          <div className="category-chart">
            <Suspense fallback={<div className="analytics-panel-state">Loading chart...</div>}>
              <CategoryPieChart data={data} />
            </Suspense>
          </div>
          <ul className="category-chart-legend">
            {data.map((item) => (
              <li key={item.category}>
                <span className="category-legend-name"><i style={{ backgroundColor: item.color }} />{item.category}</span>
                <strong>{currency(item.raw_total)}</strong>
                <small>{item.percentage}%</small>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};

export default CategorySpendingSection;
