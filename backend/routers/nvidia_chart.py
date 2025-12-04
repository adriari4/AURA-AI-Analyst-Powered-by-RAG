from fastapi import APIRouter
from backend.thesis_logic import get_nvidia_chart

router = APIRouter(prefix="/thesis/nvidia", tags=["NVIDIA Chart"])

@router.get("/chart")
async def thesis_chart():
    return get_nvidia_chart()
