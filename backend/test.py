from app.db import SessionLocal
from app.services.price_change_request_service import reject_price_change_request

REQUEST_ID = 10
REJECTED_BY_USER_ID = 1

db = SessionLocal()

try:
    request = reject_price_change_request(
        db=db,
        price_change_request_id=REQUEST_ID,
        rejected_by_user_id=REJECTED_BY_USER_ID,
        reason="Requested price increase is not aligned with current pricing strategy.",
    )

    print(request.id)
    print(request.status)
    print(request.rejection_reason)
    print(request.rejected_by_user_id)
    print(request.rejected_at)

finally:
    db.close()
