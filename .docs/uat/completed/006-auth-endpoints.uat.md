# UAT 006 — /auth Endpoints with fastapi-users

> **Task**: [006-auth-endpoints](../tasks/006-auth-endpoints.md)
> **Python**: `backend/.venv/bin/python`
> **DB**: PostgreSQL on localhost:5432 (workoutwiz)

---

## Test 1 — User model file exists and extends SQLAlchemyBaseUserTableUUID

**Method**: Static file + import check

**Steps**:
```python
import subprocess, sys
result = subprocess.run(
    ["backend/.venv/bin/python", "-c",
     "from app.models.user import User; from fastapi_users.db import SQLAlchemyBaseUserTableUUID; "
     "assert issubclass(User, SQLAlchemyBaseUserTableUUID), 'User does not extend SQLAlchemyBaseUserTableUUID'; "
     "print('PASS')"],
    capture_output=True, text=True, cwd="backend"
)
print(result.stdout, result.stderr)
```

**Expected**: `PASS` with no errors

**Result**: [x] PASS  [ ] FAIL

---

## Test 2 — auth.py exports fastapi_users, current_active_user, auth_backend

**Method**: Import check

**Steps**:
```python
# Run from /backend:
# backend/.venv/bin/python -c "
# from app.auth import fastapi_users, current_active_user, auth_backend
# assert fastapi_users is not None
# assert current_active_user is not None
# assert auth_backend is not None
# print('PASS')
# "
```

**Expected**: `PASS` with no errors

**Result**: [x] PASS  [ ] FAIL

---

## Test 3 — schemas/user.py has UserRead, UserCreate, UserUpdate

**Method**: Import check

**Steps**:
```python
# backend/.venv/bin/python -c "
# from app.schemas.user import UserRead, UserCreate, UserUpdate
# from fastapi_users import schemas
# assert issubclass(UserRead, schemas.BaseUser)
# assert issubclass(UserCreate, schemas.BaseUserCreate)
# assert issubclass(UserUpdate, schemas.BaseUserUpdate)
# print('PASS')
# "
```

**Expected**: `PASS` with no errors

**Result**: [x] PASS  [ ] FAIL

---

## Test 4 — Migration file exists for the user table

**Method**: File existence + content check

**Steps**:
```python
# backend/.venv/bin/python -c "
# import os, glob
# files = glob.glob('migrations/versions/*.py')
# content = ''
# for f in files:
#     with open(f) as fh:
#         content += fh.read()
# assert 'create_table' in content and \"'user'\" in content, 'No user table migration found'
# print('PASS')
# "
```

**Expected**: `PASS` — migration file containing `create_table` for `user` table exists

**Result**: [x] PASS  [ ] FAIL

---

## Test 5 — POST /auth/register creates a user (in-process httpx)

**Method**: httpx AsyncClient with ASGITransport + real DB

**Steps**:
```python
# backend/.venv/bin/python -c "
# import asyncio, uuid
# import httpx
# from httpx import AsyncClient, ASGITransport
# from app.main import app
#
# async def test():
#     email = f'test-{uuid.uuid4().hex[:8]}@example.com'
#     async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
#         r = await client.post('/auth/register', json={'email': email, 'password': 'Password123!'})
#     assert r.status_code == 201, f'Expected 201, got {r.status_code}: {r.text}'
#     data = r.json()
#     assert data['email'] == email, f'Email mismatch: {data}'
#     assert 'id' in data, f'No id in response: {data}'
#     print('PASS')
#
# asyncio.run(test())
# "
```

**Expected**: `PASS` — HTTP 201 with UserRead JSON containing `id` and `email`

**Result**: [x] PASS  [ ] FAIL

---

## Test 6 — POST /auth/jwt/login returns a bearer token

**Method**: httpx AsyncClient with ASGITransport + real DB (register then login)

**Steps**:
```python
# backend/.venv/bin/python -c "
# import asyncio, uuid
# import httpx
# from httpx import AsyncClient, ASGITransport
# from app.main import app
#
# async def test():
#     email = f'login-{uuid.uuid4().hex[:8]}@example.com'
#     password = 'Password123!'
#     async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
#         await client.post('/auth/register', json={'email': email, 'password': password})
#         r = await client.post('/auth/jwt/login', data={'username': email, 'password': password})
#     assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
#     data = r.json()
#     assert 'access_token' in data, f'No access_token: {data}'
#     assert data['token_type'] == 'bearer', f'Wrong token_type: {data}'
#     print('PASS')
#
# asyncio.run(test())
# "
```

**Expected**: `PASS` — HTTP 200 with `{"access_token": "...", "token_type": "bearer"}`

**Result**: [x] PASS  [ ] FAIL

---

## Test 7 — GET /auth/me with token returns user data; without token returns 401

**Method**: httpx AsyncClient with ASGITransport + real DB

**Steps**:
```python
# backend/.venv/bin/python -c "
# import asyncio, uuid
# import httpx
# from httpx import AsyncClient, ASGITransport
# from app.main import app
#
# async def test():
#     email = f'me-{uuid.uuid4().hex[:8]}@example.com'
#     password = 'Password123!'
#     async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
#         await client.post('/auth/register', json={'email': email, 'password': password})
#         login = await client.post('/auth/jwt/login', data={'username': email, 'password': password})
#         token = login.json()['access_token']
#         # Authenticated request
#         r_auth = await client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
#         assert r_auth.status_code == 200, f'Expected 200 with token, got {r_auth.status_code}: {r_auth.text}'
#         data = r_auth.json()
#         assert 'email' in data, f'No email in response: {data}'
#         assert data['email'] == email, f'Email mismatch: {data}'
#         # Unauthenticated request
#         r_unauth = await client.get('/auth/me')
#         assert r_unauth.status_code == 401, f'Expected 401 without token, got {r_unauth.status_code}: {r_unauth.text}'
#     print('PASS')
#
# asyncio.run(test())
# "
```

**Expected**: `PASS` — authenticated returns 200 with user data; unauthenticated returns 401

**Result**: [x] PASS  [ ] FAIL

---

## Test 8 — Duplicate email registration returns 400

**Method**: httpx AsyncClient with ASGITransport + real DB

**Steps**:
```python
# backend/.venv/bin/python -c "
# import asyncio, uuid
# import httpx
# from httpx import AsyncClient, ASGITransport
# from app.main import app
#
# async def test():
#     email = f'dup-{uuid.uuid4().hex[:8]}@example.com'
#     password = 'Password123!'
#     async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
#         r1 = await client.post('/auth/register', json={'email': email, 'password': password})
#         assert r1.status_code == 201, f'First register failed: {r1.status_code} {r1.text}'
#         r2 = await client.post('/auth/register', json={'email': email, 'password': password})
#         assert r2.status_code == 400, f'Expected 400 for duplicate, got {r2.status_code}: {r2.text}'
#     print('PASS')
#
# asyncio.run(test())
# "
```

**Expected**: `PASS` — second registration with same email returns HTTP 400

**Result**: [x] PASS  [ ] FAIL

---

## Summary

| # | Test | Status |
|---|------|--------|
| 1 | User model extends SQLAlchemyBaseUserTableUUID | PASS |
| 2 | auth.py exports fastapi_users, current_active_user, auth_backend | PASS |
| 3 | schemas/user.py has UserRead, UserCreate, UserUpdate | PASS |
| 4 | Migration file exists for user table | PASS |
| 5 | POST /auth/register creates a user | PASS |
| 6 | POST /auth/jwt/login returns bearer token | PASS |
| 7 | GET /auth/me with/without token | PASS |
| 8 | Duplicate email returns 400 | PASS |
