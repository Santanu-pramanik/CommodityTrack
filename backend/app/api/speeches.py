from fastapi import APIRouter

router = APIRouter(prefix="/api/speeches", tags=["Speeches"])


@router.get("/")
def get_speeches():
    return {
        "speeches": []
    }