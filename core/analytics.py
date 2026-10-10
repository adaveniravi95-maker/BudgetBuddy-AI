from datetime import date, datetime
from decimal import Decimal
from django.db.models import Sum, Count
from .models import Income, Expense, Budget, SavingsGoal


def parse_date_params(month=None, start_date=None, end_date=None, year=None):
    """
    Parses and sanitizes date filtering parameters.
    Returns (start_date_obj, end_date_obj, target_month_obj, target_year_int)
    """
    start_obj = None
    end_obj = None
    month_obj = None
    year_int = None

    if start_date:
        try:
            start_obj = datetime.strptime(str(start_date).strip(), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_obj = None

    if end_date:
        try:
            end_obj = datetime.strptime(str(end_date).strip(), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            end_obj = None

    if month:
        try:
            m_str = str(month).strip()
            if len(m_str) == 7: # 'YYYY-MM'
                month_obj = datetime.strptime(f"{m_str}-01", '%Y-%m-%d').date()
            else: # 'YYYY-MM-DD'
                month_obj = datetime.strptime(m_str, '%Y-%m-%d').date().replace(day=1)
        except (ValueError, TypeError):
            month_obj = None

    if year:
        try:
            year_int = int(str(year).strip())
        except (ValueError, TypeError):
            year_int = None

    return start_obj, end_obj, month_obj, year_int


def get_financial_overview(user, month=None, start_date=None, end_date=None, year=None):
    """
    Generates a comprehensive financial analytics summary for a user with flexible date filters.
    Zero-safe math and robust against empty records.
    """
    start_obj, end_obj, month_obj, year_int = parse_date_params(month, start_date, end_date, year)

    incomes = Income.objects.filter(user=user)
    expenses = Expense.objects.filter(user=user)
    budgets = Budget.objects.filter(user=user)

    # Apply date filters
    filter_label = "All Time"
    if start_obj and end_obj:
        incomes = incomes.filter(date__gte=start_obj, date__lte=end_obj)
        expenses = expenses.filter(date__gte=start_obj, date__lte=end_obj)
        filter_label = f"{start_obj.strftime('%Y-%m-%d')} to {end_obj.strftime('%Y-%m-%d')}"
    elif month_obj:
        incomes = incomes.filter(date__year=month_obj.year, date__month=month_obj.month)
        expenses = expenses.filter(date__year=month_obj.year, date__month=month_obj.month)
        budgets = budgets.filter(month__year=month_obj.year, month__month=month_obj.month)
        filter_label = month_obj.strftime('%B %Y')
    elif year_int:
        incomes = incomes.filter(date__year=year_int)
        expenses = expenses.filter(date__year=year_int)
        budgets = budgets.filter(month__year=year_int)
        filter_label = f"Year {year_int}"

    # Calculate Totals
    income_agg = incomes.aggregate(total=Sum('amount'), count=Count('id'))
    total_income = income_agg['total'] or Decimal('0.00')
    income_count = income_agg['count'] or 0

    expense_agg = expenses.aggregate(total=Sum('amount'), count=Count('id'))
    total_expenses = expense_agg['total'] or Decimal('0.00')
    expense_count = expense_agg['count'] or 0

    net_savings = total_income - total_expenses
    savings_rate = round(float((net_savings / total_income) * 100), 2) if total_income > Decimal('0.00') else 0.0

    # Category Breakdown (All 6 standard categories)
    category_summary = []
    cat_exp_map = {cat[0]: Decimal('0.00') for cat in Expense.CATEGORY_CHOICES}
    cat_count_map = {cat[0]: 0 for cat in Expense.CATEGORY_CHOICES}

    for exp in expenses:
        if exp.category in cat_exp_map:
            cat_exp_map[exp.category] += exp.amount
            cat_count_map[exp.category] += 1

    for cat_code, cat_name in Expense.CATEGORY_CHOICES:
        cat_total = cat_exp_map.get(cat_code, Decimal('0.00'))
        cat_pct = round(float((cat_total / total_expenses) * 100), 2) if total_expenses > Decimal('0.00') else 0.0
        category_summary.append({
            'category': cat_code,
            'total_amount': f'{cat_total:.2f}',
            'raw_total': float(cat_total),
            'percentage': cat_pct,
            'count': cat_count_map.get(cat_code, 0),
        })

    # Sort categories by total_amount descending
    category_summary.sort(key=lambda x: x['raw_total'], reverse=True)

    # Source Breakdown
    source_summary = []
    src_inc_map = {src[0]: Decimal('0.00') for src in Income.SOURCE_CHOICES}
    src_count_map = {src[0]: 0 for src in Income.SOURCE_CHOICES}

    for inc in incomes:
        if inc.source in src_inc_map:
            src_inc_map[inc.source] += inc.amount
            src_count_map[inc.source] += 1

    for src_code, src_name in Income.SOURCE_CHOICES:
        src_total = src_inc_map.get(src_code, Decimal('0.00'))
        src_pct = round(float((src_total / total_income) * 100), 2) if total_income > Decimal('0.00') else 0.0
        source_summary.append({
            'source': src_code,
            'total_amount': f'{src_total:.2f}',
            'raw_total': float(src_total),
            'percentage': src_pct,
            'count': src_count_map.get(src_code, 0),
        })

    source_summary.sort(key=lambda x: x['raw_total'], reverse=True)

    # Budget Utilization
    budget_agg = budgets.aggregate(total=Sum('amount'))
    total_budgeted = budget_agg['total'] or Decimal('0.00')
    budget_utilization = round(float((total_expenses / total_budgeted) * 100), 2) if total_budgeted > Decimal('0.00') else 0.0

    # Savings Goals Snapshot
    user_goals = SavingsGoal.objects.filter(user=user)
    goals_target_agg = user_goals.aggregate(target_sum=Sum('target_amount'), saved_sum=Sum('current_amount'))
    total_goal_target = goals_target_agg['target_sum'] or Decimal('0.00')
    total_goal_saved = goals_target_agg['saved_sum'] or Decimal('0.00')
    overall_goal_progress = round(float((total_goal_saved / total_goal_target) * 100), 2) if total_goal_target > Decimal('0.00') else 0.0
    completed_goals_count = sum(1 for g in user_goals if g.is_completed)

    return {
        'filter_applied': filter_label,
        'total_income': f'{total_income:.2f}',
        'total_expenses': f'{total_expenses:.2f}',
        'net_savings': f'{net_savings:.2f}',
        'savings_rate': savings_rate,
        'income_count': income_count,
        'expense_count': expense_count,
        'categories': category_summary,
        'sources': source_summary,
        'budget': {
            'total_budgeted': f'{total_budgeted:.2f}',
            'total_spent': f'{total_expenses:.2f}',
            'remaining_budget': f'{(total_budgeted - total_expenses):.2f}',
            'utilization_percentage': budget_utilization,
        },
        'savings_goals': {
            'total_goals_count': user_goals.count(),
            'completed_goals_count': completed_goals_count,
            'total_target_amount': f'{total_goal_target:.2f}',
            'total_saved_amount': f'{total_goal_saved:.2f}',
            'overall_progress_percentage': overall_goal_progress,
        }
    }


def get_monthly_trends(user, months_count=6, year=None, end_month=None):
    """
    Calculates month-by-month financial trends (income, expenses, net savings, savings rate).
    """
    today = date.today()
    month_list = []

    if year:
        try:
            target_year = int(year)
            for m in range(1, 13):
                month_list.append(date(target_year, m, 1))
        except (ValueError, TypeError):
            target_year = today.year
            for m in range(1, 13):
                month_list.append(date(target_year, m, 1))
    else:
        try:
            m_count = max(1, min(int(months_count), 24))
        except (ValueError, TypeError):
            m_count = 6

        anchor_month = parse_date_params(month=end_month)[2] or today.replace(day=1)
        curr_y = anchor_month.year
        curr_m = anchor_month.month

        for i in range(m_count - 1, -1, -1):
            calc_m = curr_m - i
            calc_y = curr_y
            while calc_m <= 0:
                calc_m += 12
                calc_y -= 1
            month_list.append(date(calc_y, calc_m, 1))

    trends = []
    for m_date in month_list:
        inc_agg = Income.objects.filter(
            user=user,
            date__year=m_date.year,
            date__month=m_date.month
        ).aggregate(total=Sum('amount'))
        inc_total = inc_agg['total'] or Decimal('0.00')

        exp_agg = Expense.objects.filter(
            user=user,
            date__year=m_date.year,
            date__month=m_date.month
        ).aggregate(total=Sum('amount'))
        exp_total = exp_agg['total'] or Decimal('0.00')

        net_val = inc_total - exp_total
        s_rate = round(float((net_val / inc_total) * 100), 2) if inc_total > Decimal('0.00') else 0.0

        trends.append({
            'month': m_date.strftime('%Y-%m'),
            'month_name': m_date.strftime('%b %Y'),
            'total_income': f'{inc_total:.2f}',
            'raw_income': float(inc_total),
            'total_expenses': f'{exp_total:.2f}',
            'raw_expenses': float(exp_total),
            'net_savings': f'{net_val:.2f}',
            'raw_net_savings': float(net_val),
            'savings_rate': s_rate,
        })

    return {
        'months_count': len(trends),
        'trends': trends
    }
