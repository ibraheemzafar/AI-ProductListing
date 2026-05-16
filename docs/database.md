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
