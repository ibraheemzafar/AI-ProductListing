from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rate_limit import enforce_ai_rate_limit
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.seo_evaluation.dependencies import get_seo_evaluation_service
from app.features.seo_evaluation.schemas import SeoAnalysisResponse
from app.features.seo_evaluation.services import SeoEvaluationService

router = APIRouter(prefix="/products", tags=["seo-evaluation"])


@router.post("/listings/{listing_id}/seo-analysis", response_model=SeoAnalysisResponse)
async def analyze_listing_seo(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    seo_service: Annotated[SeoEvaluationService, Depends(get_seo_evaluation_service)],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> SeoAnalysisResponse:
    return await seo_service.analyze_listing_seo(
        user_id=current_user.id,
        listing_id=listing_id,
    )
