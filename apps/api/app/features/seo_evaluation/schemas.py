from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.features.seo_evaluation.models import SeoAnalysis


class SeoEvaluationContent(BaseModel):
    seo_score: int = Field(ge=0, le=100)
    readability_score: int = Field(ge=0, le=100)
    keyword_optimization_feedback: str = Field(min_length=1, max_length=1000)
    title_quality_feedback: str = Field(min_length=1, max_length=1000)
    description_quality_feedback: str = Field(min_length=1, max_length=1000)
    strengths: list[str] = Field(min_length=1, max_length=10)
    weaknesses: list[str] = Field(min_length=1, max_length=10)
    improvement_suggestions: list[str] = Field(min_length=1, max_length=10)

    @field_validator("strengths", "weaknesses", "improvement_suggestions")
    @classmethod
    def validate_non_empty_values(cls, values: list[str]) -> list[str]:
        cleaned_values = [value.strip() for value in values if value.strip()]
        if not cleaned_values:
            msg = "At least one non-empty value is required"
            raise ValueError(msg)
        return cleaned_values


class SeoAnalysisResponse(BaseModel):
    id: str
    listing_id: str
    product_id: str
    analysis: SeoEvaluationContent
    created_at: datetime

    @classmethod
    def from_model(cls, analysis: SeoAnalysis) -> "SeoAnalysisResponse":
        return cls(
            id=analysis.id,
            listing_id=analysis.listing_id,
            product_id=analysis.product_id,
            analysis=SeoEvaluationContent(
                seo_score=analysis.seo_score,
                readability_score=analysis.readability_score,
                keyword_optimization_feedback=analysis.keyword_optimization_feedback,
                title_quality_feedback=analysis.title_quality_feedback,
                description_quality_feedback=analysis.description_quality_feedback,
                strengths=analysis.strengths,
                weaknesses=analysis.weaknesses,
                improvement_suggestions=analysis.improvement_suggestions,
            ),
            created_at=analysis.created_at,
        )
