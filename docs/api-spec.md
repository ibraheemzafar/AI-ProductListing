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
