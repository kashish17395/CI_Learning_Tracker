# API contract

Prefix: `/api/v1`. Authentication uses cookies; unsafe methods require a permitted Origin and `X-CSRF-Token`. Roles: M=MANAGER, E=EMPLOYEE. Owner endpoints return 404 for inaccessible records. No separate Admin role exists.

| Method | Endpoint | Access | Request | Response / purpose |
|---|---|---|---|---|
| POST | /auth/login | Public | email, password | user; HttpOnly access/refresh and readable CSRF cookie |
| POST | /auth/refresh | Refresh session | refresh cookie, CSRF header | rotate access/refresh |
| POST | /auth/logout | Session | CSRF header | 204; revoke session |
| GET | /auth/me | M/E | — | user/profile |
| GET | /employees | M | search, department, active, paging/sort | employee page |
| POST | /employees | M | employee_code, name, email, password, profile fields | 201 employee |
| GET | /employees/{id} | M/owner | — | profile |
| PATCH | /employees/{id} | M | profile fields, is_active | updated profile |
| GET | /employees/{id}/learning | M/owner | learning filters, paging | history |
| GET | /teams | M | search, paging/sort | team page |
| POST | /teams | M | name, optional manager_user_id | 201 team |
| GET | /courses | M/E | search, category, active, paging/sort | catalog page |
| POST | /courses | M | course_code, name, description, category, provider, duration minutes | 201 course |
| GET | /courses/{id} | M/E | — | course |
| PATCH | /courses/{id} | M | course fields, is_active | course |
| GET | /learning-tracks | M/E | search, active, paging/sort | track page |
| POST | /learning-tracks | M | name, description, ordered course_ids | 201 track |
| GET | /learning-tracks/{id} | M/E | — | track and courses |
| PATCH | /learning-tracks/{id} | M | name, description, is_active | track |
| PUT | /learning-tracks/{id}/courses | M | ordered unique course_ids | changed track |
| GET | /assignments | M | employee_id, include_cancelled, learning filters, paging/sort | assignments |
| POST | /assignments | M | employee_id, exactly one course_id/learning_track_id, target_date, policies | 201 assignment and items |
| GET | /assignments/{id} | M/owner | — | assignment/items |
| PATCH | /assignments/{id} | M | version, reason, deadline/policies, cancel | updated assignment |
| GET | /my-learning | M/E own | history, learning filters, paging | own course attempts |
| GET | /my-learning/options | M/E own | — | own course/track filter options |
| GET | /completions/{attempt_id} | M/owner | — | progress and evidence |
| PATCH | /completions/{attempt_id} | M/owner | version, status, completion_date; manager reason | updated attempt |
| GET | /certificates | M/owner | search, employee_id (M), attempt_id, paging/sort | metadata |
| POST | /certificates | M/owner | multipart attempt_id + file | 201 metadata |
| GET | /certificates/{id}/download | M/owner | — | attachment bytes |
| PATCH | /certificates/{id}/revoke | M | reason | revoked metadata |
| GET | /dashboard/me | M/E own | learning filters | personal metrics |
| GET | /dashboard/manager | M | employee_id + learning filters | team/course metrics |
| GET | /dashboard/capability-gaps | M | learning filters, paging | course signals |
| GET | /audit-logs | M | search, actor_user_id, entity_id, action, date_from/to, paging/sort | audit page |

Learning filters: `search`, `status` (including derived OVERDUE), `course_id`, `track_id`, `department`, `target_from`, `target_to`. Lists default to page 1, size 20, maximum size 100. Catalog search is literal and case-insensitive. Catalog sorting uses an explicit whitelist; learning/history lists use newest-first unless assignment sort is provided. Responses: `{items,total,page,page_size}`.

Errors: `{error:{code,message,details,request_id}}`. Validation details omit submitted input. Codes include 401 unauthenticated, 403 forbidden/CSRF, 404 missing/inaccessible, 409 duplicate/stale version, 413 oversized file, 422 validation, 429 throttled. Development OpenAPI includes exact generated schemas.
