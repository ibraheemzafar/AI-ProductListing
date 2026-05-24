from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rate_limit import enforce_ai_rate_limit
from app.features.ai_analysis.dependencies import get_ai_analysis_service
from app.features.ai_analysis.schemas import ProductAnalysisResponse
from app.features.ai_analysis.services import AiAnalysisService
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User

router = APIRouter(
    prefix="/products",
    tags=["ai-analysis"],
    dependencies=[Depends(enforce_ai_rate_limit)],
)


@router.post("/images/{image_id}/analysis", response_model=ProductAnalysisResponse)
async def analyze_product_image(
    image_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AiAnalysisService, Depends(get_ai_analysis_service)],
) -> ProductAnalysisResponse:
    return await analysis_service.analyze_uploaded_image(
        user_id=current_user.id,
        image_id=image_id,
    )
