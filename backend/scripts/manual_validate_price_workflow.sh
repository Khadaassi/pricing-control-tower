#!/bin/bash

set -e

API_BASE_URL="http://127.0.0.1:8000"
DB_NAME="pct"
DB_USER="pct_user"
DB_CONTAINER="pct-postgres"

PRODUCT_ID=31
COUNTRY_ID=5
STORE_ID=null
REQUESTED_BY_USER_ID=1
APPROVED_BY_USER_ID=1
REJECTED_BY_USER_ID=1

APPROVAL_PRICE_AMOUNT="24.99"
APPROVAL_EFFECTIVE_DATE="2027-03-01"

REJECTION_PRICE_AMOUNT="26.99"
REJECTION_EFFECTIVE_DATE="2027-04-01"

echo "=================================================="
echo "T83 - Manual validation of price change workflow"
echo "=================================================="
echo ""

echo "Checking API health..."
curl -s "${API_BASE_URL}/health"
echo ""
echo ""

echo "=================================================="
echo "Scenario A - Approval workflow"
echo "=================================================="

echo "Creating a valid price change request for approval..."

APPROVAL_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/price-change-requests" \
  -H "Content-Type: application/json" \
  -d "{
    \"product_id\": ${PRODUCT_ID},
    \"country_id\": ${COUNTRY_ID},
    \"store_id\": ${STORE_ID},
    \"requested_price_amount\": \"${APPROVAL_PRICE_AMOUNT}\",
    \"justification\": \"Manual validation of approval workflow.\",
    \"requested_effective_date\": \"${APPROVAL_EFFECTIVE_DATE}\",
    \"requested_by_user_id\": ${REQUESTED_BY_USER_ID}
  }")

echo "Creation response:"
echo "${APPROVAL_RESPONSE}"
echo ""

APPROVAL_REQUEST_ID=$(echo "${APPROVAL_RESPONSE}" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
APPROVAL_CURRENT_PRICE_ID=$(echo "${APPROVAL_RESPONSE}" | python -c "import sys, json; print(json.load(sys.stdin)['current_price_id'])")

echo "Approval request ID: ${APPROVAL_REQUEST_ID}"
echo "Approval current price ID: ${APPROVAL_CURRENT_PRICE_ID}"
echo ""

echo "Checking initial PENDING status..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    id,
    status,
    current_price_id,
    old_price_amount,
    requested_price_amount,
    requested_effective_date
from pct_core.price_change_request
where id = ${APPROVAL_REQUEST_ID};
"

echo "Approving the request..."

APPROVE_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/price-change-requests/${APPROVAL_REQUEST_ID}/approve" \
  -H "Content-Type: application/json" \
  -d "{
    \"approved_by_user_id\": ${APPROVED_BY_USER_ID}
  }")

echo "Approve response:"
echo "${APPROVE_RESPONSE}"
echo ""

echo "Checking APPLIED status..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    id,
    status,
    current_price_id,
    old_price_amount,
    requested_price_amount,
    requested_effective_date
from pct_core.price_change_request
where id = ${APPROVAL_REQUEST_ID};
"

echo "Checking price_history..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    history_id,
    price_change_request_id,
    previous_price_id,
    new_price_id,
    old_price_amount,
    new_price_amount,
    applied_by_user_id,
    applied_at
from pct_core.price_history
where price_change_request_id = ${APPROVAL_REQUEST_ID};
"

echo "Checking old and new prices..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    id,
    product_id,
    country_id,
    store_id,
    price_scope,
    amount,
    effective_from,
    effective_to,
    status
from pct_core.price
where id in (
    select previous_price_id
    from pct_core.price_history
    where price_change_request_id = ${APPROVAL_REQUEST_ID}
    union
    select new_price_id
    from pct_core.price_history
    where price_change_request_id = ${APPROVAL_REQUEST_ID}
)
order by effective_from;
"

echo "Checking audit_log for approval workflow..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    audit_id,
    price_change_request_id,
    action_type,
    performed_by_user_id,
    description,
    created_at
from pct_core.audit_log
where price_change_request_id = ${APPROVAL_REQUEST_ID}
order by created_at;
"

echo "Checking price-history API endpoint..."
curl -s "${API_BASE_URL}/price-history?price_change_request_id=${APPROVAL_REQUEST_ID}"
echo ""
echo ""

echo "Testing invalid transition: approve an already APPLIED request..."

INVALID_APPROVE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${API_BASE_URL}/price-change-requests/${APPROVAL_REQUEST_ID}/approve" \
  -H "Content-Type: application/json" \
  -d "{
    \"approved_by_user_id\": ${APPROVED_BY_USER_ID}
  }")

echo "${INVALID_APPROVE_RESPONSE}"
echo ""

echo "=================================================="
echo "Scenario B - Rejection workflow"
echo "=================================================="

echo "Creating a valid price change request for rejection..."

REJECTION_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/price-change-requests" \
  -H "Content-Type: application/json" \
  -d "{
    \"product_id\": ${PRODUCT_ID},
    \"country_id\": ${COUNTRY_ID},
    \"store_id\": ${STORE_ID},
    \"requested_price_amount\": \"${REJECTION_PRICE_AMOUNT}\",
    \"justification\": \"Manual validation of rejection workflow.\",
    \"requested_effective_date\": \"${REJECTION_EFFECTIVE_DATE}\",
    \"requested_by_user_id\": ${REQUESTED_BY_USER_ID}
  }")

echo "Creation response:"
echo "${REJECTION_RESPONSE}"
echo ""

REJECT_REQUEST_ID=$(echo "${REJECTION_RESPONSE}" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
REJECT_CURRENT_PRICE_ID=$(echo "${REJECTION_RESPONSE}" | python -c "import sys, json; print(json.load(sys.stdin)['current_price_id'])")

echo "Reject request ID: ${REJECT_REQUEST_ID}"
echo "Reject current price ID: ${REJECT_CURRENT_PRICE_ID}"
echo ""

echo "Checking price before rejection..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    id,
    product_id,
    country_id,
    store_id,
    price_scope,
    amount,
    effective_from,
    effective_to,
    status
from pct_core.price
where id = ${REJECT_CURRENT_PRICE_ID};
"

echo "Rejecting the request..."

REJECT_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/price-change-requests/${REJECT_REQUEST_ID}/reject" \
  -H "Content-Type: application/json" \
  -d "{
    \"rejected_by_user_id\": ${REJECTED_BY_USER_ID},
    \"reason\": \"Requested price is not aligned with the pricing strategy.\"
  }")

echo "Reject response:"
echo "${REJECT_RESPONSE}"
echo ""

echo "Checking REJECTED status and rejection fields..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    id,
    status,
    rejection_reason,
    rejected_by_user_id,
    rejected_at
from pct_core.price_change_request
where id = ${REJECT_REQUEST_ID};
"

echo "Checking price after rejection. It must be unchanged..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    id,
    product_id,
    country_id,
    store_id,
    price_scope,
    amount,
    effective_from,
    effective_to,
    status
from pct_core.price
where id = ${REJECT_CURRENT_PRICE_ID};
"

echo "Checking that no price_history was created for rejected request..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select *
from pct_core.price_history
where price_change_request_id = ${REJECT_REQUEST_ID};
"

echo "Checking audit_log for rejection workflow..."
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
select
    audit_id,
    price_change_request_id,
    action_type,
    performed_by_user_id,
    description,
    created_at
from pct_core.audit_log
where price_change_request_id = ${REJECT_REQUEST_ID}
order by created_at;
"

echo "Testing invalid transition: reject an already REJECTED request..."

INVALID_REJECT_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${API_BASE_URL}/price-change-requests/${REJECT_REQUEST_ID}/reject" \
  -H "Content-Type: application/json" \
  -d "{
    \"rejected_by_user_id\": ${REJECTED_BY_USER_ID},
    \"reason\": \"Second rejection attempt.\"
  }")

echo "${INVALID_REJECT_RESPONSE}"
echo ""

echo "=================================================="
echo "T83 validation completed"
echo "=================================================="
echo ""
echo "Expected validation points:"
echo "- Approval request is created with PENDING status."
echo "- Approval endpoint changes status to APPLIED."
echo "- Previous price is closed."
echo "- New price is created."
echo "- price_history contains before/after values."
echo "- audit_log contains REQUEST_CREATED and PRICE_APPLIED."
echo "- Rejection request is created with PENDING status."
echo "- Reject endpoint changes status to REJECTED."
echo "- Rejection reason is stored."
echo "- No price_history is created for rejected request."
echo "- Price is unchanged after rejection."
echo "- audit_log contains REQUEST_CREATED and REQUEST_REJECTED."
echo "- Invalid transitions return 409 Conflict."