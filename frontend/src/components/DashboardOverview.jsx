import {
  ArrowDownRight,
  ArrowUpRight,
  AlertTriangle,
  Bell,
  CalendarDays,
  Check,
  CircleDollarSign,
  Coins,
  FileDown,
  FileSpreadsheet,
  Plus,
  PiggyBank,
  Search,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import CategorySpendingSection from './analytics/CategorySpendingSection';
import FinancialSummarySection from './analytics/FinancialSummarySection';
import MonthlyTrendsSection from './analytics/MonthlyTrendsSection';
import CurrentDateDisplay from './CurrentDateDisplay';
import TransactionCsvImport from './TransactionCsvImport';

const currency = (value) => `₹${Number(value || 0).toLocaleString(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})}`;

const formatDate = (value) => new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
  month: 'short',
  day: 'numeric',
});

const DashboardOverview = ({
  user,
  greeting,
  overview,
  trends,
  categories,
  analyticsMonth,
  onAnalyticsMonthChange,
  transactions = [],
  notifications = [],
  goals = [],
  budgetSummary,
  isLoadingAnalytics,
  analyticsError,
  isLoadingSummary,
  summaryError,
  isLoadingNotifications,
  notificationsError,
  notificationsMessage,
  isLoadingGoals,
  goalsError,
  isLoadingBudget,
  budgetError,
  onNavigate,
  onReadNotification,
  onMarkAllRead,
  isMarkingAllRead,
  searchQuery,
  onSearch,
  onReportDownload,
  onTransactionsImported,
  exportingReport,
  reportMessage,
}) => {
  const budgetCategories = (budgetSummary?.categories || [])
    .filter((category) => Number(category.allocated_budget) > 0)
    .sort((first, second) => Number(second.utilization_percentage) - Number(first.utilization_percentage))
    .slice(0, 3);
  const search = searchQuery.trim().toLowerCase();
  const searchResults = search
    ? [
        ...transactions
          .filter((transaction) => `${transaction.title} ${transaction.description}`.toLowerCase().includes(search))
          .map((transaction) => ({
            id: transaction.id,
            label: `${transaction.title} · ${currency(transaction.raw_amount)}`,
            type: transaction.type === 'income' ? 'incomes' : 'expenses',
          })),
        ...goals
          .filter((goal) => goal.name.toLowerCase().includes(search))
          .map((goal) => ({ id: `goal-${goal.id}`, label: goal.name, type: 'savings' })),
      ].slice(0, 5)
    : [];

  const metrics = [
    {
      label: 'Total Income',
      value: overview ? currency(overview.total_income) : null,
      count: `${overview?.income_count || 0} records this month`,
      icon: Wallet,
      tone: 'income',
      trend: <ArrowUpRight size={14} />,
    },
    {
      label: 'Total Expenses',
      value: overview ? currency(overview.total_expenses) : null,
      count: `${overview?.expense_count || 0} records this month`,
      icon: CircleDollarSign,
      tone: 'expense',
      trend: <ArrowDownRight size={14} />,
    },
    {
      label: 'Remaining Balance',
      value: overview ? currency(overview.net_savings) : null,
      count: 'Income after expenses',
      icon: Coins,
      tone: 'balance',
      trend: <TrendingUp size={14} />,
    },
    {
      label: 'Savings Rate',
      value: overview ? `${Number(overview.savings_rate || 0)}%` : null,
      count: 'of total income',
      icon: PiggyBank,
      tone: 'savings',
      trend: <Target size={14} />,
    },
  ];

  return (
    <div className="overview-page">
      <header className="overview-toolbar">
        <div className="overview-search-wrap">
          <Search size={17} aria-hidden="true" />
          <input
            aria-label="Search transactions and savings goals"
            placeholder="Search transactions or goals"
            value={searchQuery}
            onChange={(event) => onSearch(event.target.value)}
          />
          {search && (
            <div className="overview-search-results">
              {searchResults.length ? searchResults.map((result) => (
                <button key={result.id} type="button" onClick={() => onNavigate(result.type)}>
                  <Search size={14} /> {result.label}
                </button>
              )) : <span>No matching records</span>}
            </div>
          )}
        </div>
        <div className="overview-toolbar-user">
          <button
            type="button"
            className="overview-toolbar-notifications"
            aria-label={`${notifications.filter((notification) => !notification.is_read).length} unread notifications`}
            onClick={() => onNavigate('notifications')}
          >
            <Bell size={18} />
            {notifications.some((notification) => !notification.is_read) && (
              <span>{notifications.filter((notification) => !notification.is_read).length}</span>
            )}
          </button>
          <span className="overview-avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</span>
          <div className="overview-user-name">
            <strong>{user?.username || 'Student'}</strong>
            <small>{user?.role || 'Student'}</small>
          </div>
        </div>
      </header>

      <div className="overview-grid">
        <main className="overview-main-column">
          <section className="overview-welcome">
            <div>
              <p className="overview-eyebrow">Your financial overview for {overview?.filter_applied || 'this month'}</p>
              <h1>{greeting}, {user?.username}! <Sparkles className="overview-greeting-icon" size={18} aria-hidden="true" /></h1>
              <p>Small steps today build better money habits tomorrow.</p>
              <CurrentDateDisplay />
            </div>
            <div className="overview-report-actions">
              <TransactionCsvImport onImported={onTransactionsImported} />
              <button type="button" onClick={() => onReportDownload('pdf')} disabled={Boolean(exportingReport)}>
                <FileDown size={14} /> {exportingReport === 'pdf' ? 'Preparing...' : 'PDF'}
              </button>
              <button type="button" onClick={() => onReportDownload('xlsx')} disabled={Boolean(exportingReport)}>
                <FileSpreadsheet size={14} /> {exportingReport === 'xlsx' ? 'Preparing...' : 'Excel'}
              </button>
            </div>
            <div className="overview-welcome-art" aria-hidden="true">
              <Coins size={31} />
              <TrendingUp size={45} />
              <PiggyBank size={36} />
            </div>
          </section>

          {reportMessage && (
            <div className={`alert alert-${reportMessage.type}`} role={reportMessage.type === 'error' ? 'alert' : 'status'}>
              {reportMessage.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
              <span>{reportMessage.text}</span>
            </div>
          )}

          <section className="overview-metrics" aria-label="Monthly financial totals">
            {metrics.map((metric) => {
              const Icon = metric.icon;
              return (
                <article className={`overview-metric metric-${metric.tone}`} key={metric.label}>
                  <div className="overview-metric-icon"><Icon size={18} /></div>
                  <span className="overview-metric-label">{metric.label}</span>
                  <strong className="overview-metric-value">
                    {metric.value || (isLoadingAnalytics ? 'Loading...' : '—')}
                  </strong>
                  <small><span className="metric-trend">{metric.trend}</span>{metric.count}</small>
                </article>
              );
            })}
          </section>

          {analyticsError && (
            <div className="overview-inline-error" role="alert">
              <span>{analyticsError}</span>
              <button type="button" onClick={() => onNavigate('refresh')}>Retry</button>
            </div>
          )}

          <section className="overview-analytics-toolbar" aria-label="Analytics period">
            <div>
              <strong>Analytics</strong>
              <span>Choose a month to update the summary and charts</span>
            </div>
            <label>
              <span>Period</span>
              <input
                type="month"
                value={analyticsMonth}
                onChange={(event) => {
                  if (event.target.value) onAnalyticsMonthChange(event.target.value);
                }}
                aria-label="Analytics month"
              />
            </label>
          </section>

          <div className="overview-charts">
            <MonthlyTrendsSection trends={trends} loading={isLoadingAnalytics} error={analyticsError} />
            <CategorySpendingSection
              categories={categories}
              periodLabel={overview?.filter_applied}
              loading={isLoadingAnalytics}
              error={analyticsError}
            />
          </div>

          <div className="overview-lower-grid">
            <section className="overview-panel overview-transactions">
              <div className="overview-panel-heading">
                <div><h2>Recent Transactions</h2><p>Your latest income and expenses</p></div>
                <button type="button" className="overview-link" onClick={() => onNavigate('activity')}>View all</button>
              </div>
              {isLoadingSummary ? (
                <div className="overview-empty">Loading transactions...</div>
              ) : summaryError ? (
                <div className="overview-inline-error" role="alert">
                  <span>{summaryError}</span>
                  <button type="button" onClick={() => onNavigate('refresh')}>Retry</button>
                </div>
              ) : transactions.length === 0 ? (
                <div className="overview-empty">No transactions yet. Add income or an expense to get started.</div>
              ) : (
                <div className="overview-transaction-list">
                  {transactions.slice(0, 5).map((transaction) => (
                    <button
                      className="overview-transaction-row"
                      key={transaction.id}
                      type="button"
                      onClick={() => onNavigate(transaction.type === 'income' ? 'incomes' : 'expenses')}
                    >
                      <span className={`transaction-kind ${transaction.type}`}>
                        {transaction.type === 'income' ? <TrendingUp size={15} /> : <TrendingDown size={15} />}
                      </span>
                      <span className="transaction-info">
                        <strong>{transaction.title}</strong>
                        <small>{transaction.description || transaction.category || transaction.source || 'Transaction'} · {formatDate(transaction.date)}</small>
                        {transaction.type === 'expense' ? (
                          <span className={`category-badge cat-${transaction.category?.toLowerCase()}`}>
                            {transaction.category}
                          </span>
                        ) : (
                          <span className={`category-badge src-${transaction.source?.toLowerCase().replace(/\s+/g, '-')}`}>
                            {transaction.source}
                          </span>
                        )}
                      </span>
                      <strong className={`transaction-amount ${transaction.type}`}>
                        {transaction.type === 'income' ? '+' : '-'}{currency(transaction.raw_amount)}
                      </strong>
                    </button>
                  ))}
                </div>
              )}
            </section>

            <FinancialSummarySection overview={overview} loading={isLoadingAnalytics} error={analyticsError} />
          </div>
        </main>

        <aside className="overview-side-column">
          <section className="overview-panel quick-actions-panel">
            <div className="overview-panel-heading"><div><h2>Quick Actions</h2></div></div>
            <div className="overview-quick-actions">
              <button type="button" className="quick-action income-action" onClick={() => onNavigate('incomes')}>
                <span><Plus size={18} /></span><small>Add Income</small>
              </button>
              <button type="button" className="quick-action expense-action" onClick={() => onNavigate('expenses')}>
                <span><TrendingDown size={18} /></span><small>Add Expense</small>
              </button>
              <button type="button" className="quick-action budget-action" onClick={() => onNavigate('budgets')}>
                <span><CalendarDays size={18} /></span><small>Create Budget</small>
              </button>
              <button type="button" className="quick-action goal-action" onClick={() => onNavigate('savings')}>
                <span><Target size={18} /></span><small>Add Goal</small>
              </button>
            </div>
          </section>

          <section className="overview-panel overview-notifications">
            <div className="overview-panel-heading">
              <div className="overview-heading-icon"><Bell size={16} /><h2>Notifications</h2></div>
              <button type="button" className="overview-link" onClick={() => onNavigate('notifications')}>View all</button>
            </div>
            {notificationsMessage && (
              <div className={`alert alert-${notificationsMessage.type}`} role={notificationsMessage.type === 'error' ? 'alert' : 'status'}>
                <span>{notificationsMessage.text}</span>
              </div>
            )}
            {isLoadingNotifications ? (
              <div className="overview-empty">Loading notifications...</div>
            ) : notificationsError ? (
              <div className="overview-inline-error" role="alert">
                <span>{notificationsError}</span>
                <button type="button" onClick={() => onNavigate('refresh')}>Retry</button>
              </div>
            ) : notifications.length === 0 ? (
              <div className="overview-empty">You’re all caught up. Budget alerts and milestones will appear here.</div>
            ) : (
              <div className="overview-notification-list">
                {notifications.slice(0, 4).map((notification) => (
                  <button
                    className={`overview-notification-row ${notification.is_read ? '' : 'unread'}`}
                    key={notification.id}
                    type="button"
                    onClick={() => onReadNotification(notification)}
                  >
                    <span className={`overview-notification-icon type-${notification.notification_type}`}>
                      {notification.notification_type === 'budget_alert' ? <AlertTriangle size={15} /> : notification.notification_type === 'goal_milestone' ? <Target size={15} /> : <Bell size={15} />}
                    </span>
                    <span className="overview-notification-copy">
                      <strong>{notification.title}</strong>
                      <small>{notification.message}</small>
                    </span>
                    {!notification.is_read && <i className="overview-unread-dot" />}
                  </button>
                ))}
              </div>
            )}
            {notifications.some((notification) => !notification.is_read) && (
              <button type="button" className="overview-mark-read" onClick={onMarkAllRead} disabled={isMarkingAllRead}>
                {isMarkingAllRead ? 'Marking...' : <><Check size={14} /> Mark all read</>}
              </button>
            )}
          </section>

          <section className="overview-panel overview-goals">
            <div className="overview-panel-heading">
              <div className="overview-heading-icon"><Target size={16} /><h2>Your Goals</h2></div>
              <button type="button" className="overview-link" onClick={() => onNavigate('savings')}>View all</button>
            </div>
            {isLoadingGoals ? (
              <div className="overview-empty">Loading savings goals...</div>
            ) : goalsError ? (
              <div className="overview-inline-error" role="alert">
                <span>{goalsError}</span>
                <button type="button" onClick={() => onNavigate('refresh')}>Retry</button>
              </div>
            ) : goals.length === 0 ? (
              <div className="overview-empty">No goals yet. Set a target to start building savings.</div>
            ) : (
              <div className="overview-goal-list">
                {goals.slice(0, 2).map((goal) => (
                  <button className="overview-goal-row" type="button" key={goal.id} onClick={() => onNavigate('savings')}>
                    <span className="overview-goal-icon"><Target size={17} /></span>
                    <span className="overview-goal-copy">
                      <span><strong>{goal.name}</strong><b>{Number(goal.progress_percentage || 0)}%</b></span>
                      <i><span style={{ width: `${Math.min(Number(goal.progress_percentage || 0), 100)}%` }} /></i>
                      <small>{currency(goal.current_amount)} saved <em>Target: {currency(goal.target_amount)}</em></small>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="overview-panel overview-budget">
            <div className="overview-panel-heading">
              <div className="overview-heading-icon"><Wallet size={16} /><h2>Budget Overview</h2></div>
              <button type="button" className="overview-link" onClick={() => onNavigate('budgets')}>View all</button>
            </div>
            {isLoadingBudget ? (
              <div className="overview-empty">Loading budgets...</div>
            ) : budgetError ? (
              <div className="overview-inline-error" role="alert">
                <span>{budgetError}</span>
                <button type="button" onClick={() => onNavigate('refresh')}>Retry</button>
              </div>
            ) : budgetCategories.length === 0 ? (
              <div className="overview-empty overview-budget-empty">
                <span className="overview-budget-empty-icon"><Wallet size={20} /></span>
                <strong>No budget for this month yet</strong>
                <p>Set a spending limit to keep your monthly plans on track.</p>
                <button type="button" onClick={() => onNavigate('budgets')}>
                  Create a budget <ArrowUpRight size={15} />
                </button>
              </div>
            ) : (
              <div className="overview-budget-list">
                {budgetCategories.map((budget) => (
                  <button type="button" className="overview-budget-row" key={budget.category} onClick={() => onNavigate('budgets')}>
                    <span className="overview-budget-icon">{budget.category.slice(0, 1)}</span>
                    <span className="overview-budget-copy">
                      <span><strong>Monthly {budget.category} Budget</strong><b>{Number(budget.utilization_percentage || 0)}%</b></span>
                      <small>{currency(budget.actual_spent)} / {currency(budget.allocated_budget)}</small>
                      <i><span className={budget.is_over_budget ? 'over' : ''} style={{ width: `${Math.min(Number(budget.utilization_percentage || 0), 100)}%` }} /></i>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
};

export default DashboardOverview;
