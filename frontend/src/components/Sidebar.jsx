import React from "react";

function Sidebar({ activePage, setActivePage, onLogout }) {
    const menuItems = [
        { name: "Dashboard", icon: "🏠" },
        { name: "Transactions", icon: "💳" },
        { name: "Budgets", icon: "💰" },
        { name: "Savings Goals", icon: "🎯" },
        { name: "Analytics", icon: "📊" },
        { name: "Reports", icon: "📄" },
        { name: "Notifications", icon: "🔔" },
        { name: "Profile", icon: "👤" },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <div className="brand-icon">₿</div>

                <div>
                    <h2>BudgetBuddy</h2>
                    <span>Student Finance</span>
                </div>
            </div>

            <nav className="sidebar-nav">
                {menuItems.map((item) => (
                    <button
                        key={item.name}
                        className={`sidebar-item ${
                            activePage === item.name ? "active" : ""
                        }`}
                        onClick={() => setActivePage(item.name)}
                    >
                        <span className="sidebar-icon">
                            {item.icon}
                        </span>

                        <span>{item.name}</span>
                    </button>
                ))}
            </nav>

            <div className="sidebar-bottom">
                <button
                    className="sidebar-item logout-item"
                    onClick={onLogout}
                >
                    <span className="sidebar-icon">🚪</span>
                    <span>Logout</span>
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;