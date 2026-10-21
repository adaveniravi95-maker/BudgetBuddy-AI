import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import "./reports.css";

const API = import.meta.env.VITE_API_URL;

function Reports() {
  const navigate = useNavigate();

  const [reports, setReports] = useState([]);
  const [income, setIncome] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [savingsGoals, setSavingsGoals] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // =========================================
  // LOAD DATA
  // =========================================

  useEffect(() => {
    loadReportData();
  }, []);

  const loadReportData = async () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      navigate("/login");
      return;
    }

    try {
      const headers = {
        Authorization: `Bearer ${token}`,
      };

      const [
        reportsResponse,
        incomeResponse,
        expensesResponse,
        budgetsResponse,
        savingsResponse,
      ] = await Promise.all([
        fetch(`${API}/my-reports/`, { headers }),
        fetch(`${API}/my-income/`, { headers }),
        fetch(`${API}/my-expenses/`, { headers }),
        fetch(`${API}/my-budgets/`, { headers }),
        fetch(`${API}/my-savings-goals/`, { headers }),
      ]);

      // =========================================
      // AUTH CHECK
      // =========================================

      if (
        reportsResponse.status === 401 ||
        incomeResponse.status === 401 ||
        expensesResponse.status === 401 ||
        budgetsResponse.status === 401 ||
        savingsResponse.status === 401
      ) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        alert("Session expired. Please login again.");
        navigate("/login");
        return;
      }

      // =========================================
      // READ DATA
      // =========================================

      const reportsData = await reportsResponse.json();
      const incomeData = await incomeResponse.json();
      const expensesData = await expensesResponse.json();
      const budgetsData = await budgetsResponse.json();
      const savingsData = await savingsResponse.json();

      setReports(
        Array.isArray(reportsData)
          ? reportsData
          : []
      );

      setIncome(
        Array.isArray(incomeData)
          ? incomeData
          : []
      );

      setExpenses(
        Array.isArray(expensesData)
          ? expensesData
          : []
      );

      setBudgets(
        Array.isArray(budgetsData)
          ? budgetsData
          : []
      );

      setSavingsGoals(
        Array.isArray(savingsData)
          ? savingsData
          : []
      );
    } catch (err) {
      console.error("Reports error:", err);
      setError("Unable to load financial data.");
    } finally {
      setLoading(false);
    }
  };

  // =========================================
  // PDF DOWNLOAD
  // =========================================

  const downloadPDF = async () => {
    const token = localStorage.getItem("access_token");

    try {
      setError("");

      const response = await fetch(
        `${API}/reports/pdf/?month=2026-09`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        navigate("/login");
        return;
      }

      if (!response.ok) {
        throw new Error("PDF download failed");
      }

      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");

      link.href = url;
      link.download = "BudgetBuddy_Report.pdf";

      document.body.appendChild(link);
      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download error:", err);

      setError("Unable to download PDF report.");
    }
  };

  // =========================================
  // EXCEL DOWNLOAD
  // =========================================

  const downloadExcel = async () => {
    const token = localStorage.getItem("access_token");

    try {
      setError("");

      const response = await fetch(
        `${API}/reports/excel/?month=2026-09`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        navigate("/login");
        return;
      }

      if (!response.ok) {
        throw new Error("Excel download failed");
      }

      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");

      link.href = url;
      link.download = "BudgetBuddy_Report.xlsx";

      document.body.appendChild(link);
      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Excel download error:", err);

      setError("Unable to download Excel report.");
    }
  };

  // =========================================
  // CALCULATIONS
  // =========================================

  const totalIncome = income.reduce(
    (total, item) =>
      total + Number(item.amount || 0),
    0
  );

  const totalExpenses = expenses.reduce(
    (total, item) =>
      total + Number(item.amount || 0),
    0
  );

  const totalBudget = budgets.reduce(
    (total, item) =>
      total + Number(item.amount || 0),
    0
  );

  const savingsTarget = savingsGoals.reduce(
    (total, goal) =>
      total + Number(goal.target_amount || 0),
    0
  );

  const currentSavings = savingsGoals.reduce(
    (total, goal) =>
      total + Number(goal.current_amount || 0),
    0
  );

  const balance = totalIncome - totalExpenses;

  // =========================================
  // SAVINGS PERCENTAGE
  // =========================================

  const savingsPercentage =
    savingsTarget > 0
      ? Math.min(
          (currentSavings / savingsTarget) * 100,
          100
        )
      : 0;

  // =========================================
  // BUDGET PERCENTAGE
  // =========================================

  const budgetPercentage =
    totalBudget > 0
      ? Math.min(
          (totalExpenses / totalBudget) * 100,
          100
        )
      : 0;

  // =========================================
  // INCOME VS EXPENSE DATA
  // =========================================

  const incomeExpenseData = [
    {
      name: "Finance",
      Income: totalIncome,
      Expenses: totalExpenses,
    },
  ];

  // =========================================
  // EXPENSE CATEGORY DATA
  // =========================================

  const categoryTotals = {};

  expenses.forEach((expense) => {
    const category = expense.category || "Other";

    categoryTotals[category] =
      (categoryTotals[category] || 0) +
      Number(expense.amount || 0);
  });

  const expenseCategoryData =
    Object.keys(categoryTotals).map(
      (category) => ({
        name: category,
        value: categoryTotals[category],
      })
    );

  // =========================================
  // SAVINGS CHART DATA
  // =========================================

  const savingsChartData = savingsGoals.map(
    (goal) => ({
      name: goal.name || "Savings",
      Current: Number(
        goal.current_amount || 0
      ),
      Target: Number(
        goal.target_amount || 0
      ),
    })
  );

  // =========================================
  // CHART COLORS
  // =========================================

  const chartColors = [
    "#ef4444",
    "#3b82f6",
    "#22c55e",
    "#f59e0b",
    "#8b5cf6",
    "#ec4899",
  ];

  // =========================================
  // LOADING
  // =========================================

  if (loading) {
    return (
      <div className="reports-page">
        <div className="reports-container">
          <div className="report-details">
            <h2>
              📊 Loading financial report...
            </h2>
          </div>
        </div>
      </div>
    );
  }

  // =========================================
  // UI
  // =========================================

  return (
    <div className="reports-page">
      <div className="reports-container">

        {/* HEADER */}

        <div className="reports-header">
          <div>
            <h1>
              📊 BudgetBuddy Reports
            </h1>

            <p>
              View your financial reports
              and summary.
            </p>
          </div>

          <button
            className="back-button"
            onClick={() =>
              navigate("/dashboard")
            }
          >
            🔙 Dashboard
          </button>
        </div>

        {/* EXPORT BUTTONS */}

        <div className="report-export-section">
          <h2>
            📥 Export Reports
          </h2>

          <div className="export-buttons">

            <button
              className="export-button pdf-button"
              onClick={downloadPDF}
            >
              📄 Download PDF
            </button>

            <button
              className="export-button excel-button"
              onClick={downloadExcel}
            >
              📊 Download Excel
            </button>

          </div>
        </div>

        {/* ERROR */}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* FINANCIAL SUMMARY */}

        <h2>
          💰 Financial Summary
        </h2>

        <div className="report-summary">

          <div className="report-card income-card">
            <h3>💵 Total Income</h3>
            <h2>
              ₹{totalIncome.toFixed(2)}
            </h2>
          </div>

          <div className="report-card expense-card">
            <h3>💸 Total Expenses</h3>
            <h2>
              ₹{totalExpenses.toFixed(2)}
            </h2>
          </div>

          <div className="report-card balance-card">
            <h3>💰 Balance</h3>
            <h2>
              ₹{balance.toFixed(2)}
            </h2>
          </div>

          <div className="report-card budget-card">
            <h3>📊 Total Budget</h3>
            <h2>
              ₹{totalBudget.toFixed(2)}
            </h2>
          </div>

          <div className="report-card savings-card">
            <h3>🎯 Savings Target</h3>
            <h2>
              ₹{savingsTarget.toFixed(2)}
            </h2>
          </div>

          <div className="report-card current-card">
            <h3>🏦 Current Savings</h3>
            <h2>
              ₹{currentSavings.toFixed(2)}
            </h2>
          </div>

        </div>

        {/* FINANCIAL CHARTS */}

        <h2>
          📊 Financial Charts
        </h2>

        <div className="charts-grid">

          {/* INCOME VS EXPENSE */}

          <div className="chart-card">
            <h3>
              💰 Income vs Expenses
            </h3>

            <ResponsiveContainer
              width="100%"
              height={320}
            >
              <BarChart
                data={incomeExpenseData}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="name"
                />

                <YAxis />

                <Tooltip />

                <Legend />

                <Bar
                  dataKey="Income"
                  fill="#22c55e"
                  radius={[6, 6, 0, 0]}
                />

                <Bar
                  dataKey="Expenses"
                  fill="#ef4444"
                  radius={[6, 6, 0, 0]}
                />

              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* EXPENSE CATEGORY */}

          <div className="chart-card">

            <h3>
              💸 Expense Categories
            </h3>

            {expenseCategoryData.length > 0 ? (

              <ResponsiveContainer
                width="100%"
                height={320}
              >
                <PieChart>

                  <Pie
                    data={expenseCategoryData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={105}
                    label
                  >

                    {expenseCategoryData.map(
                      (entry, index) => (
                        <Cell
                          key={`cell-${index}`}
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

                  <Tooltip />

                  <Legend />

                </PieChart>
              </ResponsiveContainer>

            ) : (

              <div className="no-chart-data">
                <p>
                  No expense data available.
                </p>
              </div>

            )}

          </div>

        </div>

        {/* SAVINGS CHART */}

        <div className="chart-card full-chart">

          <h3>
            🎯 Savings Progress
          </h3>

          {savingsChartData.length > 0 ? (

            <ResponsiveContainer
              width="100%"
              height={320}
            >

              <BarChart
                data={savingsChartData}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="name"
                />

                <YAxis />

                <Tooltip />

                <Legend />

                <Bar
                  dataKey="Current"
                  fill="#3b82f6"
                  radius={[6, 6, 0, 0]}
                />

                <Bar
                  dataKey="Target"
                  fill="#8b5cf6"
                  radius={[6, 6, 0, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          ) : (

            <div className="no-chart-data">
              <p>
                No savings goals available.
              </p>
            </div>

          )}

        </div>

        {/* SAVINGS PROGRESS */}

        <h2>
          🎯 Savings Progress
        </h2>

        <div className="report-details">

          <div className="progress-info">

            <span>
              ₹{currentSavings.toFixed(2)}
              {" saved out of "}
              ₹{savingsTarget.toFixed(2)}
            </span>

            <strong>
              {savingsPercentage.toFixed(1)}%
            </strong>

          </div>

          <div className="progress-bar">

            <div
              className="progress-fill savings-fill"
              style={{
                width: `${savingsPercentage}%`,
              }}
            />

          </div>

          <p>
            <strong>
              {savingsPercentage.toFixed(1)}%
            </strong>
            {" "}of savings target completed.
          </p>

        </div>

        {/* BUDGET STATUS */}

        <h2>
          📊 Budget Status
        </h2>

        <div className="report-details">

          <div className="progress-info">

            <span>
              ₹{totalExpenses.toFixed(2)}
              {" spent out of "}
              ₹{totalBudget.toFixed(2)}
            </span>

            <strong>
              {budgetPercentage.toFixed(1)}%
            </strong>

          </div>

          <div className="progress-bar">

            <div
              className={`progress-fill ${
                budgetPercentage >= 90
                  ? "budget-danger"
                  : budgetPercentage >= 70
                  ? "budget-warning"
                  : "budget-safe"
              }`}
              style={{
                width: `${budgetPercentage}%`,
              }}
            />

          </div>

          <p>
            <strong>
              {budgetPercentage.toFixed(1)}%
            </strong>
            {" "}of your budget has been used.
          </p>

          {totalExpenses > totalBudget &&
            totalBudget > 0 && (
              <p className="budget-alert">
                ⚠️ You have exceeded your
                budget.
              </p>
            )}

        </div>

        {/* REPORT DETAILS */}

        <h2>
          📄 Report Details
        </h2>

        {reports.length === 0 ? (

          <div className="no-reports">
            No reports found.
          </div>

        ) : (

          reports.map((report) => (

            <div
              className="report-details report-item"
              key={report.id}
            >

              <h2>
                {report.title}
              </h2>

              <div className="report-info-grid">

                <p>
                  <strong>
                    Report Type
                  </strong>

                  <span>
                    {report.report_type ||
                      "N/A"}
                  </span>
                </p>

                <p>
                  <strong>
                    Start Date
                  </strong>

                  <span>
                    {report.start_date ||
                      "N/A"}
                  </span>
                </p>

                <p>
                  <strong>
                    End Date
                  </strong>

                  <span>
                    {report.end_date ||
                      "N/A"}
                  </span>
                </p>

                <p>
                  <strong>
                    Created
                  </strong>

                  <span>
                    {report.created_at
                      ? new Date(
                          report.created_at
                        ).toLocaleString()
                      : "N/A"}
                  </span>
                </p>

              </div>

            </div>

          ))

        )}

      </div>
    </div>
  );
}

export default Reports;