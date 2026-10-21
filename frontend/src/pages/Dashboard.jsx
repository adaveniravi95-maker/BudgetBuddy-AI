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