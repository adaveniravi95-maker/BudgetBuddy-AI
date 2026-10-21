import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";

const todayString = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

const formatCurrency = (amount) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(amount) || 0);

const formatDate = (date) => {
  if (!date) return "Not set";

  const parsed = new Date(`${date}T00:00:00`);

  if (Number.isNaN(parsed.getTime())) return "Not set";

  return parsed.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

const daysBetween = (start, end) => {
  if (!start || !end) return null;

  const startDate = new Date(`${start}T00:00:00`);
  const endDate = new Date(`${end}T00:00:00`);

  if (
    Number.isNaN(startDate.getTime()) ||
    Number.isNaN(endDate.getTime())
  ) {
    return null;
  }

  return Math.round(
    (endDate.getTime() - startDate.getTime()) / 86400000
  );
};

const getProgress = (goal) => {
  const target = Number(goal.target_amount) || 0;
  const saved = Number(goal.amount_saved) || 0;

  if (target <= 0) return 0;

  return Math.min(100, Math.max(0, (saved / target) * 100));
};

const getGoalStatus = (goal) => {
  if (goal.is_completed || getProgress(goal) >= 100) {
    return {
      label: "Completed",
      color: "#16a34a",
      background: "#dcfce7",
    };
  }

  if (
    goal.target_date &&
    daysBetween(todayString(), goal.target_date) < 0
  ) {
    return {
      label: "Overdue",
      color: "#dc2626",
      background: "#fee2e2",
    };
  }

  return {
    label: "Active",
    color: "#2563eb",
    background: "#dbeafe",
  };
};

/*
 * Safely extract year and month directly from YYYY-MM-DD.
 *
 * Example:
 * "2026-10-04" -> { year: 2026, month: 10 }
 * "2026-09-15" -> { year: 2026, month: 9 }
 */
const getGoalPeriod = (date) => {
  if (!date || typeof date !== "string") {
    return null;
  }

  const datePart = date.slice(0, 10);

  const match = datePart.match(/^(\d{4})-(\d{2})-(\d{2})$/);

  if (!match) {
    return null;
  }

  return {
    year: Number(match[1]),
    month: Number(match[2]),
  };
};

const SavingsGoals = ({
  month,
  year,
  viewMode,
  setMonth,
  setYear,
  setViewMode,
}) => {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [goalName, setGoalName] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [amountSaved, setAmountSaved] = useState("0");
  const [startDate, setStartDate] = useState(todayString());
  const [targetDate, setTargetDate] = useState("");

  const [editingGoal, setEditingGoal] = useState(null);
  const [editGoalName, setEditGoalName] = useState("");
  const [editTargetAmount, setEditTargetAmount] = useState("");
  const [editAmountSaved, setEditAmountSaved] = useState("");
  const [editStartDate, setEditStartDate] = useState("");
  const [editTargetDate, setEditTargetDate] = useState("");

  useEffect(() => {
    if (!message && !error) return;

    const timer = setTimeout(() => {
      setMessage("");
      setError("");
    }, 3500);

    return () => clearTimeout(timer);
  }, [message, error]);

  // GET: Load all savings goals
  const loadGoals = async () => {
    try {
      setLoading(true);

      const response = await api("/savings-goals");

      setGoals(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error("Savings Goals Loading Error:", err);
      setError(err.message || "Unable to load savings goals.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGoals();
  }, []);

  /*
   * FILTERING LOGIC
   *
   * Monthly:
   * Shows goals whose START DATE belongs to the
   * selected month and selected year.
   *
   * Yearly:
   * Shows ALL goals whose START DATE belongs to
   * the selected year, regardless of month.
   *
   * Example:
   *
   * September 2026 goal -> appears in September 2026
   * October 2026 goal   -> appears in October 2026
   *
   * Yearly 2026 -> shows both September + October goals
   */
  const filteredGoals = useMemo(() => {
    if (!goals.length) {
      return [];
    }

    const selectedYear = Number(year);
    const selectedMonth = Number(month);

    return goals.filter((goal) => {
      const goalPeriod = getGoalPeriod(goal.start_date);

      // Goals without a valid start date cannot be assigned
      // to a particular month/year.
      if (!goalPeriod) {
        return false;
      }

      // YEARLY VIEW
      if (viewMode === "Yearly") {
        return goalPeriod.year === selectedYear;
      }

      // MONTHLY VIEW
      return (
        goalPeriod.year === selectedYear &&
        goalPeriod.month === selectedMonth
      );
    });
  }, [goals, month, year, viewMode]);

  // Summary is based ONLY on the currently filtered goals.
  const summary = useMemo(() => {
    const totalTarget = filteredGoals.reduce(
      (sum, goal) => sum + (Number(goal.target_amount) || 0),
      0
    );

    const totalSaved = filteredGoals.reduce(
      (sum, goal) => sum + (Number(goal.amount_saved) || 0),
      0
    );

    const completedGoals = filteredGoals.filter(
      (goal) => goal.is_completed || getProgress(goal) >= 100
    ).length;

    return {
      totalTarget,
      totalSaved,
      remaining: Math.max(0, totalTarget - totalSaved),
      overallProgress:
        totalTarget > 0
          ? Math.min(100, (totalSaved / totalTarget) * 100)
          : 0,
      completedGoals,
      activeGoals: filteredGoals.length - completedGoals,
    };
  }, [filteredGoals]);

  // POST: Create savings goal
  const handleCreateGoal = async (event) => {
    event.preventDefault();

    const target = Number(targetAmount);
    const saved = Number(amountSaved);

    if (!goalName.trim()) {
      setError("Please enter a goal name.");
      return;
    }

    if (!Number.isFinite(target) || target <= 0) {
      setError("Target amount must be greater than zero.");
      return;
    }

    if (!Number.isFinite(saved) || saved < 0 || saved > target) {
      setError("Amount saved must be between zero and the target amount.");
      return;
    }

    if (!startDate || !targetDate) {
      setError("Please select both start date and target date.");
      return;
    }

    if (targetDate < startDate) {
      setError("Target date cannot be earlier than start date.");
      return;
    }

    try {
      await api("/savings-goals", {
        method: "POST",
        body: JSON.stringify({
          goal_name: goalName.trim(),
          target_amount: target,
          amount_saved: saved,
          start_date: startDate,
          target_date: targetDate,
        }),
      });

      setGoalName("");
      setTargetAmount("");
      setAmountSaved("0");
      setStartDate(todayString());
      setTargetDate("");

      setMessage("Savings goal created successfully!");

      await loadGoals();
    } catch (err) {
      console.error("Savings Goal Creation Error:", err);
      setError(err.message || "Unable to create savings goal.");
    }
  };

  const openEdit = (goal) => {
    setEditingGoal(goal);
    setEditGoalName(goal.goal_name || "");
    setEditTargetAmount(String(goal.target_amount ?? ""));
    setEditAmountSaved(String(goal.amount_saved ?? 0));
    setEditStartDate(goal.start_date || "");
    setEditTargetDate(goal.target_date || "");
  };

  // PUT: Update savings goal
  const handleUpdateGoal = async (event) => {
    event.preventDefault();

    if (!editingGoal) return;

    const target = Number(editTargetAmount);
    const saved = Number(editAmountSaved);

    if (!editGoalName.trim()) {
      setError("Please enter a goal name.");
      return;
    }

    if (!Number.isFinite(target) || target <= 0) {
      setError("Target amount must be greater than zero.");
      return;
    }

    if (!Number.isFinite(saved) || saved < 0 || saved > target) {
      setError("Amount saved must be between zero and the target amount.");
      return;
    }

    if (editStartDate && editTargetDate && editTargetDate < editStartDate) {
      setError("Target date cannot be earlier than start date.");
      return;
    }

    try {
      await api(`/savings-goals/${editingGoal.id}`, {
        method: "PUT",
        body: JSON.stringify({
          goal_name: editGoalName.trim(),
          target_amount: target,
          amount_saved: saved,
          start_date: editStartDate || null,
          target_date: editTargetDate || null,
        }),
      });

      setEditingGoal(null);
      setMessage("Savings goal updated successfully!");

      await loadGoals();
    } catch (err) {
      console.error("Savings Goal Update Error:", err);
      setError(err.message || "Unable to update savings goal.");
    }
  };

  // DELETE: Remove savings goal
  const handleDeleteGoal = async (goal) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${goal.goal_name}"?`
    );

    if (!confirmed) return;

    try {
      await api(`/savings-goals/${goal.id}`, {
        method: "DELETE",
      });

      setMessage("Savings goal deleted.");

      await loadGoals();
    } catch (err) {
      console.error("Savings Goal Deletion Error:", err);
      setError(err.message || "Unable to delete savings goal.");
    }
  };

  const renderGoalTiming = (goal) => {
    const duration = daysBetween(goal.start_date, goal.target_date);

    const remainingDays = goal.target_date
      ? daysBetween(todayString(), goal.target_date)
      : null;

    return (
      <div className="goal-timing-grid">
        <div className="goal-timing-item">
          <span>Start Date</span>
          <strong>{formatDate(goal.start_date)}</strong>
        </div>

        <div className="goal-timing-item">
          <span>Target Date</span>
          <strong>{formatDate(goal.target_date)}</strong>
        </div>

        <div className="goal-timing-item">
          <span>Duration</span>
          <strong>
            {duration === null
              ? "Not available"
              : `${Math.max(0, duration)} days`}
          </strong>
        </div>

        <div className="goal-timing-item">
          <span>Time Remaining</span>
          <strong
            style={{
              color:
                remainingDays !== null && remainingDays < 0
                  ? "#dc2626"
                  : "inherit",
            }}
          >
            {remainingDays === null
              ? "Not available"
              : remainingDays < 0
              ? `${Math.abs(remainingDays)} days overdue`
              : remainingDays === 0
              ? "Due today"
              : `${remainingDays} days left`}
          </strong>
        </div>
      </div>
    );
  };

  return (
    <div className="page-content savings-goals-page">
      {message && (
        <div className="budget-toast success">{message}</div>
      )}

      {error && (
        <div className="budget-toast error">{error}</div>
      )}

      <div className="page-header">
        <div>
          <h1>Savings Goals</h1>
          <p>
            Plan your savings, track progress, and achieve your dreams.
          </p>
        </div>

        <div className="period-controls">
          {setViewMode && (
            <select
              value={viewMode || "Monthly"}
              onChange={(event) => setViewMode(event.target.value)}
            >
              <option value="Monthly">Monthly</option>
              <option value="Yearly">Yearly</option>
            </select>
          )}

          {setMonth && (
            <select
              value={month ?? new Date().getMonth() + 1}
              onChange={(event) => setMonth(Number(event.target.value))}
            >
              {[
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
              ].map((name, index) => (
                <option key={name} value={index + 1}>
                  {name}
                </option>
              ))}
            </select>
          )}

          {setYear && (
            <select
              value={year ?? new Date().getFullYear()}
              onChange={(event) => setYear(Number(event.target.value))}
            >
              {Array.from(
                { length: 7 },
                (_, index) => new Date().getFullYear() - 2 + index
              ).map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      <div className="savings-summary-grid">
        <div className="savings-summary-card">
          <span>Total Target</span>
          <h2>{formatCurrency(summary.totalTarget)}</h2>
          <small>Combined savings goals</small>
        </div>

        <div className="savings-summary-card">
          <span>Total Saved</span>
          <h2>{formatCurrency(summary.totalSaved)}</h2>
          <small>Amount accumulated so far</small>
        </div>

        <div className="savings-summary-card">
          <span>Remaining Amount</span>
          <h2>{formatCurrency(summary.remaining)}</h2>
          <small>Amount left to reach targets</small>
        </div>

        <div className="savings-summary-card">
          <span>Overall Progress</span>
          <h2>{summary.overallProgress.toFixed(1)}%</h2>
          <div className="savings-mini-progress">
            <div style={{ width: `${summary.overallProgress}%` }} />
          </div>
        </div>

        <div className="savings-summary-card">
          <span>Goals Completed</span>
          <h2>{summary.completedGoals}</h2>
          <small>{summary.activeGoals} goals still active</small>
        </div>
      </div>

      <section className="budget-card savings-create-card">
        <div className="section-heading">
          <div>
            <h2>Create a Savings Goal</h2>
            <p>Set a target and choose when you want to achieve it.</p>
          </div>
        </div>

        <form className="savings-form" onSubmit={handleCreateGoal}>
          <div className="savings-form-grid">
            <div className="form-group">
              <label htmlFor="goalName">Goal Name</label>
              <input
                id="goalName"
                type="text"
                list="goalSuggestions"
                placeholder="e.g. Laptop, Phone, Emergency Fund"
                value={goalName}
                onChange={(event) => setGoalName(event.target.value)}
                required
              />

              <datalist id="goalSuggestions">
                <option value="Laptop" />
                <option value="Phone" />
                <option value="Education" />
                <option value="Emergency Fund" />
                <option value="Travel" />
                <option value="New Vehicle" />
              </datalist>
            </div>

            <div className="form-group">
              <label htmlFor="targetAmount">Target Amount (₹)</label>
              <input
                id="targetAmount"
                type="number"
                min="1"
                step="0.01"
                placeholder="50000"
                value={targetAmount}
                onChange={(event) => setTargetAmount(event.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="amountSaved">Amount Saved (₹)</label>
              <input
                id="amountSaved"
                type="number"
                min="0"
                step="0.01"
                placeholder="0"
                value={amountSaved}
                onChange={(event) => setAmountSaved(event.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="startDate">Start Date</label>
              <input
                id="startDate"
                type="date"
                value={startDate}
                max={targetDate || undefined}
                onChange={(event) => setStartDate(event.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="targetDate">Target Date</label>
              <input
                id="targetDate"
                type="date"
                value={targetDate}
                min={startDate || undefined}
                onChange={(event) => setTargetDate(event.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="budget-primary-button">
            + Create Savings Goal
          </button>
        </form>
      </section>

      <section className="savings-goals-section">
        <div className="section-heading">
          <div>
            <h2>Your Goals</h2>
            <p>
              {viewMode === "Yearly"
                ? "Monitor your savings journey for the selected year."
                : "Monitor your savings journey for the selected month."}
            </p>
          </div>

          <span className="goal-count">
            {filteredGoals.length}{" "}
            {filteredGoals.length === 1 ? "goal" : "goals"}
          </span>
        </div>

        {loading ? (
          <div className="empty-state">Loading savings goals...</div>
        ) : filteredGoals.length === 0 ? (
          <div className="empty-state">
            <h3>
              No savings goals for this{" "}
              {viewMode === "Yearly" ? "year" : "month"}
            </h3>
            <p>
              You have not created any savings goals for the selected{" "}
              {viewMode === "Yearly" ? "year" : "month"}.
            </p>
          </div>
        ) : (
          <div className="savings-goals-list">
            {filteredGoals.map((goal) => {
              const progress = getProgress(goal);
              const status = getGoalStatus(goal);
              const saved = Number(goal.amount_saved) || 0;
              const target = Number(goal.target_amount) || 0;
              const remaining = Math.max(0, target - saved);

              return (
                <article
                  className={`savings-goal-card ${
                    status.label === "Completed" ? "completed" : ""
                  }`}
                  key={goal.id}
                >
                  <div className="savings-goal-top">
                    <div>
                      <h3>{goal.goal_name}</h3>

                      <span
                        className="goal-status-badge"
                        style={{
                          color: status.color,
                          background: status.background,
                        }}
                      >
                        {status.label}
                      </span>
                    </div>

                    <div className="goal-actions">
                      <button
                        type="button"
                        className="goal-edit-button"
                        onClick={() => openEdit(goal)}
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        className="goal-delete-button"
                        onClick={() => handleDeleteGoal(goal)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="goal-amount-row">
                    <div>
                      <span>Saved so far</span>
                      <strong>{formatCurrency(saved)}</strong>
                    </div>

                    <div>
                      <span>Target amount</span>
                      <strong>{formatCurrency(target)}</strong>
                    </div>

                    <div>
                      <span>Remaining</span>
                      <strong>{formatCurrency(remaining)}</strong>
                    </div>
                  </div>

                  <div className="goal-progress-heading">
                    <span>Goal Progress</span>
                    <strong>{progress.toFixed(1)}%</strong>
                  </div>

                  <div
                    className="goal-progress-track"
                    role="progressbar"
                    aria-valuenow={Math.round(progress)}
                    aria-valuemin="0"
                    aria-valuemax="100"
                    aria-label={`${goal.goal_name} progress`}
                  >
                    <div
                      className="goal-progress-fill"
                      style={{ width: `${progress}%` }}
                    />
                  </div>

                  {renderGoalTiming(goal)}
                </article>
              );
            })}
          </div>
        )}
      </section>

      {editingGoal && (
        <div
          className="savings-modal-overlay"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setEditingGoal(null);
            }
          }}
        >
          <div
            className="savings-edit-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="editGoalTitle"
          >
            <div className="modal-heading">
              <div>
                <h2 id="editGoalTitle">Edit Savings Goal</h2>
                <p>Update your target and timeline.</p>
              </div>

              <button
                type="button"
                className="modal-close-button"
                onClick={() => setEditingGoal(null)}
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleUpdateGoal}>
              <div className="form-group">
                <label htmlFor="editGoalName">Goal Name</label>
                <input
                  id="editGoalName"
                  value={editGoalName}
                  onChange={(event) => setEditGoalName(event.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="editTargetAmount">Target Amount (₹)</label>
                <input
                  id="editTargetAmount"
                  type="number"
                  min="1"
                  step="0.01"
                  value={editTargetAmount}
                  onChange={(event) =>
                    setEditTargetAmount(event.target.value)
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="editAmountSaved">Amount Saved (₹)</label>
                <input
                  id="editAmountSaved"
                  type="number"
                  min="0"
                  step="0.01"
                  value={editAmountSaved}
                  onChange={(event) =>
                    setEditAmountSaved(event.target.value)
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="editStartDate">Start Date</label>
                <input
                  id="editStartDate"
                  type="date"
                  value={editStartDate}
                  max={editTargetDate || undefined}
                  onChange={(event) => setEditStartDate(event.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="editTargetDate">Target Date</label>
                <input
                  id="editTargetDate"
                  type="date"
                  value={editTargetDate}
                  min={editStartDate || undefined}
                  onChange={(event) => setEditTargetDate(event.target.value)}
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="goal-cancel-button"
                  onClick={() => setEditingGoal(null)}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="budget-primary-button"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SavingsGoals;