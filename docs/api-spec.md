# API Specification

## POST /api/listings/generate

### Request
{
  "images": []
}

### Response
{
  "title": "",
  "short_description": "",
  "long_description": "",
  "tags": []
}

---

## POST /api/images/enhance

### Request
{
  "image_url": ""
}

### Response
{
  "enhanced_image_url": ""
}

---

## POST /api/v1/products/listings/{listing_id}/generated-images

### Request
{
  "category": "marketplace_hero_image",
  "custom_prompt": null
}

### Response
{
  "id": "",
  "generated_image_url": "",
  "category": "",
  "status": ""
}

---

## GET /api/v1/products/listings/{listing_id}/generated-images

Lists generated images owned by the current user.

---

## GET /api/v1/products/listings/{listing_id}/generated-images/{image_id}/download

Downloads a generated image owned by the current user.

---

## DELETE /api/v1/products/listings/{listing_id}/generated-images/{image_id}

Deletes a generated image record and attempts to remove the storage file.
