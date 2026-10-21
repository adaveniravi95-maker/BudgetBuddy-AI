import { useState, useEffect, useCallback } from 'react';
import { analyticsAPI } from '../../services/api';
import { MONTHS, currentYear } from '../../constants/finance';
import IncomeExpenseSummary from './IncomeExpenseSummary';
import FinancialSummary from './FinancialSummary';
import CategorySpending from './CategorySpending';
import MonthlyTrends from './MonthlyTrends';
import SavingsProgress from './SavingsProgress';
import BudgetSummary from './BudgetSummary';

export default function AnalyticsSection() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [month, setMonth] = useState(0); // 0 = all time
  const [year, setYear] = useState(currentYear());

  const fetchAnalytics = useCallback(async (m = month, y = year) => {
    setLoading(true);
    setError('');
    try {
      const params = m > 0 ? { month: m, year: y } : {};
      const r = await analyticsAPI.get(params);
      setData(r.data);
    } catch (err) {
      setData(null);
      setError(err.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [month, year]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const noData = data && !data.has_data && (data.savings_summary?.total_goals ?? 0) === 0;

  return (
    <div className="section-card anim-fadeInUp">
      <div className="section-header">
        <span className="section-title">
          <span className="section-title-mark" /> Analytics Dashboard
        </span>
        <div className="section-actions">
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="filter-select"
            aria-label="Filter by month"
          >
            <option value={0}>All Time</option>
            {MONTHS.slice(1).map((m, i) => (
              <option key={i + 1} value={i + 1}>{m}</option>
            ))}
          </select>
          {month > 0 && (
            <select
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="filter-select"
              aria-label="Filter by year"
            >
              <option value={2025}>2025</option>
              <option value={2026}>2026</option>
              <option value={2027}>2027</option>
            </select>
          )}
          <button
            className="btn-report btn-report-ghost"
            onClick={() => fetchAnalytics()}
            disabled={loading}
          >
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="report-error">{error}</div>}

      {loading && !data ? (
        <>
          <div className="stats-grid">
            {[1, 2].map((i) => (
              <div key={i} className="skeleton" style={{ height: 96, borderRadius: 14 }} />
            ))}
          </div>
          <div className="ana-layout">
            <div className="skeleton" style={{ height: 300, borderRadius: 14 }} />
            <div className="skeleton" style={{ height: 300, borderRadius: 14 }} />
          </div>
        </>
      ) : error && !data ? (
        <div className="empty-state">
          <div className="empty-state-mark">An</div>
          <p>Analytics could not be loaded. Try again.</p>
        </div>
      ) : noData ? (
        <div className="empty-state">
          <div className="empty-state-mark">An</div>
          <p>No data yet. Add income, expenses or savings goals to see analytics.</p>
        </div>
      ) : data ? (
        <>
          <IncomeExpenseSummary data={data} />
          <FinancialSummary data={data} month={month} year={year} />

          <div className="ana-layout">
            <CategorySpending categories={data.category_summary} />
            <MonthlyTrends trends={data.monthly_trends} />
          </div>

          <div className="ana-layout">
            <SavingsProgress summary={data.savings_summary} />
            <BudgetSummary summary={data.budget_summary} />
          </div>
        </>
      ) : null}
    </div>
  );
}
