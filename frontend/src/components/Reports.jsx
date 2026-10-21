import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import "./Reports.css";

function Reports() {
    const [reports, setReports] = useState([]);
    const [selectedReport, setSelectedReport] = useState(null);

    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [updating, setUpdating] = useState(false);

    const [error, setError] = useState("");
    const [message, setMessage] = useState("");

    const [period, setPeriod] = useState(() => {
        const now = new Date();

        return `${now.getFullYear()}-${String(
            now.getMonth() + 1
        ).padStart(2, "0")}`;
    });

    const [editPeriod, setEditPeriod] = useState("");

    const [reportMode, setReportMode] = useState("monthly");
    const [selectedYear, setSelectedYear] = useState(() => new Date().getFullYear().toString());

    const formatPeriod = (value) => {
        if (!value) {
            return "";
        }

        const [year, month] = value.split("-");

        const date = new Date(
            Number(year),
            Number(month) - 1,
            1
        );

        return date.toLocaleDateString("en-IN", {
            month: "long",
            year: "numeric",
        });
    };

    const formatReportPeriod = (value, reportType = "") => {
        if (reportType === "Yearly Financial Report" || /^\d{4}$/.test(String(value || ""))) {
            return String(value || "");
        }
        return formatPeriod(value);
    };

    const formatDateTime = (value) => {
        if (!value) {
            return "Not available";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return date.toLocaleString("en-IN", {
            dateStyle: "medium",
            timeStyle: "short",
        });
    };


    const formatCurrency = (value) => {
        const number = Number(value);

        if (Number.isNaN(number)) {
            return "₹0.00";
        }

        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(number);
    };

    const parseSummary = (value) => {
        if (!value) {
            return null;
        }

        if (typeof value === "object") {
            return value;
        }

        try {
            return JSON.parse(value);
        } catch {
            return null;
        }
    };

    const loadReports = async (showRefresh = false) => {
        try {
            if (showRefresh) {
                setRefreshing(true);
            } else {
                setLoading(true);
            }

            setError("");

            const data = await api("/reports");

            setReports(
                Array.isArray(data)
                    ? data
                    : []
            );

            if (selectedReport) {
                const updatedSelected = data.find(
                    (report) =>
                        report.id === selectedReport.id
                );

                setSelectedReport(
                    updatedSelected || null
                );
            }
        } catch (err) {
            setError(
                err.message ||
                "Unable to load reports."
            );
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadReports();
    }, []);

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

    const generateReport = async () => {
        try {
            setGenerating(true);
            setError("");
            setMessage("");

            const endpoint = reportMode === "yearly"
                ? `/reports/generate-year/${selectedYear}`
                : `/reports/generate/${period}`;

            const data = await api(endpoint, { method: "POST" });

            await loadReports();
            setSelectedReport(data);
            setEditPeriod(data.period);

            setMessage(
                reportMode === "yearly"
                    ? `Yearly report generated for ${selectedYear}.`
                    : `Monthly report generated for ${formatPeriod(period)}.`
            );
        } catch (err) {
            setError(err.message || "Unable to generate report.");
        } finally {
            setGenerating(false);
        }
    };

    const downloadReportFile = async (reportPeriod, format, reportType = "") => {
        if (!reportPeriod) {
            setError("Please select a report period.");
            return;
        }

        try {
            setError("");
            setMessage("");

            const token = localStorage.getItem("token");
            const isYearly = reportType === "Yearly Financial Report" || /^\d{4}$/.test(String(reportPeriod));
            const extension = format === "pdf" ? "pdf" : "xlsx";
            const endpoint = isYearly
                ? (format === "pdf" ? `/reports/yearly/pdf/${reportPeriod}` : `/reports/yearly/excel/${reportPeriod}`)
                : (format === "pdf" ? `/reports/pdf/${reportPeriod}` : `/reports/excel/${reportPeriod}`);

            const response = await fetch(
                `http://127.0.0.1:8000/api${endpoint}`,
                {
                    method: "GET",
                    headers: token ? { Authorization: `Bearer ${token}` } : {},
                }
            );

            if (!response.ok) {
                let message = "Unable to download report.";
                try {
                    const data = await response.json();
                    if (typeof data?.detail === "string") message = data.detail;
                } catch {}
                throw new Error(message);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = isYearly
                ? `BudgetBuddy_Yearly_Report_${reportPeriod}.${extension}`
                : `BudgetBuddy_Report_${reportPeriod}.${extension}`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);

            setMessage(`${format.toUpperCase()} report downloaded successfully.`);
        } catch (err) {
            setError(err.message || "Unable to download report.");
        }
    };

    const openReport = async (reportId) => {
        try {
            setError("");

            const data = await api(
                `/reports/${reportId}`
            );

            setSelectedReport(data);
            setEditPeriod(data.period);
        } catch (err) {
            setError(
                err.message ||
                "Unable to open report."
            );
        }
    };

    const updateReport = async () => {
        if (!selectedReport) return;

        try {
            setUpdating(true);
            setError("");
            setMessage("");

            const isYearly = selectedReport.report_type === "Yearly Financial Report";
            const endpoint = isYearly
                ? `/reports/generate-year/${selectedReport.period}`
                : `/reports/generate/${editPeriod || selectedReport.period}`;

            const updated = await api(endpoint, { method: "POST" });
            await loadReports();
            setSelectedReport(updated);
            setEditPeriod(updated.period);
            setMessage("Report refreshed with the latest saved data.");
        } catch (err) {
            setError(err.message || "Unable to refresh report.");
        } finally {
            setUpdating(false);
        }
    };

    const deleteReport = async (report) => {
        const confirmed = window.confirm(
            `Delete the ${formatPeriod(
                report.period
            )} report?\n\nThis action cannot be undone.`
        );

        if (!confirmed) {
            return;
        }

        try {
            setDeleting(true);
            setError("");
            setMessage("");

            await api(
                `/reports/${report.id}`,
                {
                    method: "DELETE",
                }
            );

            if (
                selectedReport &&
                selectedReport.id === report.id
            ) {
                setSelectedReport(null);
                setEditPeriod("");
            }

            await loadReports();

            setMessage(
                "Report deleted successfully."
            );
        } catch (err) {
            setError(
                err.message ||
                "Unable to delete report."
            );
        } finally {
            setDeleting(false);
        }
    };

    const visibleReports = useMemo(() => {
        return reports.filter((report) => {
            if (reportMode === "yearly") {
                return report.report_type === "Yearly Financial Report" && String(report.period) === String(selectedYear);
            }
            return report.report_type === "Monthly Financial Report";
        });
    }, [reports, reportMode, selectedYear]);

    useEffect(() => {
        if (reportMode === "monthly") {
            const matching = reports.find((report) =>
                report.report_type === "Monthly Financial Report" && report.period === period
            );
            setSelectedReport(matching || null);
            setEditPeriod(matching?.period || period);
        } else {
            const matching = reports.find((report) =>
                report.report_type === "Yearly Financial Report" && String(report.period) === String(selectedYear)
            );
            setSelectedReport(matching || null);
            setEditPeriod(matching?.period || String(selectedYear));
        }
    }, [reportMode, period, selectedYear, reports]);

    const summaryStats = useMemo(() => {
        return {
            totalReports: visibleReports.length,

            latestPeriod:
                visibleReports.length > 0
                    ? visibleReports[0].period
                    : null,

            reportTypes: new Set(
                visibleReports.map(
                    (report) =>
                        report.report_type
                )
            ).size,
        };
    }, [visibleReports]);

    return (
        <div className="reports-page">

            {message && (
                <div className="report-toast report-toast-success">
                    <span>✓</span>
                    <span>{message}</span>
                </div>
            )}

            {error && (
                <div className="report-toast report-toast-error">
                    <span>!</span>
                    <span>{error}</span>
                </div>
            )}

            <div className="reports-hero">

                <div className="reports-hero-content">

                    <div className="reports-hero-icon">
                        📊
                    </div>

                    <div>
                        <span className="reports-eyebrow">
                            FINANCIAL MANAGEMENT
                        </span>

                        <h1>
                            Reports
                        </h1>

                        <p>
                            Generate, review and manage
                            your monthly financial reports.
                        </p>
                    </div>

                </div>

                <button
                    type="button"
                    className="reports-refresh-button"
                    onClick={() => loadReports(true)}
                    disabled={refreshing}
                >
                    <span
                        className={
                            refreshing
                                ? "refresh-spinning"
                                : ""
                        }
                    >
                        ↻
                    </span>

                    {refreshing
                        ? "Refreshing..."
                        : "Refresh"}
                </button>

            </div>

            <div className="reports-mode-switch">
                <button type="button" className={reportMode === "monthly" ? "active" : ""} onClick={() => setReportMode("monthly")}>Monthly</button>
                <button type="button" className={reportMode === "yearly" ? "active" : ""} onClick={() => setReportMode("yearly")}>Yearly</button>
            </div>

            <div className="reports-generate-card">

                <div className="reports-generate-icon">
                    ✨
                </div>

                <div className="reports-generate-content">

                    <h2>
                        {reportMode === "yearly" ? "Generate Yearly Report" : "Generate Monthly Report"}
                    </h2>

                    <p>
                        {reportMode === "yearly"
                            ? "Generate an overall yearly report from your saved monthly reports."
                            : "Select a month to create or refresh its financial report."}
                    </p>

                </div>

                <div className="report-generate-controls">

                    {reportMode === "yearly" ? (
                        <input
                            type="number"
                            min="2000"
                            max="2100"
                            value={selectedYear}
                            onChange={(event) => setSelectedYear(event.target.value)}
                        />
                    ) : (
                        <input
                            type="month"
                            value={period}
                            onChange={(event) => setPeriod(event.target.value)}
                        />
                    )}

                    <button
                        type="button"
                        className="report-generate-button"
                        onClick={generateReport}
                        disabled={generating}
                    >
                        {generating
                            ? "Generating..."
                            : "Generate Report"}
                    </button>

                </div>

            </div>

            <div className="reports-summary-grid">

                <div className="reports-summary-card reports-summary-blue">
                    <div>
                        <span>Total Reports</span>

                        <strong>
                            {summaryStats.totalReports}
                        </strong>

                        <small>
                            Generated reports
                        </small>
                    </div>

                    <div className="reports-summary-icon">
                        📄
                    </div>
                </div>

                <div className="reports-summary-card reports-summary-green">
                    <div>
                        <span>Latest Report</span>

                        <strong>
                            {summaryStats.latestPeriod
                                ? formatReportPeriod(
                                      summaryStats.latestPeriod,
                                      visibleReports[0]?.report_type || ""
                                  )
                                : "No reports"}
                        </strong>

                        <small>
                            Most recent period
                        </small>
                    </div>

                    <div className="reports-summary-icon">
                        📅
                    </div>
                </div>

                <div className="reports-summary-card reports-summary-purple">
                    <div>
                        <span>Report Types</span>

                        <strong>
                            {summaryStats.reportTypes}
                        </strong>

                        <small>
                            Available report types
                        </small>
                    </div>

                    <div className="reports-summary-icon">
                        📊
                    </div>
                </div>

            </div>

            <div className="reports-main-grid">

                <section className="reports-card">

                    <div className="reports-card-header">

                        <div>
                            <h2>
                                Financial Reports
                            </h2>

                            <p>
                                Your generated {reportMode === "yearly" ? "yearly" : "monthly"}
                                reports
                            </p>
                        </div>

                        <span className="reports-count-badge">
                            {visibleReports.length}
                        </span>

                    </div>

                    {loading ? (
                        <div className="reports-loading">
                            <div className="reports-spinner">
                                ↻
                            </div>

                            <span>
                                Loading reports...
                            </span>
                        </div>
                    ) : visibleReports.length === 0 ? (
                        <div className="reports-empty">

                            <div className="reports-empty-icon">
                                📄
                            </div>

                            <h3>
                                No reports yet
                            </h3>

                            <p>
                                Select a month above and
                                generate your first
                                financial report.
                            </p>

                        </div>
                    ) : (
                        <div className="reports-list">

                            {visibleReports.map((report) => (
                                <div
                                    className={`report-list-item ${
                                        selectedReport?.id ===
                                        report.id
                                            ? "selected"
                                            : ""
                                    }`}
                                    key={report.id}
                                >

                                    <div className="report-item-icon">
                                        📄
                                    </div>

                                    <div className="report-item-info">

                                        <div className="report-item-title">
                                            <h3>
                                                {
                                                    report.report_type
                                                }
                                            </h3>

                                            <span>
                                                {formatReportPeriod(report.period, report.report_type)}
                                            </span>
                                        </div>

                                        <small>
                                            Generated{" "}
                                            {formatDateTime(
                                                report.generated_at
                                            )}
                                        </small>

                                    </div>

                                    <div className="report-item-actions">

                                        <button
                                            type="button"
                                            className="report-view-button"
                                            onClick={() =>
                                                openReport(
                                                    report.id
                                                )
                                            }
                                        >
                                            View
                                        </button>

                                        <button
                                            type="button"
                                            className="report-delete-button"
                                            onClick={() =>
                                                deleteReport(
                                                    report
                                                )
                                            }
                                            disabled={deleting}
                                        >
                                            🗑
                                        </button>

                                    </div>

                                </div>
                            ))}

                        </div>
                    )}

                </section>

                <section className="reports-card report-details-card">

                    <div className="reports-card-header">

                        <div>
                            <h2>
                                Report Details
                            </h2>

                            <p>
                                View and update the selected
                                report
                            </p>
                        </div>

                    </div>

                    {!selectedReport ? (
                        <div className="reports-details-empty">

                            <div className="reports-empty-icon">
                                📊
                            </div>

                            <h3>
                                No report selected
                            </h3>

                            <p>
                                Select a report from the list
                                to view its details.
                            </p>

                        </div>
                    ) : (
                        <div className="report-details">

                            <div className="report-detail-title">

                                <div>
                                    <span>
                                        REPORT TYPE
                                    </span>

                                    <h3>
                                        {
                                            selectedReport.report_type
                                        }
                                    </h3>
                                </div>

                                <span className="report-period-badge">
                                    {formatReportPeriod(selectedReport.period, selectedReport.report_type)}
                                </span>

                            </div>

                            <div className="report-detail-grid">

                                <div className="report-detail-box">
                                    <span>
                                        Report ID
                                    </span>

                                    <strong>
                                        #
                                        {
                                            selectedReport.id
                                        }
                                    </strong>
                                </div>

                                <div className="report-detail-box">
                                    <span>
                                        Period
                                    </span>

                                    <input
                                        type={selectedReport.report_type === "Yearly Financial Report" ? "number" : "month"}
                                        min={selectedReport.report_type === "Yearly Financial Report" ? "2000" : undefined}
                                        max={selectedReport.report_type === "Yearly Financial Report" ? "2100" : undefined}
                                        value={editPeriod}
                                        onChange={(event) =>
                                            setEditPeriod(event.target.value)
                                        }
                                    />
                                </div>

                                <div className="report-detail-box">
                                    <span>
                                        Generated
                                    </span>

                                    <strong>
                                        {formatDateTime(
                                            selectedReport.generated_at
                                        )}
                                    </strong>
                                </div>

                                <div className="report-detail-box">
                                    <span>
                                        User ID
                                    </span>

                                    <strong>
                                        {
                                            selectedReport.user_id
                                        }
                                    </strong>
                                </div>

                            </div>

                            <div
                                className="report-summary-section"
                                style={{
                                    marginTop: "24px",
                                }}
                            >
                                {(() => {
                                    const summary = parseSummary(
                                        selectedReport.summary
                                    );

                                    if (!summary) {
                                        return (
                                            <div
                                                style={{
                                                    padding: "20px",
                                                    borderRadius: "12px",
                                                    background: "#f8f8fb",
                                                    color: "#555",
                                                    lineHeight: 1.6,
                                                    whiteSpace: "pre-wrap",
                                                    overflowWrap: "anywhere",
                                                }}
                                            >
                                                {selectedReport.summary}
                                            </div>
                                        );
                                    }

                                    const financial =
                                        summary.financial_summary || {};
                                    const transactions =
                                        summary.transaction_summary || {};
                                    const categories =
                                        summary.category_expenses || {};
                                    const budget =
                                        summary.budget_summary || {};
                                    const savings =
                                        summary.savings_summary || {};
                                    const goals = Array.isArray(
                                        savings.goals
                                    )
                                        ? savings.goals
                                        : [];

                                    const sectionTitleStyle = {
                                        margin: 0,
                                        fontSize: "17px",
                                        fontWeight: 700,
                                        color: "#27272a",
                                    };

                                    const sectionDescriptionStyle = {
                                        margin: "4px 0 0",
                                        fontSize: "13px",
                                        color: "#71717a",
                                    };

                                    const tableStyle = {
                                        width: "100%",
                                        borderCollapse: "collapse",
                                        marginTop: "14px",
                                        fontSize: "13px",
                                    };

                                    const headerCellStyle = {
                                        padding: "11px 12px",
                                        background: "#6c5ce7",
                                        color: "#ffffff",
                                        fontWeight: 700,
                                        textAlign: "left",
                                        border: "1px solid #e5e7eb",
                                    };

                                    const bodyCellStyle = {
                                        padding: "11px 12px",
                                        border: "1px solid #e5e7eb",
                                        color: "#3f3f46",
                                        background: "#ffffff",
                                    };

                                    const rightBodyCellStyle = {
                                        ...bodyCellStyle,
                                        textAlign: "right",
                                        fontWeight: 600,
                                    };

                                    const metricCardStyle = {
                                        padding: "16px",
                                        border: "1px solid #e5e7eb",
                                        borderRadius: "12px",
                                        background: "#fafafa",
                                    };

                                    const metricLabelStyle = {
                                        display: "block",
                                        fontSize: "12px",
                                        color: "#71717a",
                                        marginBottom: "7px",
                                    };

                                    const metricValueStyle = {
                                        display: "block",
                                        fontSize: "18px",
                                        fontWeight: 700,
                                        whiteSpace: "nowrap",
                                        color: "#27272a",
                                    };

                                    return (
                                        <div
                                            style={{
                                                display: "flex",
                                                flexDirection: "column",
                                                gap: "26px",
                                            }}
                                        >
                                            <div>
                                                <h3
                                                    style={
                                                        sectionTitleStyle
                                                    }
                                                >
                                                    Financial Summary
                                                </h3>
                                                <p
                                                    style={
                                                        sectionDescriptionStyle
                                                    }
                                                >
                                                    Generated from your
                                                    actual transactions
                                                </p>

                                                <div
                                                    style={{
                                                        display: "grid",
                                                        gridTemplateColumns:
                                                            "repeat(auto-fit, minmax(220px, 1fr))",
                                                        gap: "12px",
                                                        marginTop: "14px",
                                                    }}
                                                >
                                                    {[
                                                        [
                                                            "Total Income",
                                                            formatCurrency(
                                                                financial.total_income
                                                            ),
                                                        ],
                                                        [
                                                            "Total Expenses",
                                                            formatCurrency(
                                                                financial.total_expenses
                                                            ),
                                                        ],
                                                        [
                                                            "Remaining Balance",
                                                            formatCurrency(
                                                                financial.balance
                                                            ),
                                                        ],
                                                        [
                                                            "Savings Rate",
                                                            `${Number(
                                                                financial.savings_rate ||
                                                                    0
                                                            ).toFixed(2)}%`,
                                                        ],
                                                    ].map(
                                                        ([label, value]) => (
                                                            <div
                                                                key={label}
                                                                style={
                                                                    metricCardStyle
                                                                }
                                                            >
                                                                <span
                                                                    style={
                                                                        metricLabelStyle
                                                                    }
                                                                >
                                                                    {label}
                                                                </span>
                                                                <strong
                                                                    style={
                                                                        metricValueStyle
                                                                    }
                                                                >
                                                                    {value}
                                                                </strong>
                                                            </div>
                                                        )
                                                    )}
                                                </div>
                                            </div>

                                            <div>
                                                <h3
                                                    style={
                                                        sectionTitleStyle
                                                    }
                                                >
                                                    Transaction Summary
                                                </h3>

                                                <table
                                                    style={tableStyle}
                                                >
                                                    <thead>
                                                        <tr>
                                                            <th
                                                                style={
                                                                    headerCellStyle
                                                                }
                                                            >
                                                                Metric
                                                            </th>
                                                            <th
                                                                style={{
                                                                    ...headerCellStyle,
                                                                    textAlign:
                                                                        "right",
                                                                }}
                                                            >
                                                                Count
                                                            </th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {[
                                                            [
                                                                "Income Transactions",
                                                                transactions.income_transactions ||
                                                                    0,
                                                            ],
                                                            [
                                                                "Expense Transactions",
                                                                transactions.expense_transactions ||
                                                                    0,
                                                            ],
                                                            [
                                                                "Total Transactions",
                                                                transactions.total_transactions ||
                                                                    0,
                                                            ],
                                                        ].map(
                                                            ([
                                                                label,
                                                                value,
                                                            ]) => (
                                                                <tr
                                                                    key={
                                                                        label
                                                                    }
                                                                >
                                                                    <td
                                                                        style={
                                                                            bodyCellStyle
                                                                        }
                                                                    >
                                                                        {
                                                                            label
                                                                        }
                                                                    </td>
                                                                    <td
                                                                        style={
                                                                            rightBodyCellStyle
                                                                        }
                                                                    >
                                                                        {
                                                                            value
                                                                        }
                                                                    </td>
                                                                </tr>
                                                            )
                                                        )}
                                                    </tbody>
                                                </table>
                                            </div>

                                            <div>
                                                <h3
                                                    style={
                                                        sectionTitleStyle
                                                    }
                                                >
                                                    Category-wise Expenses
                                                </h3>

                                                <table
                                                    style={tableStyle}
                                                >
                                                    <thead>
                                                        <tr>
                                                            <th
                                                                style={
                                                                    headerCellStyle
                                                                }
                                                            >
                                                                Category
                                                            </th>
                                                            <th
                                                                style={{
                                                                    ...headerCellStyle,
                                                                    textAlign:
                                                                        "right",
                                                                }}
                                                            >
                                                                Amount
                                                            </th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {Object.keys(
                                                            categories
                                                        ).length === 0 ? (
                                                            <tr>
                                                                <td
                                                                    style={
                                                                        bodyCellStyle
                                                                    }
                                                                    colSpan="2"
                                                                >
                                                                    No expenses
                                                                    recorded for
                                                                    this month.
                                                                </td>
                                                            </tr>
                                                        ) : (
                                                            Object.entries(
                                                                categories
                                                            ).map(
                                                                ([
                                                                    category,
                                                                    amount,
                                                                ]) => (
                                                                    <tr
                                                                        key={
                                                                            category
                                                                        }
                                                                    >
                                                                        <td
                                                                            style={
                                                                                bodyCellStyle
                                                                            }
                                                                        >
                                                                            {
                                                                                category
                                                                            }
                                                                        </td>
                                                                        <td
                                                                            style={
                                                                                rightBodyCellStyle
                                                                            }
                                                                        >
                                                                            {formatCurrency(
                                                                                amount
                                                                            )}
                                                                        </td>
                                                                    </tr>
                                                                )
                                                            )
                                                        )}
                                                    </tbody>
                                                </table>
                                            </div>

                                            <div>
                                                <h3
                                                    style={
                                                        sectionTitleStyle
                                                    }
                                                >
                                                    Budget Summary
                                                </h3>

                                                <div
                                                    style={{
                                                        display: "grid",
                                                        gridTemplateColumns:
                                                            "repeat(auto-fit, minmax(220px, 1fr))",
                                                        gap: "12px",
                                                        marginTop: "14px",
                                                    }}
                                                >
                                                    {[
                                                        [
                                                            "Total Allocated",
                                                            formatCurrency(
                                                                budget.total_allocated
                                                            ),
                                                        ],
                                                        [
                                                            "Total Spent",
                                                            formatCurrency(
                                                                budget.total_spent
                                                            ),
                                                        ],
                                                    ].map(
                                                        ([label, value]) => (
                                                            <div
                                                                key={label}
                                                                style={
                                                                    metricCardStyle
                                                                }
                                                            >
                                                                <span
                                                                    style={
                                                                        metricLabelStyle
                                                                    }
                                                                >
                                                                    {label}
                                                                </span>
                                                                <strong
                                                                    style={
                                                                        metricValueStyle
                                                                    }
                                                                >
                                                                    {value}
                                                                </strong>
                                                            </div>
                                                        )
                                                    )}
                                                </div>

                                                <table
                                                    style={tableStyle}
                                                >
                                                    <thead>
                                                        <tr>
                                                            {[
                                                                "Category",
                                                                "Budget",
                                                                "Spent",
                                                                "Utilization",
                                                            ].map(
                                                                (
                                                                    heading,
                                                                    index
                                                                ) => (
                                                                    <th
                                                                        key={
                                                                            heading
                                                                        }
                                                                        style={{
                                                                            ...headerCellStyle,
                                                                            textAlign:
                                                                                index ===
                                                                                0
                                                                                    ? "left"
                                                                                    : "right",
                                                                        }}
                                                                    >
                                                                        {
                                                                            heading
                                                                        }
                                                                    </th>
                                                                )
                                                            )}
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {(
                                                            budget.categories ||
                                                            []
                                                        ).length === 0 ? (
                                                            <tr>
                                                                <td
                                                                    style={
                                                                        bodyCellStyle
                                                                    }
                                                                    colSpan="4"
                                                                >
                                                                    No budgets
                                                                    recorded for
                                                                    this month.
                                                                </td>
                                                            </tr>
                                                        ) : (
                                                            budget.categories.map(
                                                                (item) => (
                                                                    <tr
                                                                        key={
                                                                            item.category
                                                                        }
                                                                    >
                                                                        <td
                                                                            style={
                                                                                bodyCellStyle
                                                                            }
                                                                        >
                                                                            {
                                                                                item.category
                                                                            }
                                                                        </td>
                                                                        <td
                                                                            style={
                                                                                rightBodyCellStyle
                                                                            }
                                                                        >
                                                                            {formatCurrency(
                                                                                item.allocated
                                                                            )}
                                                                        </td>
                                                                        <td
                                                                            style={
                                                                                rightBodyCellStyle
                                                                            }
                                                                        >
                                                                            {formatCurrency(
                                                                                item.spent
                                                                            )}
                                                                        </td>
                                                                        <td
                                                                            style={
                                                                                rightBodyCellStyle
                                                                            }
                                                                        >
                                                                            {Number(
                                                                                item.utilization_percentage ||
                                                                                    0
                                                                            ).toFixed(
                                                                                2
                                                                            )}
                                                                            %
                                                                        </td>
                                                                    </tr>
                                                                )
                                                            )
                                                        )}
                                                    </tbody>
                                                </table>
                                            </div>

                                            <div>
                                                <h3
                                                    style={
                                                        sectionTitleStyle
                                                    }
                                                >
                                                    Savings Summary
                                                </h3>

                                                <div
                                                    style={{
                                                        display: "grid",
                                                        gridTemplateColumns:
                                                            "repeat(auto-fit, minmax(220px, 1fr))",
                                                        gap: "12px",
                                                        marginTop: "14px",
                                                    }}
                                                >
                                                    {[
                                                        [
                                                            "Total Target",
                                                            formatCurrency(
                                                                savings.total_target
                                                            ),
                                                        ],
                                                        [
                                                            "Total Saved",
                                                            formatCurrency(
                                                                savings.total_saved
                                                            ),
                                                        ],
                                                        [
                                                            "Overall Progress",
                                                            `${Number(
                                                                savings.progress_percentage ||
                                                                    0
                                                            ).toFixed(2)}%`,
                                                        ],
                                                        [
                                                            "Completed Goals",
                                                            `${
                                                                savings.completed_goals ||
                                                                0
                                                            } / ${
                                                                savings.total_goals ||
                                                                0
                                                            }`,
                                                        ],
                                                    ].map(
                                                        ([label, value]) => (
                                                            <div
                                                                key={label}
                                                                style={
                                                                    metricCardStyle
                                                                }
                                                            >
                                                                <span
                                                                    style={
                                                                        metricLabelStyle
                                                                    }
                                                                >
                                                                    {label}
                                                                </span>
                                                                <strong
                                                                    style={
                                                                        metricValueStyle
                                                                    }
                                                                >
                                                                    {value}
                                                                </strong>
                                                            </div>
                                                        )
                                                    )}
                                                </div>

                                                {goals.length > 0 && (
                                                    <table
                                                        style={tableStyle}
                                                    >
                                                        <thead>
                                                            <tr>
                                                                {[
                                                                    "Goal",
                                                                    "Saved",
                                                                    "Target",
                                                                    "Progress",
                                                                ].map(
                                                                    (
                                                                        heading,
                                                                        index
                                                                    ) => (
                                                                        <th
                                                                            key={
                                                                                heading
                                                                            }
                                                                            style={{
                                                                                ...headerCellStyle,
                                                                                textAlign:
                                                                                    index ===
                                                                                    0
                                                                                        ? "left"
                                                                                        : "right",
                                                                            }}
                                                                        >
                                                                            {
                                                                                heading
                                                                            }
                                                                        </th>
                                                                    )
                                                                )}
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {goals.map(
                                                                (goal) => (
                                                                    <tr
                                                                        key={
                                                                            goal.goal_name
                                                                        }
                                                                    >
                                                                        <td
                                                                            style={
                                                                                bodyCellStyle
                                                                            }
                                                                        >
                                                                            {
                                                                                goal.goal_name
                                                                            }
                                                                        </td>
                                                                        <td
                                                                            style={
                                                                                rightBodyCellStyle
                                                                            }
                                                                        >
                                                                            {formatCurrency(
                                                                                goal.amount_saved
                                                                            )}
                                                                        </td>
                                                                        <td
                                                                            style={
                                                                                rightBodyCellStyle
                                                                            }
                                                                        >
                                                                            {formatCurrency(
                                                                                goal.target_amount
                                                                            )}
                                                                        </td>
                                                                        <td
                                                                            style={
                                                                                rightBodyCellStyle
                                                                            }
                                                                        >
                                                                            {Number(
                                                                                goal.progress_percentage ||
                                                                                    0
                                                                            ).toFixed(
                                                                                2
                                                                            )}
                                                                            %
                                                                        </td>
                                                                    </tr>
                                                                )
                                                            )}
                                                        </tbody>
                                                    </table>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })()}
                            </div>

                            <div className="report-details-actions">

                                <button
                                    type="button"
                                    className="report-update-button"
                                    onClick={() =>
                                        downloadReportFile(
                                            selectedReport.period,
                                            "pdf",
                                            selectedReport.report_type
                                        )
                                    }
                                >
                                    📄 Download PDF
                                </button>

                                <button
                                    type="button"
                                    className="report-update-button"
                                    onClick={() =>
                                        downloadReportFile(
                                            selectedReport.period,
                                            "excel",
                                            selectedReport.report_type
                                        )
                                    }
                                >
                                    📊 Download Excel
                                </button>

                                <button
                                    type="button"
                                    className="report-update-button"
                                    onClick={updateReport}
                                    disabled={updating}
                                >
                                    ✏️{" "}
                                    {updating
                                        ? "Updating..."
                                        : "Update Report"}
                                </button>

                                <button
                                    type="button"
                                    className="report-danger-button"
                                    onClick={() =>
                                        deleteReport(
                                            selectedReport
                                        )
                                    }
                                    disabled={deleting}
                                >
                                    🗑{" "}
                                    {deleting
                                        ? "Deleting..."
                                        : "Delete Report"}
                                </button>

                            </div>

                        </div>
                    )}

                </section>

            </div>

        </div>
    );
}

export default Reports;