# Product Uploads Feature

This feature owns the MVP image upload workflow.

Boundaries:

- Routers translate multipart requests and JSON responses only.
- Services validate files, generate storage names, call storage, and coordinate persistence.
- Repositories own PostgreSQL writes and reads.
- Storage is accessed through `app.shared.storage.StorageProvider` so local disk can later be
  replaced with AWS S3 without changing upload orchestration.

AI analysis and listing generation must not be added here.

