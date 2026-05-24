from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.features.ai_analysis.dependencies import get_ai_analysis_service
from app.features.ai_analysis.models import ProductAnalysisResult
from app.features.ai_analysis.schemas import ProductAnalysisResponse, ProductAttributes
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.main import create_app


class FakeAiAnalysisService:
    async def analyze_uploaded_image(
        self,
        user_id: str,
        image_id: str,
    ) -> ProductAnalysisResponse:
        assert user_id == "user-1"
        return ProductAnalysisResponse.from_model(
            ProductAnalysisResult(
                id="analysis-1",
                product_id="product-1",
                image_id=image_id,
                category="Home",
                product_type="Mug",
                color="White",
                material="Ceramic",
                style="Modern",
                visible_text_brand="ACME",
                target_audience="Coffee drinkers",
                raw_attributes=ProductAttributes(
                    category="Home",
                    product_type="Mug",
                    color="White",
                    material="Ceramic",
                    style="Modern",
                    visible_text_brand="ACME",
                    target_audience="Coffee drinkers",
                ).model_dump(),
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
    app.dependency_overrides[get_ai_analysis_service] = lambda: FakeAiAnalysisService()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_analyze_product_image_returns_structured_attributes(client: TestClient) -> None:
    response = client.post("/api/v1/products/images/image-1/analysis")

    assert response.status_code == 200
    payload = response.json()
    assert payload["image_id"] == "image-1"
    assert payload["attributes"]["product_type"] == "Mug"
    assert payload["attributes"]["visible_text_brand"] == "ACME"
