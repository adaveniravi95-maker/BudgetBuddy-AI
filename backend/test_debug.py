import requests
BASE = 'http://localhost:8000/api'
r = requests.post(BASE + '/auth/register/', json={'username': 'debug1', 'email': 'd1@t.com', 'password': 'SecurePass123!', 'password_confirm': 'SecurePass123!'}, timeout=5)
h = {'Authorization': 'Bearer ' + r.json()['tokens']['access']}
requests.post(BASE + '/incomes/', json={'amount': 5000, 'source': 'scholarship', 'date': '2026-09-10'}, headers=h, timeout=5)
requests.post(BASE + '/incomes/', json={'amount': 5000, 'source': 'freelance', 'date': '2026-09-10'}, headers=h, timeout=5)
requests.post(BASE + '/incomes/', json={'amount': 5000, 'source': 'pocket_money', 'date': '2026-09-10'}, headers=h, timeout=5)
for c in ['food','travel','shopping','education','entertainment','miscellaneous']:
    requests.post(BASE + '/expenses/', json={'amount': 500, 'category': c, 'date': '2026-09-15'}, headers=h, timeout=5)
requests.put(BASE + '/expenses/1/', json={'category': 'travel'}, headers=h, timeout=5)
r = requests.get(BASE + '/transactions/summary/', headers=h, timeout=5)
s = r.json()
print('total_income type:', type(s['total_income']), 'value:', repr(s['total_income']))
print('total_expenses type:', type(s['total_expenses']), 'value:', repr(s['total_expenses']))
print('balance type:', type(s['balance']), 'value:', repr(s['balance']))
print('income==15000.0:', s['total_income'] == 15000.0)
print('expenses==3000.0:', s['total_expenses'] == 3000.0)
print('balance==12000.0:', s['balance'] == 12000.0)
r = requests.get(BASE + '/expenses/?category=food', headers=h, timeout=5)
print('Food filter total:', r.json()['total'])
r = requests.get(BASE + '/transactions/', headers=h, timeout=5)
cats = set(t['category'] for t in r.json()['transactions'])
print('All tx categories:', cats, 'count:', len(cats))
