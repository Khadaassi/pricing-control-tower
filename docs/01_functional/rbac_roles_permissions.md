# RBAC Roles and Permissions

## 1. Objective

This document defines the Role-Based Access Control rules for the Pricing Control Tower MVP.

The goal is to secure access to pricing data, promotion data, KPI analytics and price change workflow actions according to the business role and operational scope of each user.

The backend remains the source of truth for authorization rules. The frontend may adapt the user interface, but it must never be the only security layer.

---

## 2. MVP Roles

The MVP defines four business roles.

| Technical role | Business label | Main responsibility |
|---|---|---|
| STORE_MANAGER | Responsable magasin | Manage pricing and promotions for one store |
| STORE_DIRECTOR | Directeur magasin | Validate pricing decisions for one store |
| COUNTRY_DIRECTOR | Directeur pays | Validate pricing decisions at country level |
| PRICING_ANALYST | Analyste pricing | Analyze pricing performance and anomalies across the full scope |

No ADMIN or VIEWER role is included in the business RBAC MVP.

Technical administration, if needed, is handled outside the business RBAC scope.

---

## 3. User Scope Rules

Each user has a business scope based on their role.

| Role | country_id | store_id | Scope |
|---|---|---|---|
| STORE_MANAGER | Required | Required | One store |
| STORE_DIRECTOR | Required | Required | One store |
| COUNTRY_DIRECTOR | Required | NULL | One country |
| PRICING_ANALYST | NULL allowed | NULL allowed | Global |

Rules:

- A store-level user must be linked to both a country and a store.
- A country-level user must be linked to one country and no specific store.
- A pricing analyst can access global analytical data.
- Inactive users must not be allowed to access protected actions.

---

## 4. Permissions Matrix

| Action | STORE_MANAGER | STORE_DIRECTOR | COUNTRY_DIRECTOR | PRICING_ANALYST |
|---|---:|---:|---:|---:|
| View dashboard | Yes | Yes | Yes | Yes |
| View analytics | Store only | Store only | Country only | Global |
| Create price change request | Yes | Yes | Yes | No |
| Approve price change request | No | Yes | Yes | No |
| Reject price change request | No | Yes | Yes | No |
| Create store promotion | Yes | Yes | No | No |
| Create country promotion | No | No | Yes | No |
| Stop store promotion | Yes | Yes | No | No |
| Stop country promotion | No | No | Yes | No |
| View all anomalies | No | No | No | Yes |
| View scoped anomalies | Yes | Yes | Yes | Yes |
| Modify price directly | No | No | No | No |

---

## 5. Sensitive Actions

The following actions are considered sensitive and must be protected by backend authorization checks:

- approve a price change request;
- reject a price change request;
- apply a price change request;
- create a promotion;
- stop a promotion;
- access data outside the user scope;
- create or update price records directly.

Direct price modification is not allowed in the MVP.

All price changes must go through the price change request workflow.

---

## 6. Pricing Workflow Governance

The Pricing Control Tower MVP follows a controlled pricing workflow.

A user may create a price change request if their role allows it and if the requested product, country or store belongs to their authorized scope.

A price change request may only be approved or rejected by a user with validation rights on the same business scope.

No user is allowed to directly update a product price outside the workflow.

This rule ensures:

- traceability;
- auditability;
- separation of duties;
- reduced operational risk;
- consistency with the price history and audit log.

---

## 7. Backend and Frontend Responsibilities

### Backend responsibilities

The backend is responsible for:

- identifying the current user;
- checking whether the user is active;
- enforcing role-based permissions;
- enforcing country and store scope;
- protecting sensitive endpoints;
- preventing direct price modification;
- keeping audit and history consistent.

### Frontend responsibilities

The frontend is responsible for:

- displaying the appropriate navigation items;
- hiding unavailable actions;
- improving the user experience according to the role;
- displaying authorization errors clearly.

The frontend must never be the only authorization layer.

---

## 8. MVP Limitations

The MVP does not include:

- dynamic permissions;
- advanced group management;
- custom permission assignment per user;
- multi-country users;
- multi-store users;
- a business ADMIN role;
- a read-only VIEWER role.

These features may be considered in a future version if the business case requires them.

---

## 9. Definition of Done

This ticket is complete when:

- the four MVP roles are documented;
- permissions are documented in a clear matrix;
- country and store scope rules are documented;
- sensitive actions are listed;
- the backend/frontend responsibility split is clear;
- MVP limitations are explicit;
- the rules are coherent with the pricing workflow.