# Database Schema

## Tables

### users
- id
- email
- password_hash
- created_at

### products
- id
- user_id
- title
- category

### product_images
- id
- product_id
- image_url

### generated_listings
- id
- product_id
- title
- description
- seo_keywords

### generated_images
- id
- user_id
- source_product_image_id
- generated_image_url
- category
- prompt
- provider
- status
- created_at

### prompt_versions
- id
- prompt_name
- version
- content

### ai_usage_logs
- id
- model_name
- token_usage
- response_time

### exports
- id
- product_id
- export_type
