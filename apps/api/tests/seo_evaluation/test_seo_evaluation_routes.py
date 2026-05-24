from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.seo_evaluation.dependencies import get_seo_evaluation_service
from app.features.seo_evaluation.models import SeoAnalysis
from app.features.seo_evaluation.schemas import SeoAnalysisResponse
from app.main import create_app


class FakeSeoEvaluationService:
    async def analyze_listing_seo(
        self,
        user_id: str,
        listing_id: str,
    ) -> SeoAnalysisResponse:
        assert user_id == "user-1"
        return SeoAnalysisResponse.from_model(
            SeoAnalysis(
                id="seo-analysis-1",
                listing_id=listing_id,
                product_id="product-1",
                seo_score=84,
                readability_score=91,
                keyword_optimization_feedback="Keywords are relevant.",
                title_quality_feedback="Title is clear.",
                description_quality_feedback="Description is readable.",
                strengths=["Clear title"],
                weaknesses=["Could add more keyword variety"],
                improvement_suggestions=["Add a buyer intent keyword"],
                raw_output={},
                created_at=datetime.now(UTC),
            ),
        )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1",
        email="seller@example.com",
        name="Test Seller",
        avatar_url=None,
        password_hash="hash",
    )
    app.dependency_overrides[get_seo_evaluation_service] = lambda: FakeSeoEvaluationService()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_analyze_listing_seo_returns_scores_and_suggestions(client: TestClient) -> None:
    response = client.post("/api/v1/products/listings/listing-1/seo-analysis")

    assert response.status_code == 200
    payload = response.json()
    assert payload["listing_id"] == "listing-1"
    assert payload["analysis"]["seo_score"] == 84
    assert payload["analysis"]["readability_score"] == 91
    assert payload["analysis"]["improvement_suggestions"] == ["Add a buyer intent keyword"]
