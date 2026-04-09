from fastapi import APIRouter

router = APIRouter(tags=["Technical"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}