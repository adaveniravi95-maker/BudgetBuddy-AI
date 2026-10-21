

import React, { useEffect, useState } from "react";

import { api } from "../api";

import Sidebar from "./Sidebar";

import Transactions from "./Transactions";

import Budgets from "./Budgets";

import SavingsGoals from "./SavingsGoals";

import Analytics from "./Analytics";

import Reports from "./Reports";

import Notifications from "./Notifications";

import Profile from "./Profile";



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



// Use local date instead of UTC to avoid month/date shifting.

function getLocalDate() {

    const date = new Date();

    const year = date.getFullYear();

    const month = String(date.getMonth() + 1).padStart(2, "0");

    const day = String(date.getDate()).padStart(2, "0");



    return `${year}-${month}-${day}`;

}



function getLocalMonth() {

    return getLocalDate().slice(0, 7);

}



function Dashboard({ user, onLogout }) {

    const today = getLocalDate();



    const [activePage, setActivePage] = useState("Dashboard");



    const [dashboard, setDashboard] = useState(null);

    const [expenses, setExpenses] = useState([]);

    const [incomes, setIncomes] = useState([]);



    const [message, setMessage] = useState("");

    const [loading, setLoading] = useState(true);

    // Small notification bell in the top-right header.
    const [unreadNotifications, setUnreadNotifications] = useState(0);



    const [viewMode, setViewMode] = useState("monthly");

    const [month, setMonth] = useState(getLocalMonth());

    const [year, setYear] = useState(

        String(new Date().getFullYear())

    );



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



    async function loadDashboard() {

        const data = await api(`/dashboard/${month}`);

        setDashboard(data);

    }



    async function loadExpenses() {

        const data = await api("/expenses");

        setExpenses(data);

    }



    async function loadIncomes() {

        const data = await api("/incomes");

        setIncomes(data);

    }



    // ==========================================

    // Load only the unread count for the small header bell.
    async function loadUnreadNotifications() {
        try {
            const data = await api("/notifications/unread-count");
            setUnreadNotifications(Number(data?.unread_count || 0));
        } catch {
            // Keep the dashboard working if the notification request fails.
        }
    }

    // Refresh the bell count periodically without changing the Notifications page.
    useEffect(() => {
        loadUnreadNotifications();

        const interval = setInterval(loadUnreadNotifications, 30000);
        return () => clearInterval(interval);
    }, []);


    // FILTER EXPENSES AND INCOME

    // ==========================================



    const filteredExpenses = expenses.filter((item) => {

        const date = String(item.expense_date || "");



        if (viewMode === "monthly") {

            return date.slice(0, 7) === month;

        }



        return date.slice(0, 4) === year;

    });



    const filteredIncomes = incomes.filter((item) => {

        const date = String(item.income_date || "");



        if (viewMode === "monthly") {

            return date.slice(0, 7) === month;

        }



        return date.slice(0, 4) === year;

    });



    // ==========================================

    // CALCULATE TOTAL INCOME

    // ==========================================



    const totalIncome = filteredIncomes.reduce(

        (total, item) => total + Number(item.amount || 0),

        0

    );



    // ==========================================

    // CALCULATE TOTAL EXPENSES

    // ==========================================



    const totalExpenses = filteredExpenses.reduce(

        (total, item) => total + Number(item.amount || 0),

        0

    );



    // ==========================================

    // CALCULATE REMAINING BALANCE

    // ==========================================



    const remainingAmount = totalIncome - totalExpenses;



    // ==========================================

    // CALCULATE CATEGORY-WISE EXPENSES

    // ==========================================



    const categoryExpenses = categories.reduce(

        (result, category) => {

            result[category] = filteredExpenses

                .filter((item) => item.category === category)

                .reduce(

                    (total, item) =>

                        total + Number(item.amount || 0),

                    0

                );



            return result;

        },

        {}

    );



    // ==========================================

    // REFRESH DASHBOARD DATA

    // ==========================================



    async function refreshAll() {

        try {

            setLoading(true);



            await Promise.all([

                loadDashboard(),

                loadExpenses(),

                loadIncomes(),

            ]);

        } catch (error) {

            setMessage(error.message);

        } finally {

            setLoading(false);

        }

    }



    useEffect(() => {

        refreshAll();

    }, [month, year, viewMode]);



    // ==========================================

    // ADD EXPENSE

    // ==========================================



    async function addExpense(event) {

        event.preventDefault();

        setMessage("");



        try {

            await api("/expenses", {

                method: "POST",

                body: JSON.stringify({

                    ...expense,

                    amount: Number(expense.amount),

                }),

            });



            setExpense({

                amount: "",

                category: "Food",

                expense_date: getLocalDate(),

                description: "",

            });



            setMessage("Expense added successfully.");



            await refreshAll();

        } catch (error) {

            setMessage(error.message);

        }

    }



    // ==========================================

    // DELETE EXPENSE

    // ==========================================



    async function deleteExpense(id) {

        const confirmed = window.confirm(

            "Are you sure you want to delete this expense?"

        );



        if (!confirmed) return;



        setMessage("");



        try {

            await api(`/expenses/${id}`, {

                method: "DELETE",

            });



            setMessage("Expense deleted successfully.");



            await refreshAll();

        } catch (error) {

            setMessage(error.message);

        }

    }



    // ==========================================

    // ADD INCOME

    // ==========================================



    async function addIncome(event) {

        event.preventDefault();

        setMessage("");



        try {

            await api("/incomes", {

                method: "POST",

                body: JSON.stringify({

                    ...income,

                    amount: Number(income.amount),

                }),

            });



            setIncome({

                amount: "",

                source: "Pocket Money",

                income_date: getLocalDate(),

                details: "",

            });



            setMessage("Income added successfully.");



            await refreshAll();

        } catch (error) {

            setMessage(error.message);

        }

    }



    // ==========================================

    // DELETE INCOME

    // ==========================================



    async function deleteIncome(id) {

        const confirmed = window.confirm(

            "Are you sure you want to delete this income?"

        );



        if (!confirmed) return;



        setMessage("");



        try {

            await api(`/incomes/${id}`, {

                method: "DELETE",

            });



            setMessage("Income deleted successfully.");



            await refreshAll();

        } catch (error) {

            setMessage(error.message);

        }

    }



    // ==========================================

    // SHARED PERIOD SELECTOR PROPS

    // ==========================================



    const periodProps = {

        month,

        year,

        viewMode,

        setMonth,

        setYear,

        setViewMode,

    };



    // ==========================================

    // LOADING SCREEN

    // ==========================================



    if (loading && !dashboard) {

        return (

            <div className="app-layout">

                <Sidebar

                    activePage="Dashboard"

                    setActivePage={setActivePage}

                    onLogout={onLogout}

                />



                <main className="app">

                    <div className="loading-screen">

                        <div>

                            <h2>Loading BudgetBuddy...</h2>

                            <p>

                                Preparing your financial dashboard.

                            </p>

                        </div>

                    </div>

                </main>

            </div>

        );

    }



    return (

        <div className="app-layout">



            <Sidebar

                activePage={activePage}

                setActivePage={(page) => {

                    setMessage("");

                    setActivePage(page);

                }}

                onLogout={onLogout}

            />



            <main className="app">



                {/* TOP BAR */}



                <header className="topbar">

                    <div>

                        <h1>BudgetBuddy</h1>

                        <p>

                            Student Budget & Personal Finance

                        </p>

                    </div>



                    <div className="user-area">
                        <span>
                            {user.full_name} ({user.role})
                        </span>

                        <button
                            type="button"
                            aria-label={`Notifications${unreadNotifications > 0 ? ` (${unreadNotifications} unread)` : ""}`}
                            title={
                                unreadNotifications > 0
                                    ? `${unreadNotifications} unread notification${unreadNotifications === 1 ? "" : "s"}`
                                    : "Notifications"
                            }
                            onClick={() => {
                                setMessage("");
                                setActivePage("Notifications");
                            }}
                            style={{
                                position: "relative",
                                width: "40px",
                                height: "40px",
                                padding: 0,
                                margin: 0,
                                border: "1px solid #e5e7eb",
                                borderRadius: "12px",
                                background: "#ffffff",
                                color: "#4f46e5",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                cursor: "pointer",
                                fontSize: "20px",
                                lineHeight: 1,
                                boxShadow: "0 4px 12px rgba(79, 70, 229, 0.10)",
                            }}
                        >
                            <span aria-hidden="true">🔔</span>

                            {unreadNotifications > 0 && (
                                <span
                                    style={{
                                        position: "absolute",
                                        top: "-5px",
                                        right: "-5px",
                                        minWidth: "18px",
                                        height: "18px",
                                        padding: "0 4px",
                                        borderRadius: "999px",
                                        background: "#ef4444",
                                        color: "#ffffff",
                                        border: "2px solid #ffffff",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        fontSize: "10px",
                                        fontWeight: 800,
                                        lineHeight: 1,
                                    }}
                                >
                                    {unreadNotifications > 99 ? "99+" : unreadNotifications}
                                </span>
                            )}
                        </button>

                        <button onClick={onLogout}>
                            Logout
                        </button>
                    </div>

                </header>



                {/* SUCCESS / ERROR MESSAGE */}



                {message && (

                    <div className="message">

                        {message}

                    </div>

                )}



                {/* DASHBOARD PAGE */}



                {activePage === "Dashboard" && (

                    <>



                        <section className="dashboard-header">

                            <div>

                                <h2>Financial Dashboard</h2>



                                <p>

                                    {viewMode === "monthly"

                                        ? `Monthly Overview: ${month}`

                                        : `Yearly Overview: ${year}`}

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

                                    onChange={(event) =>

                                        setViewMode(event.target.value)

                                    }

                                >

                                    <option value="monthly">

                                        Monthly

                                    </option>



                                    <option value="yearly">

                                        Yearly

                                    </option>

                                </select>



                                {viewMode === "monthly" ? (

                                    <input

                                        type="month"

                                        value={month}

                                        max={getLocalMonth()}

                                        onChange={(event) =>

                                            setMonth(event.target.value)

                                        }

                                    />

                                ) : (

                                    <select

                                        value={year}

                                        onChange={(event) =>

                                            setYear(event.target.value)

                                        }

                                    >

                                        {Array.from(

                                            {

                                                length:

                                                    new Date().getFullYear() -

                                                    2020 + 1,

                                            },

                                            (_, index) =>

                                                String(2020 + index)

                                        )

                                            .reverse()

                                            .map((itemYear) => (

                                                <option

                                                    key={itemYear}

                                                    value={itemYear}

                                                >

                                                    {itemYear}

                                                </option>

                                            ))}

                                    </select>

                                )}



                                <button

                                    className="secondary-button"

                                    onClick={refreshAll}

                                >

                                    Refresh

                                </button>

                            </div>

                        </section>



                        {/* SUMMARY CARDS */}



                        <section className="summary-grid">

                            <div className="summary-card">

                                <span>Total Income</span>

                                <strong>

                                    ₹{totalIncome.toFixed(2)}

                                </strong>

                            </div>



                            <div className="summary-card">

                                <span>Total Expenses</span>

                                <strong>

                                    ₹{totalExpenses.toFixed(2)}

                                </strong>

                            </div>



                            <div className="summary-card">

                                <span>Remaining</span>

                                <strong>

                                    ₹{Math.abs(remainingAmount).toFixed(2)}

                                </strong>

                            </div>

                        </section>



                        {/* ADD EXPENSE + ADD INCOME */}



                        <section className="two">



                            <div className="card">

                                <h2>Add Expense</h2>

                                <p>Record your daily spending.</p>



                                <form onSubmit={addExpense}>

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

                                            <option

                                                key={category}

                                                value={category}

                                            >

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

                                        Add Expense

                                    </button>

                                </form>

                            </div>



                            <div className="card">

                                <h2>Add Income</h2>

                                <p>Record money received.</p>



                                <form onSubmit={addIncome}>

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

                                            <option

                                                key={source}

                                                value={source}

                                            >

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

                                        Add Income

                                    </button>

                                </form>

                            </div>

                        </section>



                        {/* SPENDING BY CATEGORY */}



                        <section className="card">

                            <div className="chart-title">

                                <div>

                                    <h2>Spending by Category</h2>

                                    <p>

                                        See where your money is going.

                                    </p>

                                </div>

                            </div>



                            {categories.map((category) => (

                                <div className="row" key={category}>

                                    <span>{category}</span>

                                    <strong>

                                        ₹{categoryExpenses[category].toFixed(2)}

                                    </strong>

                                </div>

                            ))}

                        </section>



                        {/* RECENT EXPENSES + INCOME */}



                        <section className="two">



                            <div className="card">

                                <h2>Recent Expenses</h2>



                                {filteredExpenses.length === 0 ? (

                                    <div className="empty-state">

                                        <div className="empty-state-icon">

                                            💳

                                        </div>

                                        <p>No expenses found.</p>

                                    </div>

                                ) : (

                                    filteredExpenses.slice(0, 5).map((item) => (

                                        <div

                                            className="row"

                                            key={item.id}

                                        >

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



                                            <div style={{ textAlign: "right" }}>

                                                <strong>₹{item.amount}</strong>

                                                <br />



                                                <button

                                                    type="button"

                                                    className="delete-button"

                                                    style={{ marginTop: "6px" }}

                                                    onClick={() =>

                                                        deleteExpense(item.id)

                                                    }

                                                >

                                                    Delete

                                                </button>

                                            </div>

                                        </div>

                                    ))

                                )}

                            </div>



                            <div className="card">

                                <h2>Recent Income</h2>



                                {filteredIncomes.length === 0 ? (

                                    <div className="empty-state">

                                        <div className="empty-state-icon">

                                            💰

                                        </div>

                                        <p>No income found.</p>

                                    </div>

                                ) : (

                                    filteredIncomes.slice(0, 5).map((item) => (

                                        <div

                                            className="row"

                                            key={item.id}

                                        >

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



                                            <div style={{ textAlign: "right" }}>

                                                <strong>₹{item.amount}</strong>

                                                <br />



                                                <button

                                                    type="button"

                                                    className="delete-button"

                                                    style={{ marginTop: "6px" }}

                                                    onClick={() =>

                                                        deleteIncome(item.id)

                                                    }

                                                >

                                                    Delete

                                                </button>

                                            </div>

                                        </div>

                                    ))

                                )}

                            </div>

                        </section>

                    </>

                )}



                {/* TRANSACTIONS PAGE */}



                {activePage === "Transactions" && (

                    <Transactions

                        {...periodProps}

                        expenses={expenses}

                        incomes={incomes}

                        expense={expense}

                        setExpense={setExpense}

                        income={income}

                        setIncome={setIncome}

                        categories={categories}

                        sources={sources}

                        addExpense={addExpense}

                        addIncome={addIncome}

                        deleteExpense={deleteExpense}

                        deleteIncome={deleteIncome}

                    />

                )}



                {/* BUDGETS PAGE */}



                {activePage === "Budgets" && (

                    <Budgets {...periodProps} />

                )}







                {/* SAVINGS GOALS PAGE */}



{activePage === "Savings Goals" && (

    <SavingsGoals {...periodProps} />

)}



                {/* ANALYTICS PAGE */}



                {activePage === "Analytics" && (

                    <Analytics {...periodProps} />

                )}



                {/* REPORTS PAGE */}



                {activePage === "Reports" && (

                    <Reports {...periodProps} />

                )}



                {/* NOTIFICATIONS PAGE */}



                {activePage === "Notifications" && (

                    <Notifications {...periodProps} />

                )}



                {/* PROFILE PAGE */}



                {activePage === "Profile" && (

                    <Profile />

                )}



            </main>

        </div>

    );

}



export default Dashboard;
