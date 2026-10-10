import { lazy, Suspense } from 'react';

const MonthlyBarChart = lazy(() => import('./AnalyticsCharts').then((module) => ({ default: module.MonthlyBarChart })));

const MonthlyTrendsSection = ({ trends = [], loading, error }) => {
  const hasTransactions = trends.some((item) => Number(item.raw_income) > 0 || Number(item.raw_expenses) > 0);
  const endingMonth = trends[trends.length - 1]?.month_name;

  return (
    <section className="analytics-panel" aria-labelledby="monthly-trends-heading">
      <div className="analytics-panel-heading">
        <div>
          <h3 id="monthly-trends-heading">Monthly Income &amp; Expenses</h3>
          <p>{endingMonth ? `Six-month comparison ending ${endingMonth}` : 'Six-month comparison from saved transactions'}</p>
        </div>
      </div>
      {loading && trends.length === 0 ? (
        <div className="analytics-panel-state" role="status">Loading monthly trends...</div>
      ) : error && trends.length === 0 ? (
        <div className="analytics-panel-state" role="alert">Monthly trends are unavailable.</div>
      ) : !hasTransactions ? (
        <div className="analytics-panel-state">No income or expense activity in these months.</div>
      ) : (
        <div className="monthly-trend-chart">
          <Suspense fallback={<div className="analytics-panel-state">Loading chart...</div>}>
            <MonthlyBarChart data={trends} />
          </Suspense>
        </div>
      )}
    </section>
  );
};

export default MonthlyTrendsSection;
