import pathlib

BASE = pathlib.Path(__file__).parent

# Live-server scripts: they hit localhost:8000 and/or call sys.exit at import
# time. They are run manually via `python test_*.py`, not under pytest.
collect_ignore_glob = [
    "test_auth_flow.py",
    "test_transactions.py",
    "test_budgets.py",
    "test_full_verify.py",
    "test_expenses.py",
    "test_incomes.py",
    "test_milestone1.py",
    "test_milestone1_final.py",
    "test_milestone2_full.py",
    "test_m2_final.py",
    "test_quick.py",
    "test_debug.py",
]
