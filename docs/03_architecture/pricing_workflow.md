# Pricing Workflow — Functional & Technical Documentation

## Objective

Ensure functional and technical traceability of the price change workflow.

---

## 1. Workflow Statuses

A price change request (`PriceChangeRequest`) can have the following statuses:

| Status     | Description                                      |
|------------|--------------------------------------------------|
| PENDING    | Request created, awaiting approval or rejection  |
| APPROVED   | Request approved, new price applied              |
| REJECTED   | Request rejected, no price change                |

---

## 2. Lifecycle of a Price Change Request

1. **Creation**: A user submits a price change request (status: PENDING).
2. **Approval**: An authorized user approves the request (status: APPROVED). The new price is applied, and a `PriceHistory` entry is created.
3. **Rejection**: An authorized user rejects the request (status: REJECTED). The reason and user are recorded.

State transitions:

- PENDING → APPROVED (via approval endpoint)
- PENDING → REJECTED (via rejection endpoint)

A request cannot be approved or rejected twice.

---

## 3. Endpoints

- `POST /price-change-requests` — Create a new price change request
- `GET /price-change-requests` — List all requests (with filters)
- `POST /price-change-requests/{id}/approve` — Approve and apply a request
- `POST /price-change-requests/{id}/reject` — Reject a request with a reason
- `GET /price-history` — List all price change history entries

See [API Design](../03_architecture/api_design.md) for details on request/response formats.

---

## 4. Application Rules for a New Price

- Only requests with status `PENDING` can be approved or rejected.
- Approval applies the new price (creates a new `Price` row, updates status to `APPROVED`).
- Rejection records the reason, user, and timestamp (status to `REJECTED`).
- All actions are logged in the `audit_log` table for traceability.
- A `PriceHistory` entry is created only on approval.

---

## 5. Historization Logic

- Every approved price change creates a `PriceHistory` entry:
    - Links to the `price_change_request` (one-to-one)
    - Stores previous and new price IDs and amounts
    - Records who applied the change and when
- The history is immutable and auditable.

---

## 6. MVP Choices & Future Evolutions

### MVP Choices
- No modification or cancellation after approval/rejection
- No multi-step validation (single approval)
- No scheduled future application (applies immediately)
- Only admin users can approve/reject

### Future Evolutions
- Multi-level approval workflow
- Scheduled price changes (effective date in future)
- Notification system (email, UI alerts)
- Bulk approval/rejection
- Enhanced audit trail (with more context)

---

## Acceptance Criteria

- The workflow is understandable without reading the code
- Statuses are documented
- Endpoints are listed
- Historization logic is explained
- MVP limitations are explicit
