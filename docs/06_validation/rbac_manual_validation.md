# RBAC Manual Validation

## 1. Objective

This document describes the manual validation of the authentication, RBAC permissions and scope filtering implemented during Sprint 8 of the Pricing Control Tower project.

The objective is to verify that:

* users can authenticate through the Django frontend;
* each MVP role has the expected permissions;
* forbidden actions are hidden in the frontend;
* forbidden actions are blocked by the FastAPI backend;
* data visibility is restricted according to the user scope;
* audit and history tables keep the correct user traceability.

This validation is part of the Sprint 8 Definition of Done.

---

## 2. Scope of validation

The validation covers the following components:

| Component             | Validation                                                         |
| --------------------- | ------------------------------------------------------------------ |
| Django authentication | Login, logout, protected pages                                     |
| FastAPI identity      | `X-User-Email` header and `/me` endpoint                           |
| RBAC permissions      | Role-permission checks on sensitive actions                        |
| Backend authorization | `403 Forbidden` on unauthorized actions                            |
| Scope filtering       | Country/store filtering on read endpoints                          |
| Frontend adaptation   | Hidden buttons/actions according to permissions                    |
| Traceability          | `audit_log`, `price_history`, `created_by`, `requested_by_user_id` |

---

## 3. Test accounts

The following demonstration accounts are used for manual validation.

| Username           | Email                        | Role               | Scope                 |
| ------------------ | ---------------------------- | ------------------ | --------------------- |
| `analyst`          | `analyst@pct.local`          | `PRICING_ANALYST`  | Global                |
| `store_manager`    | `store.manager@pct.local`    | `STORE_MANAGER`    | France / Lille Centre |
| `store_director`   | `store.director@pct.local`   | `STORE_DIRECTOR`   | France / Lille Centre |
| `country_director` | `country.director@pct.local` | `COUNTRY_DIRECTOR` | France                |

Default password for local demo accounts:

```text
Password123!
```

The business scope used for the demo is:

| Entity  |  ID | Code / Name  |
| ------- | --: | ------------ |
| Country | `1` | France       |
| Store   | `1` | Lille Centre |

---

## 4. RBAC permission matrix

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

Note: `APPLY_PRICE_REQUEST` exists in the permission catalog but is not assigned to any MVP role. In the MVP workflow, approving a request automatically applies the price change.

---

## 5. Backend source of truth

The frontend only improves the user experience by hiding unavailable actions.

The backend remains the source of truth for:

* identifying the business user;
* checking active status;
* checking permissions;
* checking data scope;
* protecting sensitive endpoints;
* maintaining audit and price history.

The identity flow is:

```text
Django authenticated user
→ request.user.email
→ X-User-Email header
→ FastAPI
→ pct_core.user_account
→ user_role
→ role_permission
→ permission
```

---

## 6. Authentication validation

### 6.1 Login

| Test                                         | Expected result                | Status      |
| -------------------------------------------- | ------------------------------ | ----------- |
| Access `/dashboard/` without being logged in | Redirect to `/accounts/login/` | To validate |
| Login with `analyst`                         | Redirect to dashboard          | To validate |
| Login with `store_manager`                   | Redirect to dashboard          | To validate |
| Login with `store_director`                  | Redirect to dashboard          | To validate |
| Login with `country_director`                | Redirect to dashboard          | To validate |

### 6.2 Logout

| Test                              | Expected result        | Status      |
| --------------------------------- | ---------------------- | ----------- |
| Click logout                      | User is disconnected   | To validate |
| Access `/dashboard/` after logout | Redirect to login page | To validate |

---

## 7. `/me` endpoint validation

### 7.1 Analyst

Command:

```bash
curl -s "http://127.0.0.1:8000/me" \
  -H "X-User-Email: analyst@pct.local" | jq
```

Expected result:

```text
roles contains PRICING_ANALYST
permissions contains VIEW_ALL_ANOMALIES
country_id = null
store_id = null
```

Status: To validate

### 7.2 Store manager

Command:

```bash
curl -s "http://127.0.0.1:8000/me" \
  -H "X-User-Email: store.manager@pct.local" | jq
```

Expected result:

```text
roles contains STORE_MANAGER
permissions contains CREATE_PRICE_REQUEST
permissions does not contain APPROVE_PRICE_REQUEST
country_id = 1
store_id = 1
```

Status: To validate

### 7.3 Store director

Command:

```bash
curl -s "http://127.0.0.1:8000/me" \
  -H "X-User-Email: store.director@pct.local" | jq
```

Expected result:

```text
roles contains STORE_DIRECTOR
permissions contains APPROVE_PRICE_REQUEST
permissions contains REJECT_PRICE_REQUEST
country_id = 1
store_id = 1
```

Status: To validate

### 7.4 Country director

Command:

```bash
curl -s "http://127.0.0.1:8000/me" \
  -H "X-User-Email: country.director@pct.local" | jq
```

Expected result:

```text
roles contains COUNTRY_DIRECTOR
permissions contains CREATE_COUNTRY_PROMOTION
permissions contains STOP_COUNTRY_PROMOTION
country_id = 1
store_id = null
```

Status: To validate

---

## 8. Frontend RBAC validation

### 8.1 Pricing analyst

Login as:

```text
analyst / Password123!
```

Expected frontend behavior:

| UI element / action         | Expected result      | Status      |
| --------------------------- | -------------------- | ----------- |
| Dashboard visible           | Yes                  | To validate |
| Prices visible              | Yes                  | To validate |
| Promotions visible          | Yes                  | To validate |
| Anomalies visible           | Yes                  | To validate |
| Price history visible       | Yes                  | To validate |
| Button “Nouvelle demande”   | Hidden               | To validate |
| Price request creation form | Hidden / unavailable | To validate |
| Approve / reject buttons    | Hidden               | To validate |
| Button “Nouvelle promotion” | Hidden               | To validate |
| Stop promotion action       | Hidden               | To validate |

### 8.2 Store manager

Login as:

```text
store_manager / Password123!
```

Expected frontend behavior:

| UI element / action         | Expected result                       | Status      |
| --------------------------- | ------------------------------------- | ----------- |
| Button “Nouvelle demande”   | Visible                               | To validate |
| Price request creation form | Visible                               | To validate |
| Country field               | Pre-filled and locked to France       | To validate |
| Store field                 | Pre-filled and locked to Lille Centre | To validate |
| Approve / reject buttons    | Hidden                                | To validate |
| Button “Nouvelle promotion” | Visible                               | To validate |
| Store promotion creation    | Available                             | To validate |
| Country promotion creation  | Not available / blocked               | To validate |
| Stop store promotion        | Available                             | To validate |
| Stop country promotion      | Hidden / unavailable                  | To validate |

### 8.3 Store director

Login as:

```text
store_director / Password123!
```

Expected frontend behavior:

| UI element / action         | Expected result                       | Status      |
| --------------------------- | ------------------------------------- | ----------- |
| Button “Nouvelle demande”   | Visible                               | To validate |
| Price request creation form | Visible                               | To validate |
| Country field               | Pre-filled and locked to France       | To validate |
| Store field                 | Pre-filled and locked to Lille Centre | To validate |
| Approve button              | Visible on pending requests           | To validate |
| Reject button               | Visible on pending requests           | To validate |
| Button “Nouvelle promotion” | Visible                               | To validate |
| Stop store promotion        | Available                             | To validate |
| Stop country promotion      | Hidden / unavailable                  | To validate |

### 8.4 Country director

Login as:

```text
country_director / Password123!
```

Expected frontend behavior:

| UI element / action         | Expected result                 | Status      |
| --------------------------- | ------------------------------- | ----------- |
| Button “Nouvelle demande”   | Visible                         | To validate |
| Price request creation form | Visible                         | To validate |
| Country field               | Pre-filled and locked to France | To validate |
| Store field                 | Limited to stores from France   | To validate |
| Approve button              | Visible on pending requests     | To validate |
| Reject button               | Visible on pending requests     | To validate |
| Button “Nouvelle promotion” | Visible                         | To validate |
| Country promotion creation  | Available                       | To validate |
| Store promotion creation    | Not available / blocked         | To validate |
| Stop country promotion      | Available                       | To validate |
| Stop store promotion        | Hidden / unavailable            | To validate |

---

## 9. Backend permission validation

These tests verify that the backend blocks unauthorized actions even if the frontend is bypassed.

### 9.1 Analyst cannot create price request

Command:

```bash
curl -i -X POST "http://127.0.0.1:8000/price-change-requests" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: analyst@pct.local" \
  -d '{
    "product_id": 31,
    "country_id": 1,
    "store_id": 1,
    "requested_price_amount": "19.99",
    "justification": "RBAC validation test.",
    "requested_effective_date": "2027-01-01"
  }'
```

Expected result:

```text
HTTP/1.1 403 Forbidden
Permission denied: CREATE_PRICE_REQUEST is required
```

Status: To validate

### 9.2 Store manager can create price request

Command:

```bash
curl -i -X POST "http://127.0.0.1:8000/price-change-requests" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: store.manager@pct.local" \
  -d '{
    "product_id": 31,
    "country_id": 1,
    "store_id": 1,
    "requested_price_amount": "21.99",
    "justification": "RBAC validation test from store manager.",
    "requested_effective_date": "2027-01-01"
  }'
```

Expected result:

```text
HTTP/1.1 201 Created
requested_by_user_id belongs to store.manager@pct.local
```

Status: To validate

### 9.3 Store manager cannot approve

Command:

```bash
curl -i -X POST "http://127.0.0.1:8000/price-change-requests/<REQUEST_ID>/approve" \
  -H "X-User-Email: store.manager@pct.local"
```

Expected result:

```text
HTTP/1.1 403 Forbidden
Permission denied: APPROVE_PRICE_REQUEST is required
```

Status: To validate

### 9.4 Store director can approve

Command:

```bash
curl -i -X POST "http://127.0.0.1:8000/price-change-requests/<REQUEST_ID>/approve" \
  -H "X-User-Email: store.director@pct.local"
```

Expected result:

```text
HTTP/1.1 200 OK
Price request status is updated
price_history.applied_by_user_id belongs to store.director@pct.local
audit_log.performed_by_user_id belongs to store.director@pct.local
```

Status: To validate

### 9.5 Store manager cannot create country promotion

Command:

```bash
curl -i -X POST "http://127.0.0.1:8000/promotions" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: store.manager@pct.local" \
  -d '{
    "code": "RBAC-COUNTRY-PROMO-BLOCKED",
    "name": "RBAC country promo blocked",
    "description": "RBAC validation test.",
    "discount_type": "PERCENTAGE",
    "discount_value": "10.00",
    "product_id": 31,
    "start_date": "2027-01-01",
    "end_date": "2027-01-31",
    "country_id": 1,
    "store_id": null
  }'
```

Expected result:

```text
HTTP/1.1 403 Forbidden
Permission denied: CREATE_COUNTRY_PROMOTION is required
```

Status: To validate

### 9.6 Country director can create country promotion

Command:

```bash
curl -i -X POST "http://127.0.0.1:8000/promotions" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: country.director@pct.local" \
  -d '{
    "code": "RBAC-COUNTRY-PROMO-OK",
    "name": "RBAC country promo allowed",
    "description": "RBAC validation test.",
    "discount_type": "PERCENTAGE",
    "discount_value": "10.00",
    "product_id": 31,
    "start_date": "2027-01-01",
    "end_date": "2027-01-31",
    "country_id": 1,
    "store_id": null
  }'
```

Expected result:

```text
HTTP/1.1 201 Created
created_by belongs to country.director@pct.local
```

Status: To validate

---

## 10. Backend scope validation

These tests verify that the backend automatically filters data according to the user scope.

### 10.1 Store manager scope

User:

```text
store.manager@pct.local
```

| API call                                | Expected result | Status      |
| --------------------------------------- | --------------- | ----------- |
| `GET /prices?store_id=1`                | `200 OK`        | To validate |
| `GET /prices?store_id=2`                | `403 Forbidden` | To validate |
| `GET /kpis?store_id=1`                  | `200 OK`        | To validate |
| `GET /kpis?store_id=2`                  | `403 Forbidden` | To validate |
| `GET /price-change-requests?store_id=1` | `200 OK`        | To validate |
| `GET /price-change-requests?store_id=2` | `403 Forbidden` | To validate |

Commands:

```bash
curl -i "http://127.0.0.1:8000/prices?store_id=1" \
  -H "X-User-Email: store.manager@pct.local"

curl -i "http://127.0.0.1:8000/prices?store_id=2" \
  -H "X-User-Email: store.manager@pct.local"

curl -i "http://127.0.0.1:8000/kpis?store_id=1" \
  -H "X-User-Email: store.manager@pct.local"

curl -i "http://127.0.0.1:8000/kpis?store_id=2" \
  -H "X-User-Email: store.manager@pct.local"
```

### 10.2 Country director scope

User:

```text
country.director@pct.local
```

| API call                       | Expected result | Status      |
| ------------------------------ | --------------- | ----------- |
| `GET /promotions?country_id=1` | `200 OK`        | To validate |
| `GET /promotions?country_id=2` | `403 Forbidden` | To validate |
| `GET /prices?country_id=1`     | `200 OK`        | To validate |
| `GET /prices?country_id=2`     | `403 Forbidden` | To validate |

Commands:

```bash
curl -i "http://127.0.0.1:8000/promotions?country_id=1" \
  -H "X-User-Email: country.director@pct.local"

curl -i "http://127.0.0.1:8000/promotions?country_id=2" \
  -H "X-User-Email: country.director@pct.local"
```

### 10.3 Global analyst scope

User:

```text
analyst@pct.local
```

| API call          | Expected result       | Status      |
| ----------------- | --------------------- | ----------- |
| `GET /prices`     | `200 OK`, global data | To validate |
| `GET /promotions` | `200 OK`, global data | To validate |
| `GET /kpis`       | `200 OK`, global data | To validate |
| `GET /anomalies`  | `200 OK`, global data | To validate |

Commands:

```bash
curl -i "http://127.0.0.1:8000/prices" \
  -H "X-User-Email: analyst@pct.local"

curl -i "http://127.0.0.1:8000/promotions" \
  -H "X-User-Email: analyst@pct.local"
```

---

## 11. Traceability validation

### 11.1 Price request creation

SQL query:

```sql
SELECT
    pcr.id,
    pcr.requested_by_user_id,
    u.email,
    pcr.status,
    pcr.created_at
FROM pct_core.price_change_request pcr
JOIN pct_core.user_account u ON u.id = pcr.requested_by_user_id
ORDER BY pcr.id DESC
LIMIT 5;
```

Expected result:

```text
The latest request created by store_manager must reference store.manager@pct.local.
```

Status: To validate

### 11.2 Price application

SQL query:

```sql
SELECT
    ph.history_id,
    ph.price_change_request_id,
    ph.applied_by_user_id,
    u.email,
    ph.applied_at
FROM pct_core.price_history ph
JOIN pct_core.user_account u ON u.id = ph.applied_by_user_id
ORDER BY ph.history_id DESC
LIMIT 5;
```

Expected result:

```text
The latest applied price change must reference store.director@pct.local or country.director@pct.local depending on the approver.
```

Status: To validate

### 11.3 Audit log

SQL query:

```sql
SELECT
    al.audit_id,
    al.price_change_request_id,
    al.action_type,
    al.performed_by_user_id,
    u.email,
    al.created_at
FROM pct_core.audit_log al
JOIN pct_core.user_account u ON u.id = al.performed_by_user_id
ORDER BY al.audit_id DESC
LIMIT 10;
```

Expected result:

```text
REQUEST_CREATED must reference the creator.
PRICE_APPLIED must reference the approver.
REQUEST_REJECTED must reference the rejecting user.
```

Status: To validate

### 11.4 Promotion creation

SQL query:

```sql
SELECT
    p.id,
    p.code,
    p.created_by,
    u.email,
    p.created_at
FROM pct_core.promotion p
JOIN pct_core.user_account u ON u.id = p.created_by
ORDER BY p.id DESC
LIMIT 5;
```

Expected result:

```text
The latest promotion must reference the connected business user in created_by.
```

Status: To validate

---

## 12. Validation results summary

| Validation area            | Result      |
| -------------------------- | ----------- |
| Login/logout               | To validate |
| `/me` endpoint             | To validate |
| Analyst role               | To validate |
| Store manager role         | To validate |
| Store director role        | To validate |
| Country director role      | To validate |
| Backend permissions        | To validate |
| Backend scope filtering    | To validate |
| Frontend action visibility | To validate |
| Audit trail                | To validate |

---

## 13. Known MVP limitations

The Sprint 8 RBAC implementation intentionally remains MVP-oriented.

Known limitations:

* no advanced group management;
* no custom permission assignment per user;
* no multi-country user scope;
* no multi-store user scope;
* no business admin role in the MVP;
* frontend visibility is an UX improvement only, not a security layer;
* backend authorization remains mandatory for all sensitive actions;
* `APPLY_PRICE_REQUEST` exists in the catalog but is not directly assigned to a user role.

---

## 14. Conclusion

The RBAC manual validation is complete when:

* all four demonstration users have been tested;
* frontend actions match the permissions returned by `/me`;
* backend endpoints reject unauthorized actions with `403 Forbidden`;
* scope filters prevent access outside the user country/store;
* authorized actions remain functional;
* audit and history tables reference the correct business user.

Final result:

```text
OK
```
