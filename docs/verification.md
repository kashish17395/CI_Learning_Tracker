# Verification

## Automated

`python -m pytest` from `backend` tests authentication, invalid credentials, refresh rotation/reuse, session revocation, CSRF/origin checks, RBAC, cross-employee access, employee/course uniqueness, tracks/order/snapshots, shared attempts, progress restrictions, completion validation, certificate metadata and upload types/limits, cancellation/history, audit behavior, rate limits, optimistic versions and dashboard calculations.

The default test database is isolated SQLite with foreign keys enabled. These tests do not exercise PostgreSQL row locks, the audit trigger, a real S3 adapter or Redis. Opt-in PostgreSQL tests use `TEST_POSTGRES_URL` and create/drop only a random `tracker_test_*` schema. Use a dedicated test database with schema-creation permission. They test simultaneous assignments, simultaneous refresh and append-only auditing.

```powershell
$env:TEST_POSTGRES_URL = 'postgresql+psycopg://USER:PASSWORD@localhost:5432/learning_test'
../.venv/Scripts/python.exe -m pytest tests/test_postgres_integration.py
```

`npm run typecheck` and `npm run build` validate the separate Next.js routes. A successful build is not browser interaction QA.

The Playwright test automates the manager-to-employee workflow, including certificate download after access-token expiration and the completed mobile dashboard. Test frontend output uses `.next-e2e`, isolated from normal `.next` output. `implementation-status.md` records completed checks and environment limits.

## Manual browser acceptance

1. Bootstrap a manager. Sign in and verify an empty dashboard has no invented data.
2. Create two employees, two courses and a track; reorder its courses.
3. Assign the track to employee A with certificate required. Assign a course from the track directly to A with an earlier deadline. Verify two assignment containers share one attempt for that course.
4. Change the track membership. Existing assignment items must remain unchanged.
5. Sign in as A. Enrol, start progress, upload a PNG/PDF and complete with today’s date. Verify both assignment contexts reflect progress.
6. Try a future completion date, forged MIME and oversized file. Verify errors preserve the current state.
7. Sign in as B. Substitute A’s assignment/attempt/certificate identifiers in API requests. Verify 404 and no leaked data. Manager-only endpoints must return 403.
8. Sign in as manager. Check dashboard counts, course gaps and overdue deadlines. Correct completion with a reason; inspect audit history.
9. Assign the completed course again. Verify a fresh attempt. Reopening the earlier completion must fail while that new attempt is unfinished.
10. Cancel assignments, deactivate an employee and a course. Verify preserved history and blocked new access/assignments.
11. Check keyboard focus, dialogs, mobile navigation and responsive tables at 375px and 1440px. Test token expiry, refresh and logout in the browser.

## PostgreSQL / storage / Redis integration

- Apply `alembic upgrade head`; run `alembic check` to confirm schema parity.
- Test simultaneous assignment creation for the same employee/course: one unfinished attempt, two assignments.
- Test simultaneous refresh with the same token: only one rotation succeeds; reuse revokes the session.
- Verify direct audit UPDATE/DELETE fails through the append-only trigger.
- Upload/download evidence through MinIO, restart the stack and retrieve it again.
- Run two backend workers and verify throttling counters are shared through Redis.

Verification results and environment limits should be reported separately from implementation completeness.
