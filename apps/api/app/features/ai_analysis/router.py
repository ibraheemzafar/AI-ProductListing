from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rate_limit import enforce_ai_rate_limit
from app.features.ai_analysis.dependencies import get_ai_analysis_service
from app.features.ai_analysis.schemas import ProductAnalysisResponse
from app.features.ai_analysis.services import AiAnalysisService
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User

router = APIRouter(prefix="/products", tags=["ai-analysis"])


@router.get("/images/{image_id}/analyses", response_model=list[ProductAnalysisResponse])
async def list_product_image_analyses(
    image_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AiAnalysisService, Depends(get_ai_analysis_service)],
) -> list[ProductAnalysisResponse]:
    return await analysis_service.list_existing_analyses(
        user_id=current_user.id,
        image_id=image_id,
    )


@router.post("/images/{image_id}/analysis", response_model=ProductAnalysisResponse)
async def analyze_product_image(
    image_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AiAnalysisService, Depends(get_ai_analysis_service)],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> ProductAnalysisResponse:
    return await analysis_service.analyze_uploaded_image(
        user_id=current_user.id,
        image_id=image_id,
    )
