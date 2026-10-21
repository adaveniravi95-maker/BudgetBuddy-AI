import csv
import io
from datetime import date, datetime, timezone
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from .. import models, schemas, auth
from ..budget_alerts import calculate_utilization, month_bounds

router = APIRouter()

SUPPORTED_FORMATS = {"json", "csv", "xlsx", "pdf"}
FORMAT_ALIASES = {
    "json": "json",
    "csv": "csv",
    "xlsx": "xlsx",
    "excel": "xlsx",
    "xls": "xlsx",
    "spreadsheet": "xlsx",
    "pdf": "pdf",
}
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _validate_period(month: int, year: int) -> None:
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")
    if not 1 <= year <= 9999:
        raise HTTPException(status_code=400, detail="year must be between 1 and 9999")


def _month_dates(month: int, year: int) -> tuple[date, date]:
    return month_bounds(year, month)


def _breakdown(rows, label_getter) -> List[schemas.ReportBreakdownItem]:
    totals: dict = {}
    for row in rows:
        label = label_getter(row)
        entry = totals.setdefault(label, {"total": 0.0, "count": 0})
        entry["total"] += float(row.amount)
        entry["count"] += 1
    grand_total = sum(v["total"] for v in totals.values())
    items = []
    for label, values in totals.items():
        percent = round((values["total"] / grand_total) * 100.0, 2) if grand_total > 0 else 0.0
        items.append(schemas.ReportBreakdownItem(
            label=label,
            total=round(values["total"], 2),
            count=values["count"],
            percent=percent,
        ))
    items.sort(key=lambda x: (-x.total, x.label))
    return items


def _collect_report_data(db: Session, user_id: int, month: int, year: int) -> dict:
    start, end = _month_dates(month, year)

    incomes = (
        db.query(models.Income)
        .filter(
            models.Income.user_id == user_id,
            models.Income.date >= start,
            models.Income.date <= end,
        )
        .order_by(models.Income.date)
        .all()
    )
    expenses = (
        db.query(models.Expense)
        .filter(
            models.Expense.user_id == user_id,
            models.Expense.date >= start,
            models.Expense.date <= end,
        )
        .order_by(models.Expense.date)
        .all()
    )

    total_income = sum(float(i.amount) for i in incomes)
    total_expenses = sum(float(e.amount) for e in expenses)
    net_savings = total_income - total_expenses
    savings_rate = round((net_savings / total_income) * 100.0, 2) if total_income > 0 else 0.0

    spent_by_category: dict = {}
    for e in expenses:
        key = e.category.value
        spent_by_category[key] = spent_by_category.get(key, 0.0) + float(e.amount)

    budget = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.month == month,
        models.Budget.year == year,
    ).first()
    budget_section = None
    if budget:
        allocations = []
        for alloc in budget.allocations:
            cat = alloc.category.value
            budgeted = float(alloc.amount)
            spent = spent_by_category.get(cat, 0.0)
            allocations.append(schemas.ReportBudgetAllocation(
                category=cat,
                budgeted=budgeted,
                spent=round(spent, 2),
                remaining=round(budgeted - spent, 2),
                utilization_percent=calculate_utilization(spent, budgeted),
            ))
        allocations.sort(key=lambda x: (-x.utilization_percent, x.category))
        total_budget = float(budget.total_amount)
        budget_section = schemas.ReportBudgetSection(
            total_budget=total_budget,
            total_spent=round(total_expenses, 2),
            remaining=round(total_budget - total_expenses, 2),
            utilization_percent=calculate_utilization(total_expenses, total_budget),
            allocations=allocations,
        )

    goals = (
        db.query(models.SavingsGoal)
        .filter(models.SavingsGoal.user_id == user_id)
        .order_by(models.SavingsGoal.created_at)
        .all()
    )
    goal_items = []
    for g in goals:
        target = float(g.target_amount)
        saved = float(g.current_saved)
        progress = round((saved / target) * 100.0, 2) if target > 0 else 0.0
        goal_items.append(schemas.ReportSavingsGoalItem(
            id=g.id,
            name=g.name,
            target_amount=target,
            current_saved=saved,
            progress_percent=min(progress, 100.0),
            is_completed=g.is_completed,
        ))
    total_target = sum(g.target_amount for g in goal_items)
    total_saved = sum(g.current_saved for g in goal_items)

    income_breakdown = _breakdown(incomes, lambda i: i.source.value)
    expense_breakdown = _breakdown(expenses, lambda e: e.category.value)

    return {
        "month": month,
        "year": year,
        "generated_at": datetime.now(timezone.utc),
        "period_start": start,
        "period_end": end,
        "income": schemas.ReportSectionTotals(
            total=round(total_income, 2),
            count=len(incomes),
            breakdown=income_breakdown,
        ),
        "expenses": schemas.ReportSectionTotals(
            total=round(total_expenses, 2),
            count=len(expenses),
            breakdown=expense_breakdown,
        ),
        "net_savings": round(net_savings, 2),
        "savings_rate_percent": savings_rate,
        "budget": budget_section,
        "savings": schemas.ReportSavingsSection(
            total_goals=len(goal_items),
            total_target=round(total_target, 2),
            total_saved=round(total_saved, 2),
            overall_progress_percent=(
                round((total_saved / total_target) * 100.0, 2) if total_target > 0 else 0.0
            ),
            goals=goal_items,
        ),
        "transaction_count": len(incomes) + len(expenses),
        "income_count": len(incomes),
        "expense_count": len(expenses),
    }


def _notify_report_generated(db: Session, user_id: int, month: int, year: int) -> None:
    profile = db.query(models.Profile).filter(models.Profile.user_id == user_id).first()
    if profile is not None and not profile.monthly_report_notifications:
        return

    related_id = year * 100 + month
    period_label = f"{month:02d}/{year}"
    existing = db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.notification_type == models.NotificationType.general,
        models.Notification.related_id == related_id,
        models.Notification.message.contains("Monthly report"),
    ).first()
    if existing:
        return

    db.add(models.Notification(
        user_id=user_id,
        notification_type=models.NotificationType.general,
        message=f"Monthly report for {period_label} generated",
        related_id=related_id,
    ))
    db.commit()


def _report_to_csv(data: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    month, year = data["month"], data["year"]

    writer.writerow(["BudgetBuddy Monthly Report", f"{MONTH_NAMES[month]} {year}"])
    writer.writerow(["Generated At", data["generated_at"].isoformat()])
    writer.writerow(["Period Start", data["period_start"].isoformat()])
    writer.writerow(["Period End", data["period_end"].isoformat()])
    writer.writerow([])

    writer.writerow(["Income Total", f"{data['income'].total:.2f}"])
    writer.writerow(["Income Count", data["income"].count])
    writer.writerow(["Income Source", "Total", "Count", "Percent"])
    for item in data["income"].breakdown:
        writer.writerow([item.label, f"{item.total:.2f}", item.count, f"{item.percent:.2f}"])
    writer.writerow([])

    writer.writerow(["Expense Total", f"{data['expenses'].total:.2f}"])
    writer.writerow(["Expense Count", data["expenses"].count])
    writer.writerow(["Expense Category", "Total", "Count", "Percent"])
    for item in data["expenses"].breakdown:
        writer.writerow([item.label, f"{item.total:.2f}", item.count, f"{item.percent:.2f}"])
    writer.writerow([])

    writer.writerow(["Net Savings", f"{data['net_savings']:.2f}"])
    writer.writerow(["Savings Rate %", f"{data['savings_rate_percent']:.2f}"])
    writer.writerow([])

    if data["budget"]:
        b = data["budget"]
        writer.writerow(["Total Budget", f"{b.total_budget:.2f}"])
        writer.writerow(["Budget Spent", f"{b.total_spent:.2f}"])
        writer.writerow(["Budget Remaining", f"{b.remaining:.2f}"])
        writer.writerow(["Budget Utilization %", f"{b.utilization_percent:.2f}"])
        writer.writerow(["Budget Category", "Budgeted", "Spent", "Remaining", "Utilization %"])
        for a in b.allocations:
            writer.writerow([
                a.category, f"{a.budgeted:.2f}", f"{a.spent:.2f}",
                f"{a.remaining:.2f}", f"{a.utilization_percent:.2f}",
            ])
    else:
        writer.writerow(["Budget", "No budget set for this month"])
    writer.writerow([])

    s = data["savings"]
    writer.writerow(["Savings Goals", s.total_goals])
    writer.writerow(["Total Target", f"{s.total_target:.2f}"])
    writer.writerow(["Total Saved", f"{s.total_saved:.2f}"])
    writer.writerow(["Overall Progress %", f"{s.overall_progress_percent:.2f}"])
    writer.writerow(["Goal", "Target", "Saved", "Progress %", "Completed"])
    for g in s.goals:
        writer.writerow([
            g.name, f"{g.target_amount:.2f}", f"{g.current_saved:.2f}",
            f"{g.progress_percent:.2f}", "Yes" if g.is_completed else "No",
        ])

    return output.getvalue()


def _report_to_xlsx(data: dict) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Monthly Report"
    month, year = data["month"], data["year"]

    ws.append(["BudgetBuddy Monthly Report", f"{MONTH_NAMES[month]} {year}"])
    ws.append(["Generated At", data["generated_at"].isoformat()])
    ws.append([])

    ws.append(["Income"])
    ws.append(["Total", data["income"].total])
    ws.append(["Count", data["income"].count])
    ws.append(["Source", "Total", "Count", "Percent"])
    for item in data["income"].breakdown:
        ws.append([item.label, item.total, item.count, item.percent])
    ws.append([])

    ws.append(["Expenses"])
    ws.append(["Total", data["expenses"].total])
    ws.append(["Count", data["expenses"].count])
    ws.append(["Category", "Total", "Count", "Percent"])
    for item in data["expenses"].breakdown:
        ws.append([item.label, item.total, item.count, item.percent])
    ws.append([])

    ws.append(["Net Savings", data["net_savings"]])
    ws.append(["Savings Rate %", data["savings_rate_percent"]])
    ws.append([])

    if data["budget"]:
        b = data["budget"]
        ws.append(["Budget"])
        ws.append(["Total Budget", b.total_budget])
        ws.append(["Spent", b.total_spent])
        ws.append(["Remaining", b.remaining])
        ws.append(["Utilization %", b.utilization_percent])
        ws.append(["Category", "Budgeted", "Spent", "Remaining", "Utilization %"])
        for a in b.allocations:
            ws.append([a.category, a.budgeted, a.spent, a.remaining, a.utilization_percent])
    else:
        ws.append(["Budget", "No budget set for this month"])
    ws.append([])

    s = data["savings"]
    ws.append(["Savings Goals"])
    ws.append(["Total Target", s.total_target])
    ws.append(["Total Saved", s.total_saved])
    ws.append(["Overall Progress %", s.overall_progress_percent])
    ws.append(["Goal", "Target", "Saved", "Progress %", "Completed"])
    for g in s.goals:
        ws.append([
            g.name, g.target_amount, g.current_saved,
            g.progress_percent, "Yes" if g.is_completed else "No",
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _report_to_pdf(data: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="BudgetBuddy Monthly Report")
    styles = getSampleStyleSheet()
    story = []
    month, year = data["month"], data["year"]

    story.append(Paragraph(
        f"BudgetBuddy Monthly Report - {MONTH_NAMES[month]} {year}",
        styles["Title"],
    ))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Generated: {data['generated_at'].strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    def add_section(title, summary_line, rows, header):
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(Paragraph(summary_line, styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))
        table_data = [header] + rows
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#D9E2F3")]),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

    add_section(
        "Income",
        f"Total Income: INR {data['income'].total:.2f} ({data['income'].count} records)",
        [[i.label, f"{i.total:.2f}", str(i.count), f"{i.percent:.2f}%"] for i in data["income"].breakdown]
        or [["-", "0.00", "0", "0.00%"]],
        ["Source", "Total", "Count", "Percent"],
    )

    add_section(
        "Expenses",
        f"Total Expenses: INR {data['expenses'].total:.2f} ({data['expenses'].count} records)",
        [[i.label, f"{i.total:.2f}", str(i.count), f"{i.percent:.2f}%"] for i in data["expenses"].breakdown]
        or [["-", "0.00", "0", "0.00%"]],
        ["Category", "Total", "Count", "Percent"],
    )

    story.append(Paragraph(
        f"Net Savings: INR {data['net_savings']:.2f} | Savings Rate: {data['savings_rate_percent']:.2f}%",
        styles["Heading2"],
    ))
    story.append(Spacer(1, 0.2 * inch))

    if data["budget"]:
        b = data["budget"]
        add_section(
            "Budget",
            f"Total: INR {b.total_budget:.2f} | Spent: INR {b.total_spent:.2f} | "
            f"Remaining: INR {b.remaining:.2f} | Utilization: {b.utilization_percent:.2f}%",
            [[a.category, f"{a.budgeted:.2f}", f"{a.spent:.2f}", f"{a.remaining:.2f}", f"{a.utilization_percent:.2f}%"]
             for a in b.allocations] or [["-", "0.00", "0.00", "0.00", "0.00%"]],
            ["Category", "Budgeted", "Spent", "Remaining", "Utilization"],
        )
    else:
        story.append(Paragraph("Budget: No budget set for this month", styles["Heading2"]))
        story.append(Spacer(1, 0.2 * inch))

    s = data["savings"]
    add_section(
        "Savings Goals",
        f"Goals: {s.total_goals} | Target: INR {s.total_target:.2f} | "
        f"Saved: INR {s.total_saved:.2f} | Progress: {s.overall_progress_percent:.2f}%",
        [[g.name, f"{g.target_amount:.2f}", f"{g.current_saved:.2f}", f"{g.progress_percent:.2f}%",
          "Yes" if g.is_completed else "No"] for g in s.goals]
        or [["-", "0.00", "0.00", "0.00%", "No"]],
        ["Goal", "Target", "Saved", "Progress", "Completed"],
    )

    doc.build(story)
    return buffer.getvalue()


def _filename(data: dict, extension: str) -> str:
    return f"budgetbuddy_report_{data['year']:04d}-{data['month']:02d}.{extension}"


@router.get("/monthly/", response_model=schemas.MonthlyReportResponse)
def generate_monthly_report(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    month: int = Query(...),
    year: int = Query(...),
    format: str = Query("json"),
):
    _validate_period(month, year)
    fmt = FORMAT_ALIASES.get(format.lower().strip())
    if fmt is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported format '{format}'. "
                f"Use one of: json, csv, xlsx (or excel), pdf"
            ),
        )

    data = _collect_report_data(db, current_user.id, month, year)
    _notify_report_generated(db, current_user.id, month, year)

    if fmt == "json":
        return schemas.MonthlyReportResponse(**data)
    if fmt == "csv":
        content = _report_to_csv(data)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{_filename(data, "csv")}"'},
        )
    if fmt == "xlsx":
        content = _report_to_xlsx(data)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{_filename(data, "xlsx")}"'},
        )
    content = _report_to_pdf(data)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_filename(data, "pdf")}"'},
    )
