from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.features.ai_analysis.router import router as ai_analysis_router
from app.features.auth.router import router as auth_router
from app.features.image_enhancement.router import router as image_enhancement_router
from app.features.lifestyle_generation.router import router as lifestyle_generation_router
from app.features.listing_exports.router import router as listing_exports_router
from app.features.listing_generation.router import router as listing_generation_router
from app.features.listing_improvement.router import router as listing_improvement_router
from app.features.marketplace_optimization.router import router as marketplace_optimization_router
from app.features.product_uploads.router import router as product_uploads_router
from app.features.seo_evaluation.router import router as seo_evaluation_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(product_uploads_router)
api_router.include_router(ai_analysis_router)
api_router.include_router(listing_generation_router)
api_router.include_router(listing_exports_router)
api_router.include_router(seo_evaluation_router)
api_router.include_router(listing_improvement_router)
api_router.include_router(marketplace_optimization_router)
api_router.include_router(image_enhancement_router)
api_router.include_router(lifestyle_generation_router)
api_router.include_router(health_router)
