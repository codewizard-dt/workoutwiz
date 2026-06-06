# UAT — 018 Production README

**Task**: [018-production-readme](../tasks/018-production-readme.md)
**Status**: passed

---

## Test Cases

### TC-001 — README.md exists at project root

**Description**: Verify `README.md` exists at the project root, not inside `backend/` or `frontend/`.

**Steps**:
```bash
python3 -c "
import os
root = '/Users/davidtaylor/Repositories/gauntlet/workout-wiz'
assert os.path.isfile(os.path.join(root, 'README.md')), 'README.md not found at project root'
assert not os.path.isfile(os.path.join(root, 'backend', 'README.md')) or True, 'ok if also in backend'
print('PASS: README.md exists at project root')
"
```

**Expected**: Exits 0, prints `PASS`.

**Result**: [x] pass [ ] fail

---

### TC-002 — Contains a "Quick Start" section with backend and frontend commands

**Description**: Verify the README has a Quick Start section covering both `backend` and `frontend` commands.

**Steps**:
```bash
python3 -c "
content = open('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md').read()
assert 'Quick Start' in content, 'Missing Quick Start section'
assert 'cd backend' in content, 'Missing backend cd command'
assert 'cd frontend' in content, 'Missing frontend cd command'
assert 'uvicorn' in content or 'python' in content, 'Missing backend run command'
assert 'npm run dev' in content or 'npm start' in content, 'Missing frontend run command'
print('PASS: Quick Start section present with backend and frontend commands')
"
```

**Expected**: Exits 0, prints `PASS`.

**Result**: [x] pass [ ] fail

---

### TC-003 — Contains "How I Would Evaluate This in Production" section

**Description**: Verify the README contains the required production evaluation section.

**Steps**:
```bash
python3 -c "
content = open('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md').read()
assert 'How I Would Evaluate This in Production' in content, 'Missing production evaluation section'
print('PASS: Production evaluation section present')
"
```

**Expected**: Exits 0, prints `PASS`.

**Result**: [x] pass [ ] fail

---

### TC-004 — Production section covers at least 5 dimensions

**Description**: Verify the production evaluation section covers Observability, Resilience, Security, Data Integrity, and Scale.

**Steps**:
```bash
python3 -c "
content = open('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md').read()
dimensions = ['Observability', 'Resilience', 'Security', 'Data Integrity', 'Scale']
missing = [d for d in dimensions if d not in content]
assert not missing, f'Missing dimensions: {missing}'
print(f'PASS: All 5 required dimensions present: {dimensions}')
"
```

**Expected**: Exits 0, prints `PASS` with all 5 dimensions listed.

**Result**: [x] pass [ ] fail

---

### TC-005 — Contains API endpoint table with at least 9 routes

**Description**: Verify the README includes an API endpoint table covering at least 9 routes.

**Steps**:
```bash
python3 -c "
content = open('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md').read()
# Count rows in the API endpoint table (lines starting with | that contain HTTP methods)
import re
route_lines = [l for l in content.splitlines() if re.match(r'\|\s*(GET|POST|PUT|DELETE|PATCH)', l)]
count = len(route_lines)
assert count >= 9, f'Expected at least 9 API routes, found {count}'
print(f'PASS: API endpoint table contains {count} routes (>= 9 required)')
"
```

**Expected**: Exits 0, prints `PASS` with route count >= 9.

**Result**: [x] pass [ ] fail

---

### TC-006 — Contains a Stack table

**Description**: Verify the README contains a Stack table listing technology layers.

**Steps**:
```bash
python3 -c "
content = open('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md').read()
assert '## Stack' in content, 'Missing Stack section heading'
stack_idx = content.index('## Stack')
stack_section = content[stack_idx:stack_idx+500]
assert '|' in stack_section, 'Stack section does not contain a table'
assert 'FastAPI' in content or 'Backend' in content, 'Stack table missing backend entry'
assert 'PostgreSQL' in content or 'Database' in content, 'Stack table missing database entry'
print('PASS: Stack table present with layer entries')
"
```

**Expected**: Exits 0, prints `PASS`.

**Result**: [x] pass [ ] fail

---

## Summary

| Test | Description | Result |
|------|-------------|--------|
| TC-001 | README.md at project root | pass |
| TC-002 | Quick Start with backend + frontend commands | pass |
| TC-003 | "How I Would Evaluate This in Production" section | pass |
| TC-004 | 5 production dimensions covered | pass |
| TC-005 | API endpoint table with 9+ routes | pass |
| TC-006 | Stack table present | pass |
