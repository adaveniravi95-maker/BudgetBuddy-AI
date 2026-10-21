
import React, { useEffect, useState } from "react";
import { api } from "../api";

const categories = [
  "Food",
  "Travel",
  "Shopping",
  "Education",
  "Entertainment",
  "Miscellaneous",
];

const sources = [
  "Pocket Money",
  "Scholarship",
  "Freelance Income",
];

function getLocalDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function Transactions({
  month,
  year,
  viewMode = "monthly",
  setMonth,
  setYear,
  setViewMode,
}) {
  const today = getLocalDate();

  const [expenses, setExpenses] = useState([]);
  const [incomes, setIncomes] = useState([]);

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const [expense, setExpense] = useState({
    amount: "",
    category: "Food",
    expense_date: today,
    description: "",
  });

  const [income, setIncome] = useState({
    amount: "",
    source: "Pocket Money",
    income_date: today,
    details: "",
  });

  const [editingExpense, setEditingExpense] = useState(null);
  const [editingIncome, setEditingIncome] = useState(null);

  async function loadTransactions() {
    try {
      setLoading(true);

      const [expenseData, incomeData] = await Promise.all([
        api("/expenses"),
        api("/incomes"),
      ]);

      setExpenses(Array.isArray(expenseData) ? expenseData : []);
      setIncomes(Array.isArray(incomeData) ? incomeData : []);
    } catch (error) {
      setMessage(error.message || "Unable to load transactions.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTransactions();
  }, []);

  // Filter expenses using the global Dashboard period.
  const filteredExpenses = expenses.filter((item) => {
    const date = String(item.expense_date || "");

    if (viewMode === "monthly") {
      return date.slice(0, 7) === month;
    }

    return date.slice(0, 4) === String(year);
  });

  // Filter income using the global Dashboard period.
  const filteredIncomes = incomes.filter((item) => {
    const date = String(item.income_date || "");

    if (viewMode === "monthly") {
      return date.slice(0, 7) === month;
    }

    return date.slice(0, 4) === String(year);
  });

  const totalExpenses = filteredExpenses.reduce(
    (total, item) => total + Number(item.amount || 0),
    0
  );

  const totalIncome = filteredIncomes.reduce(
    (total, item) => total + Number(item.amount || 0),
    0
  );

  const balance = totalIncome - totalExpenses;

  const periodLabel =
    viewMode === "monthly"
      ? month
      : year;

  async function saveExpense(event) {
    event.preventDefault();
    setMessage("");

    if (expense.expense_date > today) {
      setMessage("Future dates are not allowed.");
      return;
    }

    try {
      if (editingExpense) {
        await api(`/expenses/${editingExpense.id}`, {
          method: "PUT",
          body: JSON.stringify({
            ...expense,
            amount: Number(expense.amount),
          }),
        });

        setMessage("Expense updated successfully.");
      } else {
        await api("/expenses", {
          method: "POST",
          body: JSON.stringify({
            ...expense,
            amount: Number(expense.amount),
          }),
        });

        setMessage("Expense added successfully.");
      }

      resetExpense();
      await loadTransactions();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function saveIncome(event) {
    event.preventDefault();
    setMessage("");

    if (income.income_date > today) {
      setMessage("Future dates are not allowed.");
      return;
    }

    try {
      if (editingIncome) {
        await api(`/incomes/${editingIncome.id}`, {
          method: "PUT",
          body: JSON.stringify({
            ...income,
            amount: Number(income.amount),
          }),
        });

        setMessage("Income updated successfully.");
      } else {
        await api("/incomes", {
          method: "POST",
          body: JSON.stringify({
            ...income,
            amount: Number(income.amount),
          }),
        });

        setMessage("Income added successfully.");
      }

      resetIncome();
      await loadTransactions();
    } catch (error) {
      setMessage(error.message);
    }
  }

  function resetExpense() {
    setExpense({
      amount: "",
      category: "Food",
      expense_date: today,
      description: "",
    });

    setEditingExpense(null);
  }

  function resetIncome() {
    setIncome({
      amount: "",
      source: "Pocket Money",
      income_date: today,
      details: "",
    });

    setEditingIncome(null);
  }

  function startEditExpense(item) {
    setEditingExpense(item);

    setExpense({
      amount: item.amount,
      category: item.category,
      expense_date: item.expense_date,
      description: item.description || "",
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  function startEditIncome(item) {
    setEditingIncome(item);

    setIncome({
      amount: item.amount,
      source: item.source,
      income_date: item.income_date,
      details: item.details || "",
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  async function deleteExpense(id) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this expense?"
    );

    if (!confirmed) return;

    try {
      await api(`/expenses/${id}`, {
        method: "DELETE",
      });

      setMessage("Expense deleted successfully.");
      await loadTransactions();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function deleteIncome(id) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this income?"
    );

    if (!confirmed) return;

    try {
      await api(`/incomes/${id}`, {
        method: "DELETE",
      });

      setMessage("Income deleted successfully.");
      await loadTransactions();
    } catch (error) {
      setMessage(error.message);
    }
  }

  if (loading) {
    return (
      <section>
        <div className="dashboard-header">
          <div>
            <h2>Transactions</h2>
            <p>Manage your income and expenses.</p>
          </div>
        </div>

        <div className="card">
          <div className="loading-screen">
            <div>
              <h3>Loading transactions...</h3>
              <p>Getting your latest financial activity.</p>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="dashboard-header">
        <div>
          <h2>Transactions</h2>
          <p>
            {viewMode === "monthly"
              ? `Showing transactions for ${periodLabel}`
              : `Showing transactions for year ${periodLabel}`}
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: "10px",
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <select
            value={viewMode}
            onChange={(event) => setViewMode?.(event.target.value)}
            aria-label="Select transaction period"
          >
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>

          {viewMode === "monthly" ? (
            <input
              type="month"
              value={month}
              max={getLocalDate().slice(0, 7)}
              onChange={(event) => setMonth?.(event.target.value)}
              aria-label="Select month"
            />
          ) : (
            <select
              value={year}
              onChange={(event) => setYear?.(event.target.value)}
              aria-label="Select year"
            >
              {Array.from(
                { length: new Date().getFullYear() - 2020 + 1 },
                (_, index) => String(2020 + index)
              )
                .reverse()
                .map((itemYear) => (
                  <option key={itemYear} value={itemYear}>
                    {itemYear}
                  </option>
                ))}
            </select>
          )}

          <button
            className="secondary-button"
            onClick={loadTransactions}
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {message && (
        <div className="message">
          {message}
        </div>
      )}

      <section className="summary-grid">
        <div className="summary-card">
          <span>Total Income</span>
          <strong>₹{totalIncome.toFixed(2)}</strong>
        </div>

        <div className="summary-card">
          <span>Total Expenses</span>
          <strong>₹{totalExpenses.toFixed(2)}</strong>
        </div>

        <div className="summary-card">
          <span>Balance</span>
          <strong>₹{Math.abs(balance).toFixed(2)}</strong>
        </div>
      </section>

      <section className="two">
        <div className="card">
          <div className="chart-title">
            <div>
              <h2>
                {editingExpense ? "Edit Expense" : "Add Expense"}
              </h2>
              <p>Track your spending.</p>
            </div>

            <span className="badge badge-danger">
              Expense
            </span>
          </div>

          <form onSubmit={saveExpense}>
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="Amount"
              required
              value={expense.amount}
              onChange={(event) =>
                setExpense({
                  ...expense,
                  amount: event.target.value,
                })
              }
            />

            <select
              value={expense.category}
              onChange={(event) =>
                setExpense({
                  ...expense,
                  category: event.target.value,
                })
              }
            >
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>

            <input
              type="date"
              max={today}
              required
              value={expense.expense_date}
              onChange={(event) =>
                setExpense({
                  ...expense,
                  expense_date: event.target.value,
                })
              }
            />

            <input
              type="text"
              maxLength="255"
              placeholder="Description"
              value={expense.description}
              onChange={(event) =>
                setExpense({
                  ...expense,
                  description: event.target.value,
                })
              }
            />

            <button type="submit">
              {editingExpense ? "Update Expense" : "Add Expense"}
            </button>

            {editingExpense && (
              <button
                type="button"
                className="secondary-button"
                onClick={resetExpense}
              >
                Cancel Edit
              </button>
            )}
          </form>
        </div>

        <div className="card">
          <div className="chart-title">
            <div>
              <h2>
                {editingIncome ? "Edit Income" : "Add Income"}
              </h2>
              <p>Record money you receive.</p>
            </div>

            <span className="badge badge-success">
              Income
            </span>
          </div>

          <form onSubmit={saveIncome}>
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="Amount"
              required
              value={income.amount}
              onChange={(event) =>
                setIncome({
                  ...income,
                  amount: event.target.value,
                })
              }
            />

            <select
              value={income.source}
              onChange={(event) =>
                setIncome({
                  ...income,
                  source: event.target.value,
                })
              }
            >
              {sources.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>

            <input
              type="date"
              max={today}
              required
              value={income.income_date}
              onChange={(event) =>
                setIncome({
                  ...income,
                  income_date: event.target.value,
                })
              }
            />

            <input
              type="text"
              maxLength="255"
              placeholder="Details"
              value={income.details}
              onChange={(event) =>
                setIncome({
                  ...income,
                  details: event.target.value,
                })
              }
            />

            <button type="submit">
              {editingIncome ? "Update Income" : "Add Income"}
            </button>

            {editingIncome && (
              <button
                type="button"
                className="secondary-button"
                onClick={resetIncome}
              >
                Cancel Edit
              </button>
            )}
          </form>
        </div>
      </section>

      <section className="card">
        <div className="chart-title">
          <div>
            <h2>Expense History</h2>
            <p>
              Expenses for the selected period.
            </p>
          </div>

          <span className="badge badge-danger">
            {filteredExpenses.length} transactions
          </span>
        </div>

        {filteredExpenses.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">💳</div>
            <h3>No expenses found</h3>
            <p>
              No expenses recorded for {periodLabel}.
            </p>
          </div>
        ) : (
          [...filteredExpenses]
            .sort((a, b) =>
              String(b.expense_date).localeCompare(
                String(a.expense_date)
              )
            )
            .map((item) => (
              <div className="row" key={item.id}>
                <div>
                  <strong>{item.category}</strong>
                  <p
                    style={{
                      margin: "5px 0 0",
                      fontSize: "12px",
                    }}
                  >
                    {item.expense_date}
                    {item.description
                      ? ` • ${item.description}`
                      : ""}
                  </p>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                >
                  <strong>
                    ₹{Number(item.amount).toFixed(2)}
                  </strong>

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => startEditExpense(item)}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="delete-button"
                    onClick={() => deleteExpense(item.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
        )}
      </section>

      <section className="card">
        <div className="chart-title">
          <div>
            <h2>Income History</h2>
            <p>
              Income for the selected period.
            </p>
          </div>

          <span className="badge badge-success">
            {filteredIncomes.length} transactions
          </span>
        </div>

        {filteredIncomes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">💰</div>
            <h3>No income found</h3>
            <p>
              No income recorded for {periodLabel}.
            </p>
          </div>
        ) : (
          [...filteredIncomes]
            .sort((a, b) =>
              String(b.income_date).localeCompare(
                String(a.income_date)
              )
            )
            .map((item) => (
              <div className="row" key={item.id}>
                <div>
                  <strong>{item.source}</strong>
                  <p
                    style={{
                      margin: "5px 0 0",
                      fontSize: "12px",
                    }}
                  >
                    {item.income_date}
                    {item.details
                      ? ` • ${item.details}`
                      : ""}
                  </p>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                >
                  <strong>
                    ₹{Number(item.amount).toFixed(2)}
                  </strong>

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => startEditIncome(item)}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="delete-button"
                    onClick={() => deleteIncome(item.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
        )}
      </section>
    </section>
  );
}

export default Transactions;
