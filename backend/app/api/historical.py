from fastapi import APIRouter

router = APIRouter(
    prefix="/api/historical",
    tags=["Historical"]
)


@router.get("/")
def get_historical():
    return {
        "data": []
    }