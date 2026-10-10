from datetime import date
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.db import connection
from django.http import Http404, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import BaseRenderer, JSONRenderer

from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Expense, Income, Budget, SavingsGoal, Notification, Report,
    ImportedTransactionIdentity,
)
from .notifications import check_and_trigger_budget_alert, check_and_trigger_goal_alert
from .analytics import get_financial_overview, get_monthly_trends
from .reports import (
    create_monthly_financial_report,
    generate_report_csv_content,
    generate_report_excel_content,
    generate_report_pdf_content,
)
from .upi_import import (
    mark_duplicate_transactions,
    parse_upi_csv,
    serialize_preview,
)
from .serializers import (
    CustomTokenObtainPairSerializer,
    ExpenseSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    IncomeSerializer,
    BudgetSerializer,
    SavingsGoalSerializer,
    NotificationSerializer,
    ReportSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    JWT login endpoint supporting:
    - Exact and Case-insensitive username (e.g. 'Ravi1' or 'ravi1')
    - Email address login
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "User registered successfully",
                    "username": user.username,
                    "email": user.email,
                    "role": user.profile.role,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class ExpenseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expenses = Expense.objects.filter(user=request.user).order_by('-date', '-id')
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            expense = serializer.save(user=request.user)
            check_and_trigger_budget_alert(user=request.user, category=expense.category, expense_date=expense.date)
            return Response(
                ExpenseSerializer(expense).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ExpenseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Expense.objects.get(pk=pk, user=user)
        except Expense.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        expense = self.get_object(pk, request.user)
        serializer = ExpenseSerializer(expense)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        expense = self.get_object(pk, request.user)
        serializer = ExpenseSerializer(expense, data=request.data)
        if serializer.is_valid():
            expense = serializer.save()
            check_and_trigger_budget_alert(user=request.user, category=expense.category, expense_date=expense.date)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        expense = self.get_object(pk, request.user)
        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            expense = serializer.save()
            check_and_trigger_budget_alert(user=request.user, category=expense.category, expense_date=expense.date)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        expense = self.get_object(pk, request.user)
        expense.delete()
        return Response({"message": "Expense deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



class IncomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        incomes = Income.objects.filter(user=request.user).order_by('-date', '-id')
        serializer = IncomeSerializer(incomes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = IncomeSerializer(data=request.data)
        if serializer.is_valid():
            income = serializer.save(user=request.user)
            return Response(
                IncomeSerializer(income).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class IncomeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Income.objects.get(pk=pk, user=user)
        except Income.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        income = self.get_object(pk, request.user)
        serializer = IncomeSerializer(income)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        income = self.get_object(pk, request.user)
        serializer = IncomeSerializer(income, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        income = self.get_object(pk, request.user)
        serializer = IncomeSerializer(income, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        income = self.get_object(pk, request.user)
        income.delete()
        return Response({"message": "Income deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class UPITransactionImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if uploaded_file is None:
            return Response(
                {'detail': 'Upload a CSV file using the "file" field.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transactions, errors = parse_upi_csv(uploaded_file)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        mark_duplicate_transactions(request.user, transactions)
        preview = serialize_preview(transactions)
        if request.query_params.get('preview', '').lower() == 'true':
            return Response({
                'transactions': preview,
                'errors': errors,
                'importable_count': sum(not item['duplicate'] for item in transactions),
                'duplicate_count': sum(item['duplicate'] for item in transactions),
            })

        if errors:
            return Response({
                'detail': 'Fix the invalid CSV rows before importing.',
                'errors': errors,
                'transactions': preview,
            }, status=status.HTTP_400_BAD_REQUEST)

        imported_count = 0
        duplicate_count = 0
        with transaction.atomic():
            for item in transactions:
                if item['duplicate']:
                    duplicate_count += 1
                    continue

                _, created = ImportedTransactionIdentity.objects.get_or_create(
                    user=request.user,
                    identity_key=item['identity_key'],
                )
                if not created:
                    duplicate_count += 1
                    continue

                if item['type'] == 'credit':
                    Income.objects.create(
                        user=request.user,
                        source='Other',
                        description=item['description'],
                        amount=item['amount'],
                        date=item['date'],
                        upi_reference=item['upi_reference'],
                    )
                else:
                    expense = Expense.objects.create(
                        user=request.user,
                        category=item['category'],
                        description=item['description'],
                        amount=item['amount'],
                        date=item['date'],
                        upi_reference=item['upi_reference'],
                    )
                    check_and_trigger_budget_alert(
                        user=request.user,
                        category=expense.category,
                        expense_date=expense.date,
                    )
                imported_count += 1

        return Response({
            'message': f'Imported {imported_count} transaction(s); skipped {duplicate_count} duplicate(s).',
            'imported_count': imported_count,
            'duplicate_count': duplicate_count,
        }, status=status.HTTP_200_OK)


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Calculate Total Income
        income_agg = Income.objects.filter(user=user).aggregate(total=Sum('amount'))
        total_income = income_agg['total'] or Decimal('0.00')

        # Calculate Total Expenses
        expense_agg = Expense.objects.filter(user=user).aggregate(total=Sum('amount'))
        total_expenses = expense_agg['total'] or Decimal('0.00')

        # Calculate Remaining Financial Amount (Total Income - Total Expenses)
        remaining_amount = total_income - total_expenses

        # Combined recent financial activity (chronologically ordered by date desc, id desc)
        incomes = Income.objects.filter(user=user)
        expenses = Expense.objects.filter(user=user)

        transactions = []
        for inc in incomes:
            transactions.append({
                'id': f'inc-{inc.id}',
                'raw_id': inc.id,
                'type': 'income',
                'title': inc.source,
                'source': inc.source,
                'category': None,
                'amount': f'{inc.amount:.2f}',
                'raw_amount': float(inc.amount),
                'date': str(inc.date),
                'description': inc.description,
                'upi_reference': inc.upi_reference,
            })

        for exp in expenses:
            transactions.append({
                'id': f'exp-{exp.id}',
                'raw_id': exp.id,
                'type': 'expense',
                'title': exp.category,
                'category': exp.category,
                'source': None,
                'amount': f'{exp.amount:.2f}',
                'raw_amount': float(exp.amount),
                'date': str(exp.date),
                'description': exp.description,
                'upi_reference': exp.upi_reference,
            })

        # Sort chronologically by date descending, then raw_id descending
        transactions.sort(key=lambda x: (x['date'], x['raw_id']), reverse=True)

        return Response({
            'total_income': f'{total_income:.2f}',
            'total_expenses': f'{total_expenses:.2f}',
            'remaining_amount': f'{remaining_amount:.2f}',
            'income_count': incomes.count(),
            'expense_count': expenses.count(),
            'recent_transactions': transactions,
        }, status=status.HTTP_200_OK)



class BudgetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        month_param = request.query_params.get('month')
        qs = Budget.objects.filter(user=request.user)
        if month_param:
            try:
                parts = month_param.split('-')
                year = int(parts[0])
                month_num = int(parts[1])
                qs = qs.filter(month__year=year, month__month=month_num)
            except Exception:
                pass
        serializer = BudgetSerializer(qs.order_by('-month', 'category'), many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BudgetSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.validated_data['category']
            month_val = serializer.validated_data['month']
            existing = Budget.objects.filter(
                user=request.user,
                category=category,
                month__year=month_val.year,
                month__month=month_val.month
            ).first()
            if existing:
                existing.amount = serializer.validated_data['amount']
                existing.month = month_val
                existing.save()
                return Response(
                    BudgetSerializer(existing).data,
                    status=status.HTTP_200_OK
                )
            budget = serializer.save(user=request.user)
            return Response(
                BudgetSerializer(budget).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class BudgetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Budget.objects.get(pk=pk, user=user)
        except Budget.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        budget = self.get_object(pk, request.user)
        serializer = BudgetSerializer(budget)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        budget = self.get_object(pk, request.user)
        serializer = BudgetSerializer(budget, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        budget = self.get_object(pk, request.user)
        serializer = BudgetSerializer(budget, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        budget = self.get_object(pk, request.user)
        budget.delete()
        return Response({"message": "Budget allocation deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class BudgetSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        month_param = request.query_params.get('month')
        if month_param:
            try:
                parts = month_param.split('-')
                year = int(parts[0])
                month_num = int(parts[1])
                target_month = date(year, month_num, 1)
            except Exception:
                target_month = date.today().replace(day=1)
        else:
            target_month = date.today().replace(day=1)

        budgets = Budget.objects.filter(
            user=user,
            month__year=target_month.year,
            month__month=target_month.month
        )
        budget_map = {b.category: b for b in budgets}

        # User expenses in this month
        expenses = Expense.objects.filter(
            user=user,
            date__year=target_month.year,
            date__month=target_month.month
        )

        categories_summary = []
        total_budget = Decimal('0.00')
        total_spent = Decimal('0.00')

        for cat_code, cat_name in Expense.CATEGORY_CHOICES:
            b_obj = budget_map.get(cat_code)
            allocated = b_obj.amount if b_obj else Decimal('0.00')
            spent_agg = expenses.filter(category=cat_code).aggregate(total=Sum('amount'))
            spent = spent_agg['total'] or Decimal('0.00')
            remaining = allocated - spent
            utilization = (float(spent) / float(allocated) * 100) if allocated > 0 else 0.0

            total_budget += allocated
            total_spent += spent

            categories_summary.append({
                'category': cat_code,
                'budget_id': b_obj.id if b_obj else None,
                'allocated_budget': f'{allocated:.2f}',
                'actual_spent': f'{spent:.2f}',
                'remaining_budget': f'{remaining:.2f}',
                'utilization_percentage': round(utilization, 1),
                'is_over_budget': (spent > allocated) if allocated > 0 else (spent > 0),
            })

        total_remaining = total_budget - total_spent

        return Response({
            'month': target_month.strftime('%Y-%m-%d'),
            'month_label': target_month.strftime('%B %Y'),
            'total_budget': f'{total_budget:.2f}',
            'total_spent': f'{total_spent:.2f}',
            'total_remaining': f'{total_remaining:.2f}',
            'categories': categories_summary,
        }, status=status.HTTP_200_OK)



class SavingsGoalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        goals = SavingsGoal.objects.filter(user=request.user).order_by('-id')
        serializer = SavingsGoalSerializer(goals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SavingsGoalSerializer(data=request.data)
        if serializer.is_valid():
            goal = serializer.save(user=request.user)
            check_and_trigger_goal_alert(goal)
            return Response(
                SavingsGoalSerializer(goal).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class SavingsGoalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return SavingsGoal.objects.get(pk=pk, user=user)
        except SavingsGoal.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        goal = self.get_object(pk, request.user)
        serializer = SavingsGoalSerializer(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        goal = self.get_object(pk, request.user)
        serializer = SavingsGoalSerializer(goal, data=request.data)
        if serializer.is_valid():
            goal = serializer.save()
            check_and_trigger_goal_alert(goal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        goal = self.get_object(pk, request.user)
        serializer = SavingsGoalSerializer(goal, data=request.data, partial=True)
        if serializer.is_valid():
            goal = serializer.save()
            check_and_trigger_goal_alert(goal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        goal = self.get_object(pk, request.user)
        goal.delete()
        return Response({"message": "Savings goal deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        unread = request.query_params.get('unread')
        if unread and unread.lower() in ('true', '1'):
            notifications = notifications.filter(is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            notification = serializer.save(user=request.user)
            return Response(
                NotificationSerializer(notification).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Notification.objects.get(pk=pk, user=user)
        except Notification.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        notification = self.get_object(pk, request.user)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        notification = self.get_object(pk, request.user)
        serializer = NotificationSerializer(notification, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        notification = self.get_object(pk, request.user)
        notification.delete()
        return Response({"message": "Notification deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class NotificationMarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            raise Http404

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({
            "message": "All notifications marked as read",
            "updated_count": updated_count
        }, status=status.HTTP_200_OK)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_financial_overview(
            user=request.user,
            month=request.query_params.get('month'),
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date'),
            year=request.query_params.get('year')
        )
        return Response(data, status=status.HTTP_200_OK)


class AnalyticsTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        months_param = request.query_params.get('months', 6)
        year_param = request.query_params.get('year')
        data = get_monthly_trends(
            user=request.user,
            months_count=months_param,
            year=year_param,
            end_month=request.query_params.get('month')
        )
        return Response(data, status=status.HTTP_200_OK)


def generate_report_response(request):
    try:
        report, created = create_monthly_financial_report(
            user=request.user,
            target_month=request.data.get('month'),
        )
    except ValueError as error:
        return Response(
            {'month': [str(error)]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        ReportSerializer(report).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


class ReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = Report.objects.filter(user=request.user).order_by('-generated_at', '-id')
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        return generate_report_response(request)


class ReportGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return generate_report_response(request)


class ReportDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Report.objects.get(pk=pk, user=user)
        except Report.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        report = self.get_object(pk, request.user)
        serializer = ReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        report = self.get_object(pk, request.user)
        report.delete()
        return Response({"message": "Report deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ReportCSVRenderer(BaseRenderer):
    """
    Custom DRF renderer allowing `?format=csv` queries for report exports.
    """
    media_type = 'text/csv'
    format = 'csv'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, str):
            return data.encode('utf-8')
        if isinstance(data, bytes):
            return data
        return str(data).encode('utf-8')


class ReportBinaryRenderer(BaseRenderer):
    charset = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, bytes):
            return data
        return bytes(data)


class ReportExcelRenderer(ReportBinaryRenderer):
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    format = 'xlsx'


class ReportExcelAliasRenderer(ReportExcelRenderer):
    format = 'excel'


class ReportPDFRenderer(ReportBinaryRenderer):
    media_type = 'application/pdf'
    format = 'pdf'


class ReportExportView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [
        JSONRenderer,
        ReportCSVRenderer,
        ReportExcelRenderer,
        ReportExcelAliasRenderer,
        ReportPDFRenderer,
    ]

    def get_object(self, pk, user):
        try:
            return Report.objects.get(pk=pk, user=user)
        except Report.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        report = self.get_object(pk, request.user)
        export_format = request.query_params.get('format', 'csv').lower()
        month_str = report.month.strftime('%Y_%m') if report.month else f"report_{report.id}"

        if export_format == 'json':
            return Response(report.data, status=status.HTTP_200_OK)

        formats = {
            'csv': (
                generate_report_csv_content(report.data),
                'text/csv',
                f'BudgetBuddy_Financial_Report_{month_str}.csv',
            ),
            'xlsx': (
                generate_report_excel_content(report.data),
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                f'BudgetBuddy_Financial_Report_{month_str}.xlsx',
            ),
            'excel': (
                generate_report_excel_content(report.data),
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                f'BudgetBuddy_Financial_Report_{month_str}.xlsx',
            ),
            'pdf': (
                generate_report_pdf_content(report.data),
                'application/pdf',
                f'BudgetBuddy_Financial_Report_{month_str}.pdf',
            ),
        }
        export = formats.get(export_format)
        if not export:
            return Response(
                {'detail': 'Unsupported export format. Use csv, xlsx, pdf, or json.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        content, content_type, filename = export
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response