import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";

const CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Entertainment",
    "Miscellaneous",
];

function getLocalMonth() {
    const today = new Date();

    return `${today.getFullYear()}-${String(
        today.getMonth() + 1
    ).padStart(2, "0")}`;
}

function Budgets({
    month,
    year,
    viewMode = "monthly",
    setMonth,
    setYear,
    setViewMode,
}) {
    const selectedMonth =
        typeof month === "string" && /^\d{4}-\d{2}$/.test(month)
            ? month
            : getLocalMonth();

    const selectedYear =
        String(year || new Date().getFullYear());

    const isMonthly = viewMode === "monthly";

    const periodLabel = isMonthly
        ? new Date(
              `${selectedMonth}-01T00:00:00`
          ).toLocaleDateString("en-IN", {
              month: "long",
              year: "numeric",
          })
        : selectedYear;

    const [budgets, setBudgets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [categoryOptions, setCategoryOptions] = useState(CATEGORIES);

    // Create budget rows
    const [budgetRows, setBudgetRows] = useState([
        {
            category: "",
            amount: "",
        },
    ]);

    // Edit modal
    const [editingBudget, setEditingBudget] = useState(null);
    const [editCategory, setEditCategory] = useState("");
    const [editAmount, setEditAmount] = useState("");
    const [editMonth, setEditMonth] = useState("");

    // ============================================================
    // AUTO CLEAR MESSAGES
    // ============================================================

    useEffect(() => {
        if (!message && !error) {
            return;
        }

        const timer = setTimeout(() => {
            setMessage("");
            setError("");
        }, 3000);

        return () => clearTimeout(timer);
    }, [message, error]);

    // ============================================================
    // LOAD BUDGETS
    // ============================================================

    const loadBudgets = async () => {
        try {
            setLoading(true);
            setError("");

            const data = await api("/budgets");

            setBudgets(Array.isArray(data) ? data : []);
        } catch (err) {
            setError(err.message || "Failed to load budgets.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadBudgets();
    }, []);

    // ============================================================
    // FILTER BUDGETS USING GLOBAL PERIOD
    // ============================================================

    const monthBudgets = useMemo(() => {
        return budgets.filter((budget) => {
            const budgetMonth = String(budget.month || "");

            if (isMonthly) {
                return budgetMonth === selectedMonth;
            }

            return budgetMonth.startsWith(`${selectedYear}-`);
        });
    }, [budgets, selectedMonth, selectedYear, isMonthly]);

    // ============================================================
    // TOTAL BUDGET
    // ============================================================

    const totalBudget = useMemo(() => {
        return monthBudgets.reduce(
            (total, budget) =>
                total + Number(budget.allocated_amount || 0),
            0
        );
    }, [monthBudgets]);

    // ============================================================
    // EXISTING CATEGORIES
    // ============================================================

    const existingCategories = useMemo(() => {
        return monthBudgets.map((budget) => budget.category);
    }, [monthBudgets]);

    // ============================================================
    // CREATE FORM HELPERS
    // ============================================================

    const addCustomCategory = (onSelect) => {
        const entered = window.prompt("Enter your new budget category:");
        const category = String(entered || "").trim();
        if (!category) return;
        const existing = categoryOptions.find(
            (item) => item.toLowerCase() === category.toLowerCase()
        );
        const finalCategory = existing || category;
        if (!existing) setCategoryOptions((previous) => [...previous, category]);
        onSelect(finalCategory);
    };

    const addBudgetRow = () => {
        setBudgetRows((previous) => [
            ...previous,
            {
                category: "",
                amount: "",
            },
        ]);
    };

    const removeBudgetRow = (index) => {
        if (budgetRows.length === 1) {
            return;
        }

        setBudgetRows((previous) =>
            previous.filter((_, rowIndex) => rowIndex !== index)
        );
    };

    const updateBudgetRow = (index, field, value) => {
        setBudgetRows((previous) =>
            previous.map((row, rowIndex) =>
                rowIndex === index
                    ? {
                          ...row,
                          [field]: value,
                      }
                    : row
            )
        );
    };

    const getAvailableCategories = (rowIndex) => {
        const selectedByOtherRows = budgetRows
            .filter((_, index) => index !== rowIndex)
            .map((row) => row.category)
            .filter(Boolean);

        return categoryOptions.filter(
            (category) =>
                !existingCategories.includes(category) &&
                !selectedByOtherRows.includes(category)
        );
    };

    const newBudgetTotal = useMemo(() => {
        return budgetRows.reduce(
            (total, row) => total + Number(row.amount || 0),
            0
        );
    }, [budgetRows]);

    // ============================================================
    // CREATE BUDGET
    // ============================================================

    const handleCreateBudget = async (event) => {
        event.preventDefault();

        setMessage("");
        setError("");

        if (!isMonthly) {
            setError(
                "Please switch to Monthly mode to create a budget."
            );
            return;
        }

        const validRows = budgetRows.filter(
            (row) => row.category && row.amount !== ""
        );

        if (validRows.length === 0) {
            setError("Please add at least one category and amount.");
            return;
        }

        const invalidAmount = validRows.some(
            (row) =>
                Number(row.amount) <= 0 ||
                Number.isNaN(Number(row.amount))
        );

        if (invalidAmount) {
            setError("All budget amounts must be greater than 0.");
            return;
        }

        const duplicateCategories = new Set();

        for (const row of validRows) {
            if (duplicateCategories.has(row.category)) {
                setError("Please select each category only once.");
                return;
            }

            duplicateCategories.add(row.category);
        }

        const allocations = validRows.map((row) => ({
            category: row.category,
            allocated_amount: Number(row.amount),
        }));

        try {
            await api("/budgets", {
                method: "POST",
                body: JSON.stringify({
                    month: selectedMonth,
                    allocations,
                }),
            });

            setMessage("Budget created successfully.");

            setBudgetRows([
                {
                    category: "",
                    amount: "",
                },
            ]);

            await loadBudgets();
        } catch (err) {
            setError(err.message || "Failed to create budget.");
        }
    };

    // ============================================================
    // EDIT
    // ============================================================

    const openEditModal = (budget) => {
        setEditingBudget(budget);
        setEditCategory(budget.category);
        setEditAmount(budget.allocated_amount);
        setEditMonth(budget.month);
        setMessage("");
        setError("");
    };

    const closeEditModal = () => {
        setEditingBudget(null);
        setEditCategory("");
        setEditAmount("");
        setEditMonth("");
    };

    const handleUpdateBudget = async () => {
        if (!editingBudget) {
            return;
        }

        setMessage("");
        setError("");

        const numericAmount = Number(editAmount);

        if (!editCategory) {
            setError("Please select a category.");
            return;
        }

        if (!numericAmount || numericAmount <= 0) {
            setError("Amount must be greater than 0.");
            return;
        }

        if (!/^\d{4}-\d{2}$/.test(editMonth)) {
            setError("Please select a valid month.");
            return;
        }

        try {
            await api(`/budgets/${editingBudget.id}`, {
                method: "PUT",
                body: JSON.stringify({
                    month: editMonth,
                    allocations: [
                        {
                            category: editCategory,
                            allocated_amount: numericAmount,
                        },
                    ],
                }),
            });

            setMessage("Budget updated successfully.");

            closeEditModal();

            await loadBudgets();
        } catch (err) {
            setError(err.message || "Failed to update budget.");
        }
    };

    // ============================================================
    // DELETE
    // ============================================================

    const handleDeleteBudget = async (budget) => {
        const confirmed = window.confirm(
            `Delete the ${budget.category} budget for ${budget.month}?`
        );

        if (!confirmed) {
            return;
        }

        setMessage("");
        setError("");

        try {
            await api(`/budgets/${budget.id}`, {
                method: "DELETE",
            });

            setMessage("Budget deleted successfully.");

            await loadBudgets();
        } catch (err) {
            setError(err.message || "Failed to delete budget.");
        }
    };

    // ============================================================
    // FORMAT CURRENCY
    // ============================================================

    const formatCurrency = (amount) => {
        return `₹${Number(amount || 0).toLocaleString("en-IN")}`;
    };

    // ============================================================
    // UI
    // ============================================================

    return (
        <div className="page-content budget-page">
            {message && (
                <div className="budget-toast budget-toast-success">
                    <span>✓</span>
                    <span>{message}</span>
                </div>
            )}

            {error && (
                <div className="budget-toast budget-toast-error">
                    <span>!</span>
                    <span>{error}</span>
                </div>
            )}

            <div className="page-header">
                <div>
                    <h1>Budgets</h1>
                    <p>
                        Plan and manage your spending limits.
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
                        aria-label="Budget period"
                        value={viewMode}
                        onChange={(event) =>
                            setViewMode?.(event.target.value)
                        }
                    >
                        <option value="monthly">Monthly</option>
                        <option value="yearly">Yearly</option>
                    </select>

                    {isMonthly ? (
                        <input
                            aria-label="Select budget month"
                            type="month"
                            value={selectedMonth}
                            max={getLocalMonth()}
                            onChange={(event) =>
                                setMonth?.(event.target.value)
                            }
                        />
                    ) : (
                        <select
                            aria-label="Select budget year"
                            value={selectedYear}
                            onChange={(event) =>
                                setYear?.(event.target.value)
                            }
                        >
                            {Array.from(
                                {
                                    length: new Date().getFullYear() - 2020 + 1,
                                },
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
                </div>
            </div>

            {/* Summary Cards */}
            <div className="budget-summary-grid">
                <div className="budget-summary-card">
                    <span className="budget-summary-label">
                        Total Budget
                    </span>

                    <strong>{formatCurrency(totalBudget)}</strong>
                </div>

                <div className="budget-summary-card">
                    <span className="budget-summary-label">
                        {isMonthly ? "Budget Month" : "Budget Year"}
                    </span>

                    <strong>{periodLabel}</strong>
                </div>

                <div className="budget-summary-card">
                    <span className="budget-summary-label">
                        Categories
                    </span>

                    <strong>{monthBudgets.length}</strong>
                </div>
            </div>

            {/* Create Budget */}
            {isMonthly ? (
                <div className="budget-card">
                    <div className="budget-card-header">
                        <div>
                            <h2>Create Budget</h2>
                            <p>
                                Add one or more spending categories for{" "}
                                {periodLabel}.
                            </p>
                        </div>
                    </div>

                    <form onSubmit={handleCreateBudget}>
                        <div className="budget-create-table">
                            <div className="budget-create-header">
                                <span>Category</span>
                                <span>Allocated Amount</span>
                                <span></span>
                            </div>

                            {budgetRows.map((row, index) => (
                                <div
                                    className="budget-create-row"
                                    key={index}
                                >
                                    <select
                                        value={row.category}
                                        onChange={(event) => {
                                            const value = event.target.value;
                                            if (value === "__add_new_category__") {
                                                addCustomCategory((category) =>
                                                    updateBudgetRow(index, "category", category)
                                                );
                                            } else {
                                                updateBudgetRow(index, "category", value);
                                            }
                                        }}
                                    >
                                        <option value="">
                                            Select Category
                                        </option>
                                        <option value="__add_new_category__">
                                            + Add New Category
                                        </option>

                                        {getAvailableCategories(index).map(
                                            (category) => (
                                                <option
                                                    key={category}
                                                    value={category}
                                                >
                                                    {category}
                                                </option>
                                            )
                                        )}

                                        {row.category &&
                                            !getAvailableCategories(index).includes(
                                                row.category
                                            ) && (
                                                <option value={row.category}>
                                                    {row.category}
                                                </option>
                                            )}
                                    </select>

                                    <div className="budget-amount-input">
                                        <span>₹</span>

                                        <input
                                            type="number"
                                            min="1"
                                            step="0.01"
                                            placeholder="0"
                                            value={row.amount}
                                            onChange={(event) =>
                                                updateBudgetRow(
                                                    index,
                                                    "amount",
                                                    event.target.value
                                                )
                                            }
                                        />
                                    </div>

                                    <button
                                        type="button"
                                        className="budget-remove-row"
                                        onClick={() =>
                                            removeBudgetRow(index)
                                        }
                                        disabled={budgetRows.length === 1}
                                        title="Remove category"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            ))}
                        </div>

                        <div className="budget-create-actions">
                            <button
                                type="button"
                                className="budget-add-category-button"
                                onClick={addBudgetRow}
                                disabled={
                                    budgetRows.length >=
                                    CATEGORIES.length -
                                        existingCategories.length
                                }
                            >
                                + Add Category
                            </button>
                        </div>

                        <div className="budget-new-total">
                            <span>New Budget Total</span>

                            <strong>
                                {formatCurrency(newBudgetTotal)}
                            </strong>
                        </div>

                        <button
                            type="submit"
                            className="budget-primary-button"
                        >
                            Create Budgets
                        </button>
                    </form>
                </div>
            ) : (
                <div className="budget-card">
                    <div className="budget-card-header">
                        <div>
                            <h2>Yearly Budget View</h2>
                            <p>
                                You are viewing budgets for {selectedYear}.
                                Switch to Monthly mode to create a budget
                                for a particular month.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Existing Budgets */}
            <div className="budget-card">
                <div className="budget-card-header">
                    <div>
                        <h2>Budget Overview</h2>
                        <p>
                            {isMonthly
                                ? `Your spending limits for ${periodLabel}.`
                                : `Your spending limits for ${selectedYear}.`}
                        </p>
                    </div>
                </div>

                {loading ? (
                    <div className="budget-empty-state">
                        Loading budgets...
                    </div>
                ) : monthBudgets.length === 0 ? (
                    <div className="budget-empty-state">
                        <div className="budget-empty-icon">
                            💰
                        </div>

                        <h3>No budgets yet</h3>

                        <p>
                            {isMonthly
                                ? `Create your first budget category for ${periodLabel}.`
                                : `No budgets have been created for ${selectedYear}.`}
                        </p>
                    </div>
                ) : (
                    <div className="budget-list">
                        {monthBudgets.map((budget) => (
                            <div
                                className="budget-list-item"
                                key={budget.id}
                            >
                                <div className="budget-category-info">
                                    <div className="budget-category-icon">
                                        {budget.category === "Food"
                                            ? "🍔"
                                            : budget.category === "Travel"
                                            ? "✈️"
                                            : budget.category === "Shopping"
                                            ? "🛍️"
                                            : budget.category === "Education"
                                            ? "📚"
                                            : budget.category ===
                                              "Entertainment"
                                            ? "🎬"
                                            : "📦"}
                                    </div>

                                    <div>
                                        <h3>{budget.category}</h3>

                                        <span>
                                            {budget.month}
                                        </span>
                                    </div>
                                </div>

                                <div className="budget-list-right">
                                    <strong>
                                        {formatCurrency(
                                            budget.allocated_amount
                                        )}
                                    </strong>

                                    <div className="budget-actions">
                                        <button
                                            type="button"
                                            className="budget-edit-button"
                                            onClick={() =>
                                                openEditModal(budget)
                                            }
                                        >
                                            Edit
                                        </button>

                                        <button
                                            type="button"
                                            className="budget-delete-button"
                                            onClick={() =>
                                                handleDeleteBudget(budget)
                                            }
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Edit Modal */}
            {editingBudget && (
                <div className="budget-modal-overlay">
                    <div className="budget-modal">
                        <div className="budget-modal-header">
                            <div>
                                <h2>Edit Budget</h2>
                                <p>
                                    Update your spending limit.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="budget-modal-close"
                                onClick={closeEditModal}
                            >
                                ×
                            </button>
                        </div>

                        <div className="budget-modal-form">
                            <label>
                                Month

                                <input
                                    type="month"
                                    value={editMonth}
                                    onChange={(event) =>
                                        setEditMonth(event.target.value)
                                    }
                                />
                            </label>

                            <label>
                                Category

                                <select
                                    value={editCategory}
                                    onChange={(event) => {
                                        const value = event.target.value;
                                        if (value === "__add_new_category__") {
                                            addCustomCategory(setEditCategory);
                                        } else {
                                            setEditCategory(value);
                                        }
                                    }}
                                >
                                    <option value="__add_new_category__">+ Add New Category</option>
                                    {categoryOptions.map((category) => (
                                        <option
                                            key={category}
                                            value={category}
                                        >
                                            {category}
                                        </option>
                                    ))}
                                </select>
                            </label>

                            <label>
                                Allocated Amount

                                <div className="budget-amount-input">
                                    <span>₹</span>

                                    <input
                                        type="number"
                                        min="1"
                                        step="0.01"
                                        value={editAmount}
                                        onChange={(event) =>
                                            setEditAmount(event.target.value)
                                        }
                                    />
                                </div>
                            </label>
                        </div>

                        <div className="budget-modal-actions">
                            <button
                                type="button"
                                className="budget-cancel-button"
                                onClick={closeEditModal}
                            >
                                Cancel
                            </button>

                            <button
                                type="button"
                                className="budget-primary-button"
                                onClick={handleUpdateBudget}
                            >
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Budgets;