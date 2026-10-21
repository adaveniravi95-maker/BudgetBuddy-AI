
import React, { useRef, useState } from "react";
import { api } from "../api";

function Chatbot() {
    const [open, setOpen] = useState(false);
    const [message, setMessage] = useState("");
    const [thinking, setThinking] = useState(false);
    const lastTopicRef = useRef(null);

    const [messages, setMessages] = useState([
        {
            sender: "bot",
            text: "Hi! I'm BudgetBuddy Assistant. I can help you with your income, expenses, balance, budgets, savings goals, notifications, analytics and reports. What would you like to know?"
        }
    ]);

    const currentMonth = () => {
        const now = new Date();
        return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    };

    const money = (value) =>
        new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 0,
        }).format(Number(value || 0));

    const normalize = (value) =>
        value
            .toLowerCase()
            .replace(/[?!.,;:'"`]/g, " ")
            .replace(/\s+/g, " ")
            .trim();

    const arrayFrom = (data, keys = []) => {
        if (Array.isArray(data)) return data;

        for (const key of keys) {
            if (Array.isArray(data?.[key])) {
                return data[key];
            }
        }

        return [];
    };

    const numberFrom = (data, keys) => {
        for (const key of keys) {
            const value = data?.[key];

            if (value !== undefined && value !== null && value !== "") {
                const n = Number(value);

                if (Number.isFinite(n)) {
                    return n;
                }
            }
        }

        return 0;
    };

    const getAnalytics = async () => {
        const data = await api(`/analytics/${currentMonth()}`);

        const income = numberFrom(data, [
            "total_income",
            "income",
            "monthly_income",
            "income_total"
        ]);

        const expenses = numberFrom(data, [
            "total_expenses",
            "expenses",
            "monthly_expenses",
            "expense_total"
        ]);

        const balance = numberFrom(data, [
            "balance",
            "remaining_balance",
            "current_balance"
        ]);

        return {
            data,
            income,
            expenses,
            balance
        };
    };

    const notificationsAnswer = async () => {
        const data = await api("/notifications");

        const list = arrayFrom(data, [
            "notifications",
            "items",
            "data"
        ]);

        const unread = list.filter((item) => {
            if (item?.is_read !== undefined) {
                return !item.is_read;
            }

            if (item?.read !== undefined) {
                return !item.read;
            }

            if (item?.read_at !== undefined) {
                return !item.read_at;
            }

            return false;
        }).length;

        if (!list.length) {
            return "You currently have no notifications.";
        }

        return `You currently have ${list.length} notification${list.length === 1 ? "" : "s"}. ${unread} ${unread === 1 ? "is" : "are"} unread.`;
    };

    const unreadAnswer = async () => {
        try {
            const data = await api("/notifications/unread-count");

            const count = numberFrom(data, [
                "count",
                "unread_count",
                "unread",
                "total"
            ]);

            return `You currently have ${count} unread notification${count === 1 ? "" : "s"}.`;
        } catch {
            return notificationsAnswer();
        }
    };

    const expensesAnswer = async () => {
        const { expenses } = await getAnalytics();

        return `For ${currentMonth()}, your total expenses are ${money(expenses)}.`;
    };

    const incomeAnswer = async () => {
        const { income } = await getAnalytics();

        return `For ${currentMonth()}, your total income is ${money(income)}.`;
    };

    const balanceAnswer = async () => {
        const { data, income, expenses, balance } = await getAnalytics();

        const hasBackendBalance = [
            "balance",
            "remaining_balance",
            "current_balance"
        ].some((key) => data?.[key] !== undefined);

        const finalBalance = hasBackendBalance
            ? balance
            : income - expenses;

        return `For ${currentMonth()}, your balance is ${money(finalBalance)}.`;
    };

    const savingsAnswer = async () => {
        const data = await api("/savings-goals");

        const goals = arrayFrom(data, [
            "goals",
            "items",
            "data"
        ]);

        if (!goals.length) {
            return "You currently have no savings goals.";
        }

        const totalTarget = goals.reduce(
            (sum, g) =>
                sum +
                Number(
                    g.target_amount ??
                    g.target ??
                    g.goal_amount ??
                    0
                ),
            0
        );

        const totalSaved = goals.reduce(
            (sum, g) =>
                sum +
                Number(
                    g.amount_saved ??
                    g.saved_amount ??
                    g.saved ??
                    g.current_amount ??
                    0
                ),
            0
        );

        const lines = goals.slice(0, 6).map((g) => {
            const name =
                g.name ||
                g.title ||
                g.goal_name ||
                "Savings goal";

            const target = Number(
                g.target_amount ??
                g.target ??
                g.goal_amount ??
                0
            );

            const saved = Number(
                g.amount_saved ??
                g.saved_amount ??
                g.saved ??
                g.current_amount ??
                0
            );

            return `• ${name}: ${money(saved)} saved of ${money(target)}`;
        });

        return `You have ${goals.length} savings goal${goals.length === 1 ? "" : "s"}.\n\n${lines.join("\n")}\n\nTotal saved: ${money(totalSaved)} of ${money(totalTarget)}.`;
    };

    /*
     * Budget helpers
     *
     * The chatbot deliberately handles several possible field names because
     * the backend response can contain slightly different names depending
     * on the endpoint/model.
     */

    const getBudgetCategory = (budget) => {
        const category =
            budget?.category ??
            budget?.category_name ??
            budget?.categoryName ??
            budget?.name ??
            budget?.title ??
            budget?.category?.name;

        if (typeof category === "string" && category.trim()) {
            return category.trim();
        }

        if (typeof budget?.category === "object" && budget?.category?.name) {
            return String(budget.category.name).trim();
        }

        return "Category";
    };

    const getBudgetAmount = (budget) => {
        const possibleValues = [
            budget?.amount,
            budget?.budget_amount,
            budget?.allocated_amount,
            budget?.allocatedAmount,
            budget?.limit,
            budget?.amount_allocated,
            budget?.monthly_amount,
            budget?.value,
            budget?.total_amount
        ];

        for (const value of possibleValues) {
            if (
                value !== undefined &&
                value !== null &&
                value !== "" &&
                !Number.isNaN(Number(value))
            ) {
                return Number(value);
            }
        }

        return 0;
    };

    const getBudgetMonth = (budget) => {
        const possibleValues = [
            budget?.month,
            budget?.budget_month,
            budget?.budgetMonth,
            budget?.period,
            budget?.month_year,
            budget?.monthYear,
            budget?.year_month
        ];

        for (const value of possibleValues) {
            if (value !== undefined && value !== null && value !== "") {
                const text = String(value);

                const match = text.match(/(\d{4})-(\d{1,2})/);

                if (match) {
                    return `${match[1]}-${String(match[2]).padStart(2, "0")}`;
                }
            }
        }

        /*
         * Some APIs may return a date instead of a YYYY-MM month.
         */
        const dateValues = [
            budget?.created_at,
            budget?.createdAt,
            budget?.date,
            budget?.start_date,
            budget?.startDate
        ];

        for (const value of dateValues) {
            if (value) {
                const date = new Date(value);

                if (!Number.isNaN(date.getTime())) {
                    return `${date.getFullYear()}-${String(
                        date.getMonth() + 1
                    ).padStart(2, "0")}`;
                }
            }
        }

        return null;
    };

    const getBudgetData = async () => {
        const month = currentMonth();

        /*
         * First try the monthly endpoint/query. If the backend does not
         * support it, fall back to the existing /budgets endpoint.
         */
        let data;

        try {
            data = await api(`/budgets?month=${month}`);
        } catch {
            data = await api("/budgets");
        }

        let budgets = arrayFrom(data, [
            "budgets",
            "items",
            "data",
            "results"
        ]);

        /*
         * If the endpoint returned all months, filter them here.
         * This prevents old months from being counted.
         */
        const budgetsWithMonth = budgets.filter(
            (budget) => getBudgetMonth(budget) !== null
        );

        if (budgetsWithMonth.length > 0) {
            const currentBudgets = budgetsWithMonth.filter(
                (budget) => getBudgetMonth(budget) === month
            );

            /*
             * Only replace the original list if the API actually supplied
             * month information and matching records exist.
             */
            if (currentBudgets.length > 0) {
                budgets = currentBudgets;
            } else {
                budgets = [];
            }
        }

        return {
            month,
            budgets
        };
    };

    const budgetsAnswer = async () => {
        const { month, budgets } = await getBudgetData();

        if (!budgets.length) {
            return `You currently have no budgets for ${month}.`;
        }

        const lines = budgets.slice(0, 12).map((budget) => {
            const category = getBudgetCategory(budget);
            const amount = getBudgetAmount(budget);

            return `• ${category}: ${money(amount)}`;
        });

        const total = budgets.reduce(
            (sum, budget) => sum + getBudgetAmount(budget),
            0
        );

        return `You have ${budgets.length} budget${budgets.length === 1 ? "" : "s"} for ${month}.\n\n${lines.join("\n")}\n\nTotal budget: ${money(total)}.`;
    };

    const specificBudgetAnswer = async (question) => {
        const { month, budgets } = await getBudgetData();

        if (!budgets.length) {
            return `You currently have no budgets for ${month}.`;
        }

        const categories = [
            "food",
            "travel",
            "shopping",
            "education",
            "entertainment",
            "miscellaneous"
        ];

        const requestedCategory = categories.find((category) =>
            question.includes(category)
        );

        if (!requestedCategory) {
            return budgetsAnswer();
        }

        const matching = budgets.filter(
            (budget) =>
                getBudgetCategory(budget).toLowerCase() ===
                requestedCategory
        );

        if (!matching.length) {
            const formatted =
                requestedCategory.charAt(0).toUpperCase() +
                requestedCategory.slice(1);

            return `You do not currently have a ${formatted} budget for ${month}.`;
        }

        const total = matching.reduce(
            (sum, budget) => sum + getBudgetAmount(budget),
            0
        );

        const formatted =
            requestedCategory.charAt(0).toUpperCase() +
            requestedCategory.slice(1);

        return `Your ${formatted} budget for ${month} is ${money(total)}.`;
    };

    const answerQuestion = async (raw) => {
        const q = normalize(raw);

        if (!q) {
            return "Please type a question and I'll help you.";
        }

        /*
         * Follow-up questions use the previous topic.
         */
        if (
            /^(how many|how much|and how many|and how much)$/.test(q)
        ) {
            if (lastTopicRef.current === "notifications") {
                return notificationsAnswer();
            }

            if (lastTopicRef.current === "unread") {
                return unreadAnswer();
            }

            if (lastTopicRef.current === "expenses") {
                return expensesAnswer();
            }

            if (lastTopicRef.current === "income") {
                return incomeAnswer();
            }

            if (lastTopicRef.current === "balance") {
                return balanceAnswer();
            }

            if (lastTopicRef.current === "savings") {
                return savingsAnswer();
            }

            if (lastTopicRef.current === "budgets") {
                return budgetsAnswer();
            }

            return "What would you like me to count or calculate? For example, “How many notifications do I have?”";
        }

        /*
         * Notifications
         */
        if (q.includes("notification")) {
            lastTopicRef.current =
                q.includes("unread") || q.includes("not read")
                    ? "unread"
                    : "notifications";

            return lastTopicRef.current === "unread"
                ? unreadAnswer()
                : notificationsAnswer();
        }

        /*
         * Budget creation instructions
         */
        if (
            q.includes("how do i create a budget") ||
            q.includes("how to create a budget") ||
            q.includes("create a budget") ||
            q.includes("add a budget") ||
            q.includes("make a budget") ||
            q.includes("how can i create budget") ||
            q.includes("how can i add budget")
        ) {
            lastTopicRef.current = "budgets";

            return "To create a budget in BudgetBuddy:\n\n1. Open Budgets from the sidebar.\n2. Select the month.\n3. Choose a spending category such as Food, Travel, Shopping or Education.\n4. Enter the allocated amount.\n5. Click Create Budgets.\n\nYour budget will then appear in the Budget Overview so you can monitor your spending against the limit.";
        }

        /*
         * Budget definition
         */
        if (
            q === "what is a budget" ||
            q.includes("what are budgets") ||
            q.includes("what does budget mean")
        ) {
            lastTopicRef.current = "budgets";

            return "A budget is a spending limit you set for a category and month. For example, you can set ₹2,000 for Food in October and compare your actual spending with that limit.";
        }

        /*
         * Specific category budget
         */
        if (
            q.includes("food budget") ||
            q.includes("travel budget") ||
            q.includes("shopping budget") ||
            q.includes("education budget") ||
            q.includes("entertainment budget") ||
            q.includes("miscellaneous budget")
        ) {
            lastTopicRef.current = "budgets";
            return specificBudgetAnswer(q);
        }

        /*
         * General budget questions
         */
        if (
            q.includes("my budget") ||
            q.includes("how much budget") ||
            q.includes("budgets do i have") ||
            q.includes("how many budgets") ||
            q.includes("budget amount") ||
            q.includes("my budgets") ||
            q === "budgets"
        ) {
            lastTopicRef.current = "budgets";
            return budgetsAnswer();
        }

        /*
         * Expenses
         */
        if (
            q.includes("how much did i spend") ||
            q.includes("how much have i spent") ||
            q.includes("my expenses") ||
            q.includes("my expense") ||
            q.includes("total expense") ||
            q.includes("total expenses") ||
            q.includes("spending")
        ) {
            lastTopicRef.current = "expenses";
            return expensesAnswer();
        }

        /*
         * Income
         */
        if (
            q.includes("my income") ||
            q.includes("how much did i earn") ||
            q.includes("how much have i earned") ||
            q.includes("total income") ||
            q.includes("my earnings") ||
            q.includes("my earning")
        ) {
            lastTopicRef.current = "income";
            return incomeAnswer();
        }

        /*
         * Balance
         */
        if (
            q === "balance" ||
            q === "my balance" ||
            q.includes("what is my balance") ||
            q.includes("current balance") ||
            q.includes("remaining balance") ||
            q.includes("how much money do i have")
        ) {
            lastTopicRef.current = "balance";
            return balanceAnswer();
        }

        /*
         * Savings
         */
        if (
            q.includes("savings goal") ||
            q.includes("saving goal") ||
            q.includes("my savings") ||
            q.includes("how much have i saved") ||
            q.includes("what are my goals") ||
            q.includes("my goals")
        ) {
            lastTopicRef.current = "savings";
            return savingsAnswer();
        }

        /*
         * Analytics
         */
        if (
            q.includes("analytics") ||
            q.includes("spending analysis") ||
            q.includes("expense analysis")
        ) {
            lastTopicRef.current = "analytics";

            return "The Analytics section gives you a visual view of your finances, including income, expenses, balance, savings rate, category-wise spending and savings-goal information for the selected period.";
        }

        /*
         * Reports
         */
        if (
            q.includes("report") ||
            q.includes("financial report") ||
            q.includes("monthly report") ||
            q.includes("yearly report")
        ) {
            lastTopicRef.current = "reports";

            return "The Reports section lets you generate and review financial reports. Reports can show income, expenses, balance, savings rate and category-wise spending for the selected reporting period.";
        }

        /*
         * BudgetBuddy
         */
        if (
            q.includes("what is budgetbuddy") ||
            q.includes("what does budgetbuddy do") ||
            q.includes("about budgetbuddy")
        ) {
            lastTopicRef.current = "general";

            return "BudgetBuddy is a personal finance management application. You can track income and expenses, create budgets, manage savings goals, view analytics, generate reports and receive notifications.";
        }

        /*
         * Help
         */
        if (
            q.includes("what can you do") ||
            q.includes("what can you help") ||
            q === "help" ||
            q.includes("help me")
        ) {
            lastTopicRef.current = "general";

            return "I can help with your BudgetBuddy data and features. Try asking:\n\n• How much did I spend this month?\n• What is my balance?\n• How many notifications do I have?\n• How many notifications are unread?\n• What are my savings goals?\n• How many budgets do I have?\n• What is my Food budget?\n• How do I create a budget?\n• What does Analytics show?\n• What are Reports?";
        }

        /*
         * Greetings
         */
        if (
            [
                "hi",
                "hello",
                "hey",
                "good morning",
                "good afternoon",
                "good evening"
            ].includes(q)
        ) {
            lastTopicRef.current = "general";

            return "Hello! I'm here to help you with BudgetBuddy. You can ask me about your income, expenses, balance, budgets, savings goals, notifications, analytics or reports.";
        }

        return "I understand that you're asking about BudgetBuddy, but I don't have a specific answer for that question yet. Try asking about your income, expenses, balance, budgets, savings goals, notifications, analytics or reports.";
    };

    const sendMessage = async (event) => {
        event.preventDefault();

        const trimmed = message.trim();

        if (!trimmed || thinking) {
            return;
        }

        setMessages((previous) => [
            ...previous,
            {
                sender: "user",
                text: trimmed
            }
        ]);

        setMessage("");
        setThinking(true);

        try {
            const answer = await answerQuestion(trimmed);

            setMessages((previous) => [
                ...previous,
                {
                    sender: "bot",
                    text: answer
                }
            ]);
        } catch (err) {
            setMessages((previous) => [
                ...previous,
                {
                    sender: "bot",
                    text: `I couldn't load that BudgetBuddy information right now. Please try again.${err?.message ? ` (${err.message})` : ""}`
                }
            ]);
        } finally {
            setThinking(false);
        }
    };

    return (
        <div className="budgetbuddy-chatbot">
            {open && (
                <div className="chatbot-window">
                    <div className="chatbot-header">
                        <div>
                            <strong>BudgetBuddy Assistant</strong>
                            <span>Personal Finance Assistant</span>
                        </div>

                        <button
                            type="button"
                            className="chatbot-close"
                            onClick={() => setOpen(false)}
                            aria-label="Close chatbot"
                        >
                            ×
                        </button>
                    </div>

                    <div className="chatbot-messages">
                        {messages.map((item, index) => (
                            <div
                                key={index}
                                className={
                                    item.sender === "user"
                                        ? "chatbot-message user-message"
                                        : "chatbot-message bot-message"
                                }
                            >
                                {item.text.split("\n").map(
                                    (line, lineIndex, lines) => (
                                        <React.Fragment key={lineIndex}>
                                            {line}

                                            {lineIndex <
                                                lines.length - 1 && <br />}
                                        </React.Fragment>
                                    )
                                )}
                            </div>
                        ))}

                        {thinking && (
                            <div className="chatbot-message bot-message">
                                Checking your BudgetBuddy data...
                            </div>
                        )}
                    </div>

                    <form
                        className="chatbot-input-area"
                        onSubmit={sendMessage}
                    >
                        <input
                            type="text"
                            placeholder="Ask BudgetBuddy..."
                            value={message}
                            onChange={(event) =>
                                setMessage(event.target.value)
                            }
                            disabled={thinking}
                            autoComplete="off"
                        />

                        <button
                            type="submit"
                            disabled={thinking || !message.trim()}
                        >
                            {thinking ? "..." : "Send"}
                        </button>
                    </form>
                </div>
            )}

            {!open && (
                <button
                    type="button"
                    className="chatbot-floating-button"
                    onClick={() => setOpen(true)}
                    aria-label="Open BudgetBuddy Assistant"
                >
                    <span className="chatbot-icon">🤖</span>
                    <span>Chat</span>
                </button>
            )}
        </div>
    );
}

export default Chatbot;
