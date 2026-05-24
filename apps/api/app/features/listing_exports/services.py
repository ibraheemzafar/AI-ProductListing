import csv
from html import escape
from io import StringIO

from app.core.errors import AppError, NotFoundError
from app.features.listing_exports.repositories import ListingExportRepository
from app.features.listing_exports.schemas import ListingCsvExport, ListingJsonExportResponse

SHOPIFY_CSV_HEADERS = [
    "Title",
    "Body (HTML)",
    "Tags",
    "Image Src",
    "SEO Title",
    "SEO Description",
]


class ListingExportService:
    def __init__(self, repository: ListingExportRepository) -> None:
        self._repository = repository

    async def export_listing_as_json(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingJsonExportResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        row = await self._repository.get_listing_export_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if row is None:
            raise NotFoundError("Generated listing was not found")

        listing, analysis, image = row
        return ListingJsonExportResponse.from_models(
            listing=listing,
            analysis=analysis,
            product_image_url=image.image_url,
        )

    async def export_listing_as_shopify_csv(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingCsvExport:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        row = await self._repository.get_listing_export_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if row is None:
            raise NotFoundError("Generated listing was not found")

        listing, _analysis, image = row
        return ListingCsvExport(
            filename=f"{listing.id}-shopify.csv",
            content=self._build_shopify_csv(
                title=listing.title,
                body_html=self._build_body_html(listing.long_description),
                tags=", ".join(listing.product_tags),
                image_src=image.image_url,
                seo_title=listing.title,
                seo_description=listing.short_description,
            ),
        )

    def _build_shopify_csv(
        self,
        title: str,
        body_html: str,
        tags: str,
        image_src: str,
        seo_title: str,
        seo_description: str,
    ) -> str:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=SHOPIFY_CSV_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(
            {
                "Title": title,
                "Body (HTML)": body_html,
                "Tags": tags,
                "Image Src": image_src,
                "SEO Title": seo_title,
                "SEO Description": seo_description,
            },
        )
        return output.getvalue()

    def _build_body_html(self, long_description: str) -> str:
        paragraphs = [
            f"<p>{escape(paragraph.strip())}</p>"
            for paragraph in long_description.splitlines()
            if paragraph.strip()
        ]
        if paragraphs:
            return "".join(paragraphs)
        return f"<p>{escape(long_description)}</p>"
