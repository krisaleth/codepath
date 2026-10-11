# Course Marketplace — Requirements Specification

| | |
|---|---|
| **Version** | v1 (revised) |
| **Status** | Draft for review |
| **Scope** | MVP |

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [User Roles](#2-user-roles)
3. [Domain Model and State Machines](#3-domain-model-and-state-machines)
4. [Functional Requirements](#4-functional-requirements)
5. [Business Rules](#5-business-rules)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Out of Scope](#7-out-of-scope)
8. [Acceptance Criteria](#8-acceptance-criteria)
9. [Traceability Matrix](#9-traceability-matrix)
10. [Open Questions](#10-open-questions)

---

## 1. Project Overview

A web-based course marketplace where instructors create and publish courses, students purchase courses and learn online, and administrators moderate courses and manage users.

### 1.1 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Node.js, Express.js, TypeScript |
| Database | PostgreSQL |
| ORM | Prisma |
| Validation | Zod |
| Payment | Mock payment for MVP (VNPAY Sandbox optional) |
| API style | REST under `/api/v1`, documented with OpenAPI/Swagger |
| Local setup | Docker Compose (PostgreSQL) + seed script |

### 1.2 General Conventions

- **Currency:** VND. Amounts are stored as non-negative integers (no decimals).
- **Timestamps:** stored in UTC, returned as ISO 8601.
- **Language:** UI in English for MVP (Vietnamese localization is future work).
- **Browsers:** latest two versions of Chrome, Edge, Firefox, and Safari. UI is responsive down to 360 px width.

---

## 2. User Roles

Each account has exactly one primary role: `STUDENT`, `INSTRUCTOR`, or `ADMIN`.

| Role | Capabilities |
|---|---|
| **Guest** | Browse published courses; search and filter; view course details and preview lessons; register and log in. |
| **Student** | All guest actions; purchase published courses; view enrolled courses and order history; access lessons of enrolled courses; track lesson progress. |
| **Instructor** | Create and manage **own** courses, sections, and lessons; mark lessons as preview; submit courses for review; view review results. Can also purchase and learn from **other instructors'** courses. Cannot approve courses or modify courses they do not own. |
| **Admin** | View and manage users; manage categories; review, approve, or reject submitted courses; unpublish courses; view orders and dashboard statistics. |

**[Decision] Instructor as learner:** Instructors may create orders and enroll in courses owned by *other* instructors, but never in their own courses. All ordering and learning rules apply equally to them.

**[Decision] Admin accounts** are created by the seed script only. Public registration accepts `STUDENT` or `INSTRUCTOR` and rejects any other role.

---

## 3. Domain Model and State Machines

### 3.1 Course Lifecycle

```
DRAFT ──submit──► PENDING_REVIEW ──approve──► PUBLISHED
  ▲                    │                          │
  │                    └──reject──► REJECTED      ├──unpublish (admin/instructor)──► ARCHIVED
  │                                    │          │
  └──────────── edit & resubmit ◄──────┘          └──republish (admin)──► PUBLISHED
```

| State | Meaning | Publicly visible | Purchasable | Editable by owner |
|---|---|---|---|---|
| `DRAFT` | Being authored | No | No | Yes |
| `PENDING_REVIEW` | Awaiting admin decision | No | No | No (locked) |
| `PUBLISHED` | Approved and live | Yes | Yes | Yes (see rules below) |
| `REJECTED` | Rejected with a reason | No | No | Yes, then resubmit |
| `ARCHIVED` | Taken offline | No | No | No |

**[Decision] Approval equals publishing.** Approving a course sets its status to `PUBLISHED` directly; there is no separate publish step.

Rules:
- A rejection **requires** a reason (10–1000 characters), which the instructor can view.
- A rejected course may be edited and resubmitted any number of times.
- A course can be submitted only if it has a title, description, category, valid price, and at least one section containing at least one lesson.
- **[Decision]** Edits to a `PUBLISHED` course apply immediately without re-review in the MVP. Admin can unpublish at any time.
- **[Decision]** Courses with at least one enrollment cannot be hard-deleted. They can only be archived. Courses with no enrollments and no paid orders may be deleted while in `DRAFT` or `REJECTED`.
- Archiving a course hides it from discovery and blocks new purchases, but **existing enrolled students keep access**.

### 3.2 Order Lifecycle

```
PENDING ──payment success──► PAID
   │
   ├──payment failure──► FAILED
   ├──student cancels──► CANCELLED
   └──timeout (30 min)──► EXPIRED
```

**[Decision] Order model:** One order contains exactly one course (no cart in MVP).

Rules:
- The order stores a **snapshot** of the course price and currency at creation time. Later price changes do not affect existing orders.
- A user cannot create an order for a course they are already enrolled in.
- A user may have at most **one `PENDING` order per course**. Creating another returns the existing pending order.
- `PENDING` orders expire after 30 minutes. Expired, failed, and cancelled orders never grant enrollment.
- Only `PENDING` orders can transition. `PAID`, `FAILED`, `CANCELLED`, and `EXPIRED` are terminal.
- **[Decision]** Free courses (price = 0) are out of scope. Course price must be greater than 0.

### 3.3 Payment Flow (Mock)

1. Student creates an order (`POST /orders`) → status `PENDING`.
2. Student starts checkout (`POST /payments/mock/checkout`) → server creates a `Payment` record with a unique `transactionRef`.
3. The mock gateway sends a **notification** to the callback endpoint (`POST /payments/mock/callback`) with `transactionRef`, `status`, and `amount`.
4. The server, inside one database transaction:
   - Locks the order row and verifies it is `PENDING`.
   - Verifies the `amount` matches the order's price snapshot.
   - Records the payment outcome and updates the order status.
   - On success, creates the enrollment.
5. **Idempotency:** replaying the same `transactionRef` returns the previously recorded result and creates nothing new.

The mock callback endpoint is registered only when `NODE_ENV` is `development` or `demo` (BR-12). In production it does not exist (returns 404).

### 3.4 Lesson Content

| Type | Content |
|---|---|
| `VIDEO` | External video URL (e.g., hosted video link) and optional duration |
| `TEXT` | Rich text / Markdown body |

Each lesson has an `isPreview` flag, **set by the owning instructor**. Preview lessons do not require separate admin review, but they are part of the course that was reviewed. Content fields (video URL, body) of non-preview lessons are **omitted from API responses** for users without a valid enrollment, so URLs cannot leak.

### 3.5 Progress Calculation

- Progress is stored per `(user, lesson)` as completed / not completed.
- Course progress % = completed lessons ÷ total lessons currently in the course, rounded down.
- When an instructor adds lessons after a student has progressed, the percentage is recalculated against the new total. Removed lessons no longer count.

### 3.6 Categories

Categories are **admin-managed** (create, rename, delete if unused) and seeded with demo data. A course belongs to exactly one category.

---

## 4. Functional Requirements

### 4.1 Authentication and Users

| ID | Requirement |
|---|---|
| FR-01 | Users can register (email, password, display name, role `STUDENT` or `INSTRUCTOR`) and log in. |
| FR-02 | Users can log out and view their own profile. |
| FR-03 | The system enforces role-based permissions on every protected endpoint. |
| FR-04 | Admin can deactivate and reactivate accounts. A deactivated user cannot log in, and existing tokens stop working immediately. |
| FR-22 | Users can edit their own profile (display name, bio, avatar URL) and change their password. |
| FR-23 | Admin can list, search, and filter users by role and status. Admin cannot change roles, delete users, or deactivate themselves or the last remaining active admin. |

### 4.2 Course Discovery

| ID | Requirement |
|---|---|
| FR-05 | Guests can browse published courses. |
| FR-06 | Users can search by title and filter by category and price range, with sorting (newest, price ascending/descending). |
| FR-07 | Users can view course details, instructor information, curriculum (section and lesson titles), and preview lessons. |

### 4.3 Course Management

| ID | Requirement |
|---|---|
| FR-08 | Instructors can create, edit, and delete (per §3.1) their own courses. |
| FR-09 | Instructors can create, edit, reorder, and remove sections and lessons in their own courses, and mark lessons as preview. |
| FR-10 | Instructors can submit a `DRAFT` or `REJECTED` course for review. |
| FR-11 | Admin can approve or reject a `PENDING_REVIEW` course (rejection requires a reason). |
| FR-24 | Instructors can list their courses and see status and rejection reasons. |
| FR-25 | Admin can list pending courses, filtered by status. Admin can unpublish a published course. |
| FR-26 | Admin can create, rename, and delete unused categories. |

### 4.4 Orders and Payments

| ID | Requirement |
|---|---|
| FR-12 | Authenticated learners (students and instructors, per §2) can create an order for a published course they do not own and are not enrolled in. |
| FR-13 | Learners can complete a mock payment in demo/development environments. |
| FR-14 | The system records every payment outcome and updates order status accordingly. |
| FR-15 | A successful, valid payment grants course enrollment exactly once. |
| FR-16 | Learners can view their own orders and enrolled courses. |
| FR-27 | Learners can cancel their own `PENDING` orders. The system expires stale pending orders after 30 minutes. |

### 4.5 Learning

| ID | Requirement |
|---|---|
| FR-17 | Enrolled users can access all lessons of their enrolled courses. |
| FR-18 | Users without enrollment can access preview lessons only. |
| FR-19 | Enrolled users can mark lessons complete or incomplete and view course progress (§3.5). |

### 4.6 Administration

| ID | Requirement |
|---|---|
| FR-20 | Admin can view users, courses, and orders (paginated, filterable by status). |
| FR-21 | Admin can view dashboard statistics: total users (by role), courses (by status), orders (by status), and total paid revenue. |

---

## 5. Business Rules

### Courses and Access

| ID | Rule |
|---|---|
| BR-01 | Only `PUBLISHED` courses are publicly discoverable. |
| BR-02 | Instructors can modify only courses they own. |
| BR-03 | Only admins can approve or reject courses. |
| BR-08 | An instructor cannot approve their own course (admins and instructors are separate roles; the check is also enforced on course ownership). |
| BR-09 | Full lesson content requires a valid enrollment, unless the lesson is a preview lesson of a `PUBLISHED` course. Authorization is checked by lesson ID on the server. |
| BR-13 | Enrollment survives course archiving; archived courses remain accessible to enrolled users. |
| BR-14 | An instructor cannot purchase or enroll in their own course. |

### Orders and Payments

| ID | Rule |
|---|---|
| BR-04 | Only `PUBLISHED` courses can be purchased. |
| BR-05 | The backend calculates prices from trusted database values. Any client-supplied price or amount is ignored. |
| BR-06 | Enrollment is granted only after valid payment confirmation (matching amount, `PENDING` order, success status). |
| BR-07 | Each user has at most one enrollment per course (enforced by a unique database constraint). |
| BR-10 | Repeated payment notifications must not create duplicate enrollments or payments (enforced by a unique `transactionRef`). |
| BR-11 | Users can access only their own orders and learning progress. |
| BR-12 | Mock payment exists only in development/demo environments and never represents real money collection. |
| BR-15 | The order price is a snapshot taken at order creation. |

---

## 6. Non-Functional Requirements

### Security

| ID | Requirement |
|---|---|
| NFR-01 | Passwords are hashed with bcrypt (cost ≥ 10) or argon2. Minimum password length is 8 characters. |
| NFR-02 | Protected endpoints enforce authentication and authorization on the server. |
| NFR-03 | All API inputs are validated with Zod before processing. |
| NFR-04 | Secrets live in environment variables and are excluded from version control. A `.env.example` is provided. |
| NFR-11 | **Auth tokens:** short-lived JWT access token (≈15 min) plus a refresh token in an `httpOnly` cookie. Logout revokes the refresh token. The server checks the user's `isActive` flag on each authenticated request. |
| NFR-12 | Login and registration endpoints are rate-limited. CORS is restricted to the configured frontend origin. Security headers are set (e.g., Helmet). |
| NFR-13 | If VNPAY Sandbox is implemented, callbacks must be signature-verified and the amount must be verified against the order. |

### Data and Reliability

| ID | Requirement |
|---|---|
| NFR-05 | Database changes are managed through versioned Prisma migrations. |
| NFR-06 | Payment confirmation, enrollment creation, and order status changes run in a single database transaction with row locking to handle concurrent callbacks. |
| NFR-14 | Integrity constraints: unique `(userId, courseId)` on enrollments; unique `transactionRef` on payments; foreign keys on all relations; non-negative amounts. |

### API Quality

| ID | Requirement |
|---|---|
| NFR-07 | List endpoints are paginated: default page size 10, maximum 50, with `page` and `limit` parameters and total count in the response. |
| NFR-08 | Errors use one consistent format: `{ "error": { "code": "COURSE_NOT_FOUND", "message": "...", "details": [...] } }` with appropriate HTTP status codes. |
| NFR-09 | An OpenAPI/Swagger document is served at `/api/docs`. |

### Delivery

| ID | Requirement |
|---|---|
| NFR-10 | The project runs locally using documented steps, Docker Compose for PostgreSQL, and seeded demo data (1 admin, 2 instructors, 2 students, categories, and courses in several statuses). |
| NFR-15 | **Testing:** unit and integration tests cover BR-05, BR-06, BR-07, BR-10, BR-09, and role permissions. Tests run with a single documented command. |
| NFR-16 | The server logs requests and errors in a structured format. Sensitive data (passwords, tokens) is never logged. |

---

## 7. Out of Scope

The following are excluded from the MVP, and no one should assume they exist:

- Live streaming and video conferencing
- Real-money payment processing
- Instructor revenue sharing and payouts
- Complex refunds and dispute management
- AI-based course recommendations
- Native mobile applications
- Advanced digital rights management
- Shopping cart, coupons, and wishlist
- Ratings and reviews
- Certificates
- Email notifications, email verification, and password reset
- Free courses
- File uploads for lesson content (external URLs only)
- Multiple roles per account

---

## 8. Acceptance Criteria

### Access and Discovery

| ID | Criterion |
|---|---|
| AC-01 | A guest can browse published courses but cannot access non-preview lessons. |
| AC-02 | Courses that are not `PUBLISHED` do not appear in public listing, search, or detail endpoints. |
| AC-03 | Search, filter, sort, and pagination return correct results and respect the page-size limit. |

### Course Management

| ID | Criterion |
|---|---|
| AC-04 | An instructor can create a course and submit it for review. |
| AC-05 | An instructor cannot edit another instructor's course (403). |
| AC-06 | An admin can approve a pending course (it becomes `PUBLISHED`) or reject it with a reason, which the instructor can see. |
| AC-07 | An instructor cannot approve their own course. |
| AC-08 | A course with no lessons cannot be submitted for review. |

### Orders and Payments

| ID | Criterion |
|---|---|
| AC-09 | A learner can create an order for a published course; a non-published course cannot be purchased. |
| AC-10 | A tampered price or amount in a client request is ignored; the server uses the stored course price. |
| AC-11 | A failed, expired, or unconfirmed payment does not grant enrollment. |
| AC-12 | A successful mock payment grants enrollment exactly once. |
| AC-13 | Replaying the same payment notification creates one enrollment, one payment record, and no error. |
| AC-14 | A callback whose amount does not match the order is rejected and grants nothing. |
| AC-15 | A user cannot order a course they are already enrolled in, nor an instructor their own course. |
| AC-16 | Mock payment endpoints are unavailable when the environment is production. |

### Learning and Privacy

| ID | Criterion |
|---|---|
| AC-17 | An enrolled user can access full lessons and save learning progress. |
| AC-18 | A non-enrolled user cannot access full lesson content by guessing a lesson ID or URL. |
| AC-19 | Users cannot access other users' orders or progress. |
| AC-20 | Archiving a course does not remove access for enrolled users. |

### Accounts and Administration

| ID | Criterion |
|---|---|
| AC-21 | A deactivated user cannot log in, and their existing tokens are rejected. |
| AC-22 | Registration cannot create an admin account. |
| AC-23 | An admin cannot deactivate themselves or the last active admin. |
| AC-24 | Admin dashboard statistics match the database counts. |

### Delivery

| ID | Criterion |
|---|---|
| AC-25 | The project can be installed and demonstrated from the README instructions alone, using seeded data. |
| AC-26 | The automated test suite passes with one documented command. |

---

## 9. Traceability Matrix

| Acceptance Criterion | Functional Req. | Business Rules / NFRs |
|---|---|---|
| AC-01 | FR-05, FR-18 | BR-01, BR-09 |
| AC-02 | FR-05, FR-07 | BR-01 |
| AC-03 | FR-06 | NFR-07 |
| AC-04 | FR-08, FR-09, FR-10 | BR-02 |
| AC-05 | FR-08, FR-09 | BR-02, NFR-02 |
| AC-06 | FR-11, FR-24 | BR-03 |
| AC-07 | FR-11 | BR-03, BR-08 |
| AC-08 | FR-10 | §3.1 |
| AC-09 | FR-12 | BR-04 |
| AC-10 | FR-12 | BR-05, BR-15 |
| AC-11 | FR-14, FR-27 | BR-06 |
| AC-12 | FR-13, FR-15 | BR-06, BR-07, NFR-06 |
| AC-13 | FR-15 | BR-10, NFR-14 |
| AC-14 | FR-14 | BR-06, NFR-13 |
| AC-15 | FR-12 | BR-07, BR-14 |
| AC-16 | FR-13 | BR-12 |
| AC-17 | FR-17, FR-19 | BR-09 |
| AC-18 | FR-17, FR-18 | BR-09, NFR-02 |
| AC-19 | FR-16, FR-19 | BR-11 |
| AC-20 | FR-17 | BR-13 |
| AC-21 | FR-04 | NFR-11 |
| AC-22 | FR-01, FR-03 | NFR-02 |
| AC-23 | FR-23 | — |
| AC-24 | FR-21 | — |
| AC-25 | — | NFR-09, NFR-10 |
| AC-26 | — | NFR-15 |

---

## 10. Open Questions

These need a product decision, but the defaults above let development proceed.

1. Should edits to a published course ever require re-review (currently: no)?
2. Is a 30-minute order expiry appropriate, and should expiry run as a scheduled job or lazily on access?
3. Should the UI language be Vietnamese rather than English?
4. Should free courses be added after the MVP, and should they bypass payment?
5. Is VNPAY Sandbox in scope for the demo, or only the mock?