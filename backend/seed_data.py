from datetime import date
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User, Income, Expense, Budget, SavingsGoal, Notification
from app.security import hash_password

db=SessionLocal()
email='student@example.com'
user=db.scalar(select(User).where(User.email==email))
if not user:
    user=User(email=email,full_name='Test Student',password_hash=hash_password('Password123'),role='student'); db.add(user); db.commit(); db.refresh(user)
    db.add_all([
        Income(user_id=user.id,amount=5000,source='Pocket Money',income_date=date.today(),details='Monthly pocket money'),
        Income(user_id=user.id,amount=3000,source='Scholarship',income_date=date.today(),details='Scholarship received'),
        Expense(user_id=user.id,amount=250,category='Food',expense_date=date.today(),description='Lunch'),
        Expense(user_id=user.id,amount=120,category='Travel',expense_date=date.today(),description='Bus'),
        Expense(user_id=user.id,amount=500,category='Education',expense_date=date.today(),description='Books'),
        Expense(user_id=user.id,amount=300,category='Entertainment',expense_date=date.today(),description='Movie'),
        Budget(user_id=user.id,month=date.today().strftime('%Y-%m'),category='Food',allocated_amount=3000),
        Budget(user_id=user.id,month=date.today().strftime('%Y-%m'),category='Travel',allocated_amount=1500),
        SavingsGoal(user_id=user.id,goal_name='New Laptop Fund',target_amount=60000,amount_saved=5000),
        Notification(user_id=user.id,title='BudgetBuddy Ready',message='Start tracking your spending today.')
    ])
    db.commit()
    print('Seed data added successfully.')
else: print('Seed user already exists.')
db.close()
