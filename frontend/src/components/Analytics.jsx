import React, { useEffect, useMemo, useState } from "react";
import {
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Tooltip,
    Legend,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    LineChart,
    Line,
    AreaChart,
    Area,
} from "recharts";
import { api } from "../api";

const MONTHS = [
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
];

const CHART_COLORS = [
    "#6c5ce7",
    "#00b894",
    "#0984e3",
    "#fdcb6e",
    "#e17055",
    "#a29bfe",
    "#00cec9",
    "#fd79a8",
];

/* Different color for each expense category */
const CATEGORY_COLORS = {
    Food: "#e17055",
    Travel: "#0984e3",
    Shopping: "#6c5ce7",
    Education: "#00b894",
    Entertainment: "#fd79a8",
    Miscellaneous: "#fdcb6e",
    Other: "#a29bfe",
};

const MONTH_CLASSES = [
    "month-purple",
    "month-blue",
    "month-green",
    "month-orange",
    "month-red",
    "month-indigo",
    "month-teal",
    "month-pink",
    "month-violet",
    "month-cyan",
    "month-amber",
    "month-rose",
];

const getCurrentYear = () => new Date().getFullYear();

const getCurrentMonth = () =>
    String(new Date().getMonth() + 1).padStart(2, "0");

const getMonthKey = (year, monthNumber) =>
    `${year}-${String(monthNumber).padStart(2, "0")}`;

const formatCurrency = (amount) =>
    new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
    }).format(Math.abs(Number(amount) || 0));

const formatPercentage = (value) =>
    `${Number(value || 0).toFixed(2)}%`;

const getMonthName = (monthKey) => {
    if (!monthKey) return "";

    const parts = String(monthKey).split("-");

    if (parts.length !== 2) return monthKey;

    const monthNumber = Number(parts[1]);

    return MONTHS[monthNumber - 1] || monthKey;
};

const getMonthNumber = (monthKey) => {
    if (!monthKey) return 1;

    const parts = String(monthKey).split("-");

    return Number(parts[1]) || 1;
};

const getYearFromMonth = (monthKey) => {
    if (!monthKey) return getCurrentYear();

    const parts = String(monthKey).split("-");

    return Number(parts[0]) || getCurrentYear();
};

const getGoalPeriod = (date) => {
    if (!date || typeof date !== "string") {
        return null;
    }

    const value = date.slice(0, 10);

    const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);

    if (!match) return null;

    return {
        year: Number(match[1]),
        month: Number(match[2]),
    };
};

function Analytics() {
    const [viewMode, setViewMode] = useState("monthly");

    const [selectedMonth, setSelectedMonth] = useState(
        `${getCurrentYear()}-${getCurrentMonth()}`
    );

    const [selectedYear, setSelectedYear] = useState(
        getCurrentYear()
    );

    const [yearData, setYearData] = useState({});

    const [savingsGoals, setSavingsGoals] = useState([]);

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");

    const loadOneMonth = async (monthKey) => {
        try {
            const data = await api(`/analytics/${monthKey}`);

            return {
                month: monthKey,
                data: data || {},
                error: null,
            };
        } catch (err) {
            return {
                month: monthKey,
                data: {},
                error: err.message || "Unable to load month.",
            };
        }
    };

    const loadYear = async (year) => {
        try {
            setLoading(true);
            setError("");

            const monthKeys = Array.from(
                { length: 12 },
                (_, index) => getMonthKey(year, index + 1)
            );

            const results = await Promise.all(
                monthKeys.map((monthKey) =>
                    loadOneMonth(monthKey)
                )
            );

            const nextYearData = {};

            results.forEach((result) => {
                nextYearData[result.month] = result.data;
            });

            setYearData(nextYearData);

            const failedMonths = results.filter(
                (result) => result.error
            );

            if (failedMonths.length === 12) {
                setError(
                    failedMonths[0]?.error ||
                        "Unable to load analytics."
                );
            }
        } catch (err) {
            setError(
                err.message ||
                    "Unable to load yearly analytics."
            );
        } finally {
            setLoading(false);
        }
    };

    const loadSavingsGoals = async () => {
        try {
            const data = await api("/savings-goals");

            const goals = Array.isArray(data)
                ? data
                : Array.isArray(data?.goals)
                ? data.goals
                : Array.isArray(data?.items)
                ? data.items
                : [];

            const normalized = goals.map((goal) => {
                const target = Number(
                    goal.target_amount || 0
                );

                const saved = Number(
                    goal.amount_saved || 0
                );

                const progress =
                    target > 0
                        ? (saved / target) * 100
                        : 0;

                return {
                    ...goal,
                    target_amount: target,
                    amount_saved: saved,
                    progress_percentage: Number(
                        goal.progress_percentage ??
                            progress
                    ),
                };
            });

            setSavingsGoals(normalized);
        } catch (err) {
            console.error(
                "Savings goals analytics error:",
                err
            );

            setSavingsGoals([]);
        }
    };

    useEffect(() => {
        loadSavingsGoals();
    }, []);

    useEffect(() => {
        loadYear(selectedYear);
    }, [selectedYear]);

    const selectedData =
        yearData[selectedMonth] || {};

    const totalIncome = Number(
        selectedData?.total_income || 0
    );

    const totalExpenses = Number(
        selectedData?.total_expenses || 0
    );

    const balance = Number(
        selectedData?.balance || 0
    );

    const savingsRate = Number(
        selectedData?.savings_rate || 0
    );

    const incomeTransactions = Number(
        selectedData?.income_transactions || 0
    );

    const expenseTransactions = Number(
        selectedData?.expense_transactions || 0
    );

    const totalTransactions = Number(
        selectedData?.total_transactions ||
            incomeTransactions +
                expenseTransactions
    );

    const categoryData = useMemo(() => {
        const categories = Array.isArray(
            selectedData?.category_expenses
        )
            ? selectedData.category_expenses
            : [];

        return categories
            .map((item) => ({
                name:
                    item.category ||
                    "Other",
                value: Number(
                    item.amount || 0
                ),
            }))
            .filter(
                (item) => item.value > 0
            )
            .sort(
                (a, b) =>
                    b.value - a.value
            );
    }, [selectedData]);

    const budgetData = useMemo(() => {
        const budgets = Array.isArray(
            selectedData?.budget_summary
        )
            ? selectedData.budget_summary
            : [];

        return budgets.map((item) => ({
            category:
                item.category ||
                "Other",

            budget: Number(
                item.allocated || 0
            ),

            spent: Number(
                item.spent || 0
            ),
        }));
    }, [selectedData]);

    const monthlyCards = useMemo(() => {
        return Array.from(
            { length: 12 },
            (_, index) => {
                const monthNumber =
                    index + 1;

                const monthKey =
                    getMonthKey(
                        selectedYear,
                        monthNumber
                    );

                const data =
                    yearData[monthKey] ||
                    {};

                const income = Number(
                    data.total_income || 0
                );

                const expenses = Number(
                    data.total_expenses || 0
                );

                const balance =
                    income - expenses;

                const categoryExpenses =
                    Array.isArray(
                        data.category_expenses
                    )
                        ? data.category_expenses
                        : [];

                const budgetSummary =
                    Array.isArray(
                        data.budget_summary
                    )
                        ? data.budget_summary
                        : [];

                const monthGoals =
                    savingsGoals.filter(
                        (goal) => {
                            const period =
                                getGoalPeriod(
                                    goal.start_date
                                );

                            return (
                                period &&
                                period.year ===
                                    Number(
                                        selectedYear
                                    ) &&
                                period.month ===
                                    monthNumber
                            );
                        }
                    );

                const goalTarget =
                    monthGoals.reduce(
                        (
                            total,
                            goal
                        ) =>
                            total +
                            Number(
                                goal.target_amount ||
                                    0
                            ),
                        0
                    );

                const goalSaved =
                    monthGoals.reduce(
                        (
                            total,
                            goal
                        ) =>
                            total +
                            Number(
                                goal.amount_saved ||
                                    0
                            ),
                        0
                    );

                const goalProgress =
                    goalTarget > 0
                        ? Math.min(
                              100,
                              (goalSaved /
                                  goalTarget) *
                                  100
                          )
                        : 0;

                const hasData =
                    income > 0 ||
                    expenses > 0 ||
                    categoryExpenses.length >
                        0 ||
                    budgetSummary.length >
                        0 ||
                    monthGoals.length > 0;

                return {
                    monthNumber,
                    monthKey,
                    monthName:
                        MONTHS[index],
                    income,
                    expenses,
                    balance,
                    savingsRate: Number(
                        data.savings_rate ||
                            0
                    ),
                    incomeTransactions:
                        Number(
                            data.income_transactions ||
                                0
                        ),
                    expenseTransactions:
                        Number(
                            data.expense_transactions ||
                                0
                        ),
                    totalTransactions:
                        Number(
                            data.total_transactions ||
                                0
                        ),
                    categoryCount:
                        categoryExpenses.length,
                    budgetCount:
                        budgetSummary.length,
                    goalCount:
                        monthGoals.length,
                    goalTarget,
                    goalSaved,
                    goalProgress,
                    hasData,
                };
            }
        );
    }, [
        yearData,
        selectedYear,
        savingsGoals,
    ]);

    const activeMonthCards = useMemo(() => {
        return monthlyCards.filter(
            (month) => month.hasData
        );
    }, [monthlyCards]);

    const yearlySummary = useMemo(() => {
        const income = monthlyCards.reduce(
            (sum, item) =>
                sum + item.income,
            0
        );

        const expenses =
            monthlyCards.reduce(
                (sum, item) =>
                    sum + item.expenses,
                0
            );

        const balance =
            income - expenses;

        const incomeTransactions =
            monthlyCards.reduce(
                (sum, item) =>
                    sum +
                    item.incomeTransactions,
                0
            );

        const expenseTransactions =
            monthlyCards.reduce(
                (sum, item) =>
                    sum +
                    item.expenseTransactions,
                0
            );

        const totalTransactions =
            incomeTransactions +
            expenseTransactions;

        const activeMonths =
            activeMonthCards.length;

        const savingsRate =
            income > 0
                ? (balance / income) * 100
                : 0;

        return {
            income,
            expenses,
            balance,
            incomeTransactions,
            expenseTransactions,
            totalTransactions,
            activeMonths,
            savingsRate,
        };
    }, [
        monthlyCards,
        activeMonthCards,
    ]);

    const yearlyTrendData = useMemo(() => {
        return monthlyCards.map(
            (item) => ({
                month:
                    item.monthName.slice(
                        0,
                        3
                    ),
                income: item.income,
                expenses:
                    item.expenses,
                balance:
                    item.balance,
            })
        );
    }, [monthlyCards]);

    const selectedMonthNumber =
        getMonthNumber(
            selectedMonth
        );

    const chartType =
        ((selectedMonthNumber - 1) % 4);

    const selectedMonthGoals =
        useMemo(() => {
            return savingsGoals.filter(
                (goal) => {
                    const period =
                        getGoalPeriod(
                            goal.start_date
                        );

                    return (
                        period &&
                        period.year ===
                            getYearFromMonth(
                                selectedMonth
                            ) &&
                        period.month ===
                            selectedMonthNumber
                    );
                }
            );
        }, [
            savingsGoals,
            selectedMonth,
            selectedMonthNumber,
        ]);

    const selectedGoalTarget =
        selectedMonthGoals.reduce(
            (sum, goal) =>
                sum +
                Number(
                    goal.target_amount || 0
                ),
            0
        );

    const selectedGoalSaved =
        selectedMonthGoals.reduce(
            (sum, goal) =>
                sum +
                Number(
                    goal.amount_saved || 0
                ),
            0
        );

    const selectedGoalProgress =
        selectedGoalTarget > 0
            ? Math.min(
                  100,
                  (selectedGoalSaved /
                      selectedGoalTarget) *
                      100
              )
            : 0;

    const handleViewModeChange = (
        event
    ) => {
        const nextMode =
            event.target.value;

        setViewMode(nextMode);

        if (
            nextMode === "yearly"
        ) {
            setSelectedYear(
                getYearFromMonth(
                    selectedMonth
                )
            );
        }
    };

    const handleMonthChange = (
        event
    ) => {
        const value =
            event.target.value;

        setSelectedMonth(value);

        setSelectedYear(
            getYearFromMonth(value)
        );
    };

    const handleYearChange = (
        event
    ) => {
        const value = Number(
            event.target.value
        );

        setSelectedYear(value);

        const monthNumber =
            getMonthNumber(
                selectedMonth
            );

        setSelectedMonth(
            getMonthKey(
                value,
                monthNumber
            )
        );
    };

    const renderBalance = (
        value
    ) => {
        const numericValue =
            Number(value) || 0;

        return (
            <div className="analytics-balance-display">
                <strong>
                    {formatCurrency(
                        numericValue
                    )}
                </strong>

                {numericValue < 0 && (
                    <small>
                        Deficit
                    </small>
                )}

                {numericValue >= 0 && (
                    <small>
                        Available
                    </small>
                )}
            </div>
        );
    };

    const renderMonthlyChart = () => {
        if (chartType === 0) {
            return (
                <div className="analytics-dynamic-chart">
                    <div className="analytics-chart-label">
                        Category Distribution
                    </div>

                    {categoryData.length ===
                    0 ? (
                        <div className="analytics-empty-chart">
                            No expense categories
                            available for{" "}
                            {getMonthName(
                                selectedMonth
                            )}
                        </div>
                    ) : (
                        <ResponsiveContainer
                            width="100%"
                            height={340}
                        >
                            <PieChart>
                                <Pie
                                    data={
                                        categoryData
                                    }
                                    dataKey="value"
                                    nameKey="name"
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={65}
                                    outerRadius={
                                        115
                                    }
                                    paddingAngle={
                                        4
                                    }
                                >
                                    {categoryData.map(
                                        (
                                            entry,
                                            index
                                        ) => (
                                            <Cell
                                                key={
                                                    entry.name +
                                                    index
                                                }
                                                fill={
                                                    CHART_COLORS[
                                                        index %
                                                            CHART_COLORS.length
                                                    ]
                                                }
                                            />
                                        )
                                    )}
                                </Pie>

                                <Tooltip
                                    formatter={(
                                        value
                                    ) =>
                                        formatCurrency(
                                            value
                                        )
                                    }
                                />

                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    )}
                </div>
            );
        }

        if (chartType === 1) {
            return (
                <div className="analytics-dynamic-chart">
                    <div className="analytics-chart-label">
                        Budget vs Actual Spending
                    </div>

                    {budgetData.length ===
                    0 ? (
                        <div className="analytics-empty-chart">
                            No budget data available
                            for{" "}
                            {getMonthName(
                                selectedMonth
                            )}
                        </div>
                    ) : (
                        <ResponsiveContainer
                            width="100%"
                            height={340}
                        >
                            <BarChart
                                data={
                                    budgetData
                                }
                            >
                                <CartesianGrid
                                    strokeDasharray="3 3"
                                />

                                <XAxis
                                    dataKey="category"
                                />

                                <YAxis />

                                <Tooltip
                                    formatter={(
                                        value
                                    ) =>
                                        formatCurrency(
                                            value
                                        )
                                    }
                                />

                                <Legend />

                                <Bar
                                    dataKey="budget"
                                    name="Budget"
                                    fill="#6c5ce7"
                                    radius={[
                                        6,
                                        6,
                                        0,
                                        0,
                                    ]}
                                />

                                <Bar
                                    dataKey="spent"
                                    name="Spent"
                                    fill="#e17055"
                                    radius={[
                                        6,
                                        6,
                                        0,
                                        0,
                                    ]}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </div>
            );
        }

        if (chartType === 2) {
            const comparisonData = [
                {
                    name: "Income",
                    amount: totalIncome,
                },
                {
                    name: "Expenses",
                    amount: totalExpenses,
                },
                {
                    name: "Balance",
                    amount: Math.abs(
                        balance
                    ),
                },
            ];

            return (
                <div className="analytics-dynamic-chart">
                    <div className="analytics-chart-label">
                        Financial Position
                    </div>

                    <ResponsiveContainer
                        width="100%"
                        height={340}
                    >
                        <BarChart
                            data={
                                comparisonData
                            }
                        >
                            <CartesianGrid
                                strokeDasharray="3 3"
                            />

                            <XAxis
                                dataKey="name"
                            />

                            <YAxis />

                            <Tooltip
                                formatter={(
                                    value
                                ) =>
                                    formatCurrency(
                                        value
                                    )
                                }
                            />

                            <Bar
                                dataKey="amount"
                                name="Amount"
                                radius={[
                                    8,
                                    8,
                                    0,
                                    0,
                                ]}
                            >
                                {comparisonData.map(
                                    (
                                        item,
                                        index
                                    ) => (
                                        <Cell
                                            key={
                                                item.name
                                            }
                                            fill={
                                                [
                                                    "#00b894",
                                                    "#e17055",
                                                    "#6c5ce7",
                                                ][
                                                    index
                                                ]
                                            }
                                        />
                                    )
                                )}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            );
        }

        return (
            <div className="analytics-dynamic-chart">
                <div className="analytics-chart-label">
                    Income vs Expense Overview
                </div>

                <ResponsiveContainer
                    width="100%"
                    height={340}
                >
                    <AreaChart
                        data={[
                            {
                                name: getMonthName(
                                    selectedMonth
                                ),
                                income:
                                    totalIncome,
                                expenses:
                                    totalExpenses,
                            },
                        ]}
                    >
                        <CartesianGrid
                            strokeDasharray="3 3"
                        />

                        <XAxis
                            dataKey="name"
                        />

                        <YAxis />

                        <Tooltip
                            formatter={(
                                value
                            ) =>
                                formatCurrency(
                                    value
                                )
                            }
                        />

                        <Legend />

                        <Area
                            type="monotone"
                            dataKey="income"
                            name="Income"
                            fill="#00b894"
                            stroke="#00b894"
                            fillOpacity={0.25}
                        />

                        <Area
                            type="monotone"
                            dataKey="expenses"
                            name="Expenses"
                            fill="#e17055"
                            stroke="#e17055"
                            fillOpacity={0.25}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="page-content analytics-page">
                <div className="page-header">
                    <div>
                        <h1>
                            Analytics
                        </h1>

                        <p>
                            Preparing your
                            financial insights...
                        </p>
                    </div>
                </div>

                <div className="analytics-loading">
                    Loading yearly analytics...
                </div>
            </div>
        );
    }

    return (
        <div className="page-content analytics-page">

            <div className="page-header analytics-header">
                <div>
                    <div className="analytics-title-row">
                        <div className="analytics-title-icon">
                            📊
                        </div>

                        <div>
                            <h1>
                                Analytics
                            </h1>

                            <p>
                                Understand your
                                spending, income
                                and savings
                                patterns.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="analytics-period-controls">

                    <div className="analytics-control-group">
                        <label>
                            View
                        </label>

                        <select
                            value={
                                viewMode
                            }
                            onChange={
                                handleViewModeChange
                            }
                        >
                            <option value="monthly">
                                Monthly
                            </option>

                            <option value="yearly">
                                Yearly
                            </option>
                        </select>
                    </div>

                    {viewMode ===
                    "monthly" ? (
                        <div className="analytics-control-group">
                            <label>
                                Month
                            </label>

                            <input
                                type="month"
                                value={
                                    selectedMonth
                                }
                                onChange={
                                    handleMonthChange
                                }
                            />
                        </div>
                    ) : (
                        <div className="analytics-control-group">
                            <label>
                                Year
                            </label>

                            <select
                                value={
                                    selectedYear
                                }
                                onChange={
                                    handleYearChange
                                }
                            >
                                {Array.from(
                                    {
                                        length: 7,
                                    },
                                    (
                                        _,
                                        index
                                    ) =>
                                        getCurrentYear() -
                                        2 +
                                        index
                                ).map(
                                    (
                                        item
                                    ) => (
                                        <option
                                            key={
                                                item
                                            }
                                            value={
                                                item
                                            }
                                        >
                                            {
                                                item
                                            }
                                        </option>
                                    )
                                )}
                            </select>
                        </div>
                    )}
                </div>
            </div>

            {error && (
                <div className="analytics-error">
                    <strong>
                        Analytics loading issue
                    </strong>

                    <p>
                        {error}
                    </p>

                    <button
                        type="button"
                        onClick={() =>
                            loadYear(
                                selectedYear
                            )
                        }
                    >
                        Try Again
                    </button>
                </div>
            )}

            {viewMode ===
                "monthly" && (
                <>
                    <div className="analytics-selected-period-banner">
                        <div>
                            <span>
                                Selected Month
                            </span>

                            <strong>
                                {getMonthName(
                                    selectedMonth
                                )}{" "}
                                {getYearFromMonth(
                                    selectedMonth
                                )}
                            </strong>
                        </div>

                        <div className="analytics-banner-badge">
                            Monthly View
                        </div>
                    </div>

                    <div className="analytics-summary-grid analytics-summary-grid-new">

                        <div className="analytics-summary-card analytics-card-income">
                            <span>
                                Total Income
                            </span>

                            <strong>
                                {formatCurrency(
                                    totalIncome
                                )}
                            </strong>

                            <small>
                                {incomeTransactions}{" "}
                                income
                                transaction
                                {incomeTransactions ===
                                1
                                    ? ""
                                    : "s"}
                            </small>
                        </div>

                        <div className="analytics-summary-card analytics-card-expense">
                            <span>
                                Total Expenses
                            </span>

                            <strong>
                                {formatCurrency(
                                    totalExpenses
                                )}
                            </strong>

                            <small>
                                {expenseTransactions}{" "}
                                expense
                                transaction
                                {expenseTransactions ===
                                1
                                    ? ""
                                    : "s"}
                            </small>
                        </div>

                        <div className="analytics-summary-card analytics-card-balance">
                            <span>
                                Remaining Balance
                            </span>

                            {renderBalance(
                                balance
                            )}
                        </div>

                        <div className="analytics-summary-card analytics-card-savings">
                            <span>
                                Savings Rate
                            </span>

                            <strong>
                                {formatPercentage(
                                    savingsRate
                                )}
                            </strong>

                            <small>
                                Based on income
                            </small>
                        </div>

                        <div className="analytics-summary-card analytics-card-transactions">
                            <span>
                                Total Transactions
                            </span>

                            <strong>
                                {
                                    totalTransactions
                                }
                            </strong>

                            <small>
                                Income +
                                expenses
                            </small>
                        </div>
                    </div>

                    <div className="analytics-card analytics-full-card analytics-dynamic-card">

                        <div className="analytics-card-header">
                            <div>
                                <h2>
                                    {getMonthName(
                                        selectedMonth
                                    )}{" "}
                                    Financial
                                    Analysis
                                </h2>

                                <p>
                                    Visualization style
                                    changes by month
                                    to give a different
                                    perspective.
                                </p>
                            </div>

                            <span className="analytics-chart-style-badge">
                                {chartType ===
                                0
                                    ? "Pie Chart"
                                    : chartType ===
                                      1
                                    ? "Budget Bar"
                                    : chartType ===
                                      2
                                    ? "Comparison Bar"
                                    : "Area Chart"}
                            </span>
                        </div>

                        {renderMonthlyChart()}
                    </div>

                    <div className="analytics-chart-grid">

                        <div className="analytics-card">

                            <div className="analytics-card-header">
                                <div>
                                    <h2>
                                        Category-wise
                                        Spending
                                    </h2>

                                    <p>
                                        Where your
                                        money went
                                    </p>
                                </div>
                            </div>

                            {categoryData.length ===
                            0 ? (
                                <div className="analytics-empty-chart">
                                    No expenses for{" "}
                                    {getMonthName(
                                        selectedMonth
                                    )}
                                </div>
                            ) : (
                                <ResponsiveContainer
                                    width="100%"
                                    height={300}
                                >
                                    <BarChart
                                        data={
                                            categoryData
                                        }
                                        layout="vertical"
                                        margin={{
                                            left: 20,
                                            right: 20,
                                        }}
                                    >
                                        <CartesianGrid
                                            strokeDasharray="3 3"
                                        />

                                        <XAxis
                                            type="number"
                                        />

                                        <YAxis
                                            type="category"
                                            dataKey="name"
                                            width={90}
                                        />

                                        <Tooltip
                                            formatter={(
                                                value
                                            ) =>
                                                formatCurrency(
                                                    value
                                                )
                                            }
                                        />

                                        <Bar
                                            dataKey="value"
                                            name="Expense"
                                            radius={[
                                                0,
                                                7,
                                                7,
                                                0,
                                            ]}
                                        >
                                            {categoryData.map(
                                                (
                                                    entry,
                                                    index
                                                ) => (
                                                    <Cell
                                                        key={`${entry.name}-${index}`}
                                                        fill={
                                                            CATEGORY_COLORS[
                                                                entry.name
                                                            ] ||
                                                            CHART_COLORS[
                                                                index %
                                                                    CHART_COLORS.length
                                                            ]
                                                        }
                                                    />
                                                )
                                            )}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            )}
                        </div>

                        <div className="analytics-card">

                            <div className="analytics-card-header">
                                <div>
                                    <h2>
                                        Budget vs
                                        Spending
                                    </h2>

                                    <p>
                                        Planned versus
                                        actual
                                    </p>
                                </div>
                            </div>

                            {budgetData.length ===
                            0 ? (
                                <div className="analytics-empty-chart">
                                    No budgets for{" "}
                                    {getMonthName(
                                        selectedMonth
                                    )}
                                </div>
                            ) : (
                                <ResponsiveContainer
                                    width="100%"
                                    height={300}
                                >
                                    <BarChart
                                        data={
                                            budgetData
                                        }
                                    >
                                        <CartesianGrid
                                            strokeDasharray="3 3"
                                        />

                                        <XAxis
                                            dataKey="category"
                                        />

                                        <YAxis />

                                        <Tooltip
                                            formatter={(
                                                value
                                            ) =>
                                                formatCurrency(
                                                    value
                                                )
                                            }
                                        />

                                        <Legend />

                                        <Bar
                                            dataKey="budget"
                                            name="Budget"
                                            fill="#6c5ce7"
                                        />

                                        <Bar
                                            dataKey="spent"
                                            name="Spent"
                                            fill="#e17055"
                                        />
                                    </BarChart>
                                </ResponsiveContainer>
                            )}
                        </div>
                    </div>

                    <div className="analytics-card analytics-full-card">

                        <div className="analytics-card-header">
                            <div>
                                <h2>
                                    {getYearFromMonth(
                                        selectedMonth
                                    )}{" "}
                                    Monthly Trend
                                </h2>

                                <p>
                                    Compare all months
                                    of the selected
                                    year.
                                </p>
                            </div>
                        </div>

                        <ResponsiveContainer
                            width="100%"
                            height={340}
                        >
                            <LineChart
                                data={
                                    yearlyTrendData
                                }
                            >
                                <CartesianGrid
                                    strokeDasharray="3 3"
                                />

                                <XAxis
                                    dataKey="month"
                                />

                                <YAxis />

                                <Tooltip
                                    formatter={(
                                        value
                                    ) =>
                                        formatCurrency(
                                            value
                                        )
                                    }
                                />

                                <Legend />

                                <Line
                                    type="monotone"
                                    dataKey="income"
                                    name="Income"
                                    stroke="#00b894"
                                    strokeWidth={3}
                                />

                                <Line
                                    type="monotone"
                                    dataKey="expenses"
                                    name="Expenses"
                                    stroke="#e17055"
                                    strokeWidth={3}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="analytics-savings-grid">

                        <div className="analytics-card">

                            <div className="analytics-card-header">
                                <div>
                                    <h2>
                                        Savings Progress
                                    </h2>

                                    <p>
                                        Goals created
                                        during this
                                        month
                                    </p>
                                </div>
                            </div>

                            <div className="analytics-goal-progress-top">
                                <strong>
                                    {formatPercentage(
                                        selectedGoalProgress
                                    )}
                                </strong>

                                <span>
                                    {formatCurrency(
                                        selectedGoalSaved
                                    )}{" "}
                                    of{" "}
                                    {formatCurrency(
                                        selectedGoalTarget
                                    )}
                                </span>
                            </div>

                            <div className="analytics-progress-track">
                                <div
                                    className="analytics-progress-fill"
                                    style={{
                                        width: `${selectedGoalProgress}%`,
                                    }}
                                />
                            </div>

                            <div className="analytics-goal-list analytics-goal-list-new">
                                {selectedMonthGoals.length ===
                                0 ? (
                                    <p className="analytics-empty-text">
                                        No savings goals
                                        created in this
                                        month.
                                    </p>
                                ) : (
                                    selectedMonthGoals.map(
                                        (
                                            goal
                                        ) => (
                                            <div
                                                className="analytics-goal-item"
                                                key={
                                                    goal.id
                                                }
                                            >
                                                <div>
                                                    <strong>
                                                        {
                                                            goal.goal_name
                                                        }
                                                    </strong>

                                                    <span>
                                                        {formatCurrency(
                                                            goal.amount_saved
                                                        )}{" "}
                                                        /{" "}
                                                        {formatCurrency(
                                                            goal.target_amount
                                                        )}
                                                    </span>
                                                </div>

                                                <strong>
                                                    {Number(
                                                        goal.progress_percentage ||
                                                            0
                                                    ).toFixed(
                                                        1
                                                    )}
                                                    %
                                                </strong>
                                            </div>
                                        )
                                    )
                                )}
                            </div>
                        </div>

                        <div className="analytics-card">

                            <div className="analytics-card-header">
                                <div>
                                    <h2>
                                        Quick Insights
                                    </h2>

                                    <p>
                                        Key information
                                        for{" "}
                                        {getMonthName(
                                            selectedMonth
                                        )}
                                    </p>
                                </div>
                            </div>

                            <div className="analytics-insights">
                                <div className="analytics-insight-item">
                                    <span>
                                        Expense
                                        Categories
                                    </span>

                                    <strong>
                                        {
                                            categoryData.length
                                        }
                                    </strong>
                                </div>

                                <div className="analytics-insight-item">
                                    <span>
                                        Budget
                                        Categories
                                    </span>

                                    <strong>
                                        {
                                            budgetData.length
                                        }
                                    </strong>
                                </div>

                                <div className="analytics-insight-item">
                                    <span>
                                        Savings Goals
                                    </span>

                                    <strong>
                                        {
                                            selectedMonthGoals.length
                                        }
                                    </strong>
                                </div>

                                <div className="analytics-insight-item">
                                    <span>
                                        Total
                                        Transactions
                                    </span>

                                    <strong>
                                        {
                                            totalTransactions
                                        }
                                    </strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {viewMode ===
                "yearly" && (
                <>
                    <div className="analytics-selected-period-banner yearly-banner">
                        <div>
                            <span>
                                Selected Year
                            </span>

                            <strong>
                                {selectedYear}
                            </strong>
                        </div>

                        <div className="analytics-banner-badge">
                            Yearly View
                        </div>
                    </div>

                    <div className="analytics-summary-grid analytics-summary-grid-new">

                        <div className="analytics-summary-card analytics-card-income">
                            <span>
                                Yearly Income
                            </span>

                            <strong>
                                {formatCurrency(
                                    yearlySummary.income
                                )}
                            </strong>

                            <small>
                                Total for{" "}
                                {selectedYear}
                            </small>
                        </div>

                        <div className="analytics-summary-card analytics-card-expense">
                            <span>
                                Yearly Expenses
                            </span>

                            <strong>
                                {formatCurrency(
                                    yearlySummary.expenses
                                )}
                            </strong>

                            <small>
                                Total spending
                            </small>
                        </div>

                        <div className="analytics-summary-card analytics-card-balance">
                            <span>
                                Yearly Balance
                            </span>

                            {renderBalance(
                                yearlySummary.balance
                            )}
                        </div>

                        <div className="analytics-summary-card analytics-card-savings">
                            <span>
                                Savings Rate
                            </span>

                            <strong>
                                {formatPercentage(
                                    yearlySummary.savingsRate
                                )}
                            </strong>

                            <small>
                                Annual rate
                            </small>
                        </div>

                        <div className="analytics-summary-card analytics-card-transactions">
                            <span>
                                Active Months
                            </span>

                            <strong>
                                {
                                    yearlySummary.activeMonths
                                }
                                /12
                            </strong>

                            <small>
                                Months with data
                            </small>
                        </div>
                    </div>

                    <div className="analytics-card analytics-full-card">

                        <div className="analytics-card-header">
                            <div>
                                <h2>
                                    Monthly Financial
                                    Overview
                                </h2>

                                <p>
                                    Each month with
                                    recorded financial
                                    activity in{" "}
                                    {selectedYear}
                                </p>
                            </div>

                            <span className="analytics-month-count-badge">
                                {
                                    activeMonthCards.length
                                }{" "}
                                active month
                                {activeMonthCards.length ===
                                1
                                    ? ""
                                    : "s"}
                            </span>
                        </div>

                        {activeMonthCards.length ===
                        0 ? (
                            <div className="analytics-empty-chart">
                                No financial activity
                                recorded in{" "}
                                {selectedYear}.
                            </div>
                        ) : (
                            <div className="analytics-month-card-grid">
                                {activeMonthCards.map(
                                    (
                                        item
                                    ) => (
                                        <button
                                            type="button"
                                            className={`analytics-month-card ${MONTH_CLASSES[item.monthNumber - 1]}`}
                                            key={
                                                item.monthKey
                                            }
                                            onClick={() => {
                                                setSelectedMonth(
                                                    item.monthKey
                                                );

                                                setViewMode(
                                                    "monthly"
                                                );
                                            }}
                                        >
                                            <div className="analytics-month-card-top">
                                                <div>
                                                    <span>
                                                        {
                                                            item.monthName
                                                        }
                                                    </span>

                                                    <small>
                                                        {
                                                            selectedYear
                                                        }
                                                    </small>
                                                </div>

                                                <b>
                                                    {
                                                        item.monthNumber
                                                    }
                                                </b>
                                            </div>

                                            <div className="analytics-month-card-main">
                                                <span>
                                                    Total
                                                    Expense
                                                </span>

                                                <strong>
                                                    {formatCurrency(
                                                        item.expenses
                                                    )}
                                                </strong>
                                            </div>

                                            <div className="analytics-month-card-details">

                                                <div>
                                                    <span>
                                                        Income
                                                    </span>

                                                    <strong>
                                                        {formatCurrency(
                                                            item.income
                                                        )}
                                                    </strong>
                                                </div>

                                                <div>
                                                    <span>
                                                        Balance
                                                    </span>

                                                    <strong>
                                                        {formatCurrency(
                                                            item.balance
                                                        )}
                                                    </strong>
                                                </div>

                                                <div>
                                                    <span>
                                                        Savings
                                                    </span>

                                                    <strong>
                                                        {formatPercentage(
                                                            item.savingsRate
                                                        )}
                                                    </strong>
                                                </div>

                                                <div>
                                                    <span>
                                                        Goals
                                                    </span>

                                                    <strong>
                                                        {
                                                            item.goalCount
                                                        }
                                                    </strong>
                                                </div>
                                            </div>

                                            <div className="analytics-month-card-footer">
                                                <span>
                                                    {
                                                        item.totalTransactions
                                                    }{" "}
                                                    transactions
                                                </span>

                                                <span>
                                                    View
                                                    details
                                                    →
                                                </span>
                                            </div>
                                        </button>
                                    )
                                )}
                            </div>
                        )}
                    </div>

                    <div className="analytics-card analytics-full-card">

                        <div className="analytics-card-header">
                            <div>
                                <h2>
                                    {selectedYear} Income
                                    & Expense Trend
                                </h2>

                                <p>
                                    Month-by-month
                                    financial
                                    movement
                                </p>
                            </div>
                        </div>

                        <ResponsiveContainer
                            width="100%"
                            height={380}
                        >
                            <AreaChart
                                data={
                                    yearlyTrendData
                                }
                            >
                                <CartesianGrid
                                    strokeDasharray="3 3"
                                />

                                <XAxis
                                    dataKey="month"
                                />

                                <YAxis />

                                <Tooltip
                                    formatter={(
                                        value
                                    ) =>
                                        formatCurrency(
                                            value
                                        )
                                    }
                                />

                                <Legend />

                                <Area
                                    type="monotone"
                                    dataKey="income"
                                    name="Income"
                                    stroke="#00b894"
                                    fill="#00b894"
                                    fillOpacity={
                                        0.18
                                    }
                                />

                                <Area
                                    type="monotone"
                                    dataKey="expenses"
                                    name="Expenses"
                                    stroke="#e17055"
                                    fill="#e17055"
                                    fillOpacity={
                                        0.18
                                    }
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="analytics-chart-grid">

                        <div className="analytics-card">

                            <div className="analytics-card-header">
                                <div>
                                    <h2>
                                        Yearly
                                        Transactions
                                    </h2>

                                    <p>
                                        Activity during{" "}
                                        {selectedYear}
                                    </p>
                                </div>
                            </div>

                            <div className="analytics-year-transaction-grid">

                                <div>
                                    <span>
                                        Income
                                        Transactions
                                    </span>

                                    <strong>
                                        {
                                            yearlySummary.incomeTransactions
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Expense
                                        Transactions
                                    </span>

                                    <strong>
                                        {
                                            yearlySummary.expenseTransactions
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Total
                                        Transactions
                                    </span>

                                    <strong>
                                        {
                                            yearlySummary.totalTransactions
                                        }
                                    </strong>
                                </div>
                            </div>
                        </div>

                        <div className="analytics-card">

                            <div className="analytics-card-header">
                                <div>
                                    <h2>
                                        Yearly
                                        Performance
                                    </h2>

                                    <p>
                                        Overall financial
                                        position
                                    </p>
                                </div>
                            </div>

                            <div className="analytics-year-performance">
                                <div>
                                    <span>
                                        Income
                                    </span>

                                    <strong>
                                        {formatCurrency(
                                            yearlySummary.income
                                        )}
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Expenses
                                    </span>

                                    <strong>
                                        {formatCurrency(
                                            yearlySummary.expenses
                                        )}
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Balance
                                    </span>

                                    <strong>
                                        {formatCurrency(
                                            yearlySummary.balance
                                        )}
                                    </strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

export default Analytics;