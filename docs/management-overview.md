# Learning Space — Phase 1 Learning Tracker

Management overview | 9 October 2026

## Introduction

Learning Space is an internal Learning Tracker that helps managers plan and assign employee learning, monitor progress, and retain completion evidence in one place. Employees can view their learning plan, update permitted progress, and upload certificates. The project covers Phase 1 only.

## Users and access

| Role | Responsibilities |
| --- | --- |
| Manager (also administrator) | Manages employees, courses, tracks and assignments; reviews team progress, certificates and audit history. |
| Employee | Views own learning, deadlines and history; updates allowed progress and provides completion evidence. |

## Features and modules

| Module | What it provides |
| --- | --- |
| Authentication | Email/password login, session renewal, logout and protected access. |
| Employee management | Create, edit, search and activate/deactivate employees; maintain department and team membership. |
| Course management | Maintain course code, description, category, provider and duration; deactivate while preserving history. |
| Learning tracks | Group courses into ordered learning paths; add, remove and reorder courses. |
| Assignments | Assign a course or track to an employee; set deadlines, update policies and cancel assignments. |
| Employee dashboard | Personal learning plan, status summaries, filters, target dates and learning history. |
| Completion tracking | Track Not Started, Enrolled, In Progress and Completed; validate dates and allow manager corrections. |
| Certificates / evidence | Upload and download PDF, PNG or JPEG evidence with ownership, file type and size checks. |
| Manager dashboard | Team progress, completion rates, pending/overdue learning and capability-building signals. |
| Audit logging | Record who changed employee, course, assignment, progress and certificate information. |

Team creation is currently available through the manager API; employee forms support selecting an existing team.

## Typical workflow

Create employee and courses → build a track → assign learning and a target date → update progress → record completion/evidence → review team results.

## Business value and scope

Managers gain a consolidated view of development needs and overdue learning. Employees have clear learning expectations and an accessible completion history.

LMS/iLearn imports, CSV/Excel processing, staging and exception reports are outside Phase 1. The service structure supports future modules without implementing them now.

Verified: 35 backend checks, frontend build/type checks, desktop/mobile workflow tests, Docker startup, database migration and an object-storage upload/download check.

## Architecture

Browser → Next.js interface → FastAPI services → PostgreSQL

FastAPI separates API handling, business rules and database access. Certificate services use private object storage; Redis supports authentication rate limits. Each frontend page has a separate route file.

## Technology stack

| Area | Technology | Purpose |
| --- | --- | --- |
| Web interface | Next.js, React, TypeScript, Tailwind CSS | Pages, forms and responsive dashboards |
| Backend | Python, FastAPI | Business rules and REST APIs |
| Data tools | SQLAlchemy, Pydantic, Alembic | Database access, validation and schema changes |
| Database | PostgreSQL | Employee, learning and audit records |
| File storage | S3-compatible storage; MinIO locally | Private certificate files |
| Security / rate limits | Argon2id, JWT, refresh tokens; Redis | Passwords, sessions and login throttling |
| Local environment | Docker Compose | Runs the application and supporting services |

## Database design

The relational database separates login accounts from employee profiles. Core records include teams, courses, tracks, assignments, individual course attempts, certificate metadata and audit logs. Track assignments capture their course list; overlapping assignments share an unfinished course attempt, avoiding duplicate progress and evidence. Later repeat learning creates a new attempt. Certificate files stay outside PostgreSQL; only metadata and storage references are saved.

## API overview

Base path: /api/v1. APIs use GET, POST, PATCH and PUT with validation, filters, pagination and consistent errors. FastAPI enforces manager permissions and employee ownership.

| API group | Purpose |
| --- | --- |
| /auth | Login, session renewal, logout and current user |
| /employees, /teams | Employee profiles, history and team creation |
| /courses, /learning-tracks | Maintain courses and ordered course groups |
| /assignments, /my-learning | Assign learning and retrieve personal plans |
| /completions | Update course progress and completion |
| /certificates | Evidence upload, listing, download and revocation |
| /dashboard | Personal/team metrics and capability signals |
| /audit-logs | Review recorded administrative changes |

## Security and record integrity

Passwords are hashed; sessions use HttpOnly cookies and CSRF protection. Overdue status is calculated from dates. Historical records are preserved through deactivation/cancellation. Production requires HTTPS and environment-based secrets.
