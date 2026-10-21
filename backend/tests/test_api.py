from datetime import date
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def register(email):
    return client.post('/api/auth/register', json={'email':email,'full_name':'Test Student','password':'Password123'})

def login(email):
    r=client.post('/api/auth/login',json={'email':email,'password':'Password123'}); return r.json()['access_token']

def test_auth_and_ownership():
    register('a@example.com'); register('b@example.com')
    a=login('a@example.com'); b=login('b@example.com')
    payload={'amount':100,'category':'Food','expense_date':str(date.today()),'description':'Lunch'}
    r=client.post('/api/expenses',json=payload,headers={'Authorization':f'Bearer {a}'})
    assert r.status_code==201
    assert client.get('/api/expenses',headers={'Authorization':f'Bearer {b}'}).json()==[]

def test_invalid_category_rejected():
    token=login('a@example.com')
    payload={'amount':100,'category':'Invalid','expense_date':str(date.today())}
    assert client.post('/api/expenses',json=payload,headers={'Authorization':f'Bearer {token}'}).status_code==422
