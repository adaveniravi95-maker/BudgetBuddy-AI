import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

const EXPENSE_CATEGORIES = ['Food', 'Travel', 'Shopping', 'Education', 'Entertainment', 'Miscellaneous'];
const INCOME_SOURCES = ['Pocket Money', 'Scholarship', 'Freelance Income'];

const EXPENSE_COLORS = {
  Food: '#f97316',
  Travel: '#3b82f6',
  Shopping: '#ec4899',
  Education: '#8b5cf6',
  Entertainment: '#eab308',
  Miscellaneous: '#64748b'
};

const INCOME_COLORS = {
  'Pocket Money': '#10b981',
  'Scholarship': '#06b6d4',
  'Freelance Income': '#6366f1'
};

function DonutChartCard({ title, total, data, emptyText, centerLabel = "TOTAL" }) {
  const radius = 55;
  const circumference = 2 * Math.PI * radius;
  let accumulatedAngle = 0;

  return (
    <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '20px', borderRadius: '12px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', flex: 1, minWidth: '280px' }}>
      <div>
        <h3 style={{ margin: '0 0 16px', fontSize: '15px', color: '#f8fafc', fontWeight: '700' }}>{title}</h3>
        {data.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '36px 0', color: '#64748b', fontSize: '13px' }}>
            {emptyText}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            <div style={{ position: 'relative', width: '140px', height: '140px' }}>
              <svg width="140" height="140" viewBox="0 0 140 140" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="70" cy="70" r={radius} fill="none" stroke="#1e293b" strokeWidth="16" />
                {data.map((item) => {
                  const strokeDash = (item.percentage / 100) * circumference;
                  const strokeOffset = -accumulatedAngle;
                  accumulatedAngle += strokeDash;
                  return (
                    <circle
                      key={item.label}
                      cx="70"
                      cy="70"
                      r={radius}
                      fill="none"
                      stroke={item.color}
                      strokeWidth="16"
                      strokeDasharray={`${strokeDash} ${circumference - strokeDash}`}
                      strokeDashoffset={strokeOffset}
                      strokeLinecap="round"
                      style={{ transition: 'stroke-dasharray 0.4s ease' }}
                    />
                  );
                })}
              </svg>
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 'bold' }}>{centerLabel}</span>
                <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#f8fafc' }}>₹{total.toLocaleString()}</span>
              </div>
            </div>

            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {data.map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0f172a', padding: '6px 10px', borderRadius: '6px', border: '1px solid #1e293b', fontSize: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: item.color }} />
                    <span style={{ color: '#cbd5e1' }}>{item.label}</span>
                  </div>
                  <div>
                    <span style={{ fontWeight: 'bold', color: '#f8fafc' }}>₹{item.amount.toLocaleString()}</span>
                    <span style={{ color: '#94a3b8', marginLeft: '5px' }}>({item.percentage}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { expenseAPI, incomeAPI, transactionAPI, budgetAPI, savingsAPI, notificationAPI, reportAPI } from '../services/api';
import AnalyticsSection from '../components/analytics/AnalyticsSection';
import {
  EXPENSE_CATEGORIES, INCOME_SOURCES, EXPENSE_COLORS, INCOME_COLORS,
  MONTHS, currentMonth, currentYear,
} from '../constants/finance';

const today = () => new Date().toISOString().split('T')[0];
const emptyExpense = { amount: '', category: 'food', description: '', date: today() };
const emptyIncome = { amount: '', source: 'pocket_money', description: '', date: today() };

const NAV = [
  { id: 'overview', label: 'Overview' },
  { id: 'budget', label: 'Budgets' },
  { id: 'savings', label: 'Savings' },
  { id: 'income', label: 'Income' },
  { id: 'expenses', label: 'Expenses' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'reports', label: 'Reports' },
];

function RecentActivity() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    transactionAPI.list({}).then((r) => setTransactions(r.data.transactions.slice(0, 5))).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="section-card">
      <div className="section-header"><span className="section-title"><span className="section-title-mark" /> Recent Activity</span></div>
      {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 48, marginBottom: 8, borderRadius: 10 }} />)}
    </div>
  );
  if (!transactions.length) return null;

  return (
    <div className="section-card anim-fadeInUp">
      <div className="section-header">
        <span className="section-title"><span className="section-title-mark" /> Recent Activity</span>
      </div>
      <div className="transaction-list">
        {transactions.map((tx) => (
          <div key={tx.type + '-' + tx.id} className="transaction-item">
            <div className={`transaction-dot ${tx.type}`} />
            <div className="transaction-details">
              <span className="transaction-desc">{tx.description || tx.category}</span>
              <span className="transaction-meta">{tx.category.replace('_', ' ')} &middot; {tx.date}</span>
            </div>
            <span className={tx.type === 'income' ? 'amount-income' : 'amount-expense'}>
              {tx.type === 'income' ? '+' : '-'} INR {tx.amount.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Dashboard() {
  const [expenses, setExpenses] = useState([]);
  const [incomes, setIncomes] = useState([]);
  const [savingsGoals, setSavingsGoals] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [budget, setBudget] = useState(null);
  const [loading, setLoading] = useState(true);

  // Profile Management State
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileTab, setProfileTab] = useState('INFO'); // 'INFO' or 'PASSWORD'
  const [profileData, setProfileData] = useState({ username: '', email: '', date_joined: '' });
  const [profileEmailInput, setProfileEmailInput] = useState('');
  const [profileMessage, setProfileMessage] = useState({ type: '', text: '' });
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Notification Dropdown
  const [showNotifications, setShowNotifications] = useState(false);

  // Forms
  const [formType, setFormType] = useState('EXPENSE');
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('Food');
  const [incomeSource, setIncomeSource] = useState('Pocket Money');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [editingId, setEditingId] = useState(null);
  const [editingType, setEditingType] = useState(null);

  // Modals
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [totalBudgetInput, setTotalBudgetInput] = useState('');
  const [allocationsInput, setAllocationsInput] = useState({});
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [goalName, setGoalName] = useState('');
  const [goalTarget, setGoalTarget] = useState('');
  const [goalCurrent, setGoalCurrent] = useState('');

  const formRef = useRef(null);
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      const expRes = await api.get('expenses/').catch(() => ({ data: [] }));
      const incRes = await api.get('incomes/').catch(() => ({ data: [] }));
      const budRes = await api.get('budgets/').catch(() => ({ data: [] }));
      const goalRes = await api.get('savings-goals/').catch(() => ({ data: [] }));
      const notifRes = await api.get('notifications/').catch(() => ({ data: [] }));

      setExpenses(expRes.data || []);
      setIncomes(incRes.data || []);
      setSavingsGoals(goalRes.data || []);
      setNotifications(notifRes.data || []);

      if (budRes.data && budRes.data.length > 0) {
        setBudget(budRes.data[0]);
      }
    } catch (err) {
      console.error('Data loading error:', err);
      if (err.response?.status === 401) {
        localStorage.clear();
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchProfile = async () => {
    try {
      const res = await api.get('profile/');
      setProfileData(res.data);
      setProfileEmailInput(res.data.email || '');
    } catch (err) {
      console.error('Failed to fetch profile', err);
    }
  };

  useEffect(() => {
    loadData();
    fetchProfile();
  }, []);

  const totalIncome = incomes.reduce((acc, curr) => acc + parseFloat(curr.amount || 0), 0);
  const totalExpenses = expenses.reduce((acc, curr) => acc + parseFloat(curr.amount || 0), 0);
  const remainingBalance = totalIncome - totalExpenses;
  const budgetAmount = budget ? parseFloat(budget.total_amount) : 0;
  const budgetUtilization = budgetAmount > 0 ? Math.round((totalExpenses / budgetAmount) * 100) : 0;
  const savingsRate = totalIncome > 0 ? Math.max(0, Math.round(((totalIncome - totalExpenses) / totalIncome) * 100)) : 0;

  const validNotifications = notifications.filter((n) => {
    if (n.notification_type === 'BUDGET_ALERT' && budgetUtilization < 80) {
      return false;
    }
    return true;
  });
  const unreadCount = validNotifications.filter((n) => !n.is_read).length;

  const expenseChartData = EXPENSE_CATEGORIES.map((cat) => {
    const sum = expenses.filter((e) => e.category === cat).reduce((acc, e) => acc + parseFloat(e.amount || 0), 0);
    const pct = totalExpenses > 0 ? (sum / totalExpenses) * 100 : 0;
    return { label: cat, amount: sum, percentage: Math.round(pct), color: EXPENSE_COLORS[cat] };
  }).filter((item) => item.amount > 0);

  const incomeChartData = INCOME_SOURCES.map((src) => {
    const sum = incomes
      .filter((i) => (i.income_type === src || i.source === src))
      .reduce((acc, i) => acc + parseFloat(i.amount || 0), 0);
    const pct = totalIncome > 0 ? (sum / totalIncome) * 100 : 0;
    return { label: src, amount: sum, percentage: Math.round(pct), color: INCOME_COLORS[src] };
  }).filter((item) => item.amount > 0);

  const cashFlowChartData = [];
  if (totalIncome > 0) {
    const spentPct = Math.round((Math.min(totalExpenses, totalIncome) / totalIncome) * 100);
    const savedPct = Math.max(0, 100 - spentPct);
    cashFlowChartData.push({ label: 'Spent', amount: totalExpenses, percentage: spentPct, color: '#ef4444' });
    if (remainingBalance > 0) {
      cashFlowChartData.push({ label: 'Net Balance', amount: remainingBalance, percentage: savedPct, color: '#10b981' });
    }
  }

  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const currentDateObj = new Date();
  const monthlyTrends = [];

  for (let i = 5; i >= 0; i--) {
    const d = new Date(currentDateObj.getFullYear(), currentDateObj.getMonth() - i, 1);
    const m = d.getMonth();
    const y = d.getFullYear();

    const mInc = incomes
      .filter((inc) => {
        const incDate = new Date(inc.date);
        return incDate.getMonth() === m && incDate.getFullYear() === y;
      })
      .reduce((acc, inc) => acc + parseFloat(inc.amount || 0), 0);

    const mExp = expenses
      .filter((exp) => {
        const expDate = new Date(exp.date);
        return expDate.getMonth() === m && expDate.getFullYear() === y;
      })
      .reduce((acc, exp) => acc + parseFloat(exp.amount || 0), 0);

    monthlyTrends.push({
      month: `${monthNames[m]} '${String(y).slice(-2)}`,
      income: mInc,
      expense: mExp
    });
  }

  const maxTrendVal = Math.max(...monthlyTrends.map((t) => Math.max(t.income, t.expense)), 1000);

  const handleEdit = (item) => {
    setEditingId(item.id);
    setEditingType(item.type);
    setFormType(item.type);
    setAmount(item.amount);
    setDate(item.date);

    if (item.type === 'EXPENSE') {
      setTitle(item.title || '');
      setCategory(item.category || 'Food');
    } else {
      setIncomeSource(item.income_type || item.source || 'Pocket Money');
    }
    formRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const resetForm = () => {
    setTitle('');
    setAmount('');
    setEditingId(null);
    setEditingType(null);
  };

  const handleSaveTransaction = async (e) => {
    e.preventDefault();
    if (parseFloat(amount) <= 0) {
      alert('Amount must be greater than 0');
      return;
    }

    try {
      if (formType === 'EXPENSE') {
        const payload = { title: title.trim(), amount: parseFloat(amount), category, date };
        if (editingId && editingType === 'EXPENSE') {
          await api.put(`expenses/${editingId}/`, payload);
        } else {
          await api.post('expenses/', payload);
        }
      } else {
        const payload = { income_type: incomeSource, source: incomeSource, amount: parseFloat(amount), date };
        if (editingId && editingType === 'INCOME') {
          await api.put(`incomes/${editingId}/`, payload);
        } else {
          await api.post('incomes/', payload);
        }
      }
      resetForm();
      loadData();
    } catch (err) {
      alert(err.response?.data?.error || 'Transaction failed to save.');
    }
  };

  const handleDelete = async (id, type) => {
    if (!window.confirm('Delete this record?')) return;
    try {
      if (type === 'EXPENSE') {
        await api.delete(`expenses/${id}/`);
      } else {
        await api.delete(`incomes/${id}/`);
      }
      loadData();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const handleSaveBudget = async (e) => {
    e.preventDefault();
    const currentDate = new Date();
    const category_allocations = Object.entries(allocationsInput)
      .filter(([_, val]) => parseFloat(val) > 0)
      .map(([cat, val]) => ({ category: cat, allocated_amount: parseFloat(val) }));

    try {
      await api.post('budgets/', {
        month: currentDate.getMonth() + 1,
        year: currentDate.getFullYear(),
        total_amount: parseFloat(totalBudgetInput),
        category_allocations
      });
      alert('Budget saved successfully!');
      setShowBudgetModal(false);
      loadData();
    } catch (err) {
      alert('Failed to save budget.');
    }
  };

  const handleSaveGoal = async (e) => {
    e.preventDefault();
    if (!goalName.trim() || parseFloat(goalTarget) <= 0) {
      alert('Enter valid goal name and target amount > 0');
      return;
    }
    try {
      await api.post('savings-goals/', {
        name: goalName.trim(),
        target_amount: parseFloat(goalTarget),
        current_amount: parseFloat(goalCurrent || 0)
      });
      alert('Savings goal created!');
      setGoalName('');
      setGoalTarget('');
      setGoalCurrent('');
      setShowGoalModal(false);
      loadData();
    } catch (err) {
      alert('Failed to create savings goal');
    }
  };

  const handleAddGoalProgress = async (goal) => {
    const addAmt = prompt(`Add saved funds to "${goal.name}":`, '500');
    if (!addAmt || isNaN(addAmt) || parseFloat(addAmt) <= 0) return;

    const newAmount = parseFloat(goal.current_amount) + parseFloat(addAmt);
    try {
      await api.patch(`savings-goals/${goal.id}/`, {
        current_amount: newAmount
      });
      loadData();
    } catch (err) {
      alert('Failed to update progress');
    }
  };

  const handleDeleteGoal = async (id) => {
    if (!window.confirm('Delete this savings goal?')) return;
    try {
      await api.delete(`savings-goals/${id}/`);
      loadData();
    } catch (err) {
      alert('Failed to delete goal');
    }
  };

  const handleExportCSV = () => {
    try {
      let csvContent = "data:text/csv;charset=utf-8,";
      csvContent += "BudgetBuddy Financial Summary Report\r\n";
      csvContent += `Generated Date,${new Date().toLocaleString()}\r\n\r\n`;

      csvContent += "METRICS,AMOUNT (INR)\r\n";
      csvContent += `Total Income,${totalIncome}\r\n`;
      csvContent += `Total Expenses,${totalExpenses}\r\n`;
      csvContent += `Remaining Balance,${remainingBalance}\r\n`;
      csvContent += `Monthly Budget,${budgetAmount}\r\n`;
      csvContent += `Savings Rate,${savingsRate}%\r\n\r\n`;

      csvContent += "TRANSACTION LOGS\r\n";
      csvContent += "Date,Type,Title / Source,Category,Amount (INR)\r\n";

      const allSorted = [
        ...incomes.map((i) => ({ date: i.date, type: 'INCOME', title: i.income_type || i.source, cat: 'Income', amt: `+${i.amount}` })),
        ...expenses.map((e) => ({ date: e.date, type: 'EXPENSE', title: e.title, cat: e.category, amt: `-${e.amount}` }))
      ].sort((a, b) => new Date(b.date) - new Date(a.date));

      allSorted.forEach((row) => {
        csvContent += `"${row.date}","${row.type}","${row.title}","${row.cat}","${row.amt}"\r\n`;
      });

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `BudgetBuddy_Financial_Report_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      alert('Failed to export CSV');
    }
  };

  const handleMarkAsRead = async (id) => {
    try {
      await api.post(`notifications/${id}/mark_read/`);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearAllNotifications = async () => {
    try {
      await api.post(`notifications/clear_all/`);
      setNotifications([]);
    } catch (err) {
      setNotifications([]);
    }
  };

  // Profile Update Handlers
  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileMessage({ type: '', text: '' });
    try {
      const res = await api.patch('profile/', { email: profileEmailInput });
      setProfileData(res.data);
      setProfileMessage({ type: 'success', text: 'Profile email updated successfully!' });
    } catch (err) {
      setProfileMessage({ type: 'error', text: err.response?.data?.email?.[0] || 'Failed to update profile.' });
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setProfileMessage({ type: '', text: '' });

    if (newPassword !== confirmPassword) {
      setProfileMessage({ type: 'error', text: 'New passwords do not match!' });
      return;
    }
    if (newPassword.length < 6) {
      setProfileMessage({ type: 'error', text: 'Password must be at least 6 characters long.' });
      return;
    }

    try {
      const res = await api.post('change-password/', {
        old_password: oldPassword,
        new_password: newPassword
      });
      setProfileMessage({ type: 'success', text: res.data.message || 'Password changed successfully!' });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.old_password?.[0] || 'Password change failed.';
      setProfileMessage({ type: 'error', text: msg });
    }
  };

  const activities = [
    ...expenses.map((e) => ({ ...e, type: 'EXPENSE', displayTitle: e.title })),
    ...incomes.map((i) => ({ ...i, type: 'INCOME', displayTitle: i.income_type || i.source }))
  ].sort((a, b) => new Date(b.date) - new Date(a.date));

  const darkInputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid #334155',
    backgroundColor: '#0f172a',
    color: '#f8fafc',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box'
  };

  if (loading) {
    return (
      <div style={{ backgroundColor: '#090d16', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: '18px', fontFamily: 'system-ui, sans-serif' }}>
        Loading BudgetBuddy Dashboard...
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: '#090d16', minHeight: '100vh', fontFamily: 'system-ui, sans-serif', padding: '24px', color: '#f8fafc' }}>
      {/* Header */}
      <div style={{ maxWidth: '1200px', margin: '0 auto 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h1 style={{ margin: 0, color: '#f8fafc', fontSize: '26px', fontWeight: '800' }}>BudgetBuddy</h1>
          <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '14px' }}>
            Welcome, <strong style={{ color: '#38bdf8' }}>{profileData.username || 'User'}</strong> • Financial Cockpit
          </p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', position: 'relative' }}>
          {/* User Profile Button */}
          <button
            onClick={() => { setShowProfileModal(true); setProfileMessage({ type: '', text: '' }); }}
            title="User Profile & Settings"
            style={{
              backgroundColor: '#131b2e',
              border: '1px solid #334155',
              color: '#cbd5e1',
              padding: '8px 12px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            👤 Profile
          </button>

          {/* Export Report */}
          <button
            onClick={handleExportCSV}
            title="Download CSV Report"
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              color: '#38bdf8',
              padding: '8px 14px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px'
            }}
          >
            📥 Export CSV
          </button>

          {/* Notification Bell */}
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            title="Notifications"
            style={{
              position: 'relative',
              backgroundColor: '#131b2e',
              border: '1px solid #1e293b',
              padding: '8px 12px',
              borderRadius: '8px',
              cursor: 'pointer',
              color: '#f8fafc',
              fontSize: '16px'
            }}
          >
            🔔
            {unreadCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '-5px',
                  right: '-5px',
                  backgroundColor: '#ef4444',
                  color: '#fff',
                  borderRadius: '10px',
                  padding: '2px 6px',
                  fontSize: '11px',
                  fontWeight: 'bold'
                }}
              >
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notification Dropdown Panel */}
          {showNotifications && (
            <div
              style={{
                position: 'absolute',
                top: '46px',
                right: '90px',
                width: '340px',
                backgroundColor: '#131b2e',
                border: '1px solid #334155',
                borderRadius: '10px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                zIndex: 1000,
                maxHeight: '400px',
                overflowY: 'auto'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #1e293b' }}>
                <span style={{ fontWeight: 'bold', fontSize: '14px', color: '#f8fafc' }}>Notifications</span>
                <button
                  onClick={handleClearAllNotifications}
                  style={{ background: 'none', border: 'none', color: '#ef4444', fontSize: '11px', cursor: 'pointer', padding: 0 }}
                >
                  Clear all
                </button>
              </div>

              {validNotifications.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
                  No active notifications.
                </div>
              ) : (
                validNotifications.map((n) => (
                  <div
                    key={n.id}
                    style={{
                      padding: '12px 16px',
                      borderBottom: '1px solid #1e293b',
                      backgroundColor: n.is_read ? '#131b2e' : '#1e293b44',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '13px', fontWeight: 'bold', color: n.notification_type === 'BUDGET_ALERT' ? '#f87171' : '#34d399' }}>
                        {n.title}
                      </span>
                      {!n.is_read && (
                        <button
                          onClick={() => handleMarkAsRead(n.id)}
                          style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '11px', cursor: 'pointer' }}
                        >
                          ✓ Read
                        </button>
                      )}
                    </div>
                    <span style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.4' }}>{n.message}</span>
                  </div>
                ))
              )}
            </div>
          )}

          <button
            onClick={() => { localStorage.clear(); navigate('/login'); }}
            style={{ backgroundColor: '#dc2626', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            Logout
          </button>
        </div>
      </div>

      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Top Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '20px', borderRadius: '12px' }}>
            <span style={{ color: '#4ade80', fontSize: '12px', fontWeight: 'bold', letterSpacing: '0.5px' }}>TOTAL INCOME</span>
            <div style={{ fontSize: '26px', fontWeight: 'bold', color: '#f8fafc', marginTop: '6px' }}>₹{totalIncome.toLocaleString()}</div>
          </div>
          <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '20px', borderRadius: '12px' }}>
            <span style={{ color: '#f87171', fontSize: '12px', fontWeight: 'bold', letterSpacing: '0.5px' }}>TOTAL EXPENSES</span>
            <div style={{ fontSize: '26px', fontWeight: 'bold', color: '#f8fafc', marginTop: '6px' }}>₹{totalExpenses.toLocaleString()}</div>
          </div>
          <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '20px', borderRadius: '12px' }}>
            <span style={{ color: '#60a5fa', fontSize: '12px', fontWeight: 'bold', letterSpacing: '0.5px' }}>REMAINING BALANCE</span>
            <div style={{ fontSize: '26px', fontWeight: 'bold', color: remainingBalance >= 0 ? '#38bdf8' : '#f87171', marginTop: '6px' }}>
              ₹{remainingBalance.toLocaleString()}
            </div>
          </div>
          <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '20px', borderRadius: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#c084fc', fontSize: '12px', fontWeight: 'bold', letterSpacing: '0.5px' }}>MONTHLY BUDGET</span>
              <button onClick={() => setShowBudgetModal(true)} style={{ backgroundColor: '#1e293b', color: '#cbd5e1', border: '1px solid #334155', fontSize: '11px', padding: '3px 8px', borderRadius: '4px', cursor: 'pointer' }}>
                ⚙️ Set
              </button>
            </div>
            <div style={{ fontSize: '26px', fontWeight: 'bold', color: '#f8fafc', marginTop: '6px' }}>
              {budgetAmount > 0 ? `₹${budgetAmount.toLocaleString()}` : 'Not Set'}
            </div>
          </div>
        </div>

        {/* Live Financial Health Strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '16px 20px', borderRadius: '12px' }}>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '600' }}>SAVINGS RATE</span>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#10b981', marginTop: '4px' }}>{savingsRate}%</div>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '600' }}>BUDGET UTILIZATION</span>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: budgetUtilization > 80 ? '#f87171' : '#38bdf8', marginTop: '4px' }}>
              {budgetUtilization}%
            </div>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '600' }}>ACTIVE SAVINGS GOALS</span>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#c084fc', marginTop: '4px' }}>
              {savingsGoals.length} ({savingsGoals.filter((g) => g.is_completed).length} Completed)
            </div>
          </div>
        </div>

        {/* Monthly Income/Expense Trends Visualization */}
        <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '24px', borderRadius: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '16px', color: '#f8fafc' }}>📈 Monthly Income vs Expense Trends</h3>
              <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#94a3b8' }}>Multi-month cash flow comparison (Last 6 Months)</p>
            </div>
            <div style={{ display: 'flex', gap: '14px', fontSize: '12px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#4ade80' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: '#10b981', borderRadius: '2px' }} /> Income
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f87171' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: '#ef4444', borderRadius: '2px' }} /> Expense
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: '160px', padding: '10px 0', borderBottom: '1px solid #334155', gap: '12px' }}>
            {monthlyTrends.map((trend) => {
              const incHeight = (trend.income / maxTrendVal) * 120;
              const expHeight = (trend.expense / maxTrendVal) * 120;
              return (
                <div key={trend.month} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', width: '100%', justifyContent: 'center' }}>
                    <div
                      title={`Income: ₹${trend.income.toLocaleString()}`}
                      style={{ width: '14px', height: `${Math.max(incHeight, 4)}px`, backgroundColor: '#10b981', borderRadius: '4px 4px 0 0', transition: 'height 0.4s ease' }}
                    />
                    <div
                      title={`Expense: ₹${trend.expense.toLocaleString()}`}
                      style={{ width: '14px', height: `${Math.max(expHeight, 4)}px`, backgroundColor: '#ef4444', borderRadius: '4px 4px 0 0', transition: 'height 0.4s ease' }}
                    />
                  </div>
                  <span style={{ fontSize: '11px', color: '#94a3b8', marginTop: '8px' }}>{trend.month}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* 3 Donut Charts */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          <DonutChartCard
            title="📉 Expense Categories"
            total={totalExpenses}
            data={expenseChartData}
            centerLabel="SPENT"
            emptyText="No expenses recorded yet."
          />
          <DonutChartCard
            title="📈 Income Sources"
            total={totalIncome}
            data={incomeChartData}
            centerLabel="EARNED"
            emptyText="No income recorded yet."
          />
          <DonutChartCard
            title="⚖️ Total Cash Flow (In vs Out)"
            total={totalIncome}
            data={cashFlowChartData}
            centerLabel="INFLOW"
            emptyText="Record income to analyze cash flow."
          />
        </div>

        {/* Savings Goals Section */}
        <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '24px', borderRadius: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '18px', color: '#f8fafc' }}>🎯 Savings Goals</h2>
              <p style={{ margin: '2px 0 0', color: '#94a3b8', fontSize: '13px' }}>Milestones & current progress tracking</p>
            </div>
            <button
              onClick={() => setShowGoalModal(true)}
              style={{ backgroundColor: '#059669', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '6px', fontWeight: '600', cursor: 'pointer', fontSize: '13px' }}
            >
              + Create New Goal
            </button>
          </div>

          {savingsGoals.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>No savings goals created yet. Click "+ Create New Goal" to start.</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
              {savingsGoals.map((g) => {
                const target = parseFloat(g.target_amount);
                const current = parseFloat(g.current_amount);
                const pct = g.progress_percentage || 0;
                return (
                  <div key={g.id} style={{ border: '1px solid #334155', borderRadius: '8px', padding: '16px', backgroundColor: g.is_completed ? '#064e3b33' : '#0f172a' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <h4 style={{ margin: 0, fontSize: '16px', color: '#f8fafc' }}>{g.name}</h4>
                        <span style={{ fontSize: '12px', color: '#94a3b8' }}>Target: ₹{target.toLocaleString()}</span>
                      </div>
                      <button onClick={() => handleDeleteGoal(g.id)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#f87171' }}>🗑️</button>
                    </div>

                    <div style={{ margin: '14px 0 6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px', color: '#cbd5e1' }}>
                        <span>Saved: ₹{current.toLocaleString()}</span>
                        <span>{pct}%</span>
                      </div>
                      <div style={{ height: '8px', width: '100%', backgroundColor: '#1e293b', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${pct}%`, height: '100%', backgroundColor: g.is_completed ? '#10b981' : '#3b82f6', transition: 'width 0.3s' }} />
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                      {g.is_completed ? (
                        <span style={{ color: '#34d399', fontSize: '12px', fontWeight: 'bold' }}>🎉 Target Reached!</span>
                      ) : (
                        <span style={{ color: '#94a3b8', fontSize: '12px' }}>Remaining: ₹{(target - current).toLocaleString()}</span>
                      )}
                      {!g.is_completed && (
                        <button
                          onClick={() => handleAddGoalProgress(g)}
                          style={{ backgroundColor: '#2563eb', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
                        >
                          + Add Funds
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Transaction Form & Activity List */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>
          {/* Form Card */}
          <div ref={formRef} style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '24px', borderRadius: '12px' }}>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
              <button
                type="button"
                onClick={() => { setFormType('EXPENSE'); resetForm(); }}
                style={{ flex: 1, padding: '10px', borderRadius: '8px', border: 'none', fontWeight: 'bold', cursor: 'pointer', backgroundColor: formType === 'EXPENSE' ? '#dc2626' : '#1e293b', color: formType === 'EXPENSE' ? '#fff' : '#94a3b8' }}
              >
                Record Expense
              </button>
              <button
                type="button"
                onClick={() => { setFormType('INCOME'); resetForm(); }}
                style={{ flex: 1, padding: '10px', borderRadius: '8px', border: 'none', fontWeight: 'bold', cursor: 'pointer', backgroundColor: formType === 'INCOME' ? '#16a34a' : '#1e293b', color: formType === 'INCOME' ? '#fff' : '#94a3b8' }}
              >
                Record Income
              </button>
            </div>

            {editingId && (
              <div style={{ backgroundColor: '#1e3a8a33', border: '1px solid #3b82f6', borderRadius: '8px', padding: '8px 12px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: '#60a5fa' }}>
                  ✏️ Editing {editingType}: <strong>{editingType === 'EXPENSE' ? title : incomeSource}</strong>
                </span>
                <button
                  type="button"
                  onClick={resetForm}
                  style={{ backgroundColor: '#334155', color: '#cbd5e1', border: 'none', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
                >
                  Cancel Edit
                </button>
              </div>
            )}

            <form onSubmit={handleSaveTransaction} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {formType === 'EXPENSE' ? (
                <>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#cbd5e1', marginBottom: '6px' }}>Title</label>
                    <input type="text" required placeholder="e.g. Hostel Mess / Books" value={title} onChange={(e) => setTitle(e.target.value)} style={darkInputStyle} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#cbd5e1', marginBottom: '6px' }}>Category</label>
                    <select value={category} onChange={(e) => setCategory(e.target.value)} style={darkInputStyle}>
                      {EXPENSE_CATEGORIES.map((c) => <option key={c} value={c} style={{ backgroundColor: '#0f172a', color: '#fff' }}>{c}</option>)}
                    </select>
                  </div>
                </>
              ) : (
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#cbd5e1', marginBottom: '6px' }}>Income Source</label>
                  <select value={incomeSource} onChange={(e) => setIncomeSource(e.target.value)} style={darkInputStyle}>
                    {INCOME_SOURCES.map((s) => <option key={s} value={s} style={{ backgroundColor: '#0f172a', color: '#fff' }}>{s}</option>)}
                  </select>
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#cbd5e1', marginBottom: '6px' }}>Amount (₹)</label>
                <input type="number" step="0.01" required placeholder="Amount in ₹" value={amount} onChange={(e) => setAmount(e.target.value)} style={darkInputStyle} />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#cbd5e1', marginBottom: '6px' }}>Date</label>
                <input type="date" required value={date} onChange={(e) => setDate(e.target.value)} style={darkInputStyle} />
              </div>

              <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                <button
                  type="submit"
                  style={{
                    flex: 1,
                    backgroundColor: editingId ? '#2563eb' : (formType === 'EXPENSE' ? '#dc2626' : '#16a34a'),
                    color: '#fff',
                    padding: '12px',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    fontSize: '15px'
                  }}
                >
                  {editingId ? 'Update Record' : `Save ${formType === 'EXPENSE' ? 'Expense' : 'Income'}`}
                </button>
                {editingId && (
                  <button
                    type="button"
                    onClick={resetForm}
                    style={{ backgroundColor: '#334155', color: '#cbd5e1', border: 'none', padding: '12px 18px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Activity Feed */}
          <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '24px', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '18px', color: '#f8fafc' }}>Recent Financial Activity</h3>
            {activities.length === 0 ? (
              <p style={{ color: '#64748b' }}>No activity recorded yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '430px', overflowY: 'auto' }}>
                {activities.map((a) => (
                  <div key={`${a.type}_${a.id}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}>
                    <div>
                      <div style={{ fontWeight: '600', color: '#f8fafc' }}>{a.displayTitle}</div>
                      <div style={{ fontSize: '12px', color: '#94a3b8' }}>{a.category || a.income_type} • {a.date}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontWeight: 'bold', color: a.type === 'EXPENSE' ? '#f87171' : '#4ade80' }}>
                        ₹{parseFloat(a.amount).toLocaleString()}
                      </span>
                      <button
                        onClick={() => handleEdit(a)}
                        title="Edit Transaction"
                        style={{ border: 'none', background: '#1e293b', padding: '6px 8px', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDelete(a.id, a.type)}
                        title="Delete Transaction"
                        style={{ border: 'none', background: '#1e293b', padding: '6px 8px', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* User Profile & Password Modal */}
      {showProfileModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: '#131b2e', border: '1px solid #334155', padding: '28px', borderRadius: '14px', width: '90%', maxWidth: '440px', boxShadow: '0 10px 30px rgba(0,0,0,0.6)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, color: '#f8fafc', fontSize: '18px' }}>👤 User Profile Management</h3>
              <button onClick={() => setShowProfileModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '18px', cursor: 'pointer' }}>✕</button>
            </div>

            {/* Profile Tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid #1e293b', paddingBottom: '10px' }}>
              <button
                type="button"
                onClick={() => { setProfileTab('INFO'); setProfileMessage({ type: '', text: '' }); }}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  border: 'none',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '13px',
                  backgroundColor: profileTab === 'INFO' ? '#2563eb' : '#1e293b',
                  color: profileTab === 'INFO' ? '#fff' : '#94a3b8'
                }}
              >
                Profile Info
              </button>
              <button
                type="button"
                onClick={() => { setProfileTab('PASSWORD'); setProfileMessage({ type: '', text: '' }); }}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  border: 'none',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '13px',
                  backgroundColor: profileTab === 'PASSWORD' ? '#2563eb' : '#1e293b',
                  color: profileTab === 'PASSWORD' ? '#fff' : '#94a3b8'
                }}
              >
                Change Password
              </button>
            </div>

            {/* Feedback Message */}
            {profileMessage.text && (
              <div style={{
                marginBottom: '16px',
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '13px',
                backgroundColor: profileMessage.type === 'success' ? '#064e3b44' : '#7f1d1d44',
                color: profileMessage.type === 'success' ? '#34d399' : '#f87171',
                border: `1px solid ${profileMessage.type === 'success' ? '#059669' : '#ef4444'}`
              }}>
                {profileMessage.text}
              </div>
            )}

            {/* Tab 1: Profile Info Form */}
            {profileTab === 'INFO' ? (
              <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '6px' }}>USERNAME (READ ONLY)</label>
                  <input type="text" disabled value={profileData.username || ''} style={{ ...darkInputStyle, backgroundColor: '#1e293b', cursor: 'not-allowed', color: '#94a3b8' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#cbd5e1', marginBottom: '6px' }}>EMAIL ADDRESS</label>
                  <input
                    type="email"
                    required
                    placeholder="Enter email"
                    value={profileEmailInput}
                    onChange={(e) => setProfileEmailInput(e.target.value)}
                    style={darkInputStyle}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '6px' }}>ACCOUNT CREATED</label>
                  <input
                    type="text"
                    disabled
                    value={profileData.date_joined ? new Date(profileData.date_joined).toLocaleDateString() : 'Active Member'}
                    style={{ ...darkInputStyle, backgroundColor: '#1e293b', cursor: 'not-allowed', color: '#94a3b8' }}
                  />
                </div>
                <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                  <button type="submit" style={{ flex: 1, backgroundColor: '#2563eb', color: '#fff', padding: '10px', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>
                    Save Profile
                  </button>
                  <button type="button" onClick={() => setShowProfileModal(false)} style={{ flex: 1, backgroundColor: '#334155', color: '#cbd5e1', padding: '10px', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                    Close
                  </button>
                </div>
              </form>
            ) : (
              /* Tab 2: Change Password Form */
              <form onSubmit={handleChangePassword} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#cbd5e1', marginBottom: '6px' }}>CURRENT PASSWORD</label>
                  <input
                    type="password"
                    required
                    placeholder="Enter current password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    style={darkInputStyle}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#cbd5e1', marginBottom: '6px' }}>NEW PASSWORD</label>
                  <input
                    type="password"
                    required
                    placeholder="Minimum 6 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    style={darkInputStyle}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#cbd5e1', marginBottom: '6px' }}>CONFIRM NEW PASSWORD</label>
                  <input
                    type="password"
                    required
                    placeholder="Re-type new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={darkInputStyle}
                  />
                </div>
                <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                  <button type="submit" style={{ flex: 1, backgroundColor: '#059669', color: '#fff', padding: '10px', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>
                    Update Password
                  </button>
                  <button type="button" onClick={() => setShowProfileModal(false)} style={{ flex: 1, backgroundColor: '#334155', color: '#cbd5e1', padding: '10px', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                    Close
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Savings Goal Modal */}
      {showGoalModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 999 }}>
          <div style={{ backgroundColor: '#131b2e', border: '1px solid #334155', padding: '28px', borderRadius: '12px', width: '90%', maxWidth: '400px' }}>
            <h3 style={{ margin: '0 0 16px', color: '#f8fafc' }}>Create Savings Goal</h3>
            <form onSubmit={handleSaveGoal} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 'bold', color: '#cbd5e1' }}>Goal Name</label>
                <input type="text" required placeholder="e.g. New Laptop" value={goalName} onChange={(e) => setGoalName(e.target.value)} style={darkInputStyle} />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 'bold', color: '#cbd5e1' }}>Target Amount (₹)</label>
                <input type="number" step="0.01" required placeholder="e.g. 50000" value={goalTarget} onChange={(e) => setGoalTarget(e.target.value)} style={darkInputStyle} />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 'bold', color: '#cbd5e1' }}>Initial Saved Amount (Optional)</label>
                <input type="number" step="0.01" placeholder="e.g. 5000" value={goalCurrent} onChange={(e) => setGoalCurrent(e.target.value)} style={darkInputStyle} />
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                <button type="submit" style={{ flex: 1, backgroundColor: '#059669', color: '#fff', padding: '10px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Save Goal</button>
                <button type="button" onClick={() => setShowGoalModal(false)} style={{ flex: 1, backgroundColor: '#334155', color: '#cbd5e1', padding: '10px', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Budget Modal */}
      {showBudgetModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 999 }}>
          <div style={{ backgroundColor: '#131b2e', border: '1px solid #334155', padding: '28px', borderRadius: '12px', width: '90%', maxWidth: '450px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3 style={{ margin: '0 0 16px', color: '#f8fafc' }}>Set Monthly Allocations</h3>
            <form onSubmit={handleSaveBudget} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 'bold', color: '#cbd5e1' }}>Total Monthly Limit (₹)</label>
                <input type="number" required placeholder="Total Budget" value={totalBudgetInput} onChange={(e) => setTotalBudgetInput(e.target.value)} style={darkInputStyle} />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 'bold', display: 'block', marginBottom: '6px', color: '#cbd5e1' }}>Category Allocations (Optional)</label>
                {EXPENSE_CATEGORIES.map((c) => (
                  <div key={c} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', color: '#cbd5e1' }}>{c}</span>
                    <input
                      type="number"
                      placeholder="₹0"
                      value={allocationsInput[c] || ''}
                      onChange={(e) => setAllocationsInput({ ...allocationsInput, [c]: e.target.value })}
                      style={{ width: '120px', padding: '6px 8px', borderRadius: '6px', border: '1px solid #334155', backgroundColor: '#0f172a', color: '#fff' }}
                    />
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                <button type="submit" style={{ flex: 1, backgroundColor: '#2563eb', color: '#fff', padding: '10px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Save to Backend</button>
                <button type="button" onClick={() => setShowBudgetModal(false)} style={{ flex: 1, backgroundColor: '#334155', color: '#cbd5e1', padding: '10px', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [msg, setMsg] = useState({ type: '', text: '' });
  const [section, setSection] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [summary, setSummary] = useState({ total_income: 0, total_expenses: 0, balance: 0, income_count: 0, expense_count: 0 });

  const [expenses, setExpenses] = useState([]);
  const [expLoading, setExpLoading] = useState(true);
  const [filterExpCat, setFilterExpCat] = useState('');
  const [showExpForm, setShowExpForm] = useState(false);
  const [expCreate, setExpCreate] = useState({ ...emptyExpense });
  const [creatingExp, setCreatingExp] = useState(false);
  const [editExpId, setEditExpId] = useState(null);
  const [editExpData, setEditExpData] = useState({ ...emptyExpense });
  const [editingExp, setEditingExp] = useState(false);

  const [incomes, setIncomes] = useState([]);
  const [incLoading, setIncLoading] = useState(true);
  const [filterIncSrc, setFilterIncSrc] = useState('');
  const [showIncForm, setShowIncForm] = useState(false);
  const [incCreate, setIncCreate] = useState({ ...emptyIncome });
  const [creatingInc, setCreatingInc] = useState(false);
  const [editIncId, setEditIncId] = useState(null);
  const [editIncData, setEditIncData] = useState({ ...emptyIncome });
  const [editingInc, setEditingInc] = useState(false);

  const [budgets, setBudgets] = useState([]);
  const [budgetLoading, setBudgetLoading] = useState(true);
  const [showBudgetForm, setShowBudgetForm] = useState(false);
  const [budgetCreate, setBudgetCreate] = useState({
    month: currentMonth(), year: currentYear(), total_amount: '',
    allocations: EXPENSE_CATEGORIES.map((c) => ({ category: c.value, amount: '' })),
  });
  const [creatingBudget, setCreatingBudget] = useState(false);
  const [selectedBudget, setSelectedBudget] = useState(null);

  const [savingsGoals, setSavingsGoals] = useState([]);
  const [savingsLoading, setSavingsLoading] = useState(true);
  const [showSavingsForm, setShowSavingsForm] = useState(false);
  const [savingsCreate, setSavingsCreate] = useState({ name: '', target_amount: '' });
  const [creatingSavings, setCreatingSavings] = useState(false);
  const [editSavingsId, setEditSavingsId] = useState(null);
  const [editSavingsData, setEditSavingsData] = useState({ name: '', target_amount: '' });
  const [editingSavings, setEditingSavings] = useState(false);
  const [progressGoalId, setProgressGoalId] = useState(null);
  const [progressAmount, setProgressAmount] = useState('');

  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);

  const [reportMonth, setReportMonth] = useState(currentMonth());
  const [reportYear, setReportYear] = useState(currentYear());
  const [reportData, setReportData] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [downloading, setDownloading] = useState('');
  const [reportError, setReportError] = useState('');

  const notify = (type, text) => { setMsg({ type, text }); setTimeout(() => setMsg({ type: '', text: '' }), 3000); };

  const fetchSummary = async () => { try { const r = await transactionAPI.summary(); setSummary(r.data); } catch {} };
  const fetchExpenses = async () => {
    try { setExpLoading(true); const p = filterExpCat ? { category: filterExpCat } : {}; const r = await expenseAPI.list(p); setExpenses(r.data.expenses); } catch {} finally { setExpLoading(false); }
  };
  const fetchIncomes = async () => {
    try { setIncLoading(true); const p = filterIncSrc ? { source: filterIncSrc } : {}; const r = await incomeAPI.list(p); setIncomes(r.data.incomes); } catch {} finally { setIncLoading(false); }
  };
  const fetchSavingsGoals = async () => { try { setSavingsLoading(true); const r = await savingsAPI.list(); setSavingsGoals(r.data.goals); } catch {} finally { setSavingsLoading(false); } };
  const fetchBudgets = async () => {
    try { setBudgetLoading(true); const r = await budgetAPI.list({}); setBudgets(r.data.budgets); if (r.data.budgets.length && !selectedBudget) setSelectedBudget(r.data.budgets[0]); } catch {} finally { setBudgetLoading(false); }
  };
  const fetchNotifications = async () => { try { const r = await notificationAPI.list(); setNotifications(r.data.notifications); setUnreadCount(r.data.unread_count); } catch {} };
  const markNotifRead = async (id) => { try { await notificationAPI.markRead(id); fetchNotifications(); } catch {} };
  const markAllNotifsRead = async () => { try { await notificationAPI.markAllRead(); fetchNotifications(); } catch {} };

  const fetchReport = async (m = reportMonth, y = reportYear) => {
    setReportLoading(true);
    setReportError('');
    try {
      const r = await reportAPI.monthly({ month: m, year: y });
      setReportData(r.data);
    } catch (err) {
      setReportData(null);
      setReportError(err.response?.data?.detail || 'Failed to load report');
    } finally {
      setReportLoading(false);
    }
  };

  const downloadReport = async (format) => {
    setDownloading(format);
    setReportError('');
    try {
      const r = await reportAPI.download({ month: reportMonth, year: reportYear, format });
      const blob = new Blob([r.data]);
      const url = window.URL.createObjectURL(blob);
      const ext = format === 'excel' || format === 'xlsx' || format === 'xls' ? 'xlsx' : format;
      const a = document.createElement('a');
      a.href = url;
      a.download = `budgetbuddy_report_${reportYear}-${String(reportMonth).padStart(2, '0')}.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      notify('success', `Report downloaded as ${ext.toUpperCase()}`);
    } catch (err) {
      let detail = 'Download failed';
      if (err.response?.data instanceof Blob) {
        try {
          const text = await err.response.data.text();
          detail = JSON.parse(text).detail || detail;
        } catch {}
      } else {
        detail = err.response?.data?.detail || detail;
      }
      notify('error', detail);
    } finally {
      setDownloading('');
    }
  };

  useEffect(() => { fetchSummary(); }, []);
  useEffect(() => { fetchExpenses(); }, [filterExpCat]);
  useEffect(() => { fetchIncomes(); }, [filterIncSrc]);
  useEffect(() => { fetchBudgets(); }, []);
  useEffect(() => { fetchSavingsGoals(); }, []);
  useEffect(() => { fetchNotifications(); }, []);
  useEffect(() => { if (section === 'reports') fetchReport(); }, [section]);

  const handleLogout = () => { logout(); navigate('/login'); };

  /* ── Savings ── */
  const handleSavingsCreate = async (e) => {
    e.preventDefault(); setCreatingSavings(true);
    try { await savingsAPI.create({ name: savingsCreate.name, target_amount: parseFloat(savingsCreate.target_amount) }); setSavingsCreate({ name: '', target_amount: '' }); setShowSavingsForm(false); notify('success', 'Goal created'); fetchSavingsGoals(); }
    catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
    finally { setCreatingSavings(false); }
  };
  const startEditSavings = (g) => { setEditSavingsId(g.id); setEditSavingsData({ name: g.name, target_amount: String(g.target_amount) }); setShowSavingsForm(false); setProgressGoalId(null); };
  const handleSavingsUpdate = async (e) => {
    e.preventDefault(); setEditingSavings(true);
    try { await savingsAPI.update(editSavingsId, { name: editSavingsData.name, target_amount: parseFloat(editSavingsData.target_amount) }); setEditSavingsId(null); notify('success', 'Updated'); fetchSavingsGoals(); }
    catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
    finally { setEditingSavings(false); }
  };
  const handleSavingsProgress = async (id) => {
    try { await savingsAPI.updateProgress(id, { current_saved: parseFloat(progressAmount) }); setProgressGoalId(null); setProgressAmount(''); notify('success', 'Updated'); fetchSavingsGoals(); }
    catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
  };
  const handleSavingsDelete = async (id) => {
    if (!window.confirm('Delete this goal?')) return;
    try { await savingsAPI.delete(id); notify('success', 'Deleted'); fetchSavingsGoals(); } catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
  };

  /* ── Budget ── */
  const handleBudgetAllocChange = (i, v) => { const a = [...budgetCreate.allocations]; a[i].amount = v; setBudgetCreate({ ...budgetCreate, allocations: a }); };
  const handleBudgetCreate = async (e) => {
    e.preventDefault(); setCreatingBudget(true);
    try {
      const a = budgetCreate.allocations.filter((x) => x.amount && parseFloat(x.amount) > 0).map((x) => ({ category: x.category, amount: parseFloat(x.amount) }));
      await budgetAPI.create({ month: parseInt(budgetCreate.month), year: parseInt(budgetCreate.year), total_amount: a.reduce((s, x) => s + x.amount, 0), allocations: a });
      setShowBudgetForm(false); setBudgetCreate({ month: currentMonth(), year: currentYear(), total_amount: '', allocations: EXPENSE_CATEGORIES.map((c) => ({ category: c.value, amount: '' })) });
      notify('success', 'Created'); fetchBudgets();
    } catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
    finally { setCreatingBudget(false); }
  };
  const handleBudgetDelete = async (id) => {
    if (!window.confirm('Delete?')) return;
    try { await budgetAPI.delete(id); if (selectedBudget?.id === id) setSelectedBudget(null); notify('success', 'Deleted'); fetchBudgets(); } catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
  };

  /* ── Expense ── */
  const handleExpCreateChange = (e) => setExpCreate({ ...expCreate, [e.target.name]: e.target.value });
  const handleExpCreate = async (e) => {
    e.preventDefault(); setCreatingExp(true);
    try { await expenseAPI.create({ amount: parseFloat(expCreate.amount), category: expCreate.category, description: expCreate.description, date: expCreate.date }); setExpCreate({ ...emptyExpense }); setShowExpForm(false); notify('success', 'Added'); fetchExpenses(); fetchSummary(); }
    catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
    finally { setCreatingExp(false); }
  };
  const startEditExp = (e) => { setEditExpId(e.id); setEditExpData({ amount: String(e.amount), category: e.category, description: e.description || '', date: e.date.split('T')[0] }); setShowExpForm(false); };
  const handleExpUpdate = async (e) => {
    e.preventDefault(); setEditingExp(true);
    try { const p = { category: editExpData.category, description: editExpData.description }; const a = parseFloat(editExpData.amount); if (!isNaN(a) && a > 0) p.amount = a; await expenseAPI.update(editExpId, p); setEditExpId(null); notify('success', 'Updated'); fetchExpenses(); fetchSummary(); }
    catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
    finally { setEditingExp(false); }
  };
  const handleExpDelete = async (id) => {
    if (!window.confirm('Delete?')) return;
    try { await expenseAPI.delete(id); notify('success', 'Deleted'); fetchExpenses(); fetchSummary(); } catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
  };

  /* ── Income ── */
  const handleIncCreateChange = (e) => setIncCreate({ ...incCreate, [e.target.name]: e.target.value });
  const handleIncCreate = async (e) => {
    e.preventDefault(); setCreatingInc(true);
    try { await incomeAPI.create({ amount: parseFloat(incCreate.amount), source: incCreate.source, description: incCreate.description, date: incCreate.date }); setIncCreate({ ...emptyIncome }); setShowIncForm(false); notify('success', 'Added'); fetchIncomes(); fetchSummary(); }
    catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
    finally { setCreatingInc(false); }
  };
  const startEditInc = (i) => { setEditIncId(i.id); setEditIncData({ amount: String(i.amount), source: i.source, description: i.description || '', date: i.date.split('T')[0] }); setShowIncForm(false); };
  const handleIncUpdate = async (e) => {
    e.preventDefault(); setEditingInc(true);
    try { const p = { source: editIncData.source, description: editIncData.description }; const a = parseFloat(editIncData.amount); if (!isNaN(a) && a > 0) p.amount = a; await incomeAPI.update(editIncId, p); setEditIncId(null); notify('success', 'Updated'); fetchIncomes(); fetchSummary(); }
    catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
    finally { setEditingInc(false); }
  };
  const handleIncDelete = async (id) => {
    if (!window.confirm('Delete?')) return;
    try { await incomeAPI.delete(id); notify('success', 'Deleted'); fetchIncomes(); fetchSummary(); } catch (err) { notify('error', err.response?.data?.detail || 'Failed'); }
  };

  const initials = (user?.first_name?.[0] || user?.username?.[0] || 'U').toUpperCase();
  const sectionLabel = NAV.find((n) => n.id === section)?.label || 'Overview';

  return (
    <div className="dashboard-layout">
      {msg.text && <div className={`toast ${msg.type}`}>{msg.text}</div>}
      <div className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`} onClick={() => setSidebarOpen(false)} />

      {/* ── Sidebar ── */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">B</div>
          <span className="sidebar-brand-text">BudgetBuddy</span>
        </div>
        <nav className="sidebar-nav">
          <div className="sidebar-section">Menu</div>
          {NAV.map((n) => (
            <button key={n.id} className={`sidebar-item ${section === n.id ? 'active' : ''}`}
              onClick={() => { setSection(n.id); setSidebarOpen(false); }}>
              {n.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user?.first_name || user?.username}</div>
              <div className="sidebar-user-email">{user?.email}</div>
            </div>
          </div>
          <button className="sidebar-logout" onClick={handleLogout}>Sign out</button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="main-content">
        <header className="main-header">
          <button className="mobile-menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>&#9776;</button>
          <h1>{sectionLabel}</h1>
          <div className="main-header-right">
            <div className="notif-bell-wrapper">
              <button className="notif-bell" onClick={() => setNotifOpen(!notifOpen)}>
                &#128276;
                {unreadCount > 0 && <span className="notif-badge">{unreadCount}</span>}
              </button>
              {notifOpen && (
                <div className="notif-dropdown">
                  <div className="notif-dropdown-header">
                    <span>Notifications</span>
                    {unreadCount > 0 && <button className="notif-mark-all" onClick={markAllNotifsRead}>Mark all read</button>}
                  </div>
                  <div className="notif-list">
                    {notifications.length === 0 ? (
                      <div className="notif-empty">No notifications</div>
                    ) : notifications.map((n) => (
                      <div key={n.id} className={`notif-item ${n.is_read ? '' : 'unread'}`} onClick={() => { if (!n.is_read) markNotifRead(n.id); }}>
                        <div className={`notif-dot ${n.notification_type}`} />
                        <div className="notif-content">
                          <div className="notif-message">{n.message}</div>
                          <div className="notif-time">{new Date(n.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <span style={{ fontSize: 12, color: 'var(--text-faint)' }}>
              {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
            </span>
          </div>
        </header>

        <div className="main-body">
          {/* ═══ OVERVIEW ═══ */}
          {section === 'overview' && (
            <>
              <div className="stats-grid anim-fadeInUp">
                <div className="stat-card is-income">
                  <div className="stat-indicator income">In</div>
                  <span className="stat-label">Total Income</span>
                  <span className="stat-value income">INR {summary.total_income.toFixed(2)}</span>
                </div>
                <div className="stat-card is-expense">
                  <div className="stat-indicator expense">Ex</div>
                  <span className="stat-label">Total Expenses</span>
                  <span className="stat-value expense">INR {summary.total_expenses.toFixed(2)}</span>
                </div>
                <div className="stat-card is-balance">
                  <div className="stat-indicator balance">Bl</div>
                  <span className="stat-label">Balance</span>
                  <span className="stat-value" style={{ color: summary.balance >= 0 ? 'var(--success)' : 'var(--error)' }}>
                    INR {summary.balance.toFixed(2)}
                  </span>
                </div>
              </div>
              <RecentActivity />
            </>
          )}

          {/* ═══ BUDGET ═══ */}
          {section === 'budget' && (
            <div className="section-card anim-fadeInUp">
              <div className="section-header">
                <span className="section-title"><span className="section-title-mark" /> Monthly Budgets</span>
                <div className="section-actions">
                  <button onClick={() => { setShowBudgetForm(!showBudgetForm); setSelectedBudget(null); }} className="btn-primary" style={{ width: 'auto', margin: 0, padding: '8px 16px', fontSize: 13 }}>
                    {showBudgetForm ? 'Cancel' : '+ New Budget'}
                  </button>
                </div>
              </div>
              {showBudgetForm && (
                <div className="form-card">
                  <h3>{MONTHS[budgetCreate.month]} {budgetCreate.year}</h3>
                  <form onSubmit={handleBudgetCreate}>
                    <div className="form-row">
                      <div className="form-group"><label>Month</label>
                        <select name="month" value={budgetCreate.month} onChange={(e) => setBudgetCreate({ ...budgetCreate, month: e.target.value })} required>
                          {MONTHS.slice(1).map((m, i) => (
                            <option key={i + 1} value={i + 1} disabled={Number(budgetCreate.year) < currentYear() || (Number(budgetCreate.year) === currentYear() && i + 1 < currentMonth())}>{m}</option>
                          ))}
                        </select>
                      </div>
                      <div className="form-group"><label>Year</label>
                        <select name="year" value={budgetCreate.year} onChange={(e) => {
                          const y = Number(e.target.value);
                          const m = Number(budgetCreate.month);
                          const month = y === currentYear() && m < currentMonth() ? currentMonth() : budgetCreate.month;
                          setBudgetCreate({ ...budgetCreate, year: e.target.value, month });
                        }} required>
                          {[currentYear() - 1, currentYear(), currentYear() + 1].map((y) => (
                            <option key={y} value={y} disabled={y < currentYear()}>{y}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="budget-alloc-grid">
                      {EXPENSE_CATEGORIES.map((cat, idx) => (
                        <div key={cat.value} className="budget-alloc-item">
                          <span className="budget-cat-label" style={{ color: EXPENSE_COLORS[cat.value] }}>{cat.label}</span>
                          <input type="number" value={budgetCreate.allocations[idx].amount} onChange={(e) => handleBudgetAllocChange(idx, e.target.value)} min="0" step="0.01" placeholder="0.00" className="edit-input" />
                        </div>
                      ))}
                    </div>
                    <button type="submit" className="btn-primary" style={{ width: 'auto', margin: 0 }} disabled={creatingBudget}>{creatingBudget ? 'Creating...' : 'Create Budget'}</button>
                  </form>
                </div>
              )}
              {budgetLoading ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                  {[1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 160, borderRadius: 14 }} />)}
                </div>
              ) : !budgets.length ? (
                <div className="empty-state"><div className="empty-state-mark">Bu</div><p>No budgets yet.</p></div>
              ) : (
                <div className="budget-grid">
                  {budgets.map((b) => (
                    <div key={b.id} className={`budget-card ${selectedBudget?.id === b.id ? 'active' : ''}`} onClick={() => setSelectedBudget(b)}>
                      <div className="budget-card-header">
                        <span className="budget-month">{MONTHS[b.month]} {b.year}</span>
                        <button onClick={(e) => { e.stopPropagation(); handleBudgetDelete(b.id); }} className="btn-delete btn-delete-sm">Del</button>
                      </div>
                      <div className="budget-total">INR {parseFloat(b.total_amount).toFixed(2)}</div>
                      <div className="budget-allocations">
                        {b.allocations.map((a) => (
                          <div key={a.id} className="budget-alloc-row">
                            <span className="budget-alloc-cat" style={{ color: EXPENSE_COLORS[a.category] }}>{a.category}</span>
                            <span className="budget-alloc-amt">INR {parseFloat(a.amount).toFixed(2)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ═══ SAVINGS ═══ */}
          {section === 'savings' && (
            <div className="section-card anim-fadeInUp">
              <div className="section-header">
                <span className="section-title"><span className="section-title-mark" /> Savings Goals</span>
                <div className="section-actions">
                  <button onClick={() => { setShowSavingsForm(!showSavingsForm); setEditSavingsId(null); setProgressGoalId(null); }} className="btn-primary" style={{ width: 'auto', margin: 0, padding: '8px 16px', fontSize: 13 }}>
                    {showSavingsForm ? 'Cancel' : '+ New Goal'}
                  </button>
                </div>
              </div>
              {showSavingsForm && (
                <div className="form-card">
                  <h3>Create Goal</h3>
                  <form onSubmit={handleSavingsCreate}>
                    <div className="form-row">
                      <div className="form-group"><label>Name</label><input type="text" value={savingsCreate.name} onChange={(e) => setSavingsCreate({ ...savingsCreate, name: e.target.value })} required placeholder="e.g. New Laptop" className="edit-input" /></div>
                      <div className="form-group"><label>Target (INR)</label><input type="number" value={savingsCreate.target_amount} onChange={(e) => setSavingsCreate({ ...savingsCreate, target_amount: e.target.value })} required min="0.01" step="0.01" placeholder="0.00" className="edit-input" /></div>
                    </div>
                    <button type="submit" className="btn-primary" style={{ width: 'auto', margin: 0 }} disabled={creatingSavings}>{creatingSavings ? 'Creating...' : 'Create Goal'}</button>
                  </form>
                </div>
              )}
              {savingsLoading ? (
                <div className="savings-grid">{[1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 140, borderRadius: 14 }} />)}</div>
              ) : !savingsGoals.length ? (
                <div className="empty-state"><div className="empty-state-mark">Sv</div><p>No savings goals yet.</p></div>
              ) : (
                <div className="savings-grid">
                  {savingsGoals.map((g) => (
                    <div key={g.id} className="savings-card">
                      {editSavingsId === g.id ? (
                        <div className="edit-form-inline">
                          <form onSubmit={handleSavingsUpdate}>
                            <div className="edit-form-row" style={{ marginBottom: 8 }}>
                              <input type="text" value={editSavingsData.name} onChange={(e) => setEditSavingsData({ ...editSavingsData, name: e.target.value })} required className="edit-input" placeholder="Name" />
                              <input type="number" value={editSavingsData.target_amount} onChange={(e) => setEditSavingsData({ ...editSavingsData, target_amount: e.target.value })} required min="0.01" step="0.01" className="edit-input" placeholder="Target" />
                            </div>
                            <div className="edit-form-row">
                              <button type="submit" className="btn-save" disabled={editingSavings}>{editingSavings ? 'Saving...' : 'Save'}</button>
                              <button type="button" className="btn-cancel" onClick={() => setEditSavingsId(null)}>Cancel</button>
                            </div>
                          </form>
                        </div>
                      ) : (
                        <>
                          <div className="savings-card-header">
                            <div className="savings-card-name">
                              {g.name}
                              {g.is_completed && <span className="savings-badge">Done</span>}
                            </div>
                            <div className="item-actions">
                              {!g.is_completed && <button onClick={() => { setProgressGoalId(progressGoalId === g.id ? null : g.id); setProgressAmount(''); }} className="btn-edit">Add</button>}
                              {!g.is_completed && <button onClick={() => startEditSavings(g)} className="btn-edit">Edit</button>}
                              <button onClick={() => handleSavingsDelete(g.id)} className="btn-delete">Del</button>
                            </div>
                          </div>
                          <div className="savings-info">
                            <span>INR {parseFloat(g.current_saved).toFixed(2)} / {parseFloat(g.target_amount).toFixed(2)}</span>
                            <span>{g.progress_percent}%</span>
                          </div>
                          <div className="savings-bar">
                            <div className={`savings-fill ${g.is_completed ? 'completed' : ''}`} style={{ width: `${g.progress_percent}%` }} />
                          </div>
                          {progressGoalId === g.id && (
                            <div className="edit-form-row" style={{ marginTop: 8 }}>
                              <input type="number" value={progressAmount} onChange={(e) => setProgressAmount(e.target.value)} min="0" step="0.01" placeholder="Amount" className="edit-input" style={{ maxWidth: 160 }} />
                              <button className="btn-save" onClick={() => handleSavingsProgress(g.id)}>Update</button>
                              <button className="btn-cancel" onClick={() => setProgressGoalId(null)}>Cancel</button>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ═══ INCOME ═══ */}
          {section === 'income' && (
            <div className="section-card anim-fadeInUp">
              <div className="section-header">
                <span className="section-title"><span className="section-title-mark" /> Income</span>
                <div className="section-actions">
                  <select value={filterIncSrc} onChange={(e) => setFilterIncSrc(e.target.value)} className="filter-select">
                    <option value="">All Sources</option>
                    {INCOME_SOURCES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                  <button onClick={() => { setShowIncForm(!showIncForm); setEditIncId(null); }} className="btn-primary" style={{ width: 'auto', margin: 0, padding: '8px 16px', fontSize: 13 }}>
                    {showIncForm ? 'Cancel' : '+ Add'}
                  </button>
                </div>
              </div>
              {showIncForm && (
                <div className="form-card">
                  <h3>New Income</h3>
                  <form onSubmit={handleIncCreate}>
                    <div className="form-row">
                      <div className="form-group"><label>Amount (INR)</label><input type="number" name="amount" value={incCreate.amount} onChange={handleIncCreateChange} required min="0.01" step="0.01" placeholder="0.00" /></div>
                      <div className="form-group"><label>Source</label><select name="source" value={incCreate.source} onChange={handleIncCreateChange} required>{INCOME_SOURCES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}</select></div>
                      <div className="form-group"><label>Date</label><input type="date" name="date" value={incCreate.date} onChange={handleIncCreateChange} required /></div>
                    </div>
                    <div className="form-group"><label>Description</label><input type="text" name="description" value={incCreate.description} onChange={handleIncCreateChange} placeholder="Details" /></div>
                    <button type="submit" className="btn-primary" style={{ width: 'auto', margin: 0 }} disabled={creatingInc}>{creatingInc ? 'Adding...' : 'Add Income'}</button>
                  </form>
                </div>
              )}
              {incLoading ? (
                <div className="item-list">{[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 52, borderRadius: 10 }} />)}</div>
              ) : !incomes.length ? (
                <div className="empty-state"><div className="empty-state-mark">In</div><p>No income records yet.</p></div>
              ) : (
                <div className="item-list">
                  {incomes.map((inc) => (
                    <div key={inc.id} className="list-item">
                      {editIncId === inc.id ? (
                        <div className="edit-form-inline">
                          <form onSubmit={handleIncUpdate}>
                            <div className="edit-form-row" style={{ marginBottom: 8 }}>
                              <input type="number" name="amount" value={editIncData.amount} onChange={(e) => setEditIncData({ ...editIncData, amount: e.target.value })} required min="0.01" step="0.01" className="edit-input" />
                              <select name="source" value={editIncData.source} onChange={(e) => setEditIncData({ ...editIncData, source: e.target.value })} required className="edit-select">{INCOME_SOURCES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}</select>
                            </div>
                            <div className="edit-form-row">
                              <input type="text" name="description" value={editIncData.description} onChange={(e) => setEditIncData({ ...editIncData, description: e.target.value })} placeholder="Description" className="edit-input edit-input-desc" />
                              <button type="submit" className="btn-save" disabled={editingInc}>{editingInc ? 'Saving...' : 'Save'}</button>
                              <button type="button" className="btn-cancel" onClick={() => setEditIncId(null)}>Cancel</button>
                            </div>
                          </form>
                        </div>
                      ) : (
                        <>
                          <div className="item-tag" style={{ backgroundColor: INCOME_COLORS[inc.source] }}>{inc.source.replace('_', ' ')}</div>
                          <div className="item-content">
                            <div className="item-title">{inc.description || 'No description'}</div>
                            <div className="item-meta">{inc.date}</div>
                          </div>
                          <div className="item-amount income">INR {parseFloat(inc.amount).toFixed(2)}</div>
                          <div className="item-actions">
                            <button onClick={() => startEditInc(inc)} className="btn-edit">Edit</button>
                            <button onClick={() => handleIncDelete(inc.id)} className="btn-delete">Del</button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ═══ EXPENSES ═══ */}
          {section === 'expenses' && (
            <div className="section-card anim-fadeInUp">
              <div className="section-header">
                <span className="section-title"><span className="section-title-mark" /> Expenses</span>
                <div className="section-actions">
                  <select value={filterExpCat} onChange={(e) => setFilterExpCat(e.target.value)} className="filter-select">
                    <option value="">All Categories</option>
                    {EXPENSE_CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                  <button onClick={() => { setShowExpForm(!showExpForm); setEditExpId(null); }} className="btn-primary" style={{ width: 'auto', margin: 0, padding: '8px 16px', fontSize: 13 }}>
                    {showExpForm ? 'Cancel' : '+ Add'}
                  </button>
                </div>
              </div>
              {showExpForm && (
                <div className="form-card">
                  <h3>New Expense</h3>
                  <form onSubmit={handleExpCreate}>
                    <div className="form-row">
                      <div className="form-group"><label>Amount (INR)</label><input type="number" name="amount" value={expCreate.amount} onChange={handleExpCreateChange} required min="0.01" step="0.01" placeholder="0.00" /></div>
                      <div className="form-group"><label>Category</label><select name="category" value={expCreate.category} onChange={handleExpCreateChange} required>{EXPENSE_CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}</select></div>
                      <div className="form-group"><label>Date</label><input type="date" name="date" value={expCreate.date} onChange={handleExpCreateChange} required /></div>
                    </div>
                    <div className="form-group"><label>Description</label><input type="text" name="description" value={expCreate.description} onChange={handleExpCreateChange} placeholder="What for?" /></div>
                    <button type="submit" className="btn-primary" style={{ width: 'auto', margin: 0 }} disabled={creatingExp}>{creatingExp ? 'Adding...' : 'Add Expense'}</button>
                  </form>
                </div>
              )}
              {expLoading ? (
                <div className="item-list">{[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 52, borderRadius: 10 }} />)}</div>
              ) : !expenses.length ? (
                <div className="empty-state"><div className="empty-state-mark">Ex</div><p>No expenses yet.</p></div>
              ) : (
                <div className="item-list">
                  {expenses.map((exp) => (
                    <div key={exp.id} className="list-item">
                      {editExpId === exp.id ? (
                        <div className="edit-form-inline">
                          <form onSubmit={handleExpUpdate}>
                            <div className="edit-form-row" style={{ marginBottom: 8 }}>
                              <input type="number" name="amount" value={editExpData.amount} onChange={(e) => setEditExpData({ ...editExpData, amount: e.target.value })} required min="0.01" step="0.01" className="edit-input" />
                              <select name="category" value={editExpData.category} onChange={(e) => setEditExpData({ ...editExpData, category: e.target.value })} required className="edit-select">{EXPENSE_CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}</select>
                            </div>
                            <div className="edit-form-row">
                              <input type="text" name="description" value={editExpData.description} onChange={(e) => setEditExpData({ ...editExpData, description: e.target.value })} placeholder="Description" className="edit-input edit-input-desc" />
                              <button type="submit" className="btn-save" disabled={editingExp}>{editingExp ? 'Saving...' : 'Save'}</button>
                              <button type="button" className="btn-cancel" onClick={() => setEditExpId(null)}>Cancel</button>
                            </div>
                          </form>
                        </div>
                      ) : (
                        <>
                          <div className="item-tag" style={{ backgroundColor: EXPENSE_COLORS[exp.category] }}>{exp.category}</div>
                          <div className="item-content">
                            <div className="item-title">{exp.description || 'No description'}</div>
                            <div className="item-meta">{exp.date}</div>
                          </div>
                          <div className="item-amount">INR {parseFloat(exp.amount).toFixed(2)}</div>
                          <div className="item-actions">
                            <button onClick={() => startEditExp(exp)} className="btn-edit">Edit</button>
                            <button onClick={() => handleExpDelete(exp.id)} className="btn-delete">Del</button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ═══ ANALYTICS ═══ */}
          {section === 'analytics' && <AnalyticsSection />}

          {/* ═══ REPORTS ═══ */}
          {section === 'reports' && (
            <div className="section-card anim-fadeInUp">
              <div className="section-header">
                <span className="section-title"><span className="section-title-mark" /> Monthly Reports</span>
                <div className="section-actions">
                  <select value={reportMonth} onChange={(e) => { const m = Number(e.target.value); setReportMonth(m); fetchReport(m, reportYear); }} className="filter-select">
                    {MONTHS.slice(1).map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
                  </select>
                  <select value={reportYear} onChange={(e) => { const y = Number(e.target.value); setReportYear(y); fetchReport(reportMonth, y); }} className="filter-select">
                    <option value={2025}>2025</option><option value={2026}>2026</option><option value={2027}>2027</option>
                  </select>
                </div>
              </div>

              <div className="report-downloads">
                <button className="btn-report" onClick={() => downloadReport('pdf')} disabled={!!downloading || reportLoading}>
                  {downloading === 'pdf' ? 'Downloading…' : '⬇ PDF'}
                </button>
                <button className="btn-report" onClick={() => downloadReport('excel')} disabled={!!downloading || reportLoading}>
                  {downloading === 'excel' ? 'Downloading…' : '⬇ Excel'}
                </button>
                <button className="btn-report" onClick={() => downloadReport('csv')} disabled={!!downloading || reportLoading}>
                  {downloading === 'csv' ? 'Downloading…' : '⬇ CSV'}
                </button>
                <button className="btn-report btn-report-ghost" onClick={() => fetchReport()} disabled={reportLoading || !!downloading}>
                  {reportLoading ? 'Loading…' : 'Refresh'}
                </button>
              </div>

              {reportError && <div className="report-error">{reportError}</div>}

              {reportLoading ? (
                <div className="item-list">{[1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 52, borderRadius: 10 }} />)}</div>
              ) : reportData ? (
                <>
                  <div className="stats-grid" style={{ marginTop: 8 }}>
                    <div className="stat-card is-income">
                      <div className="stat-indicator income">In</div>
                      <span className="stat-label">Income</span>
                      <span className="stat-value income">INR {Number(reportData.income?.total ?? 0).toFixed(2)}</span>
                    </div>
                    <div className="stat-card is-expense">
                      <div className="stat-indicator expense">Ex</div>
                      <span className="stat-label">Expenses</span>
                      <span className="stat-value expense">INR {Number(reportData.expenses?.total ?? 0).toFixed(2)}</span>
                    </div>
                    <div className="stat-card is-balance">
                      <div className="stat-indicator balance">Bl</div>
                      <span className="stat-label">Net Savings</span>
                      <span className="stat-value" style={{ color: reportData.net_savings >= 0 ? 'var(--success)' : 'var(--error)' }}>
                        INR {Number(reportData.net_savings ?? 0).toFixed(2)}
                      </span>
                    </div>
                  </div>

                  <div className="report-meta">
                    {MONTHS[reportMonth]} {reportData.year} · Savings rate {Number(reportData.savings_rate_percent ?? 0).toFixed(1)}% · {reportData.transaction_count ?? 0} transactions
                  </div>

                  {reportData.expenses?.breakdown?.length > 0 && (
                    <div className="report-block">
                      <h4>Expenses by Category</h4>
                      <div className="item-list">
                        {reportData.expenses.breakdown.map((c) => (
                          <div key={c.label} className="list-item">
                            <div className="item-tag" style={{ backgroundColor: EXPENSE_COLORS[c.label] || 'var(--primary)' }}>{c.label}</div>
                            <div className="item-content">
                              <div className="item-title">INR {Number(c.total).toFixed(2)}</div>
                              <div className="item-meta">{c.count} transactions · {c.percent}% of expenses</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {reportData.income?.breakdown?.length > 0 && (
                    <div className="report-block">
                      <h4>Income Sources</h4>
                      <div className="item-list">
                        {reportData.income.breakdown.map((c) => (
                          <div key={c.label} className="list-item">
                            <div className="item-tag" style={{ backgroundColor: INCOME_COLORS[c.label] || 'var(--success)' }}>{c.label}</div>
                            <div className="item-content">
                              <div className="item-title">INR {Number(c.total).toFixed(2)}</div>
                              <div className="item-meta">{c.count} transactions · {c.percent}% of income</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {reportData.budget?.allocations?.length > 0 && (
                    <div className="report-block">
                      <h4>Budget Utilization</h4>
                      <div className="item-list">
                        {reportData.budget.allocations.map((b) => (
                          <div key={b.category} className="list-item">
                            <div className="item-tag" style={{ backgroundColor: EXPENSE_COLORS[b.category] || 'var(--primary)' }}>{b.category}</div>
                            <div className="item-content">
                              <div className="item-title">{Number(b.utilization_percent).toFixed(1)}% used</div>
                              <div className="item-meta">INR {Number(b.spent).toFixed(2)} of {Number(b.budgeted).toFixed(2)}</div>
                              <div className="savings-bar" style={{ marginTop: 6 }}>
                                <div className={`savings-fill ${b.utilization_percent >= 100 ? 'completed' : ''}`} style={{ width: `${Math.min(Number(b.utilization_percent), 100)}%`, backgroundColor: b.utilization_percent >= 100 ? 'var(--error)' : undefined }} />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="empty-state"><div className="empty-state-mark">Rp</div><p>No report loaded.</p></div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import "./Dashboard.css";

const API = import.meta.env.VITE_API_URL;

function Dashboard() {
  const navigate = useNavigate();

  const [expenses, setExpenses] = useState([]);
  const [income, setIncome] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [savingsGoals, setSavingsGoals] = useState([]);
  const [notifications, setNotifications] = useState([]);

  const [analyticsData, setAnalyticsData] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [analyticsError, setAnalyticsError] = useState("");

  const [loading, setLoading] = useState(true);

  const [expenseForm, setExpenseForm] = useState({
    category: "",
    amount: "",
    date: "",
    description: "",
  });

  const [incomeForm, setIncomeForm] = useState({
    source: "",
    amount: "",
    date: "",
    description: "",
  });

  const [budgetForm, setBudgetForm] = useState({
    category: "",
    amount: "",
    start_date: "",
    end_date: "",
  });

  const [savingsForm, setSavingsForm] = useState({
    name: "",
    target_amount: "",
    current_amount: "",
    target_date: "",
  });

  const getToken = () => {
    return localStorage.getItem("access_token");
  };

  const authHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
  });

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  };

  const loadDashboardData = async () => {
    const token = getToken();

    if (!token) {
      navigate("/login");
      return;
    }

    setAnalyticsLoading(true);
    setAnalyticsError("");

    try {
      const headers = {
        Authorization: `Bearer ${token}`,
      };

      const [
        expensesResponse,
        incomeResponse,
        budgetsResponse,
        savingsResponse,
        notificationsResponse,
        analyticsResponse,
      ] = await Promise.all([
        fetch(`${API}/my-expenses/`, { headers }),
        fetch(`${API}/my-income/`, { headers }),
        fetch(`${API}/my-budgets/`, { headers }),
        fetch(`${API}/my-savings-goals/`, { headers }),
        fetch(`${API}/my-notifications/`, { headers }),
        fetch(`${API}/analytics/`, { headers }),
      ]);

      if (
        expensesResponse.status === 401 ||
        incomeResponse.status === 401 ||
        budgetsResponse.status === 401 ||
        savingsResponse.status === 401 ||
        notificationsResponse.status === 401 ||
        analyticsResponse.status === 401
      ) {
        alert("Session expired. Please login again.");
        handleLogout();
        return;
      }

      const expensesData = await expensesResponse.json();
      const incomeData = await incomeResponse.json();
      const budgetsData = await budgetsResponse.json();
      const savingsData = await savingsResponse.json();
      const notificationsData = await notificationsResponse.json();

      setExpenses(Array.isArray(expensesData) ? expensesData : []);
      setIncome(Array.isArray(incomeData) ? incomeData : []);
      setBudgets(Array.isArray(budgetsData) ? budgetsData : []);
      setSavingsGoals(Array.isArray(savingsData) ? savingsData : []);
      setNotifications(
        Array.isArray(notificationsData)
          ? notificationsData
          : []
      );

      if (!analyticsResponse.ok) {
        const errorData = await analyticsResponse
          .json()
          .catch(() => ({}));

        console.error("Analytics API error:", errorData);

        setAnalyticsError("Unable to load analytics data.");
        setAnalyticsData(null);
      } else {
        const analyticsResult = await analyticsResponse.json();

        console.log("Analytics API response:", analyticsResult);

        setAnalyticsData(analyticsResult);
        setAnalyticsError("");
      }
    } catch (error) {
      console.error("Dashboard loading error:", error);

      setAnalyticsError(
        "Unable to connect to the analytics service."
      );

      setAnalyticsData(null);
    } finally {
      setLoading(false);
      setAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleMarkNotificationRead = async (id) => {
    try {
      const response = await fetch(
        `${API}/notifications/${id}/read/`,
        {
          method: "POST",
          headers: authHeaders(),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        console.error(await response.json());
        alert("Could not mark notification as read.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Notification read error:", error);
    }
  };

  const handleExpenseSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API}/expenses/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          category: expenseForm.category,
          amount: Number(expenseForm.amount),
          date: expenseForm.date,
          description: expenseForm.description,
        }),
      });

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();

        console.error("Expense error:", errorData);

        alert("Could not add expense.");
        return;
      }

      setExpenseForm({
        category: "",
        amount: "",
        date: "",
        description: "",
      });

      await loadDashboardData();

      alert("Expense added successfully!");
    } catch (error) {
      console.error("Error adding expense:", error);
      alert("Could not add expense.");
    }
  };

  const handleEditExpense = async (expense) => {
    const category = window.prompt(
      "Enter category:",
      expense.category
    );

    if (category === null) return;

    const amount = window.prompt(
      "Enter amount:",
      expense.amount
    );

    if (amount === null) return;

    const date = window.prompt(
      "Enter date (YYYY-MM-DD):",
      expense.date
    );

    if (date === null) return;

    const description = window.prompt(
      "Enter description:",
      expense.description || ""
    );

    if (description === null) return;

    try {
      const response = await fetch(
        `${API}/expenses/${expense.id}/`,
        {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify({
            category,
            amount: Number(amount),
            date,
            description,
          }),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        console.error(await response.json());
        alert("Could not edit expense.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Edit expense error:", error);
    }
  };

  const handleDeleteExpense = async (id) => {
    if (!window.confirm("Delete this expense?")) {
      return;
    }

    try {
      const response = await fetch(
        `${API}/expenses/${id}/`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        alert("Could not delete expense.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Delete expense error:", error);
    }
  };

  const handleIncomeSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API}/income/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          source: incomeForm.source,
          amount: Number(incomeForm.amount),
          date: incomeForm.date,
          description: incomeForm.description,
        }),
      });

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        console.error(await response.json());
        alert("Could not add income.");
        return;
      }

      setIncomeForm({
        source: "",
        amount: "",
        date: "",
        description: "",
      });

      await loadDashboardData();
    } catch (error) {
      console.error("Add income error:", error);
    }
  };

  const handleEditIncome = async (item) => {
    const source = window.prompt(
      "Enter income source:",
      item.source
    );

    if (source === null) return;

    const amount = window.prompt(
      "Enter amount:",
      item.amount
    );

    if (amount === null) return;

    const date = window.prompt(
      "Enter date (YYYY-MM-DD):",
      item.date
    );

    if (date === null) return;

    const description = window.prompt(
      "Enter description:",
      item.description || ""
    );

    if (description === null) return;

    try {
      const response = await fetch(
        `${API}/income/${item.id}/`,
        {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify({
            source,
            amount: Number(amount),
            date,
            description,
          }),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        console.error(await response.json());
        alert("Could not edit income.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Edit income error:", error);
    }
  };

  const handleDeleteIncome = async (id) => {
    if (!window.confirm("Delete this income?")) {
      return;
    }

    try {
      const response = await fetch(
        `${API}/income/${id}/`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        alert("Could not delete income.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Delete income error:", error);
    }
  };

  const handleBudgetSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API}/budgets/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          category: budgetForm.category,
          amount: Number(budgetForm.amount),
          start_date: budgetForm.start_date,
          end_date: budgetForm.end_date,
        }),
      });

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        console.error(await response.json());
        alert("Could not add budget.");
        return;
      }

      setBudgetForm({
        category: "",
        amount: "",
        start_date: "",
        end_date: "",
      });

      await loadDashboardData();
    } catch (error) {
      console.error("Add budget error:", error);
    }
  };

  const handleEditBudget = async (budget) => {
    const category = window.prompt(
      "Enter budget category:",
      budget.category
    );

    if (category === null) return;

    const amount = window.prompt(
      "Enter budget amount:",
      budget.amount
    );

    if (amount === null) return;

    const start_date = window.prompt(
      "Enter start date (YYYY-MM-DD):",
      budget.start_date
    );

    if (start_date === null) return;

    const end_date = window.prompt(
      "Enter end date (YYYY-MM-DD):",
      budget.end_date
    );

    if (end_date === null) return;

    try {
      const response = await fetch(
        `${API}/budgets/${budget.id}/`,
        {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify({
            category,
            amount: Number(amount),
            start_date,
            end_date,
          }),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        console.error(await response.json());
        alert("Could not edit budget.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Edit budget error:", error);
    }
  };

  const handleDeleteBudget = async (id) => {
    if (!window.confirm("Delete this budget?")) {
      return;
    }

    try {
      const response = await fetch(
        `${API}/budgets/${id}/`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        alert("Could not delete budget.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Delete budget error:", error);
    }
  };

  const handleSavingsSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(
        `${API}/savings-goals/`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            name: savingsForm.name,
            target_amount: Number(
              savingsForm.target_amount
            ),
            current_amount: Number(
              savingsForm.current_amount
            ),
            target_date: savingsForm.target_date,
          }),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        console.error(await response.json());
        alert("Could not add savings goal.");
        return;
      }

      setSavingsForm({
        name: "",
        target_amount: "",
        current_amount: "",
        target_date: "",
      });

      await loadDashboardData();
    } catch (error) {
      console.error("Add savings error:", error);
    }
  };

  const handleEditSavingsGoal = async (goal) => {
    const name = window.prompt(
      "Enter savings goal name:",
      goal.name
    );

    if (name === null) return;

    const target_amount = window.prompt(
      "Enter target amount:",
      goal.target_amount
    );

    if (target_amount === null) return;

    const current_amount = window.prompt(
      "Enter current savings:",
      goal.current_amount
    );

    if (current_amount === null) return;

    const target_date = window.prompt(
      "Enter target date (YYYY-MM-DD):",
      goal.target_date
    );

    if (target_date === null) return;

    try {
      const response = await fetch(
        `${API}/savings-goals/${goal.id}/`,
        {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify({
            name,
            target_amount: Number(target_amount),
            current_amount: Number(current_amount),
            target_date,
          }),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        console.error(await response.json());
        alert("Could not edit savings goal.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Edit savings error:", error);
    }
  };

  const handleDeleteSavingsGoal = async (id) => {
    if (!window.confirm("Delete this savings goal?")) {
      return;
    }

    try {
      const response = await fetch(
        `${API}/savings-goals/${id}/`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (!response.ok) {
        alert("Could not delete savings goal.");
        return;
      }

      await loadDashboardData();
    } catch (error) {
      console.error("Delete savings error:", error);
    }
  };

  const totalBudget = budgets.reduce(
    (total, item) =>
      total + Number(item.amount || 0),
    0
  );

  const analyticsIncome = Number(
    analyticsData?.summary?.total_income || 0
  );

  const analyticsExpenses = Number(
    analyticsData?.summary?.total_expenses || 0
  );

  const analyticsBalance = Number(
    analyticsData?.summary?.balance || 0
  );

  const categoryWiseExpenses = Array.isArray(
    analyticsData?.category_wise_expenses
  )
    ? analyticsData.category_wise_expenses
    : [];

  const expenseCategoryData = categoryWiseExpenses
    .filter(
      (item) => Number(item.amount || 0) > 0
    )
    .map((item) => ({
      name: item.category || "Other",
      value: Number(item.amount || 0),
    }));

  const monthlyTrends = Array.isArray(
    analyticsData?.monthly_trends
  )
    ? analyticsData.monthly_trends
    : [];

  const monthlyTrendData = monthlyTrends.map(
    (item) => ({
      month: item.month || "",
      Income: Number(item.income || 0),
      Expenses: Number(item.expense || 0),
    })
  );

  const savingsSummary =
    analyticsData?.savings_summary || {};

  const savingsTarget = Number(
    savingsSummary.total_target || 0
  );

  const currentSavings = Number(
    savingsSummary.total_saved || 0
  );

  const savingsRemaining = Number(
    savingsSummary.remaining || 0
  );

  const savingsCompletion = Number(
    savingsSummary.completion_percentage || 0
  );

  const safeSavingsPercentage = Math.min(
    100,
    Math.max(0, savingsCompletion)
  );

  const chartColors = [
    "#ef4444",
    "#3b82f6",
    "#22c55e",
    "#f59e0b",
    "#8b5cf6",
    "#ec4899",
  ];

  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard-container">
          <h2>Loading BudgetBuddy...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-container">

        <nav className="dashboard-nav">

          <h2>💰 BudgetBuddy</h2>

          <div className="nav-buttons">

            <button
              type="button"
              onClick={() => navigate("/profile")}
            >
              👤 Profile
            </button>

            <button
              type="button"
              onClick={() => navigate("/reports")}
            >
              📊 Reports
            </button>

            <button
              type="button"
              onClick={handleLogout}
            >
              🚪 Logout
            </button>

          </div>

        </nav>

        <div className="dashboard-title">

          <h1>💰 BudgetBuddy Dashboard</h1>

          <p>
            Manage your income, expenses,
            budgets and savings.
          </p>

        </div>

        <div className="analytics-dashboard">

          <h2>📊 Analytics Dashboard</h2>

          {analyticsLoading && (
            <div className="section">
              <p>Loading analytics data...</p>
            </div>
          )}

          {!analyticsLoading && analyticsError && (
            <div className="section">

              <p>❌ {analyticsError}</p>

              <button
                type="button"
                onClick={loadDashboardData}
              >
                🔄 Retry
              </button>

            </div>
          )}

          {!analyticsLoading &&
            !analyticsError &&
            analyticsData && (
              <>

                <div className="section">

                  <h2>💰 Financial Summary</h2>

                  <div className="summary-grid">

                    <div className="summary-card">

                      <h3>💵 Total Income</h3>

                      <h2>
                        ₹
                        {analyticsIncome.toFixed(2)}
                      </h2>

                    </div>

                    <div className="summary-card">

                      <h3>💸 Total Expenses</h3>

                      <h2>
                        ₹
                        {analyticsExpenses.toFixed(2)}
                      </h2>

                    </div>

                    <div className="summary-card">

                      <h3>💰 Balance</h3>

                      <h2>
                        ₹
                        {analyticsBalance.toFixed(2)}
                      </h2>

                    </div>

                    <div className="summary-card">

                      <h3>📊 Total Budget</h3>

                      <h2>
                        ₹
                        {totalBudget.toFixed(2)}
                      </h2>

                    </div>

                  </div>

                </div>

                <div className="section">

                  <h2>
                    💵 Income & Expense Summary
                  </h2>

                  {analyticsIncome === 0 &&
                  analyticsExpenses === 0 ? (

                    <p>
                      No income or expense data
                      available.
                    </p>

                  ) : (

                    <div className="chart-card">

                      <h3>
                        Income vs Expenses
                      </h3>

                      <ResponsiveContainer
                        width="100%"
                        height={320}
                      >

                        <BarChart
                          data={[
                            {
                              name: "Finance",
                              Income:
                                analyticsIncome,
                              Expenses:
                                analyticsExpenses,
                            },
                          ]}
                        >

                          <CartesianGrid
                            strokeDasharray="3 3"
                          />

                          <XAxis dataKey="name" />

                          <YAxis
                            tickFormatter={(value) =>
                              `₹${value}`
                            }
                          />

                          <Tooltip
                            formatter={(value) =>
                              `₹${Number(value).toFixed(2)}`
                            }
                          />

                          <Legend />

                          <Bar
                            dataKey="Income"
                            fill="#22c55e"
                            name="Income"
                          />

                          <Bar
                            dataKey="Expenses"
                            fill="#ef4444"
                            name="Expenses"
                          />

                        </BarChart>

                      </ResponsiveContainer>

                    </div>

                  )}

                </div>

                <div className="section">

                  <h2>🛒 Category-wise Spending</h2>

                  {expenseCategoryData.length === 0 ? (

                    <p>
                      No expense data available
                      for category analysis.
                    </p>

                  ) : (

                    <div className="chart-card">

                      <h3>
                        Expense by Category
                      </h3>

                      <ResponsiveContainer
                        width="100%"
                        height={400}
                      >

                        <PieChart>

                          <Pie
                            data={expenseCategoryData}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            outerRadius={120}
                            label={({ name, value }) =>
                              `${name}: ₹${Number(value).toFixed(0)}`
                            }
                          >

                            {expenseCategoryData.map(
                              (entry, index) => (

                                <Cell
                                  key={`${entry.name}-${index}`}
                                  fill={
                                    chartColors[
                                      index %
                                      chartColors.length
                                    ]
                                  }
                                />

                              )
                            )}

                          </Pie>

                          <Tooltip
                            formatter={(value) =>
                              `₹${Number(value).toFixed(2)}`
                            }
                          />

                          <Legend />

                        </PieChart>

                      </ResponsiveContainer>

                    </div>

                  )}

                </div>

                <div className="section">

                  <h2>
                    📈 Monthly Income & Expense Trends
                  </h2>

                  {monthlyTrendData.length === 0 ? (

                    <p>
                      No monthly trend data available.
                    </p>

                  ) : (

                    <div className="chart-card">

                      <h3>
                        Monthly Income vs Expenses
                      </h3>

                      <ResponsiveContainer
                        width="100%"
                        height={350}
                      >

                        <LineChart
                          data={monthlyTrendData}
                          margin={{
                            top: 20,
                            right: 30,
                            left: 20,
                            bottom: 20,
                          }}
                        >

                          <CartesianGrid
                            strokeDasharray="3 3"
                          />

                          <XAxis dataKey="month" />

                          <YAxis
                            tickFormatter={(value) =>
                              `₹${value}`
                            }
                          />

                          <Tooltip
                            formatter={(value) =>
                              `₹${Number(value).toFixed(2)}`
                            }
                          />

                          <Legend />

                          <Line
                            type="monotone"
                            dataKey="Income"
                            stroke="#22c55e"
                            strokeWidth={3}
                            dot={{ r: 5 }}
                            name="Income"
                          />

                          <Line
                            type="monotone"
                            dataKey="Expenses"
                            stroke="#ef4444"
                            strokeWidth={3}
                            dot={{ r: 5 }}
                            name="Expenses"
                          />

                        </LineChart>

                      </ResponsiveContainer>

                    </div>

                  )}

                </div>

                <div className="section">

                  <h2>🎯 Savings Progress</h2>

                  {savingsTarget === 0 &&
                  currentSavings === 0 ? (

                    <p>
                      No savings data available.
                    </p>

                  ) : (

                    <div className="chart-card">

                      <h3>
                        Overall Savings Progress
                      </h3>

                      <div
                        style={{
                          marginBottom: "20px",
                        }}
                      >

                        <p>
                          <strong>Saved:</strong>{" "}
                          ₹
                          {currentSavings.toFixed(2)}
                        </p>

                        <p>
                          <strong>Target:</strong>{" "}
                          ₹
                          {savingsTarget.toFixed(2)}
                        </p>

                        <p>
                          <strong>Remaining:</strong>{" "}
                          ₹
                          {savingsRemaining.toFixed(2)}
                        </p>

                        <p>
                          <strong>Completion:</strong>{" "}
                          {safeSavingsPercentage.toFixed(
                            1
                          )}
                          %
                        </p>

                      </div>

                      <div
                        style={{
                          width: "100%",
                          height: "30px",
                          backgroundColor: "#e5e7eb",
                          borderRadius: "15px",
                          overflow: "hidden",
                          marginBottom: "20px",
                        }}
                      >

                        <div
                          style={{
                            width: `${safeSavingsPercentage}%`,
                            height: "100%",
                            backgroundColor: "#3b82f6",
                            borderRadius: "15px",
                            transition:
                              "width 0.5s ease",
                          }}
                        />

                      </div>

                      <ResponsiveContainer
                        width="100%"
                        height={280}
                      >

                        <BarChart
                          data={[
                            {
                              name: "Savings",
                              Saved:
                                currentSavings,
                              Target:
                                savingsTarget,
                            },
                          ]}
                        >

                          <CartesianGrid
                            strokeDasharray="3 3"
                          />

                          <XAxis dataKey="name" />

                          <YAxis
                            tickFormatter={(value) =>
                              `₹${value}`
                            }
                          />

                          <Tooltip
                            formatter={(value) =>
                              `₹${Number(value).toFixed(2)}`
                            }
                          />

                          <Legend />

                          <Bar
                            dataKey="Saved"
                            fill="#3b82f6"
                            name="Saved"
                          />

                          <Bar
                            dataKey="Target"
                            fill="#8b5cf6"
                            name="Target"
                          />

                        </BarChart>

                      </ResponsiveContainer>

                    </div>

                  )}

                </div>

              </>
            )}

        </div>

        <div className="section">

          <h2>➕ Add Expense</h2>

          <form
            className="form"
            onSubmit={handleExpenseSubmit}
          >

            <select
              value={expenseForm.category}
              onChange={(e) =>
                setExpenseForm({
                  ...expenseForm,
                  category: e.target.value,
                })
              }
              required
            >

              <option value="">
                Select Category
              </option>

              <option value="Food">Food</option>
              <option value="Travel">Travel</option>
              <option value="Shopping">Shopping</option>
              <option value="Education">
                Education
              </option>
              <option value="Entertainment">
                Entertainment
              </option>
              <option value="Miscellaneous">
                Miscellaneous
              </option>

            </select>

            <input
              type="number"
              placeholder="Amount"
              value={expenseForm.amount}
              onChange={(e) =>
                setExpenseForm({
                  ...expenseForm,
                  amount: e.target.value,
                })
              }
              required
            />

            <input
              type="date"
              value={expenseForm.date}
              onChange={(e) =>
                setExpenseForm({
                  ...expenseForm,
                  date: e.target.value,
                })
              }
              required
            />

            <input
              type="text"
              placeholder="Description"
              value={expenseForm.description}
              onChange={(e) =>
                setExpenseForm({
                  ...expenseForm,
                  description:
                    e.target.value,
                })
              }
            />

            <button type="submit">
              Add Expense
            </button>

          </form>

          <h2>My Expenses</h2>

          {expenses.length === 0 ? (

            <p>No expenses found.</p>

          ) : (

            <ul className="data-list">

              {expenses.map((expense) => (

                <li key={expense.id}>

                  <strong>
                    {expense.category}
                  </strong>

                  {" - ₹"}

                  {Number(
                    expense.amount
                  ).toFixed(2)}

                  {" - "}

                  {expense.date}

                  {" - "}

                  {expense.description}

                  <div
                    style={{
                      marginTop: "10px",
                    }}
                  >

                    <button
                      type="button"
                      onClick={() =>
                        handleEditExpense(
                          expense
                        )
                      }
                    >
                      ✏️ Edit
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleDeleteExpense(
                          expense.id
                        )
                      }
                      style={{
                        marginLeft: "8px",
                      }}
                    >
                      🗑️ Delete
                    </button>

                  </div>

                </li>

              ))}

            </ul>

          )}

        </div>

        <div className="section">

          <h2>➕ Add Income</h2>

          <form
            className="form"
            onSubmit={handleIncomeSubmit}
          >

            <input
              type="text"
              placeholder="Income Source"
              value={incomeForm.source}
              onChange={(e) =>
                setIncomeForm({
                  ...incomeForm,
                  source: e.target.value,
                })
              }
              required
            />

            <input
              type="number"
              placeholder="Amount"
              value={incomeForm.amount}
              onChange={(e) =>
                setIncomeForm({
                  ...incomeForm,
                  amount: e.target.value,
                })
              }
              required
            />

            <input
              type="date"
              value={incomeForm.date}
              onChange={(e) =>
                setIncomeForm({
                  ...incomeForm,
                  date: e.target.value,
                })
              }
              required
            />

            <input
              type="text"
              placeholder="Description"
              value={incomeForm.description}
              onChange={(e) =>
                setIncomeForm({
                  ...incomeForm,
                  description:
                    e.target.value,
                })
              }
            />

            <button type="submit">
              Add Income
            </button>

          </form>

          <h2>My Income</h2>

          {income.length === 0 ? (

            <p>No income found.</p>

          ) : (

            <ul className="data-list">

              {income.map((item) => (

                <li key={item.id}>

                  <strong>
                    {item.source}
                  </strong>

                  {" - ₹"}

                  {Number(
                    item.amount
                  ).toFixed(2)}

                  {" - "}

                  {item.date}

                  {" - "}

                  {item.description}

                  <div
                    style={{
                      marginTop: "10px",
                    }}
                  >

                    <button
                      type="button"
                      onClick={() =>
                        handleEditIncome(item)
                      }
                    >
                      ✏️ Edit
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleDeleteIncome(
                          item.id
                        )
                      }
                      style={{
                        marginLeft: "8px",
                      }}
                    >
                      🗑️ Delete
                    </button>

                  </div>

                </li>

              ))}

            </ul>

          )}

        </div>

        <div className="section">

          <h2>➕ Add Budget</h2>

          <form
            className="form"
            onSubmit={handleBudgetSubmit}
          >

            <input
              type="text"
              placeholder="Category"
              value={budgetForm.category}
              onChange={(e) =>
                setBudgetForm({
                  ...budgetForm,
                  category: e.target.value,
                })
              }
              required
            />

            <input
              type="number"
              placeholder="Budget Amount"
              value={budgetForm.amount}
              onChange={(e) =>
                setBudgetForm({
                  ...budgetForm,
                  amount: e.target.value,
                })
              }
              required
            />

            <label>Start Date:</label>

            <input
              type="date"
              value={budgetForm.start_date}
              onChange={(e) =>
                setBudgetForm({
                  ...budgetForm,
                  start_date:
                    e.target.value,
                })
              }
              required
            />

            <label>End Date:</label>

            <input
              type="date"
              value={budgetForm.end_date}
              onChange={(e) =>
                setBudgetForm({
                  ...budgetForm,
                  end_date:
                    e.target.value,
                })
              }
              required
            />

            <button type="submit">
              Add Budget
            </button>

          </form>

          <h2>My Budgets</h2>

          {budgets.length === 0 ? (

            <p>No budgets found.</p>

          ) : (

            <ul className="data-list">

              {budgets.map((budget) => (

                <li key={budget.id}>

                  <strong>
                    {budget.category}
                  </strong>

                  {" - ₹"}

                  {Number(
                    budget.amount
                  ).toFixed(2)}

                  {" - "}

                  {budget.start_date}

                  {" to "}

                  {budget.end_date}

                  <div
                    style={{
                      marginTop: "10px",
                    }}
                  >

                    <button
                      type="button"
                      onClick={() =>
                        handleEditBudget(
                          budget
                        )
                      }
                    >
                      ✏️ Edit
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleDeleteBudget(
                          budget.id
                        )
                      }
                      style={{
                        marginLeft: "8px",
                      }}
                    >
                      🗑️ Delete
                    </button>

                  </div>

                </li>

              ))}

            </ul>

          )}

        </div>

        <div className="section">

          <h2>➕ Add Savings Goal</h2>

          <form
            className="form"
            onSubmit={handleSavingsSubmit}
          >

            <input
              type="text"
              placeholder="Savings Goal Name"
              value={savingsForm.name}
              onChange={(e) =>
                setSavingsForm({
                  ...savingsForm,
                  name: e.target.value,
                })
              }
              required
            />

            <input
              type="number"
              placeholder="Target Amount"
              value={savingsForm.target_amount}
              onChange={(e) =>
                setSavingsForm({
                  ...savingsForm,
                  target_amount:
                    e.target.value,
                })
              }
              required
            />

            <input
              type="number"
              placeholder="Current Savings"
              value={savingsForm.current_amount}
              onChange={(e) =>
                setSavingsForm({
                  ...savingsForm,
                  current_amount:
                    e.target.value,
                })
              }
              required
            />

            <label>Target Date:</label>

            <input
              type="date"
              value={savingsForm.target_date}
              onChange={(e) =>
                setSavingsForm({
                  ...savingsForm,
                  target_date:
                    e.target.value,
                })
              }
              required
            />

            <button type="submit">
              Add Savings Goal
            </button>

          </form>

          <h2>My Savings Goals</h2>

          {savingsGoals.length === 0 ? (

            <p>No savings goals found.</p>

          ) : (

            <ul className="data-list">

              {savingsGoals.map((goal) => (

                <li key={goal.id}>

                  <strong>{goal.name}</strong>

                  {" - ₹"}

                  {Number(
                    goal.current_amount
                  ).toFixed(2)}

                  {" / ₹"}

                  {Number(
                    goal.target_amount
                  ).toFixed(2)}

                  {" - "}

                  {goal.target_date}

                  {" - Status: "}

                  {goal.status}

                  <div
                    style={{
                      marginTop: "10px",
                    }}
                  >

                    <button
                      type="button"
                      onClick={() =>
                        handleEditSavingsGoal(
                          goal
                        )
                      }
                    >
                      ✏️ Edit
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleDeleteSavingsGoal(
                          goal.id
                        )
                      }
                      style={{
                        marginLeft: "8px",
                      }}
                    >
                      🗑️ Delete
                    </button>

                  </div>

                </li>

              ))}

            </ul>

          )}

        </div>

        <div className="section">

          <h2>🔔 My Notifications</h2>

          {notifications.length === 0 ? (

            <p>No notifications found.</p>

          ) : (

            notifications.map(
              (notification) => (

                <div
                  className="notification"
                  key={notification.id}
                  style={{
                    padding: "15px",
                    marginBottom: "12px",
                    border: "1px solid #ddd",
                    borderRadius: "8px",
                    backgroundColor:
                      notification.is_read
                        ? "#f5f5f5"
                        : "#fff8e1",
                  }}
                >

                  <h3>
                    {notification.title ||
                      "Notification"}
                  </h3>

                  <p>
                    {notification.message}
                  </p>

                  <p>
                    <strong>Type:</strong>{" "}
                    {
                      notification.notification_type
                    }
                  </p>

                  <p>
                    <strong>Status:</strong>{" "}
                    {notification.is_read
                      ? "✅ Read"
                      : "🔔 Unread"}
                  </p>

                  <p>
                    <strong>Created:</strong>{" "}
                    {notification.created_at
                      ? new Date(
                          notification.created_at
                        ).toLocaleString()
                      : "N/A"}
                  </p>

                  {!notification.is_read && (

                    <button
                      type="button"
                      onClick={() =>
                        handleMarkNotificationRead(
                          notification.id
                        )
                      }
                    >
                      ✓ Mark as Read
                    </button>

                  )}

                </div>

              )
            )

          )}

        </div>

      </div>
    </div>
  );
}

export default Dashboard;
export default Dashboard;
