# Authentication and RBAC Architecture

## 1. Objective

This document describes the authentication and Role-Based Access Control architecture implemented in the Pricing Control Tower MVP.

The objective of Sprint 8 is to secure the application by introducing:

* user authentication through the Django frontend;
* business user identification in the FastAPI backend;
* a Role-Based Access Control model based on roles and permissions;
* backend protection for sensitive business actions;
* automatic data filtering according to the user business scope;
* frontend adaptation according to the permissions returned by the backend;
* traceability of user actions in audit and history tables.

The implementation remains MVP-oriented, simple and defendable for the RNCP certification project.

---

## 2. Architecture overview

The Pricing Control Tower application is split into two main application layers:

| Layer                 | Responsibility                                              |
| --------------------- | ----------------------------------------------------------- |
| Django frontend       | User session authentication, pages, forms, user interface   |
| FastAPI backend       | Business rules, data access, authorization, audit trail     |
| PostgreSQL database   | Business data, users, roles, permissions, audit and history |
| dbt / analytics layer | Analytical models and KPI data                              |

The RBAC architecture follows this principle:

```text
Django authenticates the user.
FastAPI authorizes the business action.
PostgreSQL stores users, roles, permissions and audit data.
```

The frontend may hide or display actions to improve user experience, but it is never the only security layer.

The backend remains the source of truth for:

* current business user identification;
* permission checks;
* scope filtering;
* action authorization;
* audit trail consistency.

---

## 3. Authentication flow

Authentication is handled by Django using the built-in session authentication system.

The user logs in through the Django frontend:

```text
User
→ Django login page
→ Django session
→ Authenticated frontend access
```

Once connected, the Django user is available through:

```python
request.user
request.user.email
```

The email is used as the link between the Django authentication user and the business user stored in PostgreSQL.

The authentication flow is:

```text
Django auth_user.email
→ X-User-Email header
→ FastAPI
→ pct_core.user_account.email
→ business user resolved
```

This means that Django is responsible for user login, while FastAPI is responsible for business authorization.

---

## 4. Business identity model

The project uses two user representations.

| User representation     | Location                   | Responsibility                            |
| ----------------------- | -------------------------- | ----------------------------------------- |
| Django `auth_user`      | Django database            | Login, password, session                  |
| `pct_core.user_account` | PostgreSQL business schema | Business identity, scope, audit reference |

The link between both systems is the email address:

```text
auth_user.email = pct_core.user_account.email
```

The `pct_core.user_account` table contains:

| Column       | Purpose                                     |
| ------------ | ------------------------------------------- |
| `id`         | Business user identifier                    |
| `email`      | Link with Django authenticated user         |
| `full_name`  | Display name                                |
| `active`     | Whether the business user is allowed to act |
| `country_id` | Country scope, when applicable              |
| `store_id`   | Store scope, when applicable                |

The `user_account` table no longer stores a single role directly. Roles are now managed through a many-to-many relationship.

---

## 5. RBAC data model

The RBAC model follows a classic User → Role → Permission structure.

```text
user_account
    ↓
user_role
    ↓
role
    ↓
role_permission
    ↓
permission
```

### Tables

| Table                      | Purpose                                   |
| -------------------------- | ----------------------------------------- |
| `pct_core.user_account`    | Business users and their scope            |
| `pct_core.role`            | Business roles                            |
| `pct_core.permission`      | Atomic permissions                        |
| `pct_core.user_role`       | Association between users and roles       |
| `pct_core.role_permission` | Association between roles and permissions |

### Design decision

A user can have multiple roles.

A role can contain multiple permissions.

Permissions are not assigned directly to users in the MVP. They are only assigned through roles.

This keeps the model simple, traceable and extensible.

---

## 6. MVP roles

The MVP defines four business roles.

| Technical role     | Business label      | Main responsibility                                      |
| ------------------ | ------------------- | -------------------------------------------------------- |
| `STORE_MANAGER`    | Responsable magasin | Manage price requests and store promotions for one store |
| `STORE_DIRECTOR`   | Directeur magasin   | Validate pricing decisions for one store                 |
| `COUNTRY_DIRECTOR` | Directeur pays      | Validate pricing decisions at country level              |
| `PRICING_ANALYST`  | Analyste pricing    | Analyze pricing performance and anomalies globally       |

No business `ADMIN` or `VIEWER` role is included in the MVP.

Technical administration is considered outside the business RBAC scope.

---

## 7. MVP permissions

The MVP permissions are defined as atomic action rights.

| Permission                 | Description                          |
| -------------------------- | ------------------------------------ |
| `VIEW_DASHBOARD`           | Access dashboard pages               |
| `VIEW_ANALYTICS`           | Access analytical data               |
| `VIEW_PRICES`              | View price data                      |
| `VIEW_PROMOTIONS`          | View promotion data                  |
| `VIEW_PRICE_REQUESTS`      | View price change requests           |
| `CREATE_PRICE_REQUEST`     | Create a price change request        |
| `APPROVE_PRICE_REQUEST`    | Approve a price change request       |
| `REJECT_PRICE_REQUEST`     | Reject a price change request        |
| `APPLY_PRICE_REQUEST`      | Apply a price change request         |
| `CREATE_STORE_PROMOTION`   | Create a store-level promotion       |
| `CREATE_COUNTRY_PROMOTION` | Create a country-level promotion     |
| `STOP_STORE_PROMOTION`     | Stop a store-level promotion         |
| `STOP_COUNTRY_PROMOTION`   | Stop a country-level promotion       |
| `VIEW_SCOPED_ANOMALIES`    | View anomalies within the user scope |
| `VIEW_ALL_ANOMALIES`       | View all anomalies                   |
| `VIEW_PRICE_HISTORY`       | View price history                   |

`APPLY_PRICE_REQUEST` exists in the permission catalog but is not assigned to any MVP role. In the MVP workflow, approving a request automatically applies the price change.

---

## 8. Role-permission matrix

| Permission                 | STORE_MANAGER | STORE_DIRECTOR | COUNTRY_DIRECTOR | PRICING_ANALYST |
| -------------------------- | ------------: | -------------: | ---------------: | --------------: |
| `VIEW_DASHBOARD`           |           Yes |            Yes |              Yes |             Yes |
| `VIEW_ANALYTICS`           |           Yes |            Yes |              Yes |             Yes |
| `VIEW_PRICES`              |           Yes |            Yes |              Yes |             Yes |
| `VIEW_PROMOTIONS`          |           Yes |            Yes |              Yes |             Yes |
| `VIEW_PRICE_REQUESTS`      |           Yes |            Yes |              Yes |             Yes |
| `CREATE_PRICE_REQUEST`     |           Yes |            Yes |              Yes |              No |
| `APPROVE_PRICE_REQUEST`    |            No |            Yes |              Yes |              No |
| `REJECT_PRICE_REQUEST`     |            No |            Yes |              Yes |              No |
| `APPLY_PRICE_REQUEST`      |            No |             No |               No |              No |
| `CREATE_STORE_PROMOTION`   |           Yes |            Yes |               No |              No |
| `CREATE_COUNTRY_PROMOTION` |            No |             No |              Yes |              No |
| `STOP_STORE_PROMOTION`     |           Yes |            Yes |               No |              No |
| `STOP_COUNTRY_PROMOTION`   |            No |             No |              Yes |              No |
| `VIEW_SCOPED_ANOMALIES`    |           Yes |            Yes |              Yes |             Yes |
| `VIEW_ALL_ANOMALIES`       |            No |             No |               No |             Yes |
| `VIEW_PRICE_HISTORY`       |           Yes |            Yes |              Yes |             Yes |

---

## 9. User scope model

The user scope is stored in `pct_core.user_account`.

Permissions define what the user can do.

Scope defines which data the user can see.

| Scope type    | `country_id` | `store_id` | Meaning                                  |
| ------------- | -----------: | ---------: | ---------------------------------------- |
| Global scope  |       `NULL` |     `NULL` | User can access all countries and stores |
| Country scope |     Required |     `NULL` | User can access one country              |
| Store scope   |     Required |   Required | User can access one store                |

### MVP scope examples

| User                         | Role               | Scope                 |
| ---------------------------- | ------------------ | --------------------- |
| `analyst@pct.local`          | `PRICING_ANALYST`  | Global                |
| `store.manager@pct.local`    | `STORE_MANAGER`    | France / Lille Centre |
| `store.director@pct.local`   | `STORE_DIRECTOR`   | France / Lille Centre |
| `country.director@pct.local` | `COUNTRY_DIRECTOR` | France                |

---

## 10. Scope filtering rules

The backend automatically applies visibility rules according to the current business user.

### Global user

A global user has:

```text
country_id = NULL
store_id = NULL
```

A global user can access all data.

### Country user

A country user has:

```text
country_id = not NULL
store_id = NULL
```

A country user can access only data from their country.

Example:

```text
country.director@pct.local
→ country_id = 1
→ can see France data only
```

If the user requests another country explicitly, the backend returns:

```text
403 Forbidden
```

### Store user

A store user has:

```text
country_id = not NULL
store_id = not NULL
```

A store user can access:

* their own store data;
* country-level data that applies to their country when `store_id IS NULL`.

Example:

```text
store.manager@pct.local
→ country_id = 1
→ store_id = 1
→ can see Lille Centre data
→ can also see France-level applicable data when relevant
```

If the user requests another store explicitly, the backend returns:

```text
403 Forbidden
```

---

## 11. Endpoints protected by scope

The following read endpoints are scoped according to the current business user:

| Endpoint                     | Scope behavior                          |
| ---------------------------- | --------------------------------------- |
| `GET /prices`                | Filter by country/store scope           |
| `GET /promotions`            | Filter by country/store scope           |
| `GET /kpis`                  | Filter analytics by allowed stores      |
| `GET /anomalies`             | Filter anomalies by allowed stores      |
| `GET /price-change-requests` | Filter requests by country/store scope  |
| `GET /analytics/sales`       | Filter analytical sales data            |
| `GET /price-history`         | Filter historical data where applicable |

The `/products`, `/countries` and `/stores` endpoints are treated as reference data in the MVP. They remain accessible as catalog data unless a specific business need requires stricter filtering later.

---

## 12. Current user endpoint

FastAPI exposes a `/me` endpoint.

The endpoint returns:

* business user id;
* email;
* full name;
* active status;
* country scope;
* store scope;
* roles;
* permissions.

Example response:

```json
{
  "id": 3,
  "email": "store.manager@pct.local",
  "full_name": "Store Manager",
  "active": true,
  "country_id": 1,
  "store_id": 1,
  "roles": ["STORE_MANAGER"],
  "permissions": [
    "CREATE_PRICE_REQUEST",
    "CREATE_STORE_PROMOTION",
    "STOP_STORE_PROMOTION",
    "VIEW_DASHBOARD",
    "VIEW_PRICES"
  ]
}
```

The Django frontend uses this endpoint to adapt the UI.

---

## 13. Backend authorization

Sensitive actions are protected by backend permission checks.

The backend checks permissions using the current business user resolved from `X-User-Email`.

| Endpoint                                                  | Required permission        |
| --------------------------------------------------------- | -------------------------- |
| `POST /price-change-requests`                             | `CREATE_PRICE_REQUEST`     |
| `POST /price-change-requests/{id}/approve`                | `APPROVE_PRICE_REQUEST`    |
| `POST /price-change-requests/{id}/reject`                 | `REJECT_PRICE_REQUEST`     |
| `POST /promotions` with `store_id`                        | `CREATE_STORE_PROMOTION`   |
| `POST /promotions` without `store_id`                     | `CREATE_COUNTRY_PROMOTION` |
| `PATCH /promotions/{id}/deactivate` for store promotion   | `STOP_STORE_PROMOTION`     |
| `PATCH /promotions/{id}/deactivate` for country promotion | `STOP_COUNTRY_PROMOTION`   |

If the permission is missing, FastAPI returns:

```text
403 Forbidden
```

Example error:

```json
{
  "detail": "Permission denied: APPROVE_PRICE_REQUEST is required"
}
```

---

## 14. Frontend adaptation

The Django frontend calls `/me` through a context processor.

The context processor exposes variables such as:

```text
current_business_user
current_user_roles
current_user_permissions
can_create_price_request
can_approve_price_request
can_reject_price_request
can_create_promotion
can_stop_store_promotion
can_stop_country_promotion
```

Templates use these variables to hide or display actions.

Examples:

| UI action              | Display rule                 |
| ---------------------- | ---------------------------- |
| New price request      | `can_create_price_request`   |
| Approve price request  | `can_approve_price_request`  |
| Reject price request   | `can_reject_price_request`   |
| New promotion          | `can_create_promotion`       |
| Stop store promotion   | `can_stop_store_promotion`   |
| Stop country promotion | `can_stop_country_promotion` |

The frontend also adapts some filters and form fields according to the user scope.

Examples:

* a store user has the country and store fields pre-filled and locked;
* a country user has the country field pre-filled and locked;
* filters that are no longer relevant for the current scope can be hidden.

This improves user experience, but does not replace backend security.

---

## 15. Audit and traceability

The RBAC implementation improves traceability by removing hardcoded user identifiers.

Before Sprint 8, some actions used fixed values such as:

```text
user_id = 1
```

After Sprint 8, the user is resolved dynamically.

### Price request creation

When a user creates a price change request:

```text
request.user.email
→ X-User-Email
→ user_account.id
→ price_change_request.requested_by_user_id
→ audit_log.performed_by_user_id
```

### Price approval and application

When a user approves a request:

```text
current business user
→ approve action
→ price_history.applied_by_user_id
→ audit_log.performed_by_user_id
```

### Promotion creation

When a user creates a promotion:

```text
current business user
→ promotion.created_by
```

The following tables provide traceability:

| Table                  | Traceability purpose            |
| ---------------------- | ------------------------------- |
| `price_change_request` | Who requested a price change    |
| `price_history`        | Who applied a price change      |
| `audit_log`            | Who performed a workflow action |
| `promotion`            | Who created a promotion         |

---

## 16. Seeded demo users

Demo users are created through reproducible seed scripts.

| Script                                           | Responsibility                                                   |
| ------------------------------------------------ | ---------------------------------------------------------------- |
| `frontend/scripts/seed_django_demo_users.py`     | Creates Django login users                                       |
| `backend/scripts/seed_business_demo_users.py`    | Creates business users and assigns roles                         |
| `backend/scripts/seed_rbac_roles_permissions.py` | Creates RBAC roles, permissions and role-permission associations |

The email address is the shared key between Django users and business users.

---

## 17. Security decisions

### Backend as source of truth

The backend is the only trusted layer for:

* permission checks;
* data scope checks;
* sensitive workflow actions;
* audit consistency.

### Frontend as UX layer

The frontend hides unavailable actions to improve usability.

However, hidden buttons are not considered security.

Every sensitive backend endpoint remains protected.

### Session-based MVP authentication

Django sessions are used for the frontend login.

The API receives the current user identity through the `X-User-Email` header.

This is acceptable for the MVP because the frontend and API are part of the same controlled local project architecture.

---

## 18. MVP limitations

The MVP does not include:

* JWT authentication;
* OAuth2 / OpenID Connect;
* refresh tokens;
* API token management;
* advanced group management;
* custom permissions assigned directly to users;
* multi-country users;
* multi-store users;
* a business admin role;
* a read-only viewer role;
* row-level security directly in PostgreSQL;
* production-grade API authentication between Django and FastAPI.

The `X-User-Email` header is a pragmatic MVP mechanism.

In a production version, it should be replaced by a stronger mechanism such as:

* signed JWT between frontend and backend;
* OAuth2 / OpenID Connect;
* shared identity provider;
* signed internal service token;
* stricter API gateway validation.

---

## 19. Definition of Done

This architecture is considered complete when:

* Django login/logout works;
* each demo user can authenticate;
* `/me` returns the correct roles, permissions and scope;
* backend endpoints block unauthorized actions;
* backend endpoints filter data according to scope;
* frontend actions are hidden according to permissions;
* audit and history tables reference the correct business user;
* MVP limitations are clearly documented.

---

## 20. Conclusion

Sprint 8 introduces a complete MVP authentication and authorization layer.

The implemented architecture provides:

* authenticated access to the Django frontend;
* business identity resolution in FastAPI;
* a normalized User → Role → Permission model;
* backend protection for sensitive actions;
* backend scope filtering for data visibility;
* frontend adaptation based on permissions;
* improved auditability and traceability.

The solution remains simple enough for a solo certification project while demonstrating professional security and governance practices.
