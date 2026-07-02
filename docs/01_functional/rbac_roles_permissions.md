# RBAC Roles and Permissions

## 1. Objective

This document defines the Role-Based Access Control rules for the Pricing Control Tower MVP.

The goal is to secure access to pricing data, promotion data, KPI analytics and price change workflow actions according to:

* the user identity;
* the business roles assigned to the user;
* the permissions attached to these roles;
* the country or store scope attached to the user.

The backend remains the source of truth for authorization rules. The frontend may adapt the user interface, but it must never be the only security layer.

---

## 2. Agile update: RBAC model evolution

### 2.1 Initial decision

The initial Sprint 8 RBAC model was based on a single role stored directly in `pct_core.user_account`.

Initial model:

```text
user_account.role
```

This first decision was intentionally simple and allowed the project to quickly define a first MVP authorization model based on four business roles:

* `STORE_MANAGER`
* `STORE_DIRECTOR`
* `COUNTRY_DIRECTOR`
* `PRICING_ANALYST`

The initial model also stored the user scope directly in `user_account` through:

* `country_id`
* `store_id`

### 2.2 Limitation identified

After review, the single-role model was considered too rigid.

The main limitation is that a user can only have one role, while a real business user may need several responsibilities.

Example:

```text
A user may need to view analytics globally while also being allowed to manage promotions for a specific store.
```

The initial model also mixed three concepts:

| Concept    | Meaning                                           |
| ---------- | ------------------------------------------------- |
| Role       | Business responsibility                           |
| Permission | Action the user is allowed to perform             |
| Scope      | Country or store perimeter where the user can act |

Because of this, adding or changing permissions would require modifying role logic directly instead of assigning permissions through a clear RBAC structure.

### 2.3 New decision

The project now moves to a more explicit RBAC model:

```text
User → Role → Permission
```

This means:

* a user can have one or more roles;
* a role can be assigned to several users;
* a role contains one or more permissions;
* a permission can be attached to several roles;
* permissions are assigned through roles only;
* the country/store scope remains stored in `user_account`.

This change keeps the MVP simple while making the authorization model more realistic, maintainable and defensible for the certification.

---

## 3. Target RBAC model

### 3.1 user_account

`pct_core.user_account` remains the business user table.

It stores the user identity and data scope.

Target fields:

| Field      | Purpose                                                         |
| ---------- | --------------------------------------------------------------- |
| id         | User identifier                                                 |
| email      | Business email, used to link Django authentication and API user |
| full_name  | Display name                                                    |
| active     | Whether the user is active                                      |
| country_id | Country scope, nullable                                         |
| store_id   | Store scope, nullable                                           |

The previously added `role` column in `user_account` is now considered obsolete and will be removed by a corrective migration.

### 3.2 role

A role represents a business responsibility.

Target table:

```text
pct_core.role
```

Expected fields:

| Field       | Purpose                  |
| ----------- | ------------------------ |
| id          | Role identifier          |
| code        | Unique technical code    |
| name        | Human-readable role name |
| description | Business description     |

MVP roles remain:

| Role code        | Business label      | Main responsibility                                             |
| ---------------- | ------------------- | --------------------------------------------------------------- |
| STORE_MANAGER    | Responsable magasin | Manage pricing and promotions for one store                     |
| STORE_DIRECTOR   | Directeur magasin   | Validate pricing decisions for one store                        |
| COUNTRY_DIRECTOR | Directeur pays      | Validate pricing decisions at country level                     |
| PRICING_ANALYST  | Analyste pricing    | Analyze pricing performance and anomalies across the full scope |

### 3.3 permission

A permission represents an allowed action.

Target table:

```text
pct_core.permission
```

Expected fields:

| Field       | Purpose                        |
| ----------- | ------------------------------ |
| id          | Permission identifier          |
| code        | Unique technical code          |
| name        | Human-readable permission name |
| description | Functional description         |

MVP permissions:

| Permission code          | Description                              |
| ------------------------ | ---------------------------------------- |
| VIEW_DASHBOARD           | View the main dashboard                  |
| VIEW_ANALYTICS           | View analytics and KPI data              |
| VIEW_PRICES              | View price data                          |
| VIEW_PROMOTIONS          | View promotion data                      |
| VIEW_PRICE_REQUESTS      | View price change requests               |
| CREATE_PRICE_REQUEST     | Create a price change request            |
| APPROVE_PRICE_REQUEST    | Approve a price change request           |
| REJECT_PRICE_REQUEST     | Reject a price change request            |
| APPLY_PRICE_REQUEST      | Apply an approved price change request   |
| CREATE_STORE_PROMOTION   | Create a store-level promotion           |
| CREATE_COUNTRY_PROMOTION | Create a country-level promotion         |
| STOP_STORE_PROMOTION     | Stop a store-level promotion             |
| STOP_COUNTRY_PROMOTION   | Stop a country-level promotion           |
| VIEW_SCOPED_ANOMALIES    | View anomalies within the user scope     |
| VIEW_ALL_ANOMALIES       | View all anomalies                       |
| VIEW_PRICE_HISTORY       | View price history and audit information |

Direct price modification is not part of the MVP permissions.

All price changes must go through the price change request workflow.

### 3.4 user_role

`pct_core.user_role` links users and roles.

Rules:

* one user can have several roles;
* one role can be assigned to several users;
* duplicate user/role associations are not allowed.

### 3.5 role_permission

`pct_core.role_permission` links roles and permissions.

Rules:

* one role can have several permissions;
* one permission can be assigned to several roles;
* duplicate role/permission associations are not allowed.

---

## 4. Role-permission matrix

| Permission               | STORE_MANAGER | STORE_DIRECTOR | COUNTRY_DIRECTOR | PRICING_ANALYST |
| ------------------------ | ------------: | -------------: | ---------------: | --------------: |
| VIEW_DASHBOARD           |           Yes |            Yes |              Yes |             Yes |
| VIEW_ANALYTICS           |           Yes |            Yes |              Yes |             Yes |
| VIEW_PRICES              |           Yes |            Yes |              Yes |             Yes |
| VIEW_PROMOTIONS          |           Yes |            Yes |              Yes |             Yes |
| VIEW_PRICE_REQUESTS      |           Yes |            Yes |              Yes |             Yes |
| CREATE_PRICE_REQUEST     |           Yes |            Yes |              Yes |              No |
| APPROVE_PRICE_REQUEST    |            No |            Yes |              Yes |              No |
| REJECT_PRICE_REQUEST     |            No |            Yes |              Yes |              No |
| APPLY_PRICE_REQUEST      |            No |             No |               No |              No |
| CREATE_STORE_PROMOTION   |           Yes |            Yes |               No |              No |
| CREATE_COUNTRY_PROMOTION |            No |             No |              Yes |              No |
| STOP_STORE_PROMOTION     |           Yes |            Yes |               No |              No |
| STOP_COUNTRY_PROMOTION   |            No |             No |              Yes |              No |
| VIEW_SCOPED_ANOMALIES    |           Yes |            Yes |              Yes |             Yes |
| VIEW_ALL_ANOMALIES       |            No |             No |               No |             Yes |
| VIEW_PRICE_HISTORY       |           Yes |            Yes |              Yes |             Yes |

`APPLY_PRICE_REQUEST` is intentionally not assigned to any MVP role by default.

This keeps price application controlled and prevents direct operational price changes without a dedicated backend decision.

---

## 5. User scope rules

The user scope is still stored in `pct_core.user_account`.

The scope defines where the user can act or view data.

| Scope type | country_id | store_id | Meaning                               |
| ---------- | ---------: | -------: | ------------------------------------- |
| Global     |       NULL |     NULL | Global access if permissions allow it |
| Country    |   Required |     NULL | Access limited to one country         |
| Store      |   Required | Required | Access limited to one store           |

Rules:

* A user with a store scope must have both `country_id` and `store_id`.
* A user with a country scope must have `country_id` and no `store_id`.
* A global user has no `country_id` and no `store_id`.
* A user cannot have a `store_id` without a `country_id`.
* Inactive users must not be allowed to access protected actions.

The backend must always check both:

```text
permission + scope
```

Example:

```text
A user with APPROVE_PRICE_REQUEST can approve a request only if the request belongs to the user's authorized scope.
```

---

## 6. Sensitive actions

The following actions are considered sensitive and must be protected by backend authorization checks:

* approve a price change request;
* reject a price change request;
* apply a price change request;
* create a store promotion;
* create a country promotion;
* stop a store promotion;
* stop a country promotion;
* access data outside the user scope;
* view all anomalies;
* access price history and audit information;
* create or update price records directly.

Direct price modification is not allowed in the MVP.

All price changes must go through the price change request workflow.

---

## 7. Pricing workflow governance

The Pricing Control Tower MVP follows a controlled pricing workflow.

A user may create a price change request only if:

* the user is active;
* the user has the required permission;
* the requested product, country or store belongs to the user’s authorized scope.

A price change request may only be approved or rejected by a user with the required permission on the same business scope.

No user is allowed to directly update a product price outside the workflow.

This rule ensures:

* traceability;
* auditability;
* separation of duties;
* reduced operational risk;
* consistency with the price history and audit log.

---

## 8. Backend and frontend responsibilities

### Backend responsibilities

The backend is responsible for:

* identifying the current business user;
* checking whether the user is active;
* retrieving the user roles;
* resolving permissions through roles;
* enforcing permission-based access;
* enforcing country and store scope;
* protecting sensitive endpoints;
* preventing direct price modification;
* keeping audit and history consistent.

### Frontend responsibilities

The frontend is responsible for:

* requiring a logged-in Django session;
* displaying the connected user;
* displaying the appropriate navigation items;
* hiding unavailable actions when possible;
* improving the user experience;
* displaying authorization errors clearly.

The frontend must never be the only authorization layer.

---

## 9. MVP limitations

The MVP does not include:

* direct permission assignment to users;
* dynamic permission management from the UI;
* role inheritance;
* advanced group management;
* multi-country users;
* multi-store users;
* a business ADMIN role;
* a read-only VIEWER role;
* direct price modification.

These features may be considered in a future version if the business case requires them.

---

## 10. Role summaries for the chatbot

These summaries are provided so that the AI chatbot can answer questions about roles
and permissions without requiring backend access.

### Store Manager (STORE_MANAGER)

A Store Manager is limited to one assigned store.

Main permissions:
- View dashboard data for their store.
- View products and prices within their scope.
- View promotions linked to their store.
- Create and stop store-level promotions.
- Create price change requests when authorized.
- View price change requests and price history within their store scope.
- View anomalies within their store scope.

Limitations:
- Cannot access another store.
- Cannot approve or reject price change requests.
- Cannot make country-level pricing decisions.
- Cannot bypass approval workflows.

### Store Director (STORE_DIRECTOR)

A Store Director supervises one store and validates pricing decisions for it.

Main permissions:
- All Store Manager permissions.
- Approve and reject price change requests within their store scope.

Limitations:
- Cannot access another store.
- Cannot make country-level pricing decisions.
- Cannot apply a price change request directly (this action is not assigned in the MVP).

### Country Director (COUNTRY_DIRECTOR)

A Country Director manages pricing decisions at the country level.

Main permissions:
- View dashboard, analytics, prices, promotions across their country scope.
- Create and stop country-level promotions.
- Approve and reject price change requests across their country scope.
- View all anomalies and price history within their country scope.

Limitations:
- Cannot create store-level promotions directly.
- Cannot apply a price change request directly (this action is not assigned in the MVP).

### Pricing Analyst (PRICING_ANALYST)

A Pricing Analyst monitors performance across the full scope.

Main permissions:
- View dashboard, analytics, prices, promotions, price change requests.
- View all anomalies (global scope).
- View price history.

Limitations:
- Cannot create price change requests.
- Cannot approve or reject price change requests.
- Cannot create or stop promotions.
- Read-only access to pricing workflow.

---

## 11. Who can change a price?

Direct price modification is not allowed in the Pricing Control Tower MVP.

All price changes must follow the price change request workflow:

1. A user with the CREATE_PRICE_REQUEST permission submits a price change request.
2. A user with the APPROVE_PRICE_REQUEST permission reviews and approves or rejects it.
3. The application applies the change if approved.

Roles that can submit a price change request: STORE_MANAGER, STORE_DIRECTOR, COUNTRY_DIRECTOR.

Roles that can approve or reject a price change request: STORE_DIRECTOR, COUNTRY_DIRECTOR.

The APPLY_PRICE_REQUEST permission is intentionally not assigned to any MVP role.

---

## 12. What can the chatbot do about RBAC?

The chatbot can explain:
- the list of RBAC roles defined in the MVP;
- the permissions attached to each role;
- the country and store scope rules;
- who can create, approve, reject or view price change requests;
- why a user cannot perform an action based on their role;
- what "STORE_MANAGER", "STORE_DIRECTOR", "COUNTRY_DIRECTOR" and "PRICING_ANALYST" mean.

The chatbot cannot:
- grant or revoke permissions;
- change or assign user roles;
- approve price change requests;
- bypass backend access control;
- tell a user their exact current role (the chatbot does not know the authenticated user's role).

If a user asks "what are my permissions?", the chatbot should explain that it can describe
role-based permissions but needs to know the user's assigned role to answer precisely.
The user should check their profile or contact an administrator for their exact role.

---

## 13. Definition of Done

This documentation is complete when:

* the initial single-role model is documented;
* the reason for changing direction is explained;
* the new User → Role → Permission model is documented;
* the MVP roles are defined;
* the MVP permissions are defined;
* the role-permission matrix is documented;
* country and store scope rules are explicit;
* sensitive actions are listed;
* backend and frontend responsibilities are clear;
* MVP limitations are explicit.
