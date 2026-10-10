import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { expensesAPI, incomesAPI, budgetsAPI, savingsGoalsAPI, notificationsAPI, dashboardAPI, analyticsAPI, reportsAPI } from '../api/api';
import DashboardOverview from '../components/DashboardOverview';
import IncomeExpenseSummary from '../components/analytics/IncomeExpenseSummary';
import CategorySpendingSection from '../components/analytics/CategorySpendingSection';
import MonthlyTrendsSection from '../components/analytics/MonthlyTrendsSection';
import FinancialSummarySection from '../components/analytics/FinancialSummarySection';
import SavingsProgressSection from '../components/analytics/SavingsProgressSection';
import CurrentDateDisplay from '../components/CurrentDateDisplay';
import {
  Database,
  DollarSign,
  PlusCircle,
  RefreshCw,
  Server,
  CheckCircle2,
  AlertTriangle,
  Edit2,
  Trash2,
  Filter,
  Calendar,
  X,
  TrendingDown,
  TrendingUp,
  Wallet,
  ShoppingBag,
  Utensils,
  Plane,
  GraduationCap,
  Film,
  HelpCircle,
  ArrowUpRight,
  ArrowDownRight,
  Briefcase,
  Gift,
  Award,
  Target,
  PiggyBank,
  Sparkles,
  Bell,
  CheckCheck,
  Check,
  FileDown,
  FileSpreadsheet,
  FileText,
} from 'lucide-react';

const CATEGORIES = [
  'Food',
  'Travel',
  'Shopping',
  'Education',
  'Entertainment',
  'Miscellaneous',
];

const CATEGORY_COLORS = {
  Food: '#f97316',
  Travel: '#0284c7',
  Shopping: '#a855f7',
  Education: '#6366f1',
  Entertainment: '#ec4899',
  Miscellaneous: '#64748b',
};

const INCOME_SOURCES = [
  'Pocket Money',
  'Scholarship',
  'Freelance Income',
  'Part-time Job',
  'Salary',
  'Other',
];

const getLocalDateString = () => {
  const today = new Date();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${today.getFullYear()}-${month}-${day}`;
};

const getCategoryIcon = (category) => {
  switch (category) {
    case 'Food':
      return <Utensils size={14} />;
    case 'Travel':
      return <Plane size={14} />;
    case 'Shopping':
      return <ShoppingBag size={14} />;
    case 'Education':
      return <GraduationCap size={14} />;
    case 'Entertainment':
      return <Film size={14} />;
    default:
      return <HelpCircle size={14} />;
  }
};

const getSourceIcon = (source) => {
  switch (source) {
    case 'Pocket Money':
      return <Gift size={14} />;
    case 'Scholarship':
      return <Award size={14} />;
    case 'Freelance Income':
      return <Briefcase size={14} />;
    default:
      return <DollarSign size={14} />;
  }
};

const Dashboard = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');

  // Summary State (Task 5)
  const [summaryData, setSummaryData] = useState({
    total_income: '0.00',
    total_expenses: '0.00',
    remaining_amount: '0.00',
    income_count: 0,
    expense_count: 0,
    recent_transactions: [],
  });
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState('');
  const [analyticsMonth, setAnalyticsMonth] = useState(() => getLocalDateString().slice(0, 7));
  const [analyticsOverview, setAnalyticsOverview] = useState(null);
  const [analyticsTrends, setAnalyticsTrends] = useState([]);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  const [analyticsError, setAnalyticsError] = useState('');
  const analyticsRequestId = useRef(0);

  // API Tester State
  const [apiResponse, setApiResponse] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);
  const [isLoadingApi, setIsLoadingApi] = useState(false);
  const [activeEndpoint, setActiveEndpoint] = useState('');

  // ----------------- EXPENSES STATE -----------------
  const [expenses, setExpenses] = useState([]);
  const [isLoadingExpenses, setIsLoadingExpenses] = useState(false);
  const [expensesError, setExpensesError] = useState('');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('ALL');
  const [expenseForm, setExpenseForm] = useState({
    category: 'Food',
    description: '',
    amount: '',
    date: getLocalDateString(),
  });
  const [expenseMsg, setExpenseMsg] = useState(null);
  const [isAddingExpense, setIsAddingExpense] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [editExpenseForm, setEditExpenseForm] = useState({
    category: 'Food',
    description: '',
    amount: '',
    date: '',
  });
  const [isUpdatingExpense, setIsUpdatingExpense] = useState(false);
  const [editExpenseMsg, setEditExpenseMsg] = useState(null);
  const [deletingExpenseId, setDeletingExpenseId] = useState(null);

  // ----------------- INCOMES STATE -----------------
  const [incomes, setIncomes] = useState([]);
  const [isLoadingIncomes, setIsLoadingIncomes] = useState(false);
  const [incomesError, setIncomesError] = useState('');
  const [selectedSourceFilter, setSelectedSourceFilter] = useState('ALL');
  const [incomeForm, setIncomeForm] = useState({
    source: 'Pocket Money',
    description: '',
    amount: '',
    date: getLocalDateString(),
  });
  const [incomeMsg, setIncomeMsg] = useState(null);
  const [isAddingIncome, setIsAddingIncome] = useState(false);
  const [editingIncome, setEditingIncome] = useState(null);
  const [editIncomeForm, setEditIncomeForm] = useState({
    source: 'Pocket Money',
    description: '',
    amount: '',
    date: '',
  });
  const [isUpdatingIncome, setIsUpdatingIncome] = useState(false);
  const [editIncomeMsg, setEditIncomeMsg] = useState(null);
  const [deletingIncomeId, setDeletingIncomeId] = useState(null);

  // ----------------- BUDGET PLANNING STATE -----------------
  const currentMonthStr = getLocalDateString().slice(0, 7);
  const [selectedBudgetMonth, setSelectedBudgetMonth] = useState(currentMonthStr);
  const [budgetSummary, setBudgetSummary] = useState({
    month: `${currentMonthStr}-01`,
    month_label: '',
    total_budget: '0.00',
    total_spent: '0.00',
    total_remaining: '0.00',
    categories: [],
  });
  const [isLoadingBudget, setIsLoadingBudget] = useState(false);
  const [budgetError, setBudgetError] = useState('');
  const [budgetForm, setBudgetForm] = useState({
    category: 'Food',
    amount: '',
    month: `${currentMonthStr}-01`,
  });
  const [budgetMsg, setBudgetMsg] = useState(null);
  const [isAddingBudget, setIsAddingBudget] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [editBudgetForm, setEditBudgetForm] = useState({
    category: 'Food',
    amount: '',
    month: '',
  });
  const [isUpdatingBudget, setIsUpdatingBudget] = useState(false);
  const [editBudgetMsg, setEditBudgetMsg] = useState(null);
  const [deletingBudgetId, setDeletingBudgetId] = useState(null);

  // ----------------- SAVINGS GOALS STATE -----------------
  const [goals, setGoals] = useState([]);
  const [isLoadingGoals, setIsLoadingGoals] = useState(false);
  const [goalsError, setGoalsError] = useState('');
  const [goalForm, setGoalForm] = useState({
    name: '',
    target_amount: '',
    current_amount: '0.00',
    target_date: '',
  });
  const [goalMsg, setGoalMsg] = useState(null);
  const [isAddingGoal, setIsAddingGoal] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [editGoalForm, setEditGoalForm] = useState({
    name: '',
    target_amount: '',
    current_amount: '',
    target_date: '',
  });
  const [isUpdatingGoal, setIsUpdatingGoal] = useState(false);
  const [editGoalMsg, setEditGoalMsg] = useState(null);
  const [depositGoal, setDepositGoal] = useState(null);
  const [depositAmount, setDepositAmount] = useState('');
  const [isDepositing, setIsDepositing] = useState(false);
  const [depositMsg, setDepositMsg] = useState(null);
  const [deletingGoalId, setDeletingGoalId] = useState(null);

  // ----------------- NOTIFICATIONS STATE -----------------
  const [notificationsList, setNotificationsList] = useState([]);
  const [isLoadingNotifications, setIsLoadingNotifications] = useState(false);
  const [selectedNotifFilter, setSelectedNotifFilter] = useState('ALL');
  const [notificationsMessage, setNotificationsMessage] = useState(null);
  const [notificationsError, setNotificationsError] = useState('');
  const [notificationActionId, setNotificationActionId] = useState(null);
  const [isMarkingAllNotificationsRead, setIsMarkingAllNotificationsRead] = useState(false);
  const [exportingReport, setExportingReport] = useState(null);
  const [reports, setReports] = useState([]);
  const [isLoadingReports, setIsLoadingReports] = useState(false);
  const [reportsError, setReportsError] = useState('');
  const [reportMessage, setReportMessage] = useState(null);

  // Initial Load
  useEffect(() => {
    refreshAllData(false);
  }, []);

  useEffect(() => {
    const hashTab = location.hash.replace('#', '');
    const validTabs = ['overview', 'expenses', 'incomes', 'budgets', 'savings', 'activity', 'notifications', 'reports'];
    if (validTabs.includes(hashTab)) {
      setActiveTab(hashTab);
    }
  }, [location.hash]);

  useEffect(() => {
    const hashTab = location.hash.replace('#', '');
    const validTabs = ['overview', 'expenses', 'incomes', 'budgets', 'savings', 'activity', 'notifications', 'reports'];
    if (!validTabs.includes(hashTab) || hashTab !== activeTab) return undefined;

    if (hashTab === 'overview') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return undefined;
    }

    const frameId = window.requestAnimationFrame(() => {
      document.getElementById('dashboard-module')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    });
    return () => window.cancelAnimationFrame(frameId);
  }, [activeTab, location.hash]);

  useEffect(() => {
    fetchBudgetSummary(selectedBudgetMonth);
  }, [selectedBudgetMonth]);

  useEffect(() => {
    fetchAnalytics(analyticsMonth);
  }, [analyticsMonth]);

  useEffect(() => {
    if (activeTab === 'reports') fetchReports();
  }, [activeTab]);

  const refreshAllData = async (refreshAnalyticsData = true) => {
    fetchSummary();
    if (refreshAnalyticsData) fetchAnalytics(analyticsMonth);
    fetchExpenses();
    fetchIncomes();
    fetchBudgetSummary(selectedBudgetMonth);
    fetchGoals();
    fetchNotificationsList();
  };

  const fetchAnalytics = async (month = analyticsMonth) => {
    const requestId = ++analyticsRequestId.current;
    setIsLoadingAnalytics(true);
    setAnalyticsError('');
    try {
      const [overviewResponse, trendsResponse] = await Promise.all([
        analyticsAPI.getOverview({ month }),
        analyticsAPI.getTrends({ months: 6, month }),
      ]);
      if (requestId !== analyticsRequestId.current) return;
      setAnalyticsOverview(overviewResponse.data);
      setAnalyticsTrends(trendsResponse.data.trends || []);
    } catch (err) {
      if (requestId !== analyticsRequestId.current) return;
      setAnalyticsError(
        err.response?.data?.detail || 'Analytics could not be loaded. Please try again.'
      );
    } finally {
      if (requestId === analyticsRequestId.current) {
        setIsLoadingAnalytics(false);
      }
    }
  };

  const fetchReports = async () => {
    setIsLoadingReports(true);
    try {
      const response = await reportsAPI.getReports();
      setReports(response.data || []);
      setReportsError('');
    } catch (err) {
      setReportsError(err.response?.data?.detail || 'Saved reports could not be loaded. Please try again.');
    } finally {
      setIsLoadingReports(false);
    }
  };

  const fetchNotificationsList = async () => {
    setIsLoadingNotifications(true);
    try {
      const res = await notificationsAPI.getNotifications();
      setNotificationsList(res.data || []);
      setNotificationsError('');
    } catch (err) {
      setNotificationsError(err.response?.data?.detail || 'Notifications could not be loaded. Please try again.');
    } finally {
      setIsLoadingNotifications(false);
    }
  };

  const handleMarkNotificationRead = async (id) => {
    setNotificationActionId(id);
    setNotificationsMessage(null);
    try {
      await notificationsAPI.markAsRead(id);
      setNotificationsList((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setNotificationsMessage({ type: 'success', text: 'Notification marked as read.' });
      setNotificationsError('');
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch (err) {
      setNotificationsError(err.response?.data?.detail || 'Could not mark notification as read.');
    } finally {
      setNotificationActionId(null);
    }
  };

  const handleMarkAllNotificationsRead = async () => {
    setIsMarkingAllNotificationsRead(true);
    setNotificationsMessage(null);
    try {
      await notificationsAPI.markAllAsRead();
      setNotificationsList((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setNotificationsMessage({ type: 'success', text: 'All notifications marked as read.' });
      setNotificationsError('');
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch (err) {
      setNotificationsError(err.response?.data?.detail || 'Could not mark notifications as read.');
    } finally {
      setIsMarkingAllNotificationsRead(false);
    }
  };

  const handleDeleteNotificationFromList = async (id) => {
    setNotificationActionId(id);
    setNotificationsMessage(null);
    try {
      await notificationsAPI.deleteNotification(id);
      setNotificationsList((prev) => prev.filter((n) => n.id !== id));
      setNotificationsMessage({ type: 'success', text: 'Notification deleted.' });
      setNotificationsError('');
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch (err) {
      setNotificationsError(err.response?.data?.detail || 'Could not delete notification.');
    } finally {
      setNotificationActionId(null);
    }
  };

  const fetchGoals = async () => {
    setIsLoadingGoals(true);
    try {
      const res = await savingsGoalsAPI.getGoals();
      setGoals(res.data);
      setGoalsError('');
    } catch (err) {
      console.error('Error fetching savings goals:', err);
      setGoalsError(err.response?.data?.detail || 'Savings goals could not be loaded. Please try again.');
    } finally {
      setIsLoadingGoals(false);
    }
  };

  const fetchSummary = async () => {
    setIsLoadingSummary(true);
    try {
      const res = await dashboardAPI.getSummary();
      setSummaryData(res.data);
      setSummaryError('');
    } catch (err) {
      console.error('Error fetching dashboard summary:', err);
      setSummaryError(err.response?.data?.detail || 'Transactions could not be loaded. Please try again.');
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const fetchExpenses = async () => {
    setIsLoadingExpenses(true);
    try {
      const res = await expensesAPI.getExpenses();
      setExpenses(res.data);
      setExpensesError('');
    } catch (err) {
      console.error('Error fetching expenses:', err);
      setExpensesError(err.response?.data?.detail || 'Expenses could not be loaded. Please try again.');
    } finally {
      setIsLoadingExpenses(false);
    }
  };

  const fetchIncomes = async () => {
    setIsLoadingIncomes(true);
    try {
      const res = await incomesAPI.getIncomes();
      setIncomes(res.data);
      setIncomesError('');
    } catch (err) {
      console.error('Error fetching incomes:', err);
      setIncomesError(err.response?.data?.detail || 'Income could not be loaded. Please try again.');
    } finally {
      setIsLoadingIncomes(false);
    }
  };

  const fetchBudgetSummary = async (monthStr) => {
    setIsLoadingBudget(true);
    try {
      const target = monthStr ? `${monthStr}-01` : undefined;
      const res = await budgetsAPI.getBudgetSummary({ month: target });
      setBudgetSummary(res.data);
      setBudgetError('');
    } catch (err) {
      console.error('Error fetching budget summary:', err);
      setBudgetError(err.response?.data?.detail || 'Budgets could not be loaded. Please try again.');
    } finally {
      setIsLoadingBudget(false);
    }
  };

  // ----------------- EXPENSE HANDLERS -----------------
  const handleAddExpense = async (e) => {
    e.preventDefault();
    if (!expenseForm.category || !expenseForm.amount || !expenseForm.date) {
      setExpenseMsg({ type: 'error', text: 'Please fill in category, amount, and date.' });
      return;
    }
    if (parseFloat(expenseForm.amount) <= 0) {
      setExpenseMsg({ type: 'error', text: 'Amount must be greater than 0.' });
      return;
    }

    setIsAddingExpense(true);
    setExpenseMsg(null);
    try {
      const res = await expensesAPI.createExpense({
        category: expenseForm.category,
        description: expenseForm.description,
        amount: parseFloat(expenseForm.amount).toFixed(2),
        date: expenseForm.date,
      });
      setExpenseMsg({
        type: 'success',
        text: `Expense "${res.data.category} - ₹${res.data.amount}" saved successfully!`,
      });
      setExpenseForm({
        category: 'Food',
        description: '',
        amount: '',
        date: getLocalDateString(),
      });
      fetchExpenses();
      fetchSummary();
      fetchAnalytics();
      fetchBudgetSummary(selectedBudgetMonth);
      fetchNotificationsList();
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to create expense';
      setExpenseMsg({ type: 'error', text: errMsg });
    } finally {
      setIsAddingExpense(false);
    }
  };

  const startEditExpense = (exp) => {
    setEditingExpense(exp);
    setEditExpenseForm({
      category: exp.category,
      description: exp.description || '',
      amount: exp.amount,
      date: exp.date,
    });
    setEditExpenseMsg(null);
  };

  const handleUpdateExpense = async (e) => {
    e.preventDefault();
    if (!editExpenseForm.category || !editExpenseForm.amount || !editExpenseForm.date) {
      setEditExpenseMsg({ type: 'error', text: 'All required fields must be provided.' });
      return;
    }
    if (parseFloat(editExpenseForm.amount) <= 0) {
      setEditExpenseMsg({ type: 'error', text: 'Amount must be greater than 0.' });
      return;
    }

    setIsUpdatingExpense(true);
    setEditExpenseMsg(null);
    try {
      await expensesAPI.updateExpense(editingExpense.id, {
        category: editExpenseForm.category,
        description: editExpenseForm.description,
        amount: parseFloat(editExpenseForm.amount).toFixed(2),
        date: editExpenseForm.date,
      });
      setEditingExpense(null);
      setExpenseMsg({ type: 'success', text: `Expense #${editingExpense.id} updated successfully!` });
      fetchExpenses();
      fetchSummary();
      fetchAnalytics();
      fetchBudgetSummary(selectedBudgetMonth);
      fetchNotificationsList();
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to update expense';
      setEditExpenseMsg({ type: 'error', text: errMsg });
    } finally {
      setIsUpdatingExpense(false);
    }
  };

  const handleDeleteExpense = async (id) => {
    if (!window.confirm('Are you sure you want to delete this expense record?')) return;
    setDeletingExpenseId(id);
    try {
      await expensesAPI.deleteExpense(id);
      setExpenseMsg({ type: 'success', text: `Expense #${id} removed successfully.` });
      fetchExpenses();
      fetchSummary();
      fetchAnalytics();
      fetchBudgetSummary(selectedBudgetMonth);
    } catch (err) {
      setExpenseMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to delete expense.',
      });
    } finally {
      setDeletingExpenseId(null);
    }
  };

  // ----------------- INCOME HANDLERS -----------------
  const handleAddIncome = async (e) => {
    e.preventDefault();
    if (!incomeForm.source || !incomeForm.amount || !incomeForm.date) {
      setIncomeMsg({ type: 'error', text: 'Please fill in source, amount, and date.' });
      return;
    }
    if (parseFloat(incomeForm.amount) <= 0) {
      setIncomeMsg({ type: 'error', text: 'Amount must be greater than 0.' });
      return;
    }

    setIsAddingIncome(true);
    setIncomeMsg(null);
    try {
      const res = await incomesAPI.createIncome({
        source: incomeForm.source,
        description: incomeForm.description,
        amount: parseFloat(incomeForm.amount).toFixed(2),
        date: incomeForm.date,
      });
      setIncomeMsg({
        type: 'success',
        text: `Income "${res.data.source} - ₹${res.data.amount}" recorded successfully!`,
      });
      setIncomeForm({
        source: 'Pocket Money',
        description: '',
        amount: '',
        date: getLocalDateString(),
      });
      fetchIncomes();
      fetchSummary();
      fetchAnalytics();
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to record income';
      setIncomeMsg({ type: 'error', text: errMsg });
    } finally {
      setIsAddingIncome(false);
    }
  };

  const startEditIncome = (inc) => {
    setEditingIncome(inc);
    setEditIncomeForm({
      source: inc.source,
      description: inc.description || '',
      amount: inc.amount,
      date: inc.date,
    });
    setEditIncomeMsg(null);
  };

  const handleUpdateIncome = async (e) => {
    e.preventDefault();
    if (!editIncomeForm.source || !editIncomeForm.amount || !editIncomeForm.date) {
      setEditIncomeMsg({ type: 'error', text: 'All required fields must be provided.' });
      return;
    }
    if (parseFloat(editIncomeForm.amount) <= 0) {
      setEditIncomeMsg({ type: 'error', text: 'Amount must be greater than 0.' });
      return;
    }

    setIsUpdatingIncome(true);
    setEditIncomeMsg(null);
    try {
      await incomesAPI.updateIncome(editingIncome.id, {
        source: editIncomeForm.source,
        description: editIncomeForm.description,
        amount: parseFloat(editIncomeForm.amount).toFixed(2),
        date: editIncomeForm.date,
      });
      setEditingIncome(null);
      setIncomeMsg({ type: 'success', text: `Income #${editingIncome.id} updated successfully!` });
      fetchIncomes();
      fetchSummary();
      fetchAnalytics();
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to update income';
      setEditIncomeMsg({ type: 'error', text: errMsg });
    } finally {
      setIsUpdatingIncome(false);
    }
  };

  const handleDeleteIncome = async (id) => {
    if (!window.confirm('Are you sure you want to delete this income record?')) return;
    setDeletingIncomeId(id);
    try {
      await incomesAPI.deleteIncome(id);
      setIncomeMsg({ type: 'success', text: `Income #${id} removed successfully.` });
      fetchIncomes();
      fetchSummary();
      fetchAnalytics();
    } catch (err) {
      setIncomeMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to delete income.',
      });
    } finally {
      setDeletingIncomeId(null);
    }
  };

  // ----------------- BUDGET PLANNING HANDLERS -----------------
  const handleAddBudget = async (e) => {
    e.preventDefault();
    if (!budgetForm.category || !budgetForm.amount) {
      setBudgetMsg({ type: 'error', text: 'Please fill in category and amount.' });
      return;
    }
    if (parseFloat(budgetForm.amount) <= 0) {
      setBudgetMsg({ type: 'error', text: 'Budget amount must be greater than 0.' });
      return;
    }

    setIsAddingBudget(true);
    setBudgetMsg(null);
    try {
      const targetMonth = `${selectedBudgetMonth}-01`;
      await budgetsAPI.createBudget({
        category: budgetForm.category,
        amount: parseFloat(budgetForm.amount).toFixed(2),
        month: targetMonth,
      });
      setBudgetMsg({
        type: 'success',
        text: `Monthly budget for "${budgetForm.category}" allocated at ₹${budgetForm.amount}!`,
      });
      setBudgetForm({
        category: 'Food',
        amount: '',
        month: targetMonth,
      });
      fetchBudgetSummary(selectedBudgetMonth);
      fetchAnalytics();
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to allocate budget';
      setBudgetMsg({ type: 'error', text: errMsg });
    } finally {
      setIsAddingBudget(false);
    }
  };

  const startEditBudget = (catItem) => {
    setEditingBudget(catItem);
    setEditBudgetForm({
      category: catItem.category,
      amount: catItem.allocated_budget !== '0.00' ? catItem.allocated_budget : '',
      month: budgetSummary.month,
    });
    setEditBudgetMsg(null);
  };

  const handleUpdateBudget = async (e) => {
    e.preventDefault();
    if (!editBudgetForm.category || !editBudgetForm.amount) {
      setEditBudgetMsg({ type: 'error', text: 'Please enter category and amount.' });
      return;
    }
    if (parseFloat(editBudgetForm.amount) <= 0) {
      setEditBudgetMsg({ type: 'error', text: 'Amount must be greater than 0.' });
      return;
    }

    setIsUpdatingBudget(true);
    setEditBudgetMsg(null);
    try {
      if (editingBudget.budget_id) {
        // Update existing allocation
        await budgetsAPI.updateBudget(editingBudget.budget_id, {
          category: editBudgetForm.category,
          amount: parseFloat(editBudgetForm.amount).toFixed(2),
          month: editBudgetForm.month,
        });
      } else {
        // Create new allocation for this category
        await budgetsAPI.createBudget({
          category: editBudgetForm.category,
          amount: parseFloat(editBudgetForm.amount).toFixed(2),
          month: editBudgetForm.month,
        });
      }
      setEditingBudget(null);
      setBudgetMsg({ type: 'success', text: `Budget for "${editBudgetForm.category}" saved successfully!` });
      fetchBudgetSummary(selectedBudgetMonth);
      fetchAnalytics();
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to update budget allocation';
      setEditBudgetMsg({ type: 'error', text: errMsg });
    } finally {
      setIsUpdatingBudget(false);
    }
  };

  const handleDeleteBudget = async (id, category) => {
    if (!window.confirm(`Delete the ${category} budget allocation?`)) return;
    setDeletingBudgetId(id);
    try {
      await budgetsAPI.deleteBudget(id);
      setBudgetMsg({ type: 'success', text: `${category} budget allocation removed.` });
      fetchBudgetSummary(selectedBudgetMonth);
      fetchAnalytics();
    } catch (err) {
      setBudgetMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to delete budget allocation.',
      });
    } finally {
      setDeletingBudgetId(null);
    }
  };

  // ----------------- SAVINGS GOALS HANDLERS -----------------
  const handleAddGoal = async (e) => {
    e.preventDefault();
    if (!goalForm.name || !goalForm.target_amount) {
      setGoalMsg({ type: 'error', text: 'Please fill in goal name and target amount.' });
      return;
    }
    if (parseFloat(goalForm.target_amount) <= 0) {
      setGoalMsg({ type: 'error', text: 'Target amount must be greater than 0.' });
      return;
    }

    setIsAddingGoal(true);
    setGoalMsg(null);
    try {
      const payload = {
        name: goalForm.name,
        target_amount: parseFloat(goalForm.target_amount).toFixed(2),
        current_amount: goalForm.current_amount ? parseFloat(goalForm.current_amount).toFixed(2) : '0.00',
        target_date: goalForm.target_date || null,
      };
      const res = await savingsGoalsAPI.createGoal(payload);
      setGoalMsg({
        type: 'success',
        text: `Savings goal "${res.data.name}" created successfully!`,
      });
      setGoalForm({
        name: '',
        target_amount: '',
        current_amount: '0.00',
        target_date: '',
      });
      fetchGoals();
      fetchAnalytics();
      fetchNotificationsList();
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to create savings goal';
      setGoalMsg({ type: 'error', text: errMsg });
    } finally {
      setIsAddingGoal(false);
    }
  };

  const startEditGoal = (goal) => {
    setEditingGoal(goal);
    setEditGoalForm({
      name: goal.name,
      target_amount: goal.target_amount,
      current_amount: goal.current_amount,
      target_date: goal.target_date || '',
    });
    setEditGoalMsg(null);
  };

  const handleUpdateGoal = async (e) => {
    e.preventDefault();
    if (!editGoalForm.name || !editGoalForm.target_amount) {
      setEditGoalMsg({ type: 'error', text: 'Goal name and target amount are required.' });
      return;
    }
    if (parseFloat(editGoalForm.target_amount) <= 0) {
      setEditGoalMsg({ type: 'error', text: 'Target amount must be greater than 0.' });
      return;
    }

    setIsUpdatingGoal(true);
    setEditGoalMsg(null);
    try {
      await savingsGoalsAPI.updateGoal(editingGoal.id, {
        name: editGoalForm.name,
        target_amount: parseFloat(editGoalForm.target_amount).toFixed(2),
        current_amount: editGoalForm.current_amount ? parseFloat(editGoalForm.current_amount).toFixed(2) : '0.00',
        target_date: editGoalForm.target_date || null,
      });
      setEditingGoal(null);
      setGoalMsg({ type: 'success', text: `Savings goal "${editGoalForm.name}" updated successfully!` });
      fetchGoals();
      fetchAnalytics();
      fetchNotificationsList();
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to update goal';
      setEditGoalMsg({ type: 'error', text: errMsg });
    } finally {
      setIsUpdatingGoal(false);
    }
  };

  const startDeposit = (goal) => {
    setDepositGoal(goal);
    setDepositAmount('');
    setDepositMsg(null);
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    if (!depositAmount || parseFloat(depositAmount) <= 0) {
      setDepositMsg({ type: 'error', text: 'Please enter a valid deposit amount greater than 0.' });
      return;
    }

    setIsDepositing(true);
    setDepositMsg(null);
    try {
      const newCurrentAmount = (parseFloat(depositGoal.current_amount) + parseFloat(depositAmount)).toFixed(2);
      await savingsGoalsAPI.patchGoal(depositGoal.id, {
        current_amount: newCurrentAmount,
      });
      setDepositGoal(null);
      setGoalMsg({
        type: 'success',
        text: `Successfully added ₹${parseFloat(depositAmount).toFixed(2)} to "${depositGoal.name}"!`,
      });
      fetchGoals();
      fetchAnalytics();
      fetchNotificationsList();
      window.dispatchEvent(new Event('notifications:refresh'));
    } catch (err) {
      const errMsg = err.response?.data
        ? typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
              .join(' | ')
          : JSON.stringify(err.response.data)
        : 'Failed to add funds to goal';
      setDepositMsg({ type: 'error', text: errMsg });
    } finally {
      setIsDepositing(false);
    }
  };

  const handleReportDownload = async (format) => {
    setExportingReport(format);
    setReportMessage(null);
    try {
      const month = analyticsMonth;
      const generated = await reportsAPI.generateReport({ month });
      const response = await reportsAPI.exportReport(generated.data.id, format);
      const contentDisposition = response.headers['content-disposition'] || '';
      const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
      const filename = filenameMatch?.[1] || `BudgetBuddy_Financial_Report_${month}.${format === 'xlsx' ? 'xlsx' : 'pdf'}`;
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      await fetchReports();
      fetchNotificationsList();
      window.dispatchEvent(new Event('notifications:refresh'));
      setReportMessage({ type: 'success', text: `Your ${month} report was generated and downloaded.` });
    } catch (err) {
      setReportMessage({
        type: 'error',
        text: err.response?.data?.month?.[0] || err.response?.data?.detail || `Could not generate the ${format.toUpperCase()} report. Please try again.`,
      });
    } finally {
      setExportingReport(null);
    }
  };

  const handleSavedReportDownload = async (reportId, format) => {
    setExportingReport(`${reportId}-${format}`);
    setReportMessage(null);
    try {
      const response = await reportsAPI.exportReport(reportId, format);
      const extension = format === 'xlsx' ? 'xlsx' : 'pdf';
      const filenameMatch = (response.headers['content-disposition'] || '').match(/filename="?([^";]+)"?/i);
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = filenameMatch?.[1] || `BudgetBuddy_Report_${reportId}.${extension}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setReportMessage({ type: 'success', text: 'Saved report downloaded.' });
    } catch (err) {
      setReportMessage({
        type: 'error',
        text: err.response?.data?.detail || `Could not download the saved ${format.toUpperCase()} report.`,
      });
    } finally {
      setExportingReport(null);
    }
  };

  const handleDeleteGoal = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete the savings goal "${name}"?`)) return;
    setDeletingGoalId(id);
    try {
      await savingsGoalsAPI.deleteGoal(id);
      setGoalMsg({ type: 'success', text: `Savings goal "${name}" removed.` });
      fetchGoals();
      fetchAnalytics();
    } catch (err) {
      setGoalMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to delete savings goal.',
      });
    } finally {
      setDeletingGoalId(null);
    }
  };

  // API Tester handler
  const handleTestEndpoint = async (endpointName, apiCall) => {
    setIsLoadingApi(true);
    setActiveEndpoint(endpointName);
    setApiResponse(null);
    setApiStatus(null);
    try {
      const res = await apiCall();
      setApiStatus({ code: res.status, text: res.statusText || 'OK', success: true });
      setApiResponse(res.data);
    } catch (err) {
      const status = err.response?.status || 500;
      setApiStatus({
        code: status,
        text: err.response?.statusText || 'Error',
        success: false,
      });
      setApiResponse(err.response?.data || { error: err.message });
    } finally {
      setIsLoadingApi(false);
    }
  };

  // Filtered lists
  const filteredExpenses = expenses.filter((exp) => {
    if (selectedCategoryFilter === 'ALL') return true;
    return exp.category === selectedCategoryFilter;
  });

  const filteredIncomes = incomes.filter((inc) => {
    if (selectedSourceFilter === 'ALL') return true;
    return inc.source === selectedSourceFilter;
  });

  const filteredNotifications = notificationsList.filter((notif) => {
    if (selectedNotifFilter === 'ALL') return true;
    if (selectedNotifFilter === 'UNREAD') return !notif.is_read;
    return notif.notification_type === selectedNotifFilter;
  });

  // Dynamic calculations for Hero
  const getGreeting = () => {
    const hr = new Date().getHours();
    if (hr < 12) return 'Good morning';
    if (hr < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const savingsSummary = analyticsOverview?.savings_goals;
  const categorySpending = (analyticsOverview?.categories || []).map((item) => {
    return {
      category: item.category,
      raw_total: Number(item.raw_total || 0),
      percentage: Number(item.percentage || 0),
      color: CATEGORY_COLORS[item.category] || '#64748b',
    };
  });
  const hasAnalyticsData = Boolean(analyticsOverview && (
    analyticsOverview.income_count > 0
    || analyticsOverview.expense_count > 0
    || Number(savingsSummary?.total_goals_count || 0) > 0
    || Number(analyticsOverview.budget?.total_budgeted || 0) > 0
    || analyticsTrends.some((trend) => Number(trend.raw_income) > 0 || Number(trend.raw_expenses) > 0)
  ));

  const handleOverviewNavigation = (tab) => {
    if (tab === 'refresh') {
      refreshAllData();
      return;
    }
    setSearchQuery('');
    navigate(`/dashboard#${tab}`);
  };

  const moduleTitles = {
    expenses: 'Expense Tracking',
    incomes: 'Income Management',
    budgets: 'Budget Planning',
    savings: 'Savings Goals',
    activity: 'Recent Activity',
    notifications: 'Notifications',
    reports: 'Financial Reports',
  };

  if (activeTab === 'overview') {
    return (
      <DashboardOverview
        user={user}
        greeting={getGreeting()}
        overview={analyticsOverview}
        trends={analyticsTrends}
        categories={categorySpending}
        analyticsMonth={analyticsMonth}
        onAnalyticsMonthChange={setAnalyticsMonth}
        transactions={summaryData.recent_transactions || []}
        notifications={notificationsList}
        goals={goals}
        budgetSummary={budgetSummary}
        isLoadingAnalytics={isLoadingAnalytics}
        analyticsError={analyticsError}
        isLoadingSummary={isLoadingSummary}
        summaryError={summaryError}
        isLoadingNotifications={isLoadingNotifications}
        notificationsError={notificationsError}
        notificationsMessage={notificationsMessage}
        isLoadingGoals={isLoadingGoals}
        goalsError={goalsError}
        isLoadingBudget={isLoadingBudget}
        budgetError={budgetError}
        onNavigate={handleOverviewNavigation}
        onReadNotification={(notification) => !notification.is_read && handleMarkNotificationRead(notification.id)}
        onMarkAllRead={handleMarkAllNotificationsRead}
        isMarkingAllRead={isMarkingAllNotificationsRead}
        searchQuery={searchQuery}
        onSearch={setSearchQuery}
        onReportDownload={handleReportDownload}
        onTransactionsImported={() => refreshAllData()}
        exportingReport={exportingReport}
        reportMessage={reportMessage}
      />
    );
  }

  return (
    <div className="dashboard-container module-only">
      <section className="module-page-heading">
        <div>
          <h1>{moduleTitles[activeTab] || 'BudgetBuddy'}</h1>
          <p>Manage your personal finances</p>
        </div>
        <button type="button" className="btn-icon-refresh" onClick={refreshAllData} title="Refresh dashboard data">
          <RefreshCw size={16} />
          <span>Refresh</span>
        </button>
      </section>
      {/* Header Banner */}
      <div className="dashboard-header">
        <div className="header-text">
          <h1>
            {getGreeting()}, <span className="text-primary">{user?.username}</span>!
          </h1>
          <p className="header-subtitle">
            BudgetBuddy Financial Hub — Track Expenses, Incomes, Budgets & Savings Targets
          </p>
        </div>
        <div className="status-badge-group">
          <div className="report-export-actions" aria-label="Report downloads">
            <button
              type="button"
              className="btn-report-export"
              onClick={() => handleReportDownload('pdf')}
              disabled={Boolean(exportingReport)}
              title="Download current month PDF report"
            >
              <FileDown size={14} />
              <span>{exportingReport === 'pdf' ? 'PDF...' : 'PDF'}</span>
            </button>
            <button
              type="button"
              className="btn-report-export"
              onClick={() => handleReportDownload('xlsx')}
              disabled={Boolean(exportingReport)}
              title="Download current month Excel report"
            >
              <FileSpreadsheet size={14} />
              <span>{exportingReport === 'xlsx' ? 'Excel...' : 'Excel'}</span>
            </button>
          </div>
        </div>
      </div>

      <section className="analytics-controls" aria-label="Analytics period">
        <div>
          <h2>Financial Analytics</h2>
          <p>{analyticsOverview?.filter_applied || 'Monthly overview from your saved transactions'}</p>
          <CurrentDateDisplay />
        </div>
        <div className="analytics-period-actions">
          <label htmlFor="analytics-month">Period</label>
          <input
            id="analytics-month"
            type="month"
            value={analyticsMonth}
            onChange={(event) => setAnalyticsMonth(event.target.value)}
          />
          <button type="button" onClick={() => fetchAnalytics()} disabled={isLoadingAnalytics}>
            <RefreshCw size={15} className={isLoadingAnalytics ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </section>

      {analyticsError && (
        <div className="analytics-error" role="alert">
          <AlertTriangle size={18} />
          <span>{analyticsError}</span>
          <button type="button" onClick={() => fetchAnalytics()}>Retry</button>
        </div>
      )}

      {isLoadingAnalytics && !analyticsOverview && (
        <div className="analytics-loading" role="status">
          <span className="spinner-sm" /> Loading your financial analytics...
        </div>
      )}

      {analyticsOverview && !hasAnalyticsData && !analyticsError && (
        <div className="analytics-empty-notice" role="status">
          No income, expenses, budgets, or savings goals are recorded for this account yet. Add a transaction or savings goal to populate analytics.
        </div>
      )}

      <div className="analytics-dashboard-grid mb-6">
        <IncomeExpenseSummary overview={analyticsOverview} loading={isLoadingAnalytics} error={analyticsError} />
        <CategorySpendingSection categories={categorySpending} loading={isLoadingAnalytics} error={analyticsError} />
        <MonthlyTrendsSection trends={analyticsTrends} loading={isLoadingAnalytics} error={analyticsError} />
        <div className="analytics-summary-stack">
          <FinancialSummarySection overview={analyticsOverview} loading={isLoadingAnalytics} error={analyticsError} />
          <SavingsProgressSection overview={analyticsOverview} loading={isLoadingAnalytics} error={analyticsError} />
        </div>
      </div>

      {/* Navigation Tabs for Modules */}
      <div className="module-tabs mb-6">
        <button
          className={`module-tab ${activeTab === 'expenses' ? 'active' : ''}`}
          onClick={() => setActiveTab('expenses')}
        >
          <TrendingDown size={17} />
          <span>Expense Tracking ({expenses.length})</span>
        </button>

        <button
          className={`module-tab ${activeTab === 'incomes' ? 'active' : ''}`}
          onClick={() => setActiveTab('incomes')}
        >
          <TrendingUp size={17} />
          <span>Income Management ({incomes.length})</span>
        </button>

        <button
          className={`module-tab ${activeTab === 'budgets' ? 'active' : ''}`}
          onClick={() => setActiveTab('budgets')}
        >
          <Target size={17} />
          <span>Budget Planning</span>
        </button>

        <button
          className={`module-tab ${activeTab === 'savings' ? 'active' : ''}`}
          onClick={() => setActiveTab('savings')}
        >
          <PiggyBank size={17} />
          <span>Savings Goals ({goals.length})</span>
        </button>

        <button
          className={`module-tab ${activeTab === 'activity' ? 'active' : ''}`}
          onClick={() => setActiveTab('activity')}
        >
          <Calendar size={17} />
          <span>Recent Activity ({summaryData.recent_transactions?.length || 0})</span>
        </button>

        <button
          className={`module-tab ${activeTab === 'notifications' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('notifications');
            fetchNotificationsList();
          }}
        >
          <Bell size={17} />
          <span>
            Notifications {notificationsList.filter((n) => !n.is_read).length > 0 && `(${notificationsList.filter((n) => !n.is_read).length})`}
          </span>
        </button>

        <button
          className={`module-tab ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          <FileText size={17} />
          <span>Reports</span>
        </button>
      </div>

      {/* ===================== TAB 1: EXPENSE MANAGEMENT ===================== */}
      {activeTab === 'expenses' && (
        <div id="dashboard-module" className="card">
          <div className="card-header">
            <div className="card-title">
              <TrendingDown className="card-icon text-danger" size={20} />
              <h3>Expense Tracking & Categorization</h3>
            </div>
            <button onClick={refreshAllData} className="btn-icon-refresh" title="Refresh records">
              <RefreshCw size={16} className={isLoadingExpenses ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
          <div className="card-body">
            {expenseMsg && (
              <div className={`alert alert-${expenseMsg.type} mb-4`}>
                {expenseMsg.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                <span>{expenseMsg.text}</span>
              </div>
            )}
            {expensesError && (
              <div className="overview-inline-error mb-4" role="alert">
                <span>{expensesError}</span>
                <button type="button" onClick={fetchExpenses}>Retry</button>
              </div>
            )}

            {/* Add Expense Form */}
            <form onSubmit={handleAddExpense} className="expense-quick-form mb-6">
              <h4>
                <PlusCircle size={16} className="inline mr-1 text-primary" /> Add New Expense
              </h4>
              <div className="form-row">
                <div className="form-group col">
                  <label>Category (Required)</label>
                  <select
                    value={expenseForm.category}
                    onChange={(e) => setExpenseForm({ ...expenseForm, category: e.target.value })}
                    required
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group col">
                  <label>Amount (₹ Required)</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    value={expenseForm.amount}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                        setExpenseForm({ ...expenseForm, amount: val });
                      }
                    }}
                    required
                  />
                </div>

                <div className="form-group col">
                  <label>Date (Required)</label>
                  <input
                    type="date"
                    value={expenseForm.date}
                    onChange={(e) => setExpenseForm({ ...expenseForm, date: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group col-wide">
                  <label>Description (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Lunch with study group"
                    value={expenseForm.description}
                    onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })}
                  />
                </div>

                <div className="form-group col-btn">
                  <label>&nbsp;</label>
                  <button type="submit" className="btn-primary" disabled={isAddingExpense}>
                    {isAddingExpense ? <span className="spinner-sm"></span> : <PlusCircle size={16} />}
                    <span>Add Expense</span>
                  </button>
                </div>
              </div>
            </form>

            {/* Filter Bar */}
            <div className="filter-bar mb-4">
              <div className="filter-label">
                <Filter size={15} />
                <span>Filter by Category:</span>
              </div>
              <div className="filter-pills">
                <button
                  className={`filter-pill ${selectedCategoryFilter === 'ALL' ? 'active' : ''}`}
                  onClick={() => setSelectedCategoryFilter('ALL')}
                >
                  All ({expenses.length})
                </button>
                {CATEGORIES.map((cat) => {
                  const count = expenses.filter((e) => e.category === cat).length;
                  return (
                    <button
                      key={cat}
                      className={`filter-pill ${selectedCategoryFilter === cat ? 'active' : ''}`}
                      onClick={() => setSelectedCategoryFilter(cat)}
                    >
                      {getCategoryIcon(cat)}
                      <span>{cat} ({count})</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Daily Expense History Table */}
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Date</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoadingExpenses ? (
                    <tr>
                      <td colSpan="6" className="text-center py-6">
                        <span className="spinner-sm"></span> Loading expense history...
                      </td>
                    </tr>
                  ) : expensesError && expenses.length === 0 ? (
                    <tr><td colSpan="6" className="text-center py-6 text-danger">Expense history is unavailable. Retry the request above.</td></tr>
                  ) : filteredExpenses.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center py-6 text-muted">
                        No expense records found. Add your first expense above!
                      </td>
                    </tr>
                  ) : (
                    filteredExpenses.map((exp) => (
                      <tr key={exp.id}>
                        <td className="font-mono text-muted">#{exp.id}</td>
                        <td>
                          <span className="date-badge">
                            <Calendar size={13} className="inline mr-1" />
                            {exp.date}
                          </span>
                        </td>
                        <td>
                          <span className={`category-badge cat-${exp.category.toLowerCase()}`}>
                            {getCategoryIcon(exp.category)}
                            <span>{exp.category}</span>
                          </span>
                        </td>
                        <td className="expense-desc">{exp.description || <span className="text-muted italic">No description</span>}</td>
                        <td className="font-semibold text-danger">-₹{parseFloat(exp.amount).toFixed(2)}</td>
                        <td className="text-right">
                          <div className="action-buttons-group">
                            <button
                              onClick={() => startEditExpense(exp)}
                              className="btn-action btn-edit"
                              title="Edit Expense"
                            >
                              <Edit2 size={14} />
                              <span>Edit</span>
                            </button>
                            <button
                              onClick={() => handleDeleteExpense(exp.id)}
                              disabled={deletingExpenseId === exp.id}
                              className="btn-action btn-delete"
                              title="Delete Expense"
                            >
                              {deletingExpenseId === exp.id ? (
                                <span className="spinner-sm"></span>
                              ) : (
                                <Trash2 size={14} />
                              )}
                              <span>Delete</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ===================== TAB 2: INCOME MANAGEMENT ===================== */}
      {activeTab === 'incomes' && (
        <div id="dashboard-module" className="card">
          <div className="card-header">
            <div className="card-title">
              <TrendingUp className="card-icon text-success" size={20} />
              <h3>Income Recording & Management</h3>
            </div>
            <button onClick={refreshAllData} className="btn-icon-refresh" title="Refresh records">
              <RefreshCw size={16} className={isLoadingIncomes ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
          <div className="card-body">
            {incomeMsg && (
              <div className={`alert alert-${incomeMsg.type} mb-4`}>
                {incomeMsg.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                <span>{incomeMsg.text}</span>
              </div>
            )}
            {incomesError && (
              <div className="overview-inline-error mb-4" role="alert">
                <span>{incomesError}</span>
                <button type="button" onClick={fetchIncomes}>Retry</button>
              </div>
            )}

            {/* Add Income Form */}
            <form onSubmit={handleAddIncome} className="expense-quick-form form-income-theme mb-6">
              <h4>
                <PlusCircle size={16} className="inline mr-1 text-success" /> Record New Income
              </h4>
              <div className="form-row">
                <div className="form-group col">
                  <label>Income Source (Required)</label>
                  <select
                    value={incomeForm.source}
                    onChange={(e) => setIncomeForm({ ...incomeForm, source: e.target.value })}
                    required
                  >
                    {INCOME_SOURCES.map((src) => (
                      <option key={src} value={src}>
                        {src}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group col">
                  <label>Amount (₹ Required)</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    value={incomeForm.amount}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                        setIncomeForm({ ...incomeForm, amount: val });
                      }
                    }}
                    required
                  />
                </div>

                <div className="form-group col">
                  <label>Date (Required)</label>
                  <input
                    type="date"
                    value={incomeForm.date}
                    onChange={(e) => setIncomeForm({ ...incomeForm, date: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group col-wide">
                  <label>Description / Details (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Monthly allowance from parents"
                    value={incomeForm.description}
                    onChange={(e) => setIncomeForm({ ...incomeForm, description: e.target.value })}
                  />
                </div>

                <div className="form-group col-btn">
                  <label>&nbsp;</label>
                  <button type="submit" className="btn-primary btn-success-action" disabled={isAddingIncome}>
                    {isAddingIncome ? <span className="spinner-sm"></span> : <PlusCircle size={16} />}
                    <span>Record Income</span>
                  </button>
                </div>
              </div>
            </form>

            {/* Source Filter Bar */}
            <div className="filter-bar mb-4">
              <div className="filter-label">
                <Filter size={15} />
                <span>Filter by Source:</span>
              </div>
              <div className="filter-pills">
                <button
                  className={`filter-pill ${selectedSourceFilter === 'ALL' ? 'active' : ''}`}
                  onClick={() => setSelectedSourceFilter('ALL')}
                >
                  All ({incomes.length})
                </button>
                {INCOME_SOURCES.map((src) => {
                  const count = incomes.filter((i) => i.source === src).length;
                  return (
                    <button
                      key={src}
                      className={`filter-pill ${selectedSourceFilter === src ? 'active' : ''}`}
                      onClick={() => setSelectedSourceFilter(src)}
                    >
                      {getSourceIcon(src)}
                      <span>{src} ({count})</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Income History Table */}
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Date</th>
                    <th>Source</th>
                    <th>Description / Details</th>
                    <th>Amount</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoadingIncomes ? (
                    <tr>
                      <td colSpan="6" className="text-center py-6">
                        <span className="spinner-sm"></span> Loading income history...
                      </td>
                    </tr>
                  ) : incomesError && incomes.length === 0 ? (
                    <tr><td colSpan="6" className="text-center py-6 text-danger">Income history is unavailable. Retry the request above.</td></tr>
                  ) : filteredIncomes.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center py-6 text-muted">
                        No income records found. Record your first income above!
                      </td>
                    </tr>
                  ) : (
                    filteredIncomes.map((inc) => (
                      <tr key={inc.id}>
                        <td className="font-mono text-muted">#{inc.id}</td>
                        <td>
                          <span className="date-badge">
                            <Calendar size={13} className="inline mr-1" />
                            {inc.date}
                          </span>
                        </td>
                        <td>
                          <span className={`category-badge src-${inc.source.toLowerCase().replace(/\s+/g, '-')}`}>
                            {getSourceIcon(inc.source)}
                            <span>{inc.source}</span>
                          </span>
                        </td>
                        <td className="expense-desc">{inc.description || <span className="text-muted italic">No details</span>}</td>
                        <td className="font-semibold text-success">+₹{parseFloat(inc.amount).toFixed(2)}</td>
                        <td className="text-right">
                          <div className="action-buttons-group">
                            <button
                              onClick={() => startEditIncome(inc)}
                              className="btn-action btn-edit"
                              title="Edit Income"
                            >
                              <Edit2 size={14} />
                              <span>Edit</span>
                            </button>
                            <button
                              onClick={() => handleDeleteIncome(inc.id)}
                              disabled={deletingIncomeId === inc.id}
                              className="btn-action btn-delete"
                              title="Delete Income"
                            >
                              {deletingIncomeId === inc.id ? (
                                <span className="spinner-sm"></span>
                              ) : (
                                <Trash2 size={14} />
                              )}
                              <span>Delete</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ===================== TAB 3: BUDGET PLANNING SYSTEM ===================== */}
      {activeTab === 'budgets' && (
        <div id="dashboard-module" className="card">
          <div className="card-header">
            <div className="card-title">
              <Target className="card-icon text-indigo" size={20} />
              <h3>Monthly Budget Planning & Allocation</h3>
            </div>
            <div className="flex items-center gap-3">
              <div className="month-picker-wrapper">
                <Calendar size={15} className="text-muted" />
                <input
                  type="month"
                  value={selectedBudgetMonth}
                  onChange={(e) => setSelectedBudgetMonth(e.target.value)}
                  className="month-input"
                />
              </div>
              <button onClick={() => fetchBudgetSummary(selectedBudgetMonth)} className="btn-icon-refresh" title="Refresh">
                <RefreshCw size={16} className={isLoadingBudget ? 'spin' : ''} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
          <div className="card-body">
            {budgetMsg && (
              <div className={`alert alert-${budgetMsg.type} mb-4`}>
                {budgetMsg.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                <span>{budgetMsg.text}</span>
              </div>
            )}
            {budgetError && (
              <div className="overview-inline-error mb-4" role="alert">
                <span>{budgetError}</span>
                <button type="button" onClick={() => fetchBudgetSummary(selectedBudgetMonth)}>Retry</button>
              </div>
            )}

            {/* Budget Month Summary Overview Banner */}
            <div className="budget-overview-banner mb-6">
              <div className="b-stat">
                <span className="b-stat-title">Month Plan</span>
                <span className="b-stat-val text-primary font-bold">{budgetSummary.month_label || selectedBudgetMonth}</span>
              </div>
              <div className="b-stat">
                <span className="b-stat-title">Total Allocated Budget</span>
                <span className="b-stat-val text-indigo font-bold">₹{budgetSummary.total_budget}</span>
              </div>
              <div className="b-stat">
                <span className="b-stat-title">Total Actual Spent</span>
                <span className="b-stat-val text-danger font-bold">₹{budgetSummary.total_spent}</span>
              </div>
              <div className="b-stat">
                <span className="b-stat-title">Remaining Budget</span>
                <span className={`b-stat-val font-bold ${parseFloat(budgetSummary.total_remaining) >= 0 ? 'text-success' : 'text-danger'}`}>
                  ₹{budgetSummary.total_remaining}
                </span>
              </div>
            </div>

            {/* Allocate Category Budget Form */}
            <form onSubmit={handleAddBudget} className="expense-quick-form form-budget-theme mb-6">
              <h4>
                <PlusCircle size={16} className="inline mr-1 text-primary" /> Set Monthly Category Budget
              </h4>
              <div className="form-row">
                <div className="form-group col">
                  <label>Category (Required)</label>
                  <select
                    value={budgetForm.category}
                    onChange={(e) => setBudgetForm({ ...budgetForm, category: e.target.value })}
                    required
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group col">
                  <label>Monthly Budget Amount (₹ Required)</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    value={budgetForm.amount}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                        setBudgetForm({ ...budgetForm, amount: val });
                      }
                    }}
                    required
                  />
                </div>

                <div className="form-group col-btn">
                  <label>&nbsp;</label>
                  <button type="submit" className="btn-primary" disabled={isAddingBudget}>
                    {isAddingBudget ? <span className="spinner-sm"></span> : <Target size={16} />}
                    <span>Save Budget</span>
                  </button>
                </div>
              </div>
            </form>

            {/* Category-Wise Budget Allocations & Utilization Grid */}
            <h4 className="section-subtitle mb-3">Category-Wise Budget Utilization ({budgetSummary.month_label})</h4>
            <div className="budget-cards-grid">
              {isLoadingBudget ? (
                <div className="col-span-full text-center py-6">
                  <span className="spinner-sm"></span> Loading category budget allocations...
                </div>
              ) : budgetError ? (
                <div className="col-span-full text-center py-6 text-danger" role="alert">
                  Budget allocations are unavailable. Retry the request above.
                </div>
              ) : (
                budgetSummary.categories.map((catItem) => {
                  const hasAllocation = parseFloat(catItem.allocated_budget) > 0;
                  const util = catItem.utilization_percentage;
                  const isOver = catItem.is_over_budget;

                  return (
                    <div key={catItem.category} className={`budget-card ${isOver ? 'border-over' : hasAllocation ? 'border-allocated' : ''}`}>
                      <div className="b-card-top">
                        <div className="b-cat-header">
                          <span className={`category-badge cat-${catItem.category.toLowerCase()}`}>
                            {getCategoryIcon(catItem.category)}
                            <span>{catItem.category}</span>
                          </span>
                          {hasAllocation && (
                            <span className={`util-badge ${isOver ? 'badge-danger' : util >= 80 ? 'badge-warning' : 'badge-success'}`}>
                              {isOver ? 'Over Budget' : `${util}% used`}
                            </span>
                          )}
                        </div>
                        <div className="b-card-actions">
                          <button
                            onClick={() => startEditBudget(catItem)}
                            className="btn-action btn-edit"
                            title="Edit or Set Budget"
                          >
                            <Edit2 size={12} />
                            <span>{hasAllocation ? 'Edit' : 'Set'}</span>
                          </button>
                          {catItem.budget_id && (
                            <button
                              onClick={() => handleDeleteBudget(catItem.budget_id, catItem.category)}
                              disabled={deletingBudgetId === catItem.budget_id}
                              className="btn-action btn-delete"
                              title="Delete Allocation"
                            >
                              <Trash2 size={12} />
                            </button>
                          )}
                        </div>
                      </div>

                      <div className="b-card-metrics mt-3">
                        <div className="b-metric-row">
                          <span className="text-muted text-xs">Allocated:</span>
                          <span className="font-semibold">{hasAllocation ? `₹${catItem.allocated_budget}` : 'Not Set'}</span>
                        </div>
                        <div className="b-metric-row">
                          <span className="text-muted text-xs">Spent:</span>
                          <span className="font-semibold text-danger">₹{catItem.actual_spent}</span>
                        </div>
                        <div className="b-metric-row">
                          <span className="text-muted text-xs">Remaining:</span>
                          <span className={`font-semibold ${parseFloat(catItem.remaining_budget) >= 0 ? 'text-success' : 'text-danger'}`}>
                            ₹{catItem.remaining_budget}
                          </span>
                        </div>
                      </div>

                      {/* Utilization Progress Bar */}
                      {hasAllocation && (
                        <div className="progress-container mt-3">
                          <div className="progress-bar-bg">
                            <div
                              className={`progress-bar-fill ${isOver ? 'fill-danger' : util >= 80 ? 'fill-warning' : 'fill-normal'}`}
                              style={{ width: `${Math.min(util, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* ===================== TAB 4: SAVINGS GOALS MANAGEMENT ===================== */}
      {activeTab === 'savings' && (
        <div id="dashboard-module" className="card">
          <div className="card-header">
            <div className="card-title">
              <PiggyBank className="card-icon text-primary" size={20} />
              <h3>Savings Goal Management & Progress Tracking</h3>
            </div>
            <button onClick={refreshAllData} className="btn-icon-refresh" title="Refresh goals">
              <RefreshCw size={16} className={isLoadingGoals ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
          <div className="card-body">
            {goalMsg && (
              <div className={`alert alert-${goalMsg.type} mb-4`}>
                {goalMsg.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                <span>{goalMsg.text}</span>
              </div>
            )}
            {goalsError && (
              <div className="overview-inline-error mb-4" role="alert">
                <span>{goalsError}</span>
                <button type="button" onClick={fetchGoals}>Retry</button>
              </div>
            )}

            {/* Add Savings Goal Quick Form */}
            <form onSubmit={handleAddGoal} className="expense-quick-form mb-6">
              <h4>
                <PlusCircle size={16} className="inline mr-1 text-primary" /> Create New Savings Goal
              </h4>
              <div className="form-row">
                <div className="form-group col">
                  <label>Goal Name (Required)</label>
                  <input
                    type="text"
                    placeholder="e.g., Laptop, Emergency Fund, Trip"
                    value={goalForm.name}
                    onChange={(e) => setGoalForm({ ...goalForm, name: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group col">
                  <label>Target Amount (₹ Required)</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="50000.00"
                    value={goalForm.target_amount}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                        setGoalForm({ ...goalForm, target_amount: val });
                      }
                    }}
                    required
                  />
                </div>

                <div className="form-group col">
                  <label>Initial Saved (₹ Optional)</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    value={goalForm.current_amount}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                        setGoalForm({ ...goalForm, current_amount: val });
                      }
                    }}
                  />
                </div>

                <div className="form-group col">
                  <label>Target Date (Optional)</label>
                  <input
                    type="date"
                    value={goalForm.target_date}
                    onChange={(e) => setGoalForm({ ...goalForm, target_date: e.target.value })}
                  />
                </div>

                <div className="form-group col-btn">
                  <label>&nbsp;</label>
                  <button type="submit" className="btn-primary" disabled={isAddingGoal}>
                    {isAddingGoal ? <span className="spinner-sm"></span> : <PlusCircle size={16} />}
                    <span>Create Goal</span>
                  </button>
                </div>
              </div>
            </form>

            {/* Savings Goals Grid */}
            <h4 className="section-subtitle mb-3">Your Savings Goals ({goals.length})</h4>
            <div className="goal-cards-grid">
              {isLoadingGoals ? (
                <div className="col-span-full text-center py-6">
                  <span className="spinner-sm"></span> Loading savings goals...
                </div>
              ) : goals.length === 0 ? (
                <div className="col-span-full text-center py-6 text-muted">
                  No savings goals created yet. Set a target amount above to begin tracking your savings progress!
                </div>
              ) : (
                goals.map((goal) => {
                  const isDone = goal.is_completed;
                  const progressPct = goal.progress_percentage || 0;

                  return (
                    <div
                      key={goal.id}
                      className={`goal-card ${isDone ? 'border-completed' : 'border-inprogress'}`}
                    >
                      <div className="g-card-top">
                        <div className="g-title-group">
                          <div className="g-goal-name">{goal.name}</div>
                          {goal.target_date && (
                            <span className="g-target-date">
                              <Calendar size={12} /> Target: {goal.target_date}
                            </span>
                          )}
                        </div>
                        <span className={`badge ${isDone ? 'badge-success' : 'badge-jwt'}`}>
                          {isDone ? (
                            <>
                              <CheckCircle2 size={13} /> Completed
                            </>
                          ) : (
                            <>
                              <Target size={13} /> In Progress
                            </>
                          )}
                        </span>
                      </div>

                      {isDone && (
                        <div className="goal-celebration-badge">
                          <Sparkles size={12} /> Target Achieved! 🏆
                        </div>
                      )}

                      <div className="g-card-metrics mt-3">
                        <div className="g-metric-row">
                          <span className="text-muted text-xs">Target Amount:</span>
                          <span className="font-semibold">₹{parseFloat(goal.target_amount).toFixed(2)}</span>
                        </div>
                        <div className="g-metric-row">
                          <span className="text-muted text-xs">Current Saved:</span>
                          <span className={`font-semibold ${isDone ? 'text-success' : 'text-primary'}`}>
                            ₹{parseFloat(goal.current_amount).toFixed(2)}
                          </span>
                        </div>
                        <div className="g-metric-row">
                          <span className="text-muted text-xs">Remaining:</span>
                          <span className={`font-semibold ${parseFloat(goal.remaining_amount) === 0 ? 'text-success' : 'text-danger'}`}>
                            ₹{parseFloat(goal.remaining_amount).toFixed(2)}
                          </span>
                        </div>
                      </div>

                      {/* Progress Bar & Percentage */}
                      <div className="progress-container mt-3">
                        <div className="g-progress-header">
                          <span className="text-muted text-xs">Progress</span>
                          <span className={`text-xs font-bold ${isDone ? 'text-success' : 'text-primary'}`}>
                            {progressPct}%
                          </span>
                        </div>
                        <div className="progress-bar-bg">
                          <div
                            className={`progress-bar-fill ${isDone ? 'fill-normal' : 'fill-warning'}`}
                            style={{
                              width: `${Math.min(progressPct, 100)}%`,
                              backgroundColor: isDone ? '#10b981' : '#4f46e5',
                            }}
                          ></div>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="b-card-actions mt-4">
                        <button
                          onClick={() => startDeposit(goal)}
                          className="btn-deposit"
                          title="Deposit funds toward this goal"
                        >
                          <PlusCircle size={14} />
                          <span>+ Deposit Funds</span>
                        </button>
                        <button
                          onClick={() => startEditGoal(goal)}
                          className="btn-action btn-edit"
                          title="Edit Goal"
                        >
                          <Edit2 size={13} />
                          <span>Edit</span>
                        </button>
                        <button
                          onClick={() => handleDeleteGoal(goal.id, goal.name)}
                          disabled={deletingGoalId === goal.id}
                          className="btn-action btn-delete"
                          title="Delete Goal"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* ===================== TAB 5: COMBINED RECENT ACTIVITY ===================== */}
      {activeTab === 'activity' && (
        <div id="dashboard-module" className="card">
          <div className="card-header">
            <div className="card-title">
              <Calendar className="card-icon text-indigo" size={20} />
              <h3>Combined Chronological Activity Feed</h3>
            </div>
            <button onClick={refreshAllData} className="btn-icon-refresh" title="Refresh">
              <RefreshCw size={16} className={isLoadingSummary ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
          <div className="card-body">
            <p className="text-muted text-sm mb-4">
              Integrated chronological view merging all user income (₹+) and expense (₹-) records by date:
            </p>

            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Date</th>
                    <th>Category / Source</th>
                    <th>Description</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoadingSummary ? (
                    <tr>
                      <td colSpan="5" className="text-center py-6">
                        <span className="spinner-sm"></span> Loading transaction feed...
                      </td>
                    </tr>
                  ) : summaryError ? (
                    <tr><td colSpan="5" className="text-center py-6 text-danger">Transaction activity is unavailable. Refresh the dashboard to try again.</td></tr>
                  ) : summaryData.recent_transactions?.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="text-center py-6 text-muted">
                        No financial activity found yet. Record an expense or income to populate!
                      </td>
                    </tr>
                  ) : (
                    summaryData.recent_transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td>
                          {tx.type === 'income' ? (
                            <span className="badge badge-success">
                              <ArrowUpRight size={14} /> Income
                            </span>
                          ) : (
                            <span className="badge badge-danger">
                              <ArrowDownRight size={14} /> Expense
                            </span>
                          )}
                        </td>
                        <td>
                          <span className="date-badge">
                            <Calendar size={13} className="inline mr-1" />
                            {tx.date}
                          </span>
                        </td>
                        <td>
                          {tx.type === 'income' ? (
                            <span className={`category-badge src-${tx.source?.toLowerCase().replace(/\s+/g, '-')}`}>
                              {getSourceIcon(tx.source)}
                              <span>{tx.source}</span>
                            </span>
                          ) : (
                            <span className={`category-badge cat-${tx.category?.toLowerCase()}`}>
                              {getCategoryIcon(tx.category)}
                              <span>{tx.category}</span>
                            </span>
                          )}
                        </td>
                        <td className="expense-desc">{tx.description || <span className="text-muted italic">None</span>}</td>
                        <td className={`font-semibold ${tx.type === 'income' ? 'text-success' : 'text-danger'}`}>
                          {tx.type === 'income' ? `+₹${parseFloat(tx.amount).toFixed(2)}` : `-₹${parseFloat(tx.amount).toFixed(2)}`}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ===================== TAB 6: NOTIFICATIONS & ALERTS ===================== */}
      {activeTab === 'notifications' && (
        <div id="dashboard-module" className="card">
          <div className="card-header">
            <div className="card-title">
              <Bell className="card-icon text-primary" size={20} />
              <h3>Notifications & Financial Alerts</h3>
            </div>
            <div className="header-actions">
              {notificationsList.some((n) => !n.is_read) && (
                <button
                  onClick={handleMarkAllNotificationsRead}
                  disabled={isMarkingAllNotificationsRead}
                  className="btn-action btn-edit mr-2"
                  title="Mark all notifications as read"
                >
                  {isMarkingAllNotificationsRead ? <span className="spinner-sm"></span> : <CheckCheck size={14} />}
                  <span>{isMarkingAllNotificationsRead ? 'Marking...' : 'Mark All Read'}</span>
                </button>
              )}
              <button
                onClick={fetchNotificationsList}
                className="btn-icon-refresh"
                title="Refresh notifications"
              >
                <RefreshCw size={16} className={isLoadingNotifications ? 'spin' : ''} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
          <div className="card-body">
            {notificationsMessage && (
              <div className={`alert alert-${notificationsMessage.type} mb-4`} role={notificationsMessage.type === 'error' ? 'alert' : 'status'}>
                {notificationsMessage.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                <span>{notificationsMessage.text}</span>
              </div>
            )}
            {notificationsError && (
              <div className="overview-inline-error mb-4" role="alert">
                <span>{notificationsError}</span>
                <button type="button" onClick={fetchNotificationsList}>Retry</button>
              </div>
            )}
            {/* Filter Chips */}
            <div className="filter-chips-row mb-6">
              <span className="filter-label">Filter Alerts:</span>
              <button
                className={`chip ${selectedNotifFilter === 'ALL' ? 'active' : ''}`}
                onClick={() => setSelectedNotifFilter('ALL')}
              >
                All ({notificationsList.length})
              </button>
              <button
                className={`chip ${selectedNotifFilter === 'UNREAD' ? 'active' : ''}`}
                onClick={() => setSelectedNotifFilter('UNREAD')}
              >
                Unread ({notificationsList.filter((n) => !n.is_read).length})
              </button>
              <button
                className={`chip ${selectedNotifFilter === 'budget_alert' ? 'active' : ''}`}
                onClick={() => setSelectedNotifFilter('budget_alert')}
              >
                <AlertTriangle size={12} className="inline mr-1 text-amber-500" />
                Budget Alerts ({notificationsList.filter((n) => n.notification_type === 'budget_alert').length})
              </button>
              <button
                className={`chip ${selectedNotifFilter === 'goal_milestone' ? 'active' : ''}`}
                onClick={() => setSelectedNotifFilter('goal_milestone')}
              >
                <Sparkles size={12} className="inline mr-1 text-indigo-500" />
                Goal Milestones ({notificationsList.filter((n) => n.notification_type === 'goal_milestone').length})
              </button>
            </div>

            {isLoadingNotifications ? (
              <div className="text-center py-10">
                <span className="spinner-sm"></span> Loading notifications...
              </div>
            ) : notificationsError && notificationsList.length === 0 ? (
              <div className="overview-empty" role="alert">
                Notifications are unavailable. Retry the request above.
              </div>
            ) : filteredNotifications.length === 0 ? (
              <div className="empty-state text-center py-12">
                <Bell size={40} className="mx-auto text-muted mb-3 opacity-40" />
                <h4 className="font-bold text-gray-700">No Notifications Found</h4>
                <p className="text-muted text-sm max-w-sm mx-auto mt-1">
                  {selectedNotifFilter === 'UNREAD'
                    ? 'You have caught up with all your notifications!'
                    : 'Alerts triggered by budget overruns and savings milestones will show up here.'}
                </p>
              </div>
            ) : (
              <div className="notifications-dashboard-grid">
                {filteredNotifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={`notification-card ${!notif.is_read ? 'unread-card' : ''}`}
                  >
                    <div className="notif-card-main">
                      <div className={`notif-type-icon-pill type-${notif.notification_type}`}>
                        {notif.notification_type === 'budget_alert' ? (
                          <AlertTriangle size={18} />
                        ) : notif.notification_type === 'goal_milestone' ? (
                          <Sparkles size={18} />
                        ) : (
                          <Bell size={18} />
                        )}
                      </div>
                      <div className="notif-card-body">
                        <div className="notif-card-header">
                          <span className="notif-card-title">{notif.title}</span>
                          <span className="notif-card-time">
                            <Calendar size={12} className="inline mr-1" />
                            {new Date(notif.created_at).toLocaleString(undefined, {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                        <p className="notif-card-text">{notif.message}</p>
                      </div>
                    </div>
                    <div className="notif-card-footer">
                      {!notif.is_read ? (
                        <button
                          onClick={() => handleMarkNotificationRead(notif.id)}
                          disabled={notificationActionId === notif.id}
                          className="btn-action btn-edit"
                          title="Mark this notification as read"
                        >
                          {notificationActionId === notif.id ? <span className="spinner-sm"></span> : <Check size={13} />}
                          <span>{notificationActionId === notif.id ? 'Updating...' : 'Mark as Read'}</span>
                        </button>
                      ) : (
                        <span className="text-xs text-muted font-medium">✓ Read</span>
                      )}
                      <button
                        onClick={() => handleDeleteNotificationFromList(notif.id)}
                        disabled={notificationActionId === notif.id}
                        className="btn-action btn-delete"
                        title="Delete notification"
                      >
                        {notificationActionId === notif.id ? <span className="spinner-sm"></span> : <Trash2 size={13} />}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'reports' && (
        <div id="dashboard-module" className="card">
          <div className="card-header">
            <div className="card-title">
              <FileText className="card-icon text-primary" size={20} />
              <h3>Financial Reports</h3>
            </div>
            <div className="overview-report-actions">
              <button type="button" onClick={() => handleReportDownload('pdf')} disabled={Boolean(exportingReport)}>
                <FileDown size={14} /> {exportingReport === 'pdf' ? 'Preparing...' : 'Generate PDF'}
              </button>
              <button type="button" onClick={() => handleReportDownload('xlsx')} disabled={Boolean(exportingReport)}>
                <FileSpreadsheet size={14} /> {exportingReport === 'xlsx' ? 'Preparing...' : 'Generate Excel'}
              </button>
            </div>
          </div>
          <div className="card-body">
            <p className="reports-period-copy">Monthly reports for {analyticsOverview?.filter_applied || analyticsMonth} include saved income, expenses, budgets, and savings goals.</p>
            {reportMessage && (
              <div className={`alert alert-${reportMessage.type} mb-4`} role={reportMessage.type === 'error' ? 'alert' : 'status'}>
                {reportMessage.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                <span>{reportMessage.text}</span>
              </div>
            )}
            {isLoadingReports ? (
              <div className="overview-empty">Loading saved reports...</div>
            ) : reportsError ? (
              <div className="overview-inline-error" role="alert">
                <span>{reportsError}</span>
                <button type="button" onClick={fetchReports}>Retry</button>
              </div>
            ) : reports.length === 0 ? (
              <div className="overview-empty">No saved reports yet. Generate a PDF or Excel report for this period.</div>
            ) : (
              <div className="saved-reports-list">
                {reports.map((report) => (
                  <div className="saved-report-row" key={report.id}>
                    <div className="saved-report-icon"><FileText size={17} /></div>
                    <div className="saved-report-copy">
                      <strong>{report.title}</strong>
                      <small>{report.month || 'Monthly'} · Created {new Date(report.generated_at).toLocaleDateString()}</small>
                    </div>
                    <button type="button" title="Download PDF" onClick={() => handleSavedReportDownload(report.id, 'pdf')} disabled={Boolean(exportingReport)}><FileDown size={16} /></button>
                    <button type="button" title="Download Excel" onClick={() => handleSavedReportDownload(report.id, 'xlsx')} disabled={Boolean(exportingReport)}><FileSpreadsheet size={16} /></button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Edit Expense Modal */}
      {editingExpense && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Edit Expense #{editingExpense.id}</h3>
              <button onClick={() => setEditingExpense(null)} className="btn-close">
                <X size={18} />
              </button>
            </div>
            {editExpenseMsg && (
              <div className={`alert alert-${editExpenseMsg.type} m-4`}>
                <AlertTriangle size={18} />
                <span>{editExpenseMsg.text}</span>
              </div>
            )}
            <form onSubmit={handleUpdateExpense} className="modal-form">
              <div className="form-group">
                <label>Category (Required)</label>
                <select
                  value={editExpenseForm.category}
                  onChange={(e) => setEditExpenseForm({ ...editExpenseForm, category: e.target.value })}
                  required
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Amount (₹ Required)</label>
                <input
                  type="text"
                  inputMode="decimal"
                  placeholder="0.00"
                  value={editExpenseForm.amount}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                      setEditExpenseForm({ ...editExpenseForm, amount: val });
                    }
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label>Date (Required)</label>
                <input
                  type="date"
                  value={editExpenseForm.date}
                  onChange={(e) => setEditExpenseForm({ ...editExpenseForm, date: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <input
                  type="text"
                  value={editExpenseForm.description}
                  onChange={(e) => setEditExpenseForm({ ...editExpenseForm, description: e.target.value })}
                  placeholder="Optional description"
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setEditingExpense(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isUpdatingExpense}>
                  {isUpdatingExpense ? <span className="spinner-sm"></span> : <CheckCircle2 size={16} />}
                  <span>Save Changes</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Income Modal */}
      {editingIncome && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Edit Income Record #{editingIncome.id}</h3>
              <button onClick={() => setEditingIncome(null)} className="btn-close">
                <X size={18} />
              </button>
            </div>
            {editIncomeMsg && (
              <div className={`alert alert-${editIncomeMsg.type} m-4`}>
                <AlertTriangle size={18} />
                <span>{editIncomeMsg.text}</span>
              </div>
            )}
            <form onSubmit={handleUpdateIncome} className="modal-form">
              <div className="form-group">
                <label>Income Source (Required)</label>
                <select
                  value={editIncomeForm.source}
                  onChange={(e) => setEditIncomeForm({ ...editIncomeForm, source: e.target.value })}
                  required
                >
                  {INCOME_SOURCES.map((src) => (
                    <option key={src} value={src}>
                      {src}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Amount (₹ Required)</label>
                <input
                  type="text"
                  inputMode="decimal"
                  placeholder="0.00"
                  value={editIncomeForm.amount}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                      setEditIncomeForm({ ...editIncomeForm, amount: val });
                    }
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label>Date (Required)</label>
                <input
                  type="date"
                  value={editIncomeForm.date}
                  onChange={(e) => setEditIncomeForm({ ...editIncomeForm, date: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Description / Details</label>
                <input
                  type="text"
                  value={editIncomeForm.description}
                  onChange={(e) => setEditIncomeForm({ ...editIncomeForm, description: e.target.value })}
                  placeholder="Optional details"
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setEditingIncome(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary btn-success-action" disabled={isUpdatingIncome}>
                  {isUpdatingIncome ? <span className="spinner-sm"></span> : <CheckCircle2 size={16} />}
                  <span>Save Changes</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Budget Modal */}
      {editingBudget && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Set Budget for {editingBudget.category}</h3>
              <button onClick={() => setEditingBudget(null)} className="btn-close">
                <X size={18} />
              </button>
            </div>
            {editBudgetMsg && (
              <div className={`alert alert-${editBudgetMsg.type} m-4`}>
                <AlertTriangle size={18} />
                <span>{editBudgetMsg.text}</span>
              </div>
            )}
            <form onSubmit={handleUpdateBudget} className="modal-form">
              <div className="form-group">
                <label>Category</label>
                <input type="text" value={editBudgetForm.category} disabled className="bg-gray-100" />
              </div>

              <div className="form-group">
                <label>Monthly Budget Amount (₹ Required)</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={editBudgetForm.amount}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                      setEditBudgetForm({ ...editBudgetForm, amount: val });
                    }
                  }}
                  placeholder="0.00"
                  required
                />
              </div>

              <div className="form-group">
                <label>Month</label>
                <input type="text" value={editBudgetForm.month} disabled className="bg-gray-100" />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setEditingBudget(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isUpdatingBudget}>
                  {isUpdatingBudget ? <span className="spinner-sm"></span> : <CheckCircle2 size={16} />}
                  <span>Save Allocation</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Savings Goal Modal */}
      {editingGoal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Edit Savings Goal #{editingGoal.id}</h3>
              <button onClick={() => setEditingGoal(null)} className="btn-close">
                <X size={18} />
              </button>
            </div>
            {editGoalMsg && (
              <div className={`alert alert-${editGoalMsg.type} m-4`}>
                <AlertTriangle size={18} />
                <span>{editGoalMsg.text}</span>
              </div>
            )}
            <form onSubmit={handleUpdateGoal} className="modal-form">
              <div className="form-group">
                <label>Goal Name (Required)</label>
                <input
                  type="text"
                  value={editGoalForm.name}
                  onChange={(e) => setEditGoalForm({ ...editGoalForm, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Target Amount (₹ Required)</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={editGoalForm.target_amount}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                      setEditGoalForm({ ...editGoalForm, target_amount: val });
                    }
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label>Current Saved (₹)</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={editGoalForm.current_amount}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                      setEditGoalForm({ ...editGoalForm, current_amount: val });
                    }
                  }}
                />
              </div>

              <div className="form-group">
                <label>Target Date</label>
                <input
                  type="date"
                  value={editGoalForm.target_date || ''}
                  onChange={(e) => setEditGoalForm({ ...editGoalForm, target_date: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setEditingGoal(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isUpdatingGoal}>
                  {isUpdatingGoal ? <span className="spinner-sm"></span> : <CheckCircle2 size={16} />}
                  <span>Save Changes</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Deposit / Add Funds Modal */}
      {depositGoal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Deposit Funds: {depositGoal.name}</h3>
              <button onClick={() => setDepositGoal(null)} className="btn-close">
                <X size={18} />
              </button>
            </div>
            {depositMsg && (
              <div className={`alert alert-${depositMsg.type} m-4`}>
                <AlertTriangle size={18} />
                <span>{depositMsg.text}</span>
              </div>
            )}
            <form onSubmit={handleDeposit} className="modal-form">
              <div className="form-group">
                <label>Target Amount</label>
                <input type="text" value={`₹${parseFloat(depositGoal.target_amount).toFixed(2)}`} disabled className="bg-gray-100" />
              </div>

              <div className="form-group">
                <label>Currently Saved</label>
                <input type="text" value={`₹${parseFloat(depositGoal.current_amount).toFixed(2)} (${depositGoal.progress_percentage}% achieved)`} disabled className="bg-gray-100" />
              </div>

              <div className="form-group">
                <label>Deposit Amount (₹ Required)</label>
                <input
                  type="text"
                  inputMode="decimal"
                  placeholder="0.00"
                  value={depositAmount}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                      setDepositAmount(val);
                    }
                  }}
                  autoFocus
                  required
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setDepositGoal(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary btn-success-action" disabled={isDepositing}>
                  {isDepositing ? <span className="spinner-sm"></span> : <PlusCircle size={16} />}
                  <span>Confirm Deposit</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Interactive Protected API Tester */}
      <div className="card mt-6">
        <div className="card-header">
          <div className="card-title">
            <Server className="card-icon text-indigo" size={20} />
            <h3>Interactive Protected API Tester</h3>
          </div>
          <span className="text-muted text-sm">Verify JWT Protected Endpoints</span>
        </div>
        <div className="card-body">
          <p className="text-muted mb-4">
            Click any button below to trigger a live protected request to the Django backend using your current JWT access token:
          </p>

          <div className="api-buttons-group">
            <button
              onClick={() => handleTestEndpoint('GET /api/savings-goals/', savingsGoalsAPI.getGoals)}
              disabled={isLoadingApi}
              className={`btn-api ${activeEndpoint === 'GET /api/savings-goals/' ? 'active' : ''}`}
            >
              <PiggyBank size={16} />
              <span>GET /api/savings-goals/</span>
            </button>

            <button
              onClick={() => handleTestEndpoint('GET /api/budgets/summary/', () => budgetsAPI.getBudgetSummary({ month: `${selectedBudgetMonth}-01` }))}
              disabled={isLoadingApi}
              className={`btn-api ${activeEndpoint === 'GET /api/budgets/summary/' ? 'active' : ''}`}
            >
              <Target size={16} />
              <span>GET /api/budgets/summary/</span>
            </button>

            <button
              onClick={() => handleTestEndpoint('GET /api/budgets/', budgetsAPI.getBudgets)}
              disabled={isLoadingApi}
              className={`btn-api ${activeEndpoint === 'GET /api/budgets/' ? 'active' : ''}`}
            >
              <Database size={16} />
              <span>GET /api/budgets/</span>
            </button>

            <button
              onClick={() => handleTestEndpoint('GET /api/dashboard/summary/', dashboardAPI.getSummary)}
              disabled={isLoadingApi}
              className={`btn-api ${activeEndpoint === 'GET /api/dashboard/summary/' ? 'active' : ''}`}
            >
              <Wallet size={16} />
              <span>GET /api/dashboard/summary/</span>
            </button>

            <button
              onClick={() => handleTestEndpoint('GET /api/expenses/', expensesAPI.getExpenses)}
              disabled={isLoadingApi}
              className={`btn-api ${activeEndpoint === 'GET /api/expenses/' ? 'active' : ''}`}
            >
              <TrendingDown size={16} />
              <span>GET /api/expenses/</span>
            </button>

            <button
              onClick={() => handleTestEndpoint('GET /api/incomes/', incomesAPI.getIncomes)}
              disabled={isLoadingApi}
              className={`btn-api ${activeEndpoint === 'GET /api/incomes/' ? 'active' : ''}`}
            >
              <TrendingUp size={16} />
              <span>GET /api/incomes/</span>
            </button>
          </div>

          {/* Response Console Display */}
          {(apiResponse !== null || isLoadingApi) && (
            <div className="response-console mt-4">
              <div className="console-header">
                <span className="console-title">
                  <strong>Target:</strong> {activeEndpoint}
                </span>
                {apiStatus && (
                  <span className={`status-pill ${apiStatus.success ? 'status-ok' : 'status-err'}`}>
                    HTTP {apiStatus.code} {apiStatus.text}
                  </span>
                )}
              </div>
              <div className="console-body">
                {isLoadingApi ? (
                  <div className="console-loading">
                    <span className="spinner-sm"></span> Sending request to backend...
                  </div>
                ) : (
                  <pre className="json-code">{JSON.stringify(apiResponse, null, 2)}</pre>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
